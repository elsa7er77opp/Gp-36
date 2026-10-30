"""Heuristic scan for rf8 phone photos (IMG_*) whose pixels are sideways relative to their labels.
Score = brightness/sky of the LEFT strip minus the TOP strip (sky on the left => needs 90 deg CW). Read-only."""
import csv, sys
from pathlib import Path
import numpy as np
from PIL import Image
R = Path(__file__).resolve().parents[2]; D = R / "road_hazards_v3a"
man = [r for r in csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")) if "/IMG_" in r["sample_id"]]
built = {r["sample_id"]: r for r in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
out = []
for r in man:
    im = Image.open(D / built[r["sample_id"]]["out_image"]).convert("RGB"); im.thumbnail((256, 256))
    a = np.asarray(im, dtype=np.float32); h, w, _ = a.shape
    def sky(x):  # bright and bluish
        return float(np.mean((x.mean(axis=2) > 150) & (x[..., 2] >= x[..., 0])))
    top, left, right, bot = sky(a[: h // 6]), sky(a[:, : w // 6]), sky(a[:, -w // 6:]), sky(a[-h // 6:])
    out.append({"sample_id": r["sample_id"], "split": r["split"], "w": im.width, "h": im.height, "top": round(top, 3), "left": round(left, 3), "right": round(right, 3), "bottom": round(bot, 3), "score_left_minus_top": round(left - top, 3)})
out.sort(key=lambda x: -x["score_left_minus_top"])
w = csv.DictWriter(open(R / "audit/independent_fix/rotation_scan.csv", "w", newline="", encoding="utf-8"), fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
known = {"IMG_4462", "IMG_4492", "IMG_4513", "IMG_4540", "IMG_4555", "IMG_4581", "IMG_4421", "IMG_4560"}
for x in out:
    if x["split"] == "test":
        print(x["sample_id"].split("/")[-1][:8], x["score_left_minus_top"], "KNOWN_SIDEWAYS" if x["sample_id"].split("/")[-1][:8] in known else "")
