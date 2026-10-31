"""Build road_hazards_v3a_r2 = road_hazards_v3a_r1 + the label corrections in review/clean_r2/corrections.csv.

Same images, same split. Images are copied byte-for-byte; only label files change, and only where a
correction row says so. r1 is read-only here; the output goes to a NEW folder (never overwritten),
built in a temp folder, strictly verified, then renamed.

    python tools/build_v3a_r2.py --dry-run            # print what would change, write nothing
    python tools/build_v3a_r2.py                       # build (test split untouched)
    python tools/build_v3a_r2.py --drop-test-image     # also apply the test-set DROP (owner approval needed)

Actions (box index = 0-based line number in the r1 label file):
  DROP_IMAGE                image (and label) left out
  REMOVE_BOX i              line i removed
  REMOVE_UNMATCHED_POTHOLE  pothole lines no v1 prediction overlaps (IoU<0.1, conf>=0.05) removed
                            (same rule that raised the flag in rank_label_errors.py)
  RECLASS_TO_SPEED_BUMP     pothole lines with a v1 speed_bump prediction (conf>=0.4, IoU>=0.5) -> class 1
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gp36data.manifest import sha256_file  # noqa: E402
from gp36data.verify import verify_dataset  # noqa: E402

SRC = ROOT / "road_hazards_v3a_r1"
DST = ROOT / "road_hazards_v3a_r2"
CORR = ROOT / "review" / "clean_r2" / "corrections.csv"
PRED = ROOT / "runs" / "detect" / "runs" / "clean"
R1_FP = "19747b58ad0393c11cf5722052cb960bb8279ec8aa0d7512830ca8d70126878d"


def boxes(path, with_conf):
    out = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").split("\n"):
            t = line.split()
            if t:
                c, x, y, w, h = int(t[0]), *map(float, t[1:5])
                out.append((c, x - w / 2, y - h / 2, x + w / 2, y + h / 2, float(t[5]) if with_conf else 1.0, line))
    return out


def iou(a, b):
    ix = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    iy = max(0.0, min(a[4], b[4]) - max(a[2], b[2]))
    inter = ix * iy
    u = (a[3] - a[1]) * (a[4] - a[2]) + (b[3] - b[1]) * (b[4] - b[2]) - inter
    return inter / u if u > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--drop-test-image", action="store_true")
    a = ap.parse_args()

    info = json.loads((SRC / "build_info.json").read_text())
    if info["fingerprint_sha256"] != R1_FP:
        sys.exit(f"r1 fingerprint changed ({info['fingerprint_sha256']}); refusing to build")
    man = list(csv.DictReader(open(SRC / "manifest.csv", encoding="utf-8")))
    ops = defaultdict(list)
    for r in csv.DictReader(open(CORR, encoding="utf-8")):
        if r["action"] == "KEEP":
            continue
        if r["split"] == "test" and not a.drop_test_image:
            continue
        ops[r["out_image"]].append(r)
    known = {m["out_image"] for m in man}
    missing = [k for k in ops if k not in known]
    if missing:
        sys.exit(f"corrections name images not in r1: {missing[:5]}")

    tally, new_labels, dropped, changes = Counter(), {}, set(), {}
    for m in man:
        img = m["out_image"]
        if img not in ops:
            continue
        split, stem = m["split"], Path(img).stem
        acts = ops[img]
        if any(r["action"] == "DROP_IMAGE" for r in acts):
            dropped.add(img)
            tally[(split, "images_dropped")] += 1
            changes[img] = "DROP_IMAGE:" + ";".join(r["reason"] for r in acts if r["action"] == "DROP_IMAGE")
            continue
        gt = boxes(SRC / "labels" / split / f"{stem}.txt", False)
        pr = boxes(PRED / f"pred_{split}_r1" / "labels" / f"{stem}.txt", True)
        remove, reclass, notes = set(), set(), []
        for r in acts:
            if r["action"] == "REMOVE_BOX":
                i = int(r["box"])
                if not 0 <= i < len(gt):
                    sys.exit(f"{img}: box {i} out of range ({len(gt)} boxes)")
                remove.add(i)
            elif r["action"] == "REMOVE_UNMATCHED_POTHOLE":
                hit = {i for i, g in enumerate(gt) if g[0] == 0 and max((iou(g, p) for p in pr), default=0.0) < 0.1}
                if not hit:
                    sys.exit(f"{img}: REMOVE_UNMATCHED_POTHOLE matched no box")
                remove |= hit
            elif r["action"] == "RECLASS_TO_SPEED_BUMP":
                hit = {i for i, g in enumerate(gt) if g[0] == 0 and any(
                    p[0] == 1 and p[5] >= 0.4 and iou(g, p) >= 0.5 for p in pr)}
                if not hit:
                    sys.exit(f"{img}: RECLASS_TO_SPEED_BUMP matched no box")
                reclass |= hit
            else:
                sys.exit(f"{img}: unknown action {r['action']}")
            notes.append(f"{r['action']}:{r['box']}:{r['reason']}")
        reclass -= remove
        lines = []
        for i, g in enumerate(gt):
            if i in remove:
                tally[(split, f"boxes_removed_{'pothole' if g[0] == 0 else 'speed_bump'}")] += 1
                continue
            if i in reclass:
                tally[(split, "boxes_reclassed_to_speed_bump")] += 1
                lines.append("1 " + g[6].split(maxsplit=1)[1])
            else:
                lines.append(g[6])
        new_labels[img] = lines
        if not lines:
            tally[(split, "images_now_background")] += 1
        changes[img] = " ".join(notes)

    for k in sorted(tally):
        print(k, tally[k])
    for s in ("train", "val", "test"):
        n = sum(1 for m in man if m["split"] == s and m["out_image"] not in dropped)
        print(f"{s}: {n} images after build")
    if a.dry_run:
        print("dry run: nothing written")
        return

    if DST.exists():
        sys.exit(f"{DST} exists; versions are never overwritten")
    tmp = DST.parent / f".{DST.name}.building"
    if tmp.exists():
        sys.exit(f"{tmp} exists from an earlier attempt; inspect and remove it by hand")
    for s in ("train", "val", "test"):
        (tmp / "images" / s).mkdir(parents=True)
        (tmp / "labels" / s).mkdir(parents=True)
    rows = []
    for m in man:
        img = m["out_image"]
        if img in dropped:
            continue
        split, stem = m["split"], Path(img).stem
        shutil.copyfile(SRC / img, tmp / img)
        lab_rel = f"labels/{split}/{stem}.txt"
        if img in new_labels:
            (tmp / lab_rel).write_text("\n".join(new_labels[img]) + ("\n" if new_labels[img] else ""), encoding="utf-8")
        else:
            shutil.copyfile(SRC / lab_rel, tmp / lab_rel)
        cls = [ln.split()[0] for ln in (tmp / lab_rel).read_text(encoding="utf-8").split("\n") if ln.strip()]
        row = dict(m)
        row["n_pothole"], row["n_speed_bump"] = cls.count("0"), cls.count("1")
        row["r2_change"] = changes.get(img, "")
        rows.append(row)
    shutil.copyfile(SRC / "data.yaml", tmp / "data.yaml")
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    shutil.copyfile(CORR, tmp / "corrections_applied.csv")
    files = sorted(p for p in tmp.rglob("*") if p.is_file() and p.name not in ("checksums.sha256", "build_info.json"))
    lines = [f"{sha256_file(p)}  {p.relative_to(tmp).as_posix()}" for p in files]
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fp = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    (tmp / "build_info.json").write_text(json.dumps({
        "version": "v3a_r2-2026-10-31", "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "fingerprint_sha256": fp, "n_samples": len(rows), "derived_from": "road_hazards_v3a_r1",
        "derived_from_fingerprint": R1_FP, "corrections_sha256": sha256_file(CORR),
        "test_image_dropped": a.drop_test_image, "summary": {f"{k[0]}:{k[1]}": v for k, v in sorted(tally.items())},
    }, indent=1), encoding="utf-8")
    rep = verify_dataset(tmp, check_near_dups=True, mode="strict")
    if rep["errors"]:
        print("\n".join(rep["errors"][:50]))
        sys.exit(f"verification FAILED; build left in {tmp}, target not created")
    os.rename(tmp, DST)
    print(json.dumps(rep["counts"], indent=1))
    print(f"built {DST.name}: {len(rows)} images, fingerprint {fp}, strict verify PASS ({len(rep['warnings'])} warnings)")


if __name__ == "__main__":
    main()
