"""Write the items CSVs (input of tools/build_part.py) for the round-r3 parts.

    python -I tools/make_items_r3.py --out review/new_data_r3/items

Parts (rules fixed here, before any model sees the data):
  rdd_ji  RDD2022 Japan + India images that contain D40. class 3 (D40) -> pothole, every other RDD class ignored
          (cracks, manholes, repairs = background, D5). All TRAIN (RDD has no drive ids; nothing of it is used for eval).
  rdd_cz  RDD2022 Czech D40 images: all TEST (unseen-country external check, kept apart since 30 Oct).
  bucko   Bucko et al. 2022 dash-cam pothole videos (Slovakia). Video names carry a location token (Ca / Pr / Pd)
          and the same location appears under several light conditions, so the group is the LOCATION.
          Ca + Pd -> train; Pr videos -> val (Vid_1_Pr, Vid_Pr_night, Vid_Pr_evening) and test (Vid_2_Pr,
          Vid_3_Pr, Vid_Pr_rain). Note: val and test share location Pr (independent of train, not of each other).
          Every --every-th frame kept (consecutive frames are near-duplicates).
  rsid    RSID selection review/new_data_r3/rsid_selection_v2.csv (tools/select_rsid.py): split by sequence.
          0 pothole -> pothole, 2 speedbump -> speed_bump, 1 manhole -> ignore (D5).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

DS = Path(__file__).resolve().parents[2] / "GP36_Dataset" / "raw_v3"
RDD_MAP = json.dumps({**{str(i): "ignore" for i in range(11)}, "3": "pothole"})


def write(path, rows):
    if path.exists():
        print(f"{path} exists - kept, not rewritten")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
        w.writeheader()
        w.writerows(rows)
    print(path, len(rows))


def rdd(countries, split):
    rows = []
    for c in countries:
        labels = {p.stem: p for d in sorted((DS / "RDD2022_D40_yolo").glob(f"{c}*")) for p in (d / "labels").glob("*.txt")}
        for img in sorted((DS / "RDD2022_D40" / c / "images").glob("*.jpg")):
            if img.stem in labels:
                rows.append({"image": str(img), "label": str(labels[img.stem]), "class_map": RDD_MAP,
                             "group": f"rdd_{c}_{img.stem}", "part_split": split, "meta": f"country={c}"})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=4)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write(out / "items_rdd_ji.csv", rdd(["Japan", "India"], "train"))
    write(out / "items_rdd_cz.csv", rdd(["Czech"], "test"))

    rows = []
    val_v, test_v = {"Vid_1_Pr", "Vid_Pr_night", "Vid_Pr_evening"}, {"Vid_2_Pr", "Vid_3_Pr", "Vid_Pr_rain"}
    for img in sorted((DS / "figshare_bucko_potholes" / "Potholes_dataset").glob("*/*.jpg")):
        m = re.match(r"(Vid_\w+?)_(\d{8,9})$", img.stem)  # second clip of a video is numbered 1xxxxxxxx
        vid, fr = m.group(1), int(m.group(2))
        if fr % args.every:
            continue
        loc = re.search(r"_(Ca|Pr|Pd)(?:_|$)", vid + "_").group(1)
        split = "val" if vid in val_v else "test" if vid in test_v else "train"
        if loc == "Pr" and split == "train":
            sys.exit(f"Pr video {vid} not assigned to val/test")
        rows.append({"image": str(img), "label": str(img.with_suffix(".txt")), "class_map": json.dumps({"0": "pothole"}),
                     "group": f"bucko_{loc}", "part_split": split, "meta": f"condition={img.parent.name};video={vid}"})
    write(out / "items_bucko.csv", rows)

    rows = []
    sel = Path(__file__).resolve().parents[1] / "review" / "new_data_r3" / "rsid_selection_v2.csv"
    for r in csv.DictReader(open(sel, newline="", encoding="utf-8")):
        base = DS / "zenodo_rsid_sel_v2"
        lbl = DS / "zenodo_rsid_labels" / r["member_label"]
        rows.append({"image": str(base / r["member_image"]), "label": str(lbl),
                     "class_map": json.dumps({"0": "pothole", "1": "ignore", "2": "speed_bump"}),
                     "group": r["seq"], "part_split": r["part_split"],
                     "meta": f"kind={r['kind']};family={r['seq'].split(':')[0]}"})
    write(out / "items_rsid.csv", rows)


if __name__ == "__main__":
    main()
