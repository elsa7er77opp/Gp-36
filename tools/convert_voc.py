"""Convert a Pascal VOC dataset (e.g. RDD2022) to YOLO labels with SOURCE class IDs.

Non-destructive: reads <xml-dir> and <img-dir>, writes only into a NEW --out folder (refuses an
existing one), then renames it into place (atomic). Writes:
  labels/<image stem>.txt   one per image that converted without errors (empty file = no objects)
  conversion_manifest.csv   per image: status, size, counts per name, issues
  names.txt, summary.json
Usage:
  python tools/convert_voc.py --xml-dir X --img-dir I --out O --names D00,D10,D20,D40
  python tools/convert_voc.py --xml-dir X --scan-only          (list object names, write nothing)
"""
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.labels import format_label  # noqa: E402
from gp36data.voc import parse_voc, scan_names  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml-dir", required=True)
    ap.add_argument("--img-dir")
    ap.add_argument("--out")
    ap.add_argument("--names", help="comma-separated accepted object names, index = source class id")
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--part", default="", help="k/n: convert only the k-th of n deterministic slices of the sorted XML list")
    a = ap.parse_args(argv)
    xmls = sorted(Path(a.xml_dir).glob("*.xml"))
    if a.scan_only:
        print(json.dumps(scan_names(p.read_text(encoding="utf-8", errors="replace") for p in xmls), indent=1))
        print("xml files:", len(xmls))
        return 0
    if a.part:
        k, n = (int(v) for v in a.part.split("/"))
        xmls = xmls[k - 1::n]
    names = [n.strip() for n in a.names.split(",") if n.strip()]
    out = Path(a.out)
    if out.exists():
        print(f"refusing: {out} already exists", file=sys.stderr)
        return 2
    tmp = out.with_name(out.name + ".partial")
    if tmp.exists():
        if not (tmp / ".gp36_partial").exists():
            print(f"refusing: {tmp} exists and is not ours", file=sys.stderr)
            return 2
        shutil.rmtree(tmp)
    (tmp / "labels").mkdir(parents=True)
    (tmp / ".gp36_partial").write_text("convert_voc temp folder")
    imgs = {}
    for p in Path(a.img_dir).iterdir():
        if p.suffix.lower() in IMG_EXT:
            stem = p.name.rsplit(".", 1)[0]
            if stem in imgs:
                print(f"ambiguous image stem {stem}", file=sys.stderr)
                return 3
            imgs[stem] = p
    rows, stats = [], {"ok": 0, "error": 0, "image_without_xml": 0, "xml_without_image": 0, "no_objects": 0}
    totals = {n: 0 for n in names}
    seen_xml = set()
    for x in xmls:
        stem = x.name.rsplit(".", 1)[0]
        seen_xml.add(stem)
        img = imgs.get(stem)
        if img is None:
            stats["xml_without_image"] += 1
            rows.append({"stem": stem, "status": "xml_without_image"})
            continue
        with Image.open(img) as im:
            size = im.size
        r = parse_voc(x.read_text(encoding="utf-8", errors="replace"), names, size)
        row = {"stem": stem, "image": img.name, "width": r.width, "height": r.height,
               "issues": ";".join(f"{i.line}:{i.code}:{i.detail}" for i in r.issues)}
        row.update({f"n_{n}": r.counts.get(n, 0) for n in names})
        if not r.ok:
            row["status"] = "error"
            stats["error"] += 1
        else:
            (tmp / "labels" / f"{stem}.txt").write_text(format_label(r.boxes), encoding="utf-8")
            row["status"] = "ok" if r.boxes else "no_objects"
            stats["ok"] += 1
            stats["no_objects"] += 0 if r.boxes else 1
            for n, c in r.counts.items():
                totals[n] += c
        rows.append(row)
    for stem, p in sorted(imgs.items()):
        if a.part:
            break
        if stem not in seen_xml:
            stats["image_without_xml"] += 1
            rows.append({"stem": stem, "image": p.name, "status": "image_without_xml"})
    cols = ["stem", "image", "status", "width", "height"] + [f"n_{n}" for n in names] + ["issues"]
    with open(tmp / "conversion_manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (tmp / "names.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
    summary = {"xml_files": len(xmls), "images": len(imgs), **stats, "boxes_per_name": totals}
    (tmp / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (tmp / ".gp36_partial").unlink()
    os.replace(tmp, out)
    print(json.dumps(summary, indent=1))
    return 0 if stats["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
