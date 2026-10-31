"""Read-only forensics of newly downloaded YOLO datasets against everything we already own.

    python -I tools/new_data_forensics.py --out review/new_data_r2b

For every new image: integrity, label parse (bbox / polygon / OBB -> bbox), source-class counts,
SHA-256, dHash of all 8 flip/rotation variants (Roboflow augmentations are flips and 90-degree
rotations) and pHash. Each image is compared with
  * every image of road_hazards_v3a_r2 (train / val / test), dHash + pHash computed here;
  * the owned raw sets in review/new_data/hashes.jsonl (SHA-256 + dHash only);
  * the other new images (exact and dihedral near-duplicates -> within-new groups).
Writes per-image CSV, groups, summary.json and sample sheets. Never modifies inputs.
"""
import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.dedup import UnionFind  # noqa: E402
from gp36data.hashing import dhash, phash  # noqa: E402
from gp36data.io_utils import inspect_image, pair_images_labels  # noqa: E402
from gp36data.labels import parse_label_file  # noqa: E402
from gp36data.manifest import sha256_file  # noqa: E402
from gp36data.overlay import contact_sheet, draw_boxes, tile  # noqa: E402

RAW3 = Path(r"C:\Users\ahmed\Desktop\GP36_Dataset\raw_v3")
NEW_SETS = {  # set id -> (folder, source class names)
    "sub5": ("roboflow_speed_unmarked_bumb_v5", ["Manhole", "Open Manhole", "Pothole", "Speed Bump", "Unmarked Bump"]),
    "qub1": ("roboflow_qassim_unmarked_bumps_v1", ["Manhole", "Pothole", "Unmarked Bump"]),
    "qub2": ("roboflow_qassim_unmarked_bumps2_v1", ["Manhole", "Pothole", "Unmarked Bump"]),
    "qubo": ("roboflow_qu_bumps_v1_obb", ["Manhole", "Pothole", "Speed Bump", "Unmarked Bump"]),
}
COLORS = {"Manhole": (160, 160, 160), "Open Manhole": (255, 140, 0), "Pothole": (255, 40, 40),
          "Speed Bump": (30, 144, 255), "Unmarked Bump": (0, 230, 230)}
DIHEDRAL = [None, Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_90, Image.ROTATE_180,
            Image.ROTATE_270, Image.TRANSPOSE, Image.TRANSVERSE]


def popcount(a):
    return np.bitwise_count(a).astype(np.int64)


def load_small(path, target=256):
    """Decode (JPEG draft mode for big files: identical treatment for all reference images)."""
    im = Image.open(path)
    if im.format == "JPEG" and max(im.size) > 2 * target:
        im.draft("RGB", (target, target))
    im.load()
    return im.convert("RGB")


def scan_new():
    rows = []
    for sid, (folder, names) in NEW_SETS.items():
        root = RAW3 / folder
        for split in ("train", "valid", "test"):
            if not (root / split / "images").exists():
                continue
            pairs, no_lbl, orphans = pair_images_labels(root / split / "images", root / split / "labels")
            for p in no_lbl:
                rows.append({"set": sid, "split": split, "file": p.name, "problem": "image_without_label"})
            for p in orphans:
                rows.append({"set": sid, "split": split, "file": p.name, "problem": "label_without_image"})
            for img, lbl in pairs:
                info = inspect_image(img)
                r = {"set": sid, "split": split, "file": img.name, "image": str(img), "label": str(lbl),
                     "ok": info["ok"], "w": info["width"], "h": info["height"], "problem": "" if info["ok"] else info["error"]}
                boxes, issues = parse_label_file(lbl)
                r["label_errors"] = ";".join(sorted({i.code for i in issues if i.severity == "error"}))
                r["boxes"] = [(b.cls, b.xc, b.yc, b.w, b.h) for b in boxes]
                r["n_obb_or_poly"] = sum(1 for b in boxes if b.kind == "poly")
                cnt = Counter(names[b.cls] if b.cls < len(names) else f"BAD{b.cls}" for b in boxes)
                for n in names:
                    r[f"n_{n}"] = cnt.get(n, 0)
                r["bad_class"] = sum(v for k, v in cnt.items() if k.startswith("BAD"))
                if info["ok"]:
                    r["sha"] = sha256_file(img)
                    with Image.open(img) as im:
                        im = im.convert("RGB")
                        r["dh8"] = [dhash(im if t is None else im.transpose(t)) for t in DIHEDRAL]
                        r["ph"] = phash(im)
                    # largest box side relative to image: oversized boxes are a known Qassim problem
                    r["max_box_area"] = max((b.w * b.h for b in boxes), default=0.0)
                rows.append(r)
    return rows


