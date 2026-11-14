"""Fix labels instead of leaving images out (STATUS Stage 40). Nothing is removed from the dataset.

    python -I tools/v5_fix.py todo   --data road_hazards_v5_all --v4std road_hazards_v4_std --v4clean road_hazards_v4_clean --out review/v5/todo.csv
    python -I tools/v5_fix.py sheets --data road_hazards_v5_all --list review/v5/todo.csv --out review/v5/sheets
    python -I tools/v5_fix.py view   --data road_hazards_v5_all --image images/train/NAME.jpg --out review/v5/views
    python -I tools/v5_fix.py apply  --data road_hazards_v5_all --fixes review/v5/fixes.jsonl --out road_hazards_v5_fixed --fixed-by claude

todo:   train images that still need a look: "bad_in_review" (looked at in Stage 39a and marked bad) and
        "not_reviewed" (left out of v4_std by the framing filter or as duplicates, so never looked at).
        Images accepted in Stage 39a are not listed.
sheets: 6 images per sheet (640x480 each, current boxes drawn, cell number + status), plus index.csv.
view:   one image at full size with a 10 % grid and the current boxes, to read box coordinates.
fixes.jsonl, one line per image whose label must change:
        {"image": "images/train/NAME.jpg", "boxes": [[1, 0.12, 0.55, 0.88, 0.63]], "why": "bump box was on the shadow"}
        boxes = the COMPLETE new list for that image, each [class, x1, y1, x2, y2] as fractions of the 960x720 frame
        (class 0 = pothole, 1 = speed_bump); [] = no hazard in the picture. Images not listed keep their labels.
apply:  <out> = the same images (hard links) with the listed train labels replaced. Val / test lines are refused.
        fix_log.csv keeps the old and the new boxes of every changed image; --fixed-by is saved in build_info.json.
Refuses to overwrite.
"""
import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

COL = {0: (255, 165, 0), 1: (255, 0, 255)}


def manifest(data):
    with open(data / "manifest.csv", newline="", encoding="utf-8") as f:
        return [m for m in csv.DictReader(f)]


def lab_path(data, image):
    p = Path(image)
    return data / "labels" / p.parent.name / (p.stem + ".txt")


def read_boxes(p):
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            v = line.split()
            if len(v) >= 5:
                cx, cy, w, h = (float(x) for x in v[1:5])
                out.append([int(float(v[0])), round(cx - w / 2, 4), round(cy - h / 2, 4), round(cx + w / 2, 4), round(cy + h / 2, 4)])
    return out


