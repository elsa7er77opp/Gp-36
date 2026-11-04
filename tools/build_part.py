"""Build one curated, versioned data PART (a small YOLO dataset of its own) from an items CSV.

    python -I tools/build_part.py --items <items.csv> --part <name> --out parts_r3/<name> [--far-tiny 0.02]

items.csv columns: image, label, class_map (JSON {src_id: "pothole"|"speed_bump"|"ignore"}), group, part_split
(train|val|test), meta (free text, e.g. condition or family; copied to the manifest for subset reports).

Per image:
1. integrity (decodes; EXIF orientation must be absent or 1, otherwise the image is skipped and logged);
2. labels parsed; every source id must be in class_map (else hard error); ignore-ids are removed
   (the object stays in the picture as background, rules D5/D6);
3. FAR_TINY: hazard boxes with sqrt(w*h) < --far-tiny (normalised) are removed. An image whose hazard boxes
   were ALL removed this way is dropped (it is neither a clean positive nor a clean negative);
4. leakage guard vs the frozen internal dataset (--internal, default road_hazards_v3a_r2, ALL splits):
   exact SHA-256, or dHash <= 4 and pHash <= 10 under the same flip/rotation -> image dropped and logged;
5. inside the part: a train image that is a near-duplicate of a val/test image of the part is dropped.
Output: <out>/images/<split>, labels/<split>, data.yaml, manifest.csv (r2-compatible columns + part, meta,
group_id), checksums.sha256, build_info.json, drop_log.csv. Built in <out>.building, renamed at the end.
"""
import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gp36data.hashing import dhash, phash  # noqa: E402
from gp36data.labels import Box, format_label, has_errors, parse_label_file  # noqa: E402
from gp36data.manifest import sha256_file  # noqa: E402
from new_data_forensics import DIHEDRAL, load_small  # noqa: E402

TARGET = {"pothole": 0, "speed_bump": 1}


