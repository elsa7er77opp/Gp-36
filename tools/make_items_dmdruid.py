"""Items CSV for part `dmd` = GitHub dm-druid/SpeedBumps-Detection (MIT licence, 2018), originals only.

    git clone --depth 1 https://github.com/dm-druid/SpeedBumps-Detection GP36_Dataset/raw_v3/github_dmdruid_speedbumps
    python -I tools/make_items_dmdruid.py --out review/new_data_r3/items/items_dmd.csv

What the source is (checked in the cloud session 2026-11-04, review/new_data_r3/CLOUD_REPORT.md §1):
  images/dataset/xqqds-0620-{train,val}/{images,labels}, YOLO txt, two ids:
    0 = speed bump (yellow/black rubber bumps on a Chinese campus road, phone held at windscreen height
        or pointed down at the bump; one recording day "0620")              -> speed_bump
    1 = person (mostly Pascal-VOC web photos of people, horses, trains)      -> ignore
  The set is AUGMENTED: every original appears 10 times (brightness/contrast copies), with the copies spread over
  its own train AND val (the index repeats with period 279: xqq0620 00001 == 00280 == 00559 ...; val
  xqq0620test01004 == train 00001). So:
  - only the first block xqq062000001 .. xqq062000279 is used (one copy per original);
  - images whose labels contain NO id 0 are skipped (the VOC person photos are not road images);
  - id 1 boxes inside road images (pedestrians) are ignored (they stay in the picture as background).
Split: ALL TRAIN. One campus and one day give no independent evaluation value, and the source's own val is a
copy of its train. group = block of 10 consecutive photo numbers (photos of one approach), recorded for
traceability only.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "GP36_Dataset" / "raw_v3" / "github_dmdruid_speedbumps"
CMAP = json.dumps({"0": "speed_bump", "1": "ignore"})
PERIOD = 279


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    d = Path(a.src) / "images" / "dataset" / "xqqds-0620-train"
    rows, n_box = [], 0
    for img in sorted((d / "images").glob("xqq0620*.jpg")):
        m = re.fullmatch(r"xqq0620(\d{5})", img.stem)
        if not m or not 1 <= int(m.group(1)) <= PERIOD:
            continue
        lbl = d / "labels" / f"{img.stem}.txt"
        ids = [ln.split()[0] for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()] if lbl.exists() else []
        if "0" not in ids:
            continue
        n_box += ids.count("0")
        k = int(m.group(1))
        rows.append({"image": str(img), "label": str(lbl), "class_map": CMAP, "group": f"dmd_{(k - 1) // 10:02d}",
                     "part_split": "train", "meta": "family=dmd;region=China;view=phone"})
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
        w.writeheader()
        w.writerows(rows)
    print(out, len(rows), "images,", n_box, "raw bump boxes (before FAR_TINY / leak guard)")


if __name__ == "__main__":
    main()
