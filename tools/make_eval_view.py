"""Read-only "view" of an external eval set in the layout tools/metrics_report.py and tools/coco_eval.py read.

    python -I tools/make_eval_view.py --src external_tests/bd_speedbreaker_v2_orig87 --split test \
        --out external_tests/bd87_eval_view

The source folder is never written (its checksums.sha256 stays valid). The view gets:
  manifest.csv   split, out_image, out_w, out_h   (one row per image in <src>/images/<split>, size read from the file)
  labels/<split>/<stem>.txt   byte copies of <src>/labels/<split>/<stem>.txt (an image without a label file gets none,
                              which metrics_report reads as a negative image)
  view_info.json source path, sha256 of every copied label file
Images are not copied: predictions come from `yolo val` on the source yaml, matched by file stem.
Refuses to overwrite an existing --out.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    src, out = Path(args.src), Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists - refusing to overwrite")
    imgs = sorted(p for p in (src / "images" / args.split).iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
    if not imgs:
        sys.exit("no images found")
    (out / "labels" / args.split).mkdir(parents=True)
    rows, hashes = [], {}
    for p in imgs:
        with Image.open(p) as im:
            w, h = im.size
        rows.append({"split": args.split, "out_image": f"images/{args.split}/{p.name}", "out_w": w, "out_h": h})
        lab = src / "labels" / args.split / f"{p.stem}.txt"
        if lab.exists():
            shutil.copyfile(lab, out / "labels" / args.split / lab.name)
            hashes[lab.name] = hashlib.sha256(lab.read_bytes()).hexdigest()
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["split", "out_image", "out_w", "out_h"])
        wr.writeheader()
        wr.writerows(rows)
    (out / "view_info.json").write_text(json.dumps({"source": str(src), "split": args.split, "n_images": len(rows),
                                                    "label_sha256": hashes}, indent=1), encoding="utf-8")
    print(f"{len(rows)} images, {len(hashes)} label files -> {out}")


if __name__ == "__main__":
    main()
