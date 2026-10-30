"""v3b = v3a + RDD2022 D40 images (Japan, India) added to TRAIN ONLY (2026-10-30).

Single-variable experiment: val and test are exactly the v3a ones, so v3a vs v3b measures the effect of
adding RDD potholes. Czech (dash-cam, closest viewpoint) is kept aside as an unseen-country test list.
China_MotorBike (top-down view) and United_States (Google Street View, many tiny far boxes) are left out
after visual inspection (review/rdd_forensics/rdd_d40_sample.jpg).
"""
import csv, glob, os, sys
from pathlib import Path
DESK = sys.argv[1]  # this machine's Desktop path
WIN = r"C:\Users\ahmed\Desktop"
def win(p): return WIN + str(p)[len(DESK):].replace("/", "\\")
rows = list(csv.DictReader(open("manifests/v3a_split_manifest.csv", encoding="utf-8")))
cols = list(rows[0].keys())
add, czech = [], []
for lab in sorted(glob.glob(f"{DESK}/GP36_Dataset/raw_v3/RDD2022_D40_yolo/*/labels/*.txt")):
    part = lab.split("/")[-3]; country = part.split("_part")[0]; stem = os.path.basename(lab)[:-4]
    img = f"{DESK}/GP36_Dataset/raw_v3/RDD2022_D40/{country}/images/{stem}.jpg"
    assert os.path.exists(img), img
    r = {"sample_id": f"rdd22/{country}/{stem}.jpg", "source": "rdd22", "split": "train", "image": win(img), "label": win(lab),
         "negative": 0, "group_id": f"rdd22:{country}", "allow_ignored_only": 0, "review": "interim"}
    if country in ("Japan", "India"): add.append(r)
    elif country == "Czech": czech.append(r)
with open("manifests/v3b_split_manifest.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows + add)
with open("manifests/v3b_unseen_country_czech.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(czech)
print("v3a rows", len(rows), "+ rdd train", len(add), "| czech aside", len(czech))