def internal_hashes(internal, cache):
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        return z["d"], z["p"], set(z["sha"].tolist()), z["sid"].tolist()
    D, P, S, sid = [], [], set(), []
    with open(internal / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            im = load_small(internal / m["out_image"])
            D.append(dhash(im))
            P.append(phash(im))
            S |= {m["out_sha256"], m["orig_sha256"]}
            sid.append(f"{m['split']}:{m['sample_id']}")
    D, P = np.array(D, dtype=np.uint64), np.array(P, dtype=np.uint64)
    np.savez(cache, d=D, p=P, sha=np.array(sorted(S)), sid=np.array(sid))
    return D, P, S, sid


def guard_hashes(specs):
    """Extra evaluation sets to protect: 'dir' (all images under dir/images) or 'dir:val,test' (those splits)."""
    D, P, S, sid = [], [], set(), []
    for spec in specs:
        d, _, sp = spec.rpartition(":")
        if not d or not all(s in ("train", "val", "test") for s in sp.split(",")):
            d, sp = spec, ""  # no split suffix (a Windows drive colon, e.g. C:\..., is not one)
        roots = [Path(d) / "images" / s for s in sp.split(",")] if sp else [Path(d) / "images"]
        for r in roots:
            for f in sorted(r.rglob("*")):
                if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    im = load_small(f)
                    D.append(dhash(im))
                    P.append(phash(im))
                    S.add(sha256_file(f))
                    sid.append(f"guard:{d}/{f.relative_to(d).as_posix()}")
    return np.array(D, dtype=np.uint64), np.array(P, dtype=np.uint64), S, sid


def hashes8(path):
    with Image.open(path) as im:
        im.draft("RGB", (512, 512))
        im = im.convert("RGB")
        tr = [im if t is None else im.transpose(t) for t in DIHEDRAL]
        return (np.array([dhash(x) for x in tr], dtype=np.uint64), np.array([phash(x) for x in tr], dtype=np.uint64))


def near8(d8, p8, D, P):
    """Bool per reference image: dHash <= 4 AND pHash <= 10 under the SAME one of the 8 flips/rotations.
    (Before 2026-11-04 the pHash was compared unrotated only, which missed flipped copies.)"""
    dd = np.stack([np.bitwise_count(np.bitwise_xor(D, v)) for v in d8])
    pp = np.stack([np.bitwise_count(np.bitwise_xor(P, v)) for v in p8])
    return ((dd <= 4) & (pp <= 10)).any(axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--internal", default="road_hazards_v3a_r2")
    ap.add_argument("--hash-cache", default="review/new_data_r3/r2_hashes.npz")
    ap.add_argument("--far-tiny", type=float, default=0.02)
    ap.add_argument("--guard", nargs="*", default=[],
                    help="extra eval sets to keep leak-free, e.g. external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    items = list(csv.DictReader(open(args.items, newline="", encoding="utf-8")))
    RD, RP, RS, rsid = internal_hashes(Path(args.internal), Path(args.hash_cache))
    if args.guard:
        GD, GP, GS, gsid = guard_hashes(args.guard)
        RD, RP, RS, rsid = np.concatenate([RD, GD]), np.concatenate([RP, GP]), RS | GS, list(rsid) + gsid

    keep, drops, stats = [], [], Counter()
    for it in items:
        img, lbl = Path(it["image"]), Path(it["label"])
        cmap = {int(k): v for k, v in json.loads(it["class_map"]).items()}
        try:
            with Image.open(img) as im:
                im.verify()
            with Image.open(img) as im:
                W, H = im.size
                orient = im.getexif().get(274, 1)
        except Exception as e:  # noqa: BLE001
            drops.append((it["image"], "unreadable", str(e)))
            continue
        if orient not in (1, None):
            drops.append((it["image"], "exif_rotation", str(orient)))
            continue
        boxes, issues = parse_label_file(lbl) if lbl.exists() else ([], [])
        if has_errors(issues):
            drops.append((it["image"], "label_error", ";".join(i.code for i in issues)))
            continue
        unknown = {b.cls for b in boxes} - set(cmap)
        if unknown:
            sys.exit(f"{lbl}: source class ids {unknown} not in class_map {cmap}")
        hz = [Box(TARGET[cmap[b.cls]], b.xc, b.yc, b.w, b.h) for b in boxes if cmap[b.cls] != "ignore"]
        n_ign = len(boxes) - len(hz)
        kept = [b for b in hz if (b.w * b.h) ** 0.5 >= args.far_tiny]
        if hz and not kept:
            drops.append((it["image"], "only_far_tiny", str(len(hz))))
            continue
        stats["far_tiny_boxes_removed"] += len(hz) - len(kept)
        stats["ignored_boxes_removed"] += n_ign
        sha = sha256_file(img)
        if sha in RS:
            drops.append((it["image"], "exact_dup_internal", ""))
            continue
        d8, p8 = hashes8(img)
        hit = np.nonzero(near8(d8, p8, RD, RP))[0]
        if len(hit):
            drops.append((it["image"], "near_dup_internal", rsid[hit[0]]))
            continue
        keep.append({**it, "W": W, "H": H, "sha": sha, "boxes": kept, "d8": d8, "p8": p8, "ph": p8[0]})

    # within-part: train vs held-out near-duplicates -> drop the train copy
    held = [k for k in keep if k["part_split"] != "train"]
    if held:
        HD = np.array([k["d8"][0] for k in held], dtype=np.uint64)
        HP = np.array([k["ph"] for k in held], dtype=np.uint64)
        k2 = []
        for k in keep:
            if k["part_split"] == "train":
                if np.any(near8(k["d8"], k["p8"], HD, HP)):
                    drops.append((k["image"], "near_dup_part_heldout", ""))
                    continue
            k2.append(k)
        keep = k2
    shas = Counter(k["sha"] for k in keep)
    dupl = {s for s, n in shas.items() if n > 1}
    if dupl:
        seen, k2 = set(), []
        for k in keep:
            if k["sha"] in seen:
                drops.append((k["image"], "exact_dup_in_part", ""))
                continue
            seen.add(k["sha"])
            k2.append(k)
        keep = k2

    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    rows = []
    for k in sorted(keep, key=lambda x: x["sha"]):
        sp = k["part_split"]
        (tmp / "images" / sp).mkdir(parents=True, exist_ok=True)
        (tmp / "labels" / sp).mkdir(parents=True, exist_ok=True)
        stem = f"{args.part}__{k['sha'][:16]}"
        dst = tmp / "images" / sp / f"{stem}{Path(k['image']).suffix.lower()}"
        shutil.copyfile(k["image"], dst)
        (tmp / "labels" / sp / f"{stem}.txt").write_text(format_label(k["boxes"]), encoding="utf-8")
        rows.append({"sample_id": f"{args.part}/{Path(k['image']).name}", "source": args.part, "split": sp,
                     "orig_image": k["image"], "orig_label": k["label"], "orig_sha256": k["sha"],
                     "out_image": dst.relative_to(tmp).as_posix(), "out_sha256": k["sha"], "out_w": k["W"], "out_h": k["H"],
                     "n_pothole": sum(b.cls == 0 for b in k["boxes"]), "n_speed_bump": sum(b.cls == 1 for b in k["boxes"]),
                     "group_id": k["group"], "part": args.part, "meta": k.get("meta", "")})
    for sp in ("train", "val", "test"):
        (tmp / "images" / sp).mkdir(parents=True, exist_ok=True)
        (tmp / "labels" / sp).mkdir(parents=True, exist_ok=True)
    (tmp / "data.yaml").write_text("train: images/train\nval: images/val\ntest: images/test\nnames:\n  0: pothole\n  1: speed_bump\n",
                                   encoding="utf-8")
    fields = ["sample_id", "source", "split", "orig_image", "orig_label", "orig_sha256", "out_image", "out_sha256",
              "out_w", "out_h", "n_pothole", "n_speed_bump", "group_id", "part", "meta"]
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(tmp / "drop_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "reason", "detail"])
        w.writerows(drops)
    lines = [f"{sha256_file(p)}  {p.relative_to(tmp).as_posix()}" for p in sorted(tmp.rglob("*")) if p.is_file()]
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summ = {sp: {"images": sum(r["split"] == sp for r in rows),
                 "negatives": sum(r["split"] == sp and r["n_pothole"] + r["n_speed_bump"] == 0 for r in rows),
                 "pothole_boxes": sum(r["n_pothole"] for r in rows if r["split"] == sp),
                 "speed_bump_boxes": sum(r["n_speed_bump"] for r in rows if r["split"] == sp),
                 "groups": len({r["group_id"] for r in rows if r["split"] == sp})} for sp in ("train", "val", "test")}
    info = {"part": args.part, "items": args.items, "n_items": len(items), "kept": len(rows),
            "drops": dict(Counter(d[1] for d in drops)), **stats, "far_tiny_threshold": args.far_tiny,
            "leakage_guard": f"exact + dHash<=4 & pHash<=10 under the same one of 8 flips/rotations (rule v2, 2026-11-04) vs {args.internal} (all splits)"
                             + (f" + {args.guard}" if args.guard else ""), "splits": summ}
    (tmp / "build_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    os.rename(tmp, out)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
