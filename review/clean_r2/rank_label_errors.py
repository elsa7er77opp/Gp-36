"""Rank train/val images by how much the v1 model disagrees with their labels.

Inference only (predictions from run_clean_step1.bat). No label or image is changed.
Flags per image:
  UNMATCHED_GT  a labelled box that no prediction (any class, conf>=0.05) overlaps (IoU<0.1):
                candidate wrong label (patch, manhole, crack, crosswalk) or a hard miss
  CONF_FP       a prediction with conf>=0.5 that overlaps no labelled box (IoU<0.3):
                candidate missing label, or a real false positive
  CLASS_SWAP    a prediction (conf>=0.4) on a labelled box (IoU>=0.5) of the other class
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "road_hazards_v3a_r1"
PRED = ROOT / "runs" / "detect" / "runs" / "clean"
NAMES = {0: "pothole", 1: "speed_bump"}


def read(p, with_conf):
    out = []
    if p.exists():
        for line in p.read_text().split("\n"):
            t = line.split()
            if not t:
                continue
            c, x, y, w, h = int(t[0]), *map(float, t[1:5])
            out.append((c, x - w / 2, y - h / 2, x + w / 2, y + h / 2, float(t[5]) if with_conf else 1.0))
    return out


def iou(a, b):
    ix = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    iy = max(0.0, min(a[4], b[4]) - max(a[2], b[2]))
    inter = ix * iy
    u = (a[3] - a[1]) * (a[4] - a[2]) + (b[3] - b[1]) * (b[4] - b[2]) - inter
    return inter / u if u > 0 else 0.0


man = {r["out_image"]: r for r in csv.DictReader(open(DS / "manifest.csv", encoding="utf-8"))}
rows = []
for split in ("val", "train"):
    for img in sorted((DS / "images" / split).iterdir()):
        if img.suffix.lower() == ".npy":
            continue
        stem = img.stem
        gt = read(DS / "labels" / split / f"{stem}.txt", False)
        pr = read(PRED / f"pred_{split}_r1" / "labels" / f"{stem}.txt", True)
        flags, score = [], 0.0
        for g in gt:
            best = max((iou(g, p) for p in pr), default=0.0)
            if best < 0.1:
                area = (g[3] - g[1]) * (g[4] - g[2])
                flags.append(f"UNMATCHED_GT:{NAMES[g[0]]}:area={area:.3f}")
                score += 1.0 + min(area * 10, 2.0)   # a big unexplained box is more suspicious
            for p in pr:
                if p[0] != g[0] and p[5] >= 0.4 and iou(g, p) >= 0.5:
                    flags.append(f"CLASS_SWAP:{NAMES[g[0]]}->{NAMES[p[0]]}:{p[5]:.2f}")
                    score += 1.5
        for p in pr:
            if p[5] >= 0.5 and max((iou(p, g) for g in gt), default=0.0) < 0.3:
                flags.append(f"CONF_FP:{NAMES[p[0]]}:{p[5]:.2f}")
                score += p[5]
        m = man[f"images/{split}/{img.name}"]
        rows.append({"split": split, "out_image": f"images/{split}/{img.name}", "source": m["source"],
                     "sample_id": m["sample_id"], "n_gt": len(gt), "n_pred_ge05": sum(p[5] >= 0.5 for p in pr),
                     "score": round(score, 3), "flags": " ".join(flags)})

rows.sort(key=lambda r: (-r["score"], r["split"], r["out_image"]))
out = Path(__file__).with_name("label_error_ranking.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

for split in ("val", "train"):
    s = [r for r in rows if r["split"] == split]
    flagged = [r for r in s if r["score"] > 0]
    by_src = {}
    for r in flagged:
        by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    kinds = {}
    for r in s:
        for fl in r["flags"].split():
            k = ":".join(fl.split(":")[:2])
            kinds[k] = kinds.get(k, 0) + 1
    print(f"{split}: {len(s)} images, {len(flagged)} flagged; by source {by_src}")
    print(f"   flag counts {dict(sorted(kinds.items()))}")
print("wrote", out.relative_to(ROOT))
