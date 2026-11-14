"""Items CSV for part `egy` = Egyptian road damage , Roboflow `road-damage-detection-wgjj4/rdd-6706t`
(CC BY 4.0), forked to `refyy-i/rdd-6706t-8szyz`, version 1 = ORIGINALS (no augmentation, no resize, auto-orient).

    download (laptop): Roboflow export of refyy-i/rdd-6706t-8szyz version 1, format yolov8, unzipped to
        ..\\GP36_Dataset\\raw_v3\\rf_egyrdd   (1,372 images; see CLOUD_REPORT.md §3 for the command)
    python -I tools/make_items_egyrdd.py --src ..\\GP36_Dataset\\raw_v3\\rf_egyrdd --out review/new_data_r3/items/items_egy.csv

Source facts (cloud session 2026-11-04, review/new_data_r3/vet/egy/):
  classes: 0 Crack -> ignore (D5), 1 Pothole -> pothole.
  families: IMG_<video>-1-_MOV-<frame>  iPhone dashcam behind the windscreen, 11 videos, 678 frames
            WhatsApp-Video-<date>-at-<time>_mp4-<frame>  phone dash videos, 4 videos, 172 frames
            Egypt_<n>  phone photos, often close-up / top-down, 520 images
  Label caveat (visual check, 20 images): some "Pothole" boxes are on manhole covers (e.g. Egypt_00087,
  WhatsApp-Video-2024-03-22-at-14_41_20_mp4-0102) = D5 violation -> labels PROVISIONAL; the val/test frames must be
  reviewed (manhole boxes removed) before the part-val is used for any decision.
Split (rule fixed before any model sees it): group = video (IMG_xxxx or WhatsApp clip). Video groups are sorted by
pothole count (desc, then name); i % 6 == 2 -> val, i % 6 == 5 -> test, else train (same rule as make_items_sr.py).
Egypt_<n> photos -> train only (not forward-view, no sequence id). Frames are already sparse in the source
(e.g. IMG_4012: 187 of 1,314 frames), so every --every-th frame is kept (default 1 = all).
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "GP36_Dataset" / "raw_v3" / "rf_egyrdd"
CMAP = json.dumps({"0": "ignore", "1": "pothole"})
RF = re.compile(r"(_(jpe?g|png|JPE?G))?\.rf\.[0-9a-f]{20,32}$")


def key(stem):
    b = RF.sub("", stem)
    m = re.match(r"(IMG_\d+)-1-_MOV-(\d+)$", b)
    if m:
        return "video", f"egy_{m.group(1)}", int(m.group(2)), b
    m = re.match(r"(WhatsApp-Video-[\d-]+-at-[\d_]+?)_mp4-(\d+)$", b)
    if m:
        return "video", f"egy_{m.group(1)}", int(m.group(2)), b
    m = re.match(r"Egypt_(\d+)$", b)
    if m:
        return "photo", f"egy_photo_{int(m.group(1)) // 25:03d}", None, b
    return None, None, None, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=1)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    rows, skipped = [], []
    for img in sorted(Path(a.src).glob("*/images/*")):
        kind, grp, fr, base = key(img.stem)
        if kind is None:
            skipped.append(img.name)
            continue
        if fr is not None and fr % a.every:
            continue
        lbl = img.parent.parent / "labels" / f"{img.stem}.txt"
        ids = [ln.split()[0] for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()] if lbl.exists() else []
        rows.append({"image": str(img), "label": str(lbl), "kind": kind, "group": grp, "base": base, "pot": ids.count("1")})
    vids = defaultdict(int)
    for r in rows:
        if r["kind"] == "video":
            vids[r["group"]] += r["pot"]
    order = sorted(vids, key=lambda g: (-vids[g], g))
    split = {g: "val" if i % 6 == 2 else "test" if i % 6 == 5 else "train" for i, g in enumerate(order)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
        w.writeheader()
        for r in rows:
            w.writerow({"image": r["image"], "label": r["label"], "class_map": CMAP, "group": r["group"],
                        "part_split": split.get(r["group"], "train"), "meta": f"family=egy_{r['kind']};base={r['base']}"})
    summ = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        s = split.get(r["group"], "train")
        summ[s][0] += 1
        summ[s][1] += r["pot"]
        summ[s][2] += r["pot"] == 0
    print(json.dumps({"out": str(out), "items": len(rows), "skipped_unknown_family": len(skipped),
                      "video_split": split, "per_split_images_potholes_negatives": summ}, indent=1))


if __name__ == "__main__":
    main()