def scan_r2(r2_root):
    refs = []
    with open(r2_root / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            p = r2_root / m["out_image"]
            im = load_small(p)
            refs.append({"ref": f"r2:{m['split']}:{m['sample_id']}", "split": m["split"], "sha": m["out_sha256"],
                         "orig_sha": m["orig_sha256"], "dh": dhash(im), "ph": phash(im)})
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--r2", default="road_hazards_v3a_r2")
    ap.add_argument("--owned", default="review/new_data/hashes.jsonl")
    ap.add_argument("--dh", type=int, default=4)
    ap.add_argument("--ph", type=int, default=10)
    ap.add_argument("--dh-loose", type=int, default=8, help="conservative screen used against r2 val/test")
    ap.add_argument("--samples", type=int, default=32)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")

    print("scanning new sets ...", flush=True)
    rows = scan_new()
    new = [r for r in rows if r.get("ok")]
    print(len(new), "readable new images; scanning r2 ...", flush=True)
    refs = scan_r2(Path(args.r2))
    owned = [json.loads(l) for l in open(args.owned, encoding="utf-8")]
    print(len(refs), "r2 images,", len(owned), "owned raw hashes", flush=True)

    R_dh = np.array([r["dh"] for r in refs], dtype=np.uint64)
    R_ph = np.array([r["ph"] for r in refs], dtype=np.uint64)
    R_split = np.array([r["split"] for r in refs])
    O_dh = np.array([o["dh"] for o in owned], dtype=np.uint64)
    O_set = np.array([o["p"].split(":")[0] for o in owned])
    sha_r2 = defaultdict(list)
    for r in refs:
        sha_r2[r["sha"]].append(r["split"])
        sha_r2[r["orig_sha"]].append(r["split"])
    sha_owned = defaultdict(set)
    for o in owned:
        sha_owned[o["sha"]].add(o["p"].split(":")[0])

    for r in new:
        d8 = np.array(r["dh8"], dtype=np.uint64)
        # min over the 8 variants of this image vs each reference
        dr = np.min(np.stack([popcount(np.bitwise_xor(R_dh, v)) for v in d8]), axis=0)
        pr = popcount(np.bitwise_xor(R_ph, np.uint64(r["ph"])))
        do = np.min(np.stack([popcount(np.bitwise_xor(O_dh, v)) for v in d8]), axis=0)
        r["exact_r2"] = ";".join(sorted(set(sha_r2.get(r["sha"], []))))
        r["exact_owned"] = ";".join(sorted(sha_owned.get(r["sha"], set())))
        strict = (dr <= args.dh) & (pr <= args.ph)
        for s in ("train", "val", "test"):
            m = R_split == s
            r[f"min_dh_r2_{s}"] = int(dr[m].min()) if m.any() else -1
            r[f"near_r2_{s}"] = int((strict & m).sum())
            r[f"loose_r2_{s}"] = int(((dr <= args.dh_loose) & m).sum())
        near_o = do <= args.dh
        r["near_owned"] = ";".join(f"{k}:{v}" for k, v in sorted(Counter(O_set[near_o]).items()))
        r["min_dh_owned"] = int(do.min())

    # within-new groups: exact or dihedral near-duplicate (dHash only; pHash is not rotation-invariant)
    uf = UnionFind(len(new))
    by_sha = defaultdict(list)
    for i, r in enumerate(new):
        by_sha[r["sha"]].append(i)
    for idx in by_sha.values():
        for j in idx[1:]:
            uf.union(idx[0], j)
    D0 = np.array([r["dh8"][0] for r in new], dtype=np.uint64)
    for i, r in enumerate(new):
        d8 = np.array(r["dh8"], dtype=np.uint64)
        dmin = np.min(np.stack([popcount(np.bitwise_xor(D0[i + 1:], v)) for v in d8]), axis=0)
        for j in np.nonzero(dmin <= args.dh)[0]:
            uf.union(i, i + 1 + int(j))
    groups = defaultdict(list)
    for i, r in enumerate(new):
        r["group"] = uf.find(i)
        groups[r["group"]].append(i)
    for r in new:
        g = groups[r["group"]]
        r["group_size"] = len(g)
        r["group_sets"] = ";".join(sorted({new[k]["set"] for k in g}))

    out.mkdir(parents=True)
    names_all = sorted({n for _, ns in NEW_SETS.values() for n in ns})
    cols = ["set", "split", "file", "ok", "problem", "w", "h", "label_errors", "bad_class", "n_obb_or_poly"] + \
           [f"n_{n}" for n in names_all] + ["max_box_area", "sha", "exact_r2", "exact_owned",
           "min_dh_r2_train", "min_dh_r2_val", "min_dh_r2_test", "near_r2_train", "near_r2_val", "near_r2_test",
           "loose_r2_train", "loose_r2_val", "loose_r2_test", "near_owned", "min_dh_owned", "group", "group_size",
           "group_sets", "image", "label"]
    with open(out / "new_images.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summ = {"thresholds": {"dh": args.dh, "ph": args.ph, "dh_loose_vs_r2": args.dh_loose,
                           "note": "dHash = min over 8 flip/rotation variants of the new image; owned refs have no pHash"},
            "r2_images": len(refs), "owned_hashes": len(owned), "sets": {}}
    for sid, (_, names) in NEW_SETS.items():
        S = [r for r in rows if r["set"] == sid]
        ok = [r for r in S if r.get("ok")]
        summ["sets"][sid] = {
            "images": len(S), "readable": len(ok), "problems": Counter(r["problem"] for r in S if r["problem"]),
            "label_error_images": sum(1 for r in ok if r["label_errors"]),
            "bad_class_boxes": sum(r["bad_class"] for r in ok),
            "boxes_by_class": {n: sum(r[f"n_{n}"] for r in ok) for n in names},
            "images_with_class": {n: sum(1 for r in ok if r[f"n_{n}"]) for n in names},
            "empty_label_images": sum(1 for r in ok if not r["boxes"]),
            "sizes": Counter(f"{r['w']}x{r['h']}" for r in ok).most_common(3),
            "exact_dup_r2": sum(1 for r in ok if r["exact_r2"]),
            "exact_dup_owned": Counter(r["exact_owned"] for r in ok if r["exact_owned"]),
            "near_r2_train": sum(1 for r in ok if r["near_r2_train"]),
            "near_r2_val": sum(1 for r in ok if r["near_r2_val"]),
            "near_r2_test": sum(1 for r in ok if r["near_r2_test"]),
            "loose_r2_valtest": sum(1 for r in ok if r["loose_r2_val"] or r["loose_r2_test"]),
            "near_owned_any": sum(1 for r in ok if r["near_owned"]),
            "near_owned_by_set": Counter(k.split(":")[0] for r in ok for k in r["near_owned"].split(";") if k),
            "within_new_groups": len({r["group"] for r in ok}),
            "groups_shared_with_other_new_sets": sum(1 for g in {r["group"] for r in ok}
                                                     if len({new[k]["set"] for k in groups[g]}) > 1),
            "max_box_area_gt_0.5": sum(1 for r in ok if r["max_box_area"] > 0.5),
        }
    (out / "summary.json").write_text(json.dumps(summ, indent=1, default=dict), encoding="utf-8")

    rng = random.Random(0)
    (out / "sheets").mkdir()
    for sid, (_, names) in NEW_SETS.items():
        ok = [r for r in new if r["set"] == sid]
        pick = rng.sample(ok, min(args.samples, len(ok)))
        tiles = []
        for r in pick:
            with Image.open(r["image"]) as im:
                img = draw_boxes(im, r["boxes"], class_colors={i: COLORS[n] for i, n in enumerate(names)})
            cnt = ",".join(f"{n[:6]}:{r['n_' + n]}" for n in names if r[f"n_{n}"])
            tiles.append(tile(img, [f"{sid}/{r['file'][:44]}", cnt or "EMPTY",
                                    f"r2 min dh tr/va/te {r['min_dh_r2_train']}/{r['min_dh_r2_val']}/{r['min_dh_r2_test']} grp{r['group_size']}"],
                              width=400))
        contact_sheet(tiles, cols=4, title=f"{sid} random {len(pick)} (seed 0) | grey Manhole, orange Open Manhole, red Pothole, blue Speed Bump, cyan Unmarked Bump").save(
            out / "sheets" / f"{sid}_random.jpg", quality=85)
    print(json.dumps(summ, indent=1, default=dict))


if __name__ == "__main__":
    main()
