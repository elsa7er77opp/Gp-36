"""Items CSV for part `sr` = Kaggle speedregulator-road-hazards-and-speed-bumps (CC BY-SA 4.0), new families only.

    python -I tools/make_items_sr.py --out review/new_data_r3/items/items_sr.csv

The Kaggle set is a merge. Families (file-name prefix) and what is done with them:
  kg_   own photos / video snapshots (North Africa): potholes, cracks, manholes          -> KEEP, group = date
  dz_   Algeria dash videos `dz_v2_IMG_xxxx_fNNNNNN`: speed bumps + potholes             -> KEEP, group = video
  rad_  RAD road-anomaly dash videos `rad_NN_DD-MM-YYYY_mp4-K`: speed bumps              -> KEEP, group = video,
        every 3rd frame (consecutive frames)
  rdd_  RDD2022 (we already hold it; contains Czech = our external test)                 -> EXCLUDE
  rf_   Roboflow speed-bump families already rejected on 31 Oct (sub5 / rf8 overlap)     -> EXCLUDE
  night_ Bucko frames (`night_Vid_Ca_evening_…`), already part `bucko`                   -> EXCLUDE
  aug_  augmented copies (flips)                                                        -> EXCLUDE
Classes: 0 nid_de_poule -> pothole, 3 dos_dane -> speed_bump, 1 fissure and 2 bouche_egout -> ignore (D5).
Split by group, per family: groups sorted by hazard count, every 6th group -> val, the next -> test, the rest
-> train (about 2/3 train). The Kaggle split is ignored (it is by image).
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "GP36_Dataset" / "raw_v3" / "kaggle_speedregulator"
CMAP = json.dumps({"0": "pothole", "1": "ignore", "2": "ignore", "3": "speed_bump"})


def group(stem):
    s = re.sub(r"_jpg\.rf\.[0-9a-f]{32}$", "", stem)
    if s.startswith("kg_"):
        m = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", s)
        return "kg", f"kg_{m.group(1)}{m.group(2)}{m.group(3)}" if m else "kg_undated", None
    m = re.match(r"dz_v2_(IMG_\d+)_f(\d+)", s)
    if m:
        return "dz", f"dz_{m.group(1)}", int(m.group(2))
    m = re.match(r"rad_(\d+_\d{2}-\d{2}-\d{4})_mp4-(\d+)", s)
    if m:
        return "rad", f"rad_{m.group(1)}", int(m.group(2))
    return None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists")
    rows = []
    for img in sorted((SRC / "images").glob("*/*.jpg")):
        fam, grp, fr = group(img.stem)
        if fam is None:
            continue
        if fam == "rad" and fr % 3:
            continue
        lbl = SRC / "labels" / img.parent.name / f"{img.stem}.txt"
        cls = [l.split()[0] for l in lbl.read_text(encoding="utf-8").splitlines() if l.strip()] if lbl.exists() else []
        rows.append({"image": str(img), "label": str(lbl), "class_map": CMAP, "group": grp, "fam": fam,
                     "haz": cls.count("0") + cls.count("3")})
    by_fam = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_fam[r["fam"]][r["group"]] += r["haz"]
    split = {}
    for fam, g in by_fam.items():
        for i, grp in enumerate(sorted(g, key=lambda k: (-g[k], k))):
            split[grp] = "val" if i % 6 == 2 else "test" if i % 6 == 5 else "train"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
        w.writeheader()
        for r in rows:
            w.writerow({"image": r["image"], "label": r["label"], "class_map": r["class_map"], "group": r["group"],
                        "part_split": split[r["group"]], "meta": f"family={r['fam']}"})
    for fam, g in by_fam.items():
        print(fam, {s: sum(1 for k in g if split[k] == s) for s in ("train", "val", "test")}, "groups;",
              {s: sum(r["fam"] == fam and split[r["group"]] == s for r in rows) for s in ("train", "val", "test")}, "images")


if __name__ == "__main__":
    main()
