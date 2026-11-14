"""Apply a reviewed TRAIN label audit to a composed dataset and write a NEW dataset folder (STATUS Stage 34).

    python -I tools/apply_train_audit.py --src road_hazards_v3b_C --cands review/label_audit_r3/candidates.csv \
        --verdicts review/label_audit_r3/verdicts.csv --out road_hazards_v3b_C2

verdicts.csv: cand_id, verdict, note. Verdicts:
  remove_not_hazard | remove_manhole | remove_bad_box   the GT line of that candidate is removed (train only)
  drop_image                                           the train image (and its label) is left out of the new dataset
  keep | uncertain | no_hazard                         nothing changes
Every removed line is checked against the candidate's coordinates (6 decimals) before anything is written.
Only train changes: val/test images and labels are copied and their sha256 must equal the source (hard error).
Images are hard-linked (same bytes, no extra disk); labels, manifest.csv, checksums.sha256 are written new;
build_info.json records the source, audit file hashes and counts; change_log.csv lists every change.
No box is ever added or resized. Refuses to overwrite --out.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REMOVE = {"remove_not_hazard", "remove_manhole", "remove_bad_box"}
NOOP = {"keep", "uncertain", "no_hazard"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--cands", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    src, out = Path(args.src), Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists - refusing to overwrite")
    cands = {r["cand_id"]: r for r in csv.DictReader(open(args.cands, encoding="utf-8"))}
    verdicts = list(csv.DictReader(open(args.verdicts, encoding="utf-8")))
    remove, drop, seen = {}, {}, set()
    for v in verdicts:
        cid, vd = v["cand_id"].strip(), v["verdict"].strip()
        if cid in seen:
            sys.exit(f"duplicate verdict for {cid}")
        seen.add(cid)
        if cid not in cands:
            sys.exit(f"unknown cand_id {cid}")
        c = cands[cid]
        if vd in REMOVE:
            if c["kind"] == "missing":
                sys.exit(f"{cid}: a remove verdict on a 'missing' candidate")
            remove.setdefault(c["stem"], []).append((int(c["gt_line"]), c, vd, v.get("note", "")))
        elif vd == "drop_image":
            drop[c["stem"]] = (c, v.get("note", ""))
        elif vd not in NOOP:
            sys.exit(f"{cid}: unknown verdict {vd!r}")
    manifest = list(csv.DictReader(open(src / "manifest.csv", encoding="utf-8")))
    fields = list(manifest[0].keys())
    by_stem = {Path(m["out_image"]).stem: m for m in manifest}
    for stem in list(remove) + list(drop):
        if stem not in by_stem or by_stem[stem]["split"] != "train":
            sys.exit(f"{stem}: not a train image of {src}")
    # plan the label edits and check every removed line
    new_labels, log = {}, []
    for stem, items in remove.items():
        if stem in drop:
            continue
        lab = src / "labels" / "train" / f"{stem}.txt"
        lines = lab.read_text(encoding="utf-8").splitlines()
        kill = set()
        for ln, c, vd, note in items:
            tok = lines[ln].split()
            xc, yc, w, h = map(float, tok[1:5])
            got = (xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2)
            want = tuple(float(c[k]) for k in ("x1", "y1", "x2", "y2"))
            if max(abs(a - b) for a, b in zip(got, want)) > 2e-6:
                sys.exit(f"{c['cand_id']}: line {ln} of {lab.name} does not match the candidate box")
            kill.add(ln)
            log.append({"change": vd, "stem": stem, "source": c["source"], "cand_id": c["cand_id"], "line": ln,
                        "label_line": lines[ln], "note": note})
        new_labels[stem] = "".join(l + "\n" for i, l in enumerate(lines) if i not in kill)
    for stem, (c, note) in drop.items():
        log.append({"change": "drop_image", "stem": stem, "source": c["source"], "cand_id": c["cand_id"], "line": "",
                    "label_line": "", "note": note})
    # write the new dataset
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True)
        (out / "labels" / split).mkdir(parents=True)
    shutil.copyfile(src / "data.yaml", out / "data.yaml")
    rows, checks = [], []
    for m in manifest:
        stem, split = Path(m["out_image"]).stem, m["split"]
        if stem in drop:
            continue
        img = src / m["out_image"]
        dst = out / m["out_image"]
        try:
            os.link(img, dst)
        except OSError:
            shutil.copyfile(img, dst)
        lab_src = src / "labels" / split / f"{stem}.txt"
        lab_dst = out / "labels" / split / f"{stem}.txt"
        if stem in new_labels:
            lab_dst.write_text(new_labels[stem], encoding="utf-8")
            lines = new_labels[stem].splitlines()
            m = {**m, "n_pothole": sum(l.split()[0] == "0" for l in lines),
                 "n_speed_bump": sum(l.split()[0] == "1" for l in lines)}
        elif lab_src.exists():
            shutil.copyfile(lab_src, lab_dst)
        if split != "train" and lab_src.exists() and sha(lab_src) != sha(lab_dst):
            sys.exit(f"{split} label changed: {stem}")
        rows.append(m)
        checks.append((sha(dst), m["out_image"]))
        if lab_dst.exists():
            checks.append((sha(lab_dst), f"labels/{split}/{stem}.txt"))
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(out / "change_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["change", "stem", "source", "cand_id", "line", "label_line", "note"])
        w.writeheader()
        w.writerows(log)
    checks = [(sha(out / "data.yaml"), "data.yaml"), (sha(out / "manifest.csv"), "manifest.csv")] + checks
    (out / "checksums.sha256").write_text("".join(f"{h}  {p}\n" for h, p in checks), encoding="utf-8")
    # val/test must be identical to the source
    for split in ("val", "test"):
        a = sorted(p.name for p in (src / "labels" / split).glob("*.txt"))
        b = sorted(p.name for p in (out / "labels" / split).glob("*.txt"))
        if a != b:
            sys.exit(f"{split} label set differs")
    cnt = Counter(l["change"] for l in log)
    per_src = Counter((l["source"], l["change"]) for l in log)
    tr = [r for r in rows if r["split"] == "train"]
    info = {"built_at": datetime.now().isoformat(timespec="seconds"), "source": str(src),
            "source_checksums_sha256": sha(src / "checksums.sha256"),
            "candidates_sha256": sha(args.cands), "verdicts_sha256": sha(args.verdicts),
            "changes": dict(cnt), "changes_by_source": {f"{s}:{c}": n for (s, c), n in sorted(per_src.items())},
            "train_images": len(tr), "train_pothole_boxes": sum(int(r["n_pothole"]) for r in tr),
            "train_speed_bump_boxes": sum(int(r["n_speed_bump"]) for r in tr),
            "val_test": "byte-identical to source (checked)", "policy": "no box added or resized; STATUS Stage 34"}
    (out / "build_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
