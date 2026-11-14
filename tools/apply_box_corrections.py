"""Apply a box audit (remove / keep, never resize) to a BUILT part and write a NEW part folder.

    python -I tools/apply_box_corrections.py --part parts_r3/egy --audit review/new_data_r3/vet/egy/box_audit.csv \
        --out parts_r3/egy_v2

box_audit.csv columns (one row per audited box of the ORIGINAL source label file):
  file          source image file name (= basename of manifest `orig_image`)
  label_sha256  SHA-256 of the original label file (manifest `orig_label`); checked before anything is applied
  line          0-based line index in that original label file
  class_id      source class id on that line (checked)
  verdict       keep | remove_manhole | remove_not_pothole | remove_bad_box | uncertain
  note          free text
Policy: remove_* -> box removed in every split; uncertain -> kept in train, removed in val/test; keep -> kept.
The box in the part label is found by its coordinates (build_part.py writes them with 6 decimals), so class
re-mapping and ignored classes in between do not matter. Every audit row must match exactly one part box,
otherwise nothing is written (hard error). Images are never dropped: an image whose hazard boxes are all removed
stays as a negative (the removed objects are background by D5). Old part folder is never modified.
--drop-images <csv> (column `file`): those images are removed from val/test (a visible but unlabelled hazard
would turn a correct detection into a false positive); a train image in the list is kept and logged.
Output: <out>/images, labels, data.yaml, manifest.csv (same columns, counts updated), checksums.sha256,
build_info.json (source part, audit sha256, counts per split and reason), change_log.csv (every change).
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

REMOVE = {"remove_manhole", "remove_not_pothole", "remove_bad_box"}
VERDICTS = REMOVE | {"keep", "uncertain"}


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def coords(line):
    p = line.split()
    return tuple(float(x) for x in p[1:5])


def same(a, b, tol=2e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def link_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--drop-images", help="CSV with column `file` (source image name): these images are removed "
                    "from val/test only (e.g. visible but unlabelled hazards); train images are never dropped")
    ap.add_argument("--orig-root", help="replace the directory of manifest orig_label paths (if the raw data moved)")
    a = ap.parse_args(argv)
    part, out = Path(a.part), Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    man = list(csv.DictReader(open(part / "manifest.csv", newline="", encoding="utf-8")))
    by_file = defaultdict(list)
    for m in man:
        by_file[Path(m["orig_image"]).name].append(m)
    audit = list(csv.DictReader(open(a.audit, newline="", encoding="utf-8")))
    errors, plan = [], defaultdict(list)  # out_image -> [(part_line_idx, verdict, note, audit_row)]
    orig_cache = {}
    for r in audit:
        if r["verdict"] not in VERDICTS:
            errors.append(f"{r['file']}:{r['line']}: unknown verdict {r['verdict']}")
            continue
        ms = by_file.get(r["file"], [])
        if len(ms) != 1:
            # not in the part (e.g. dropped by the leak guard or FAR_TINY) -> recorded, not an error
            plan[None].append((None, r["verdict"], "file not in part" if not ms else "file name not unique", r))
            continue
        m = ms[0]
        ol = Path(m["orig_label"])
        if a.orig_root:
            ol = Path(a.orig_root) / ol.name
        if ol not in orig_cache:
            if not ol.exists():
                errors.append(f"{r['file']}: original label {ol} not found")
                continue
            orig_cache[ol] = (sha256(ol), ol.read_text(encoding="utf-8").splitlines())
        osha, olines = orig_cache[ol]
        if osha != r["label_sha256"]:
            errors.append(f"{r['file']}: label_sha256 mismatch (audit {r['label_sha256'][:12]}, file {osha[:12]})")
            continue
        li = int(r["line"])
        if li >= len(olines) or olines[li].split()[:1] != [r["class_id"]]:
            errors.append(f"{r['file']}:{li}: class_id {r['class_id']} not on that line")
            continue
        c = coords(olines[li])
        plines = (part / "labels" / m["split"] / (Path(m["out_image"]).stem + ".txt")).read_text(encoding="utf-8").splitlines()
        hits = [k for k, pl in enumerate(plines) if pl.strip() and same(coords(pl), c)]
        if len(hits) > 1:
            errors.append(f"{r['file']}:{li}: {len(hits)} matching boxes in the part label (need 1)")
            continue
        if not hits:  # removed by the build already (ignore class or FAR_TINY): logged, nothing to do
            plan[None].append((None, r["verdict"], "box not in part label (removed at build)", r))
            continue
        plan[m["out_image"]].append((hits[0], r["verdict"], r.get("note", ""), r))
    if errors:
        sys.exit("NOTHING WRITTEN, audit does not match the part:\n  " + "\n  ".join(errors[:50]) +
                 (f"\n  ... {len(errors) - 50} more" if len(errors) > 50 else ""))

    drop_imgs = set()
    if a.drop_images:
        drop_imgs = {r["file"] for r in csv.DictReader(open(a.drop_images, newline="", encoding="utf-8"))}
        unknown = drop_imgs - set(by_file)
        if unknown:
            sys.exit(f"--drop-images: files not in the part: {sorted(unknown)[:5]}")
    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    log, counts, rows = [], defaultdict(Counter), []
    dropped = []
    for m in man:
        sp = m["split"]
        if Path(m["orig_image"]).name in drop_imgs:
            if sp in ("val", "test"):
                dropped.append(m["out_image"])
                counts[sp]["images_dropped"] += 1
                log.append({"out_image": m["out_image"], "split": sp, "orig_file": Path(m["orig_image"]).name,
                            "orig_line": "", "part_line": "", "verdict": "drop_image", "action": "image removed",
                            "note": "listed in --drop-images"})
                continue
            log.append({"out_image": m["out_image"], "split": sp, "orig_file": Path(m["orig_image"]).name,
                        "orig_line": "", "part_line": "", "verdict": "drop_image", "action": "kept (train is never dropped)",
                        "note": "listed in --drop-images"})
        (tmp / "images" / sp).mkdir(parents=True, exist_ok=True)
        (tmp / "labels" / sp).mkdir(parents=True, exist_ok=True)
        src_img = part / m["out_image"]
        link_or_copy(src_img, tmp / m["out_image"])
        stem = Path(m["out_image"]).stem
        plines = [ln for ln in (part / "labels" / sp / f"{stem}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
        drop = set()
        for k, verdict, note, r in plan.get(m["out_image"], []):
            act = "remove" if verdict in REMOVE or (verdict == "uncertain" and sp != "train") else "keep"
            counts[sp][f"{verdict}:{act}"] += 1
            if act == "remove":
                drop.add(k)
            log.append({"out_image": m["out_image"], "split": sp, "orig_file": r["file"], "orig_line": r["line"],
                        "part_line": k, "verdict": verdict, "action": act, "note": note})
        new = [ln for k, ln in enumerate(plines) if k not in drop]
        (tmp / "labels" / sp / f"{stem}.txt").write_text("".join(ln + "\n" for ln in new), encoding="utf-8")
        nm = dict(m)
        nm["n_pothole"] = sum(ln.split()[0] == "0" for ln in new)
        nm["n_speed_bump"] = sum(ln.split()[0] == "1" for ln in new)
        nm["part"] = out.name
        rows.append(nm)
        if plines and not new:
            counts[sp]["images_now_negative"] += 1
    for _, verdict, note, r in plan.get(None, []):
        log.append({"out_image": "", "split": "", "orig_file": r["file"], "orig_line": r["line"], "part_line": "",
                    "verdict": verdict, "action": note, "note": r.get("note", "")})
    shutil.copyfile(part / "data.yaml", tmp / "data.yaml")
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(man[0]))
        w.writeheader()
        w.writerows(rows)
    with open(tmp / "change_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["out_image", "split", "orig_file", "orig_line", "part_line", "verdict", "action", "note"])
        w.writeheader()
        w.writerows(log)
    summ = {sp: {"images": sum(r["split"] == sp for r in rows),
                 "negatives": sum(r["split"] == sp and int(r["n_pothole"]) + int(r["n_speed_bump"]) == 0 for r in rows),
                 "pothole_boxes": sum(int(r["n_pothole"]) for r in rows if r["split"] == sp),
                 "speed_bump_boxes": sum(int(r["n_speed_bump"]) for r in rows if r["split"] == sp),
                 "changes": dict(counts[sp])} for sp in ("train", "val", "test")}
    lines = [f"{sha256(p)}  {p.relative_to(tmp).as_posix()}" for p in sorted(tmp.rglob("*")) if p.is_file()]
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    info = {"part": out.name, "source_part": str(part), "source_build_info_sha256": sha256(part / "build_info.json")
            if (part / "build_info.json").exists() else None, "audit": str(a.audit), "audit_sha256": sha256(a.audit),
            "policy": "remove_* removed in all splits; uncertain kept in train, removed in val/test; boxes never resized",
            "audit_rows": len(audit), "audit_rows_not_in_part": len(plan.get(None, [])),
            "drop_images": str(a.drop_images) if a.drop_images else None,
            "drop_images_sha256": sha256(a.drop_images) if a.drop_images else None,
            "images_dropped_valtest": sorted(dropped), "splits": summ}
    (tmp / "build_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    os.rename(tmp, out)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