def draw(im, boxes, grid=False):
    d = ImageDraw.Draw(im)
    W, H = im.size
    if grid:
        for k in range(1, 10):
            d.line([(W * k // 10, 0), (W * k // 10, H)], fill=(0, 255, 255), width=1)
            d.line([(0, H * k // 10), (W, H * k // 10)], fill=(0, 255, 255), width=1)
            d.text((W * k // 10 + 2, 2), f"{k / 10:.1f}", fill=(255, 255, 0))
            d.text((2, H * k // 10 + 2), f"{k / 10:.1f}", fill=(255, 255, 0))
    for c, x1, y1, x2, y2 in boxes:
        d.rectangle([x1 * W, y1 * H, x2 * W, y2 * H], outline=COL.get(c, (0, 255, 0)), width=2)
    return im


def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def do_todo(a):
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    std = {Path(m["out_image"]).stem for m in manifest(Path(a.v4std)) if m["split"] == "train"}
    clean = {Path(m["out_image"]).stem for m in manifest(Path(a.v4clean)) if m["split"] == "train"}
    rows, n = [], Counter()
    for m in manifest(Path(a.data)):
        if m["split"] != "train":
            continue
        st = Path(m["out_image"]).stem
        status = "accepted" if st in clean else ("bad_in_review" if st in std else "not_reviewed")
        n[status] += 1
        if status != "accepted":
            rows.append((m["out_image"], m.get("source", ""), status))
    rows.sort(key=lambda r: (r[1], r[2], r[0]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "source", "status"])
        w.writerows(rows)
    print(dict(n), "->", out, f"({len(rows)} images to look at)")


def do_sheets(a):
    data, out = Path(a.data), Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    with open(a.list, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out.mkdir(parents=True)
    with open(out / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet", "cell", "image", "source", "status", "current_boxes"])
        for s in range(0, len(rows), 6):
            sid = s // 6 + 1
            sh = Image.new("RGB", (3 * 640, 2 * 480), "black")
            for j, r in enumerate(rows[s:s + 6]):
                b = read_boxes(lab_path(data, r["image"]))
                im = draw(Image.open(data / r["image"]).convert("RGB").resize((640, 480), Image.BILINEAR), b)
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, 260, 15], fill=(0, 0, 0))
                d.text((3, 2), f"{j + 1}  {r['source']}  {r['status']}" + ("" if b else "  no box"), fill=(255, 255, 0))
                sh.paste(im, ((j % 3) * 640, (j // 3) * 480))
                w.writerow([f"{sid:04d}", j + 1, r["image"], r["source"], r["status"], json.dumps(b)])
            sh.save(out / f"sheet_{sid:04d}.jpg", quality=88)
            if sid % 100 == 0:
                print(f"  sheet {sid}", flush=True)
    print(f"{out}: {(len(rows) + 5) // 6} sheets for {len(rows)} images")


def do_view(a):
    data, out = Path(a.data), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for image in a.image:
        b = read_boxes(lab_path(data, image))
        im = draw(Image.open(data / image).convert("RGB"), b, grid=True)
        im.save(out / (Path(image).stem + "_grid.jpg"), quality=90)
        print(image, "current boxes [class, x1, y1, x2, y2]:", json.dumps(b))


def do_apply(a):
    data, out = Path(a.data), Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    rows = manifest(data)
    split_of = {m["out_image"]: m["split"] for m in rows}
    fixes = {}
    for ln, line in enumerate(Path(a.fixes).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            j = json.loads(line)
            image = j["image"].replace("\\", "/")
            boxes = j["boxes"]
        except (ValueError, KeyError) as e:
            sys.exit(f"fixes line {ln}: {e}")
        if split_of.get(image) != "train":
            sys.exit(f"fixes line {ln}: {image} is not a train image of {data} (val/test labels are never changed)")
        for b in boxes:
            if not (len(b) == 5 and b[0] in (0, 1) and 0 <= b[1] < b[3] <= 1 and 0 <= b[2] < b[4] <= 1):
                sys.exit(f"fixes line {ln}: bad box {b} (need [class 0/1, x1, y1, x2, y2] inside 0..1 with x1<x2, y1<y2)")
        fixes[image] = (boxes, str(j.get("why", "")))
    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        sys.exit(f"{tmp} exists (an earlier run stopped); rename or remove it yourself")
    log = []
    for m in rows:
        image = m["out_image"]
        link(data / image, tmp / image)
        dst = lab_path(tmp, image)
        if image in fixes:
            boxes, why = fixes[image]
            old = read_boxes(lab_path(data, image))
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("".join(f"{c} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}\n" for c, x1, y1, x2, y2 in boxes), encoding="utf-8")
            m["n_pothole"], m["n_speed_bump"] = sum(b[0] == 0 for b in boxes), sum(b[0] == 1 for b in boxes)
            log.append((image, m.get("source", ""), json.dumps(old), json.dumps(boxes), why))
        else:
            link(lab_path(data, image), dst)
    for name in ("data.yaml", "data_stdframe.yaml", "val_stdframe.txt", "test_stdframe.txt"):
        if (data / name).exists():
            shutil.copyfile(data / name, tmp / name)
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(tmp / "fix_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "source", "old_boxes", "new_boxes", "why"])
        w.writerows(log)
    info = {"from": str(data), "fixes": str(a.fixes), "fixed_by": a.fixed_by, "images_changed": len(log),
            "changed_by_source": dict(Counter(r[1] for r in log)), "splits": {}}
    for sp in ("train", "val", "test"):
        rs = [m for m in rows if m["split"] == sp]
        info["splits"][sp] = {"images": len(rs), "pothole_boxes": sum(int(m.get("n_pothole") or 0) for m in rs),
                              "speed_bump_boxes": sum(int(m.get("n_speed_bump") or 0) for m in rs)}
    (tmp / "build_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    tmp.rename(out)
    print(json.dumps(info, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("todo")
    for x in ("--data", "--v4std", "--v4clean", "--out"):
        t.add_argument(x, required=True)
    s = sub.add_parser("sheets")
    for x in ("--data", "--list", "--out"):
        s.add_argument(x, required=True)
    v = sub.add_parser("view")
    v.add_argument("--data", required=True)
    v.add_argument("--image", nargs="+", required=True)
    v.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    for x in ("--data", "--fixes", "--out", "--fixed-by"):
        p.add_argument(x, required=True)
    a = ap.parse_args()
    {"todo": do_todo, "sheets": do_sheets, "view": do_view, "apply": do_apply}[a.cmd](a)


if __name__ == "__main__":
    main()
