"""
GP36 - Step 1: build the road-hazard dataset for YOLO training.

Input  (the GP36_Dataset folder on the laptop):
    GP36_Dataset/speed_bumps/images/*.jpg  + labels/*.txt   (class 0 = speed bump)
    GP36_Dataset/potholes/images/*.jpg     + labels/*.txt   (class 0 = pothole)
    GP36_Dataset/roboflow/{train,valid,test}/images + labels  (optional, Roboflow
        "Humps/Bumps & Potholes" v8, YOLOv8 export: 0 = Pothole, 1 = Speed Bump)

Output (YOLO format, ready for Ultralytics):
    road_hazards/images/{train,val,test}/  road_hazards/labels/{train,val,test}/
    road_hazards/data.yaml
    classes: 0 = pothole, 1 = speed_bump

Speed bump photos are 1920x1080 dash-cam frames where the bump is very thin
(median box height ~1.7 % of the image). To make the bump larger for the
network we crop a 960x540 region of interest around the road in front of
the car (same aspect ratio, 2x zoom) and shift the labels accordingly.

Usage:
    python prepare_dataset.py --src /path/to/GP36_Dataset --out road_hazards
"""
import argparse
import random
import shutil
from pathlib import Path

from PIL import Image

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def read_labels(txt):
    boxes = []
    if txt.exists():
        for line in txt.read_text().splitlines():
            p = line.split()
            if len(p) == 5:
                boxes.append([float(v) for v in p[1:]])  # xc, yc, w, h (normalised)
            elif len(p) > 5 and len(p) % 2 == 1:         # polygon -> bounding box
                xs = [float(v) for v in p[1::2]]; ys = [float(v) for v in p[2::2]]
                boxes.append([(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)])
    return boxes


def read_labels_with_class(txt):
    out = []
    if txt.exists():
        for line in txt.read_text().splitlines():
            p = line.split()
            if not p:
                continue
            b = read_labels_from_line(line)
            if b:
                out.append((int(float(p[0])), b))
    return out


def read_labels_from_line(line):
    p = line.split()
    if len(p) == 5:
        return [float(v) for v in p[1:]]
    if len(p) > 5 and len(p) % 2 == 1:
        xs = [float(v) for v in p[1::2]]; ys = [float(v) for v in p[2::2]]
        return [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)]
    return None


def save_as_jpg(src_file, dst_file):
    """Copy jpg/png directly; convert other formats (e.g. GIF) to JPG.
    The extension is appended (not replaced) because Roboflow file names contain dots."""
    if src_file.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        try:
            with Image.open(src_file) as im:
                if im.format in ("JPEG", "PNG"):
                    shutil.copy(src_file, Path(str(dst_file) + src_file.suffix.lower()))
                    return
        except Exception:
            return
    with Image.open(src_file) as im:
        im.convert("RGB").save(Path(str(dst_file) + ".jpg"), quality=95)


def write_labels(txt, cls, boxes):
    txt.write_text("".join(f"{cls} {b[0]:.6f} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f}\n" for b in boxes))


def roi_crop(img, boxes, cw_frac=0.5, ch_frac=0.5):
    """Crop a window (cw_frac x ch_frac of the image) that contains all boxes."""
    W, H = img.size
    cw, ch = int(W * cw_frac), int(H * ch_frac)
    if boxes:
        x1 = min((b[0] - b[2] / 2) * W for b in boxes); x2 = max((b[0] + b[2] / 2) * W for b in boxes)
        y1 = min((b[1] - b[3] / 2) * H for b in boxes); y2 = max((b[1] + b[3] / 2) * H for b in boxes)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if x2 - x1 > cw or y2 - y1 > ch:          # boxes too spread -> keep full frame
            return img, boxes
    else:
        cx, cy = W / 2, H * 0.6                    # road area in front of the car
    left = int(min(max(cx - cw / 2, 0), W - cw))
    top = int(min(max(cy - ch / 2, 0), H - ch))
    crop = img.crop((left, top, left + cw, top + ch))
    new = []
    for xc, yc, w, h in boxes:
        new.append([(xc * W - left) / cw, (yc * H - top) / ch, w * W / cw, h * H / ch])
    return crop, new


def split_list(items, ratios=(0.7, 0.2, 0.1), seed=0, shuffle=True):
    items = list(items)
    if shuffle:
        random.Random(seed).shuffle(items)
    n = len(items)
    a, b = int(n * ratios[0]), int(n * (ratios[0] + ratios[1]))
    return {"train": items[:a], "val": items[a:b], "test": items[b:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="GP36_Dataset folder")
    ap.add_argument("--out", default="road_hazards")
    args = ap.parse_args()
    src, out = Path(args.src), Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    for s in ("train", "val", "test"):
        (out / "images" / s).mkdir(parents=True)
        (out / "labels" / s).mkdir(parents=True)

    counts = {}
    # potholes -> class 0, random split
    pot = sorted(p for p in (src / "potholes" / "images").iterdir() if p.suffix.lower() in IMG_EXT)
    for s, files in split_list(pot).items():
        for f in files:
            boxes = read_labels(src / "potholes" / "labels" / (f.stem + ".txt"))
            save_as_jpg(f, out / "images" / s / f"pot_{f.stem}")
            write_labels(out / "labels" / s / f"pot_{f.stem}.txt", 0, boxes)
            counts[("pothole", s)] = counts.get(("pothole", s), 0) + 1

    # speed bumps -> class 1. Frames come from video, so split in time order
    # (no shuffle) to avoid near-identical frames in both train and val.
    sb = sorted(p for p in (src / "speed_bumps" / "images").iterdir() if p.suffix.lower() in IMG_EXT)
    for s, files in split_list(sb, shuffle=False).items():
        for f in files:
            boxes = read_labels(src / "speed_bumps" / "labels" / (f.stem + ".txt"))
            img = Image.open(f).convert("RGB")
            img, boxes = roi_crop(img, boxes)
            img.save(out / "images" / s / f"sb_{f.stem}.jpg", quality=95)
            write_labels(out / "labels" / s / f"sb_{f.stem}.txt", 1, boxes)
            counts[("speed_bump", s)] = counts.get(("speed_bump", s), 0) + 1

    # Roboflow dataset (already split by its authors) -> keep its split and class ids
    rf = src / "roboflow"
    if rf.exists():
        names = {0: "pothole", 1: "speed_bump"}
        for rf_split, s in (("train", "train"), ("valid", "val"), ("test", "test")):
            img_dir = rf / rf_split / "images"
            if not img_dir.exists():
                continue
            for f in sorted(img_dir.iterdir()):
                if f.suffix.lower() not in IMG_EXT:
                    continue
                labels = read_labels_with_class(rf / rf_split / "labels" / (f.stem + ".txt"))
                name = f"rf_{f.stem[:60]}"
                save_as_jpg(f, out / "images" / s / name)
                (out / "labels" / s / f"{name}.txt").write_text(
                    "".join(f"{c} {b[0]:.6f} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f}\n" for c, b in labels if c in names))
                for c in {c for c, _ in labels if c in names} or {"background"}:
                    key = (names.get(c, "background") + "(rf)", s)
                    counts[key] = counts.get(key, 0) + 1
    else:
        print("No roboflow folder found - using potholes + speed_bumps only")

    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\ntrain: images/train\nval: images/val\ntest: images/test\n\n"
        "names:\n  0: pothole\n  1: speed_bump\n")
    print("Images per split:")
    for k in sorted(counts):
        print(f"  {k[0]:11s} {k[1]:5s} {counts[k]}")
    print("Dataset written to", out.resolve())


if __name__ == "__main__":
    main()
