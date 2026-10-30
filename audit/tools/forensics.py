"""Read-only forensic pass over GP36 raw datasets and road_hazards_v2. Writes JSON only to scratchpad."""
import hashlib, json, re, sys, collections
from pathlib import Path
import numpy as np
from PIL import Image, ExifTags

sys.stdout.reconfigure(encoding="utf-8")
DS = Path(r"C:\Users\ahmed\Desktop\GP36_Dataset")
V2 = Path(r"C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v2")
OUT = Path(sys.argv[1])
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
ORIENT = [k for k, v in ExifTags.TAGS.items() if v == "Orientation"][0]


def dhash(im):
    g = np.asarray(im.convert("L").resize((9, 8), Image.BILINEAR), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def inspect_image(p):
    r = {"path": str(p), "ok": True}
    try:
        data = p.read_bytes()
        r["sha256"] = hashlib.sha256(data).hexdigest()
        with Image.open(p) as im:
            r["format"] = im.format
            r["size"] = im.size
            try:
                r["exif_orient"] = im.getexif().get(ORIENT, 1)
            except Exception:
                r["exif_orient"] = None
            im.load()
            r["dhash"] = dhash(im)
    except Exception as e:
        r["ok"] = False
        r["err"] = repr(e)
    return r


def inspect_label(t):
    r = {"lines": 0, "bbox": 0, "poly": 0, "bad": [], "classes": collections.Counter(), "boxes": []}
    if not t.exists():
        r["missing"] = True
        return r
    seen = set()
    dup = 0
    for i, line in enumerate(t.read_text(encoding="utf-8", errors="replace").splitlines()):
        p = line.split()
        if not p:
            continue
        r["lines"] += 1
        try:
            vals = [float(v) for v in p]
        except ValueError:
            r["bad"].append((i, "nonnumeric"))
            continue
        c = vals[0]
        if c != int(c):
            r["bad"].append((i, "nonint_class"))
        r["classes"][int(c)] += 1
        if len(p) == 5:
            r["bbox"] += 1
            xc, yc, w, h = vals[1:]
        elif len(p) > 5 and len(p) % 2 == 1:
            r["poly"] += 1
            xs, ys = vals[1::2], vals[2::2]
            if any(v < 0 or v > 1 for v in xs + ys):
                r["bad"].append((i, "poly_out_of_range"))
            if len(xs) < 3:
                r["bad"].append((i, "poly_lt3pts"))
            xc, yc, w, h = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)
        else:
            r["bad"].append((i, f"ntokens={len(p)}"))
            continue
        if w <= 0 or h <= 0:
            r["bad"].append((i, "nonpositive_wh"))
        if not (0 <= xc <= 1 and 0 <= yc <= 1 and w <= 1 and h <= 1):
            r["bad"].append((i, "coord_out_of_range"))
        if xc - w / 2 < -1e-3 or xc + w / 2 > 1 + 1e-3 or yc - h / 2 < -1e-3 or yc + h / 2 > 1 + 1e-3:
            r["bad"].append((i, "box_exceeds_image"))
        key = (int(c), round(xc, 4), round(yc, 4), round(w, 4), round(h, 4))
        if key in seen:
            dup += 1
        seen.add(key)
        r["boxes"].append([int(c), xc, yc, w, h])
    r["dup_lines"] = dup
    return r


def scan(name, img_dir, lbl_dir):
    imgs = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXT)
    lbls = sorted(lbl_dir.glob("*.txt")) if lbl_dir.exists() else []
    img_stems = {p.stem for p in imgs}
    lbl_stems = {p.stem for p in lbls}
    recs = []
    for p in imgs:
        r = inspect_image(p)
        L = inspect_label(lbl_dir / (p.stem + ".txt"))
        L["classes"] = dict(L["classes"])
        r["label"] = L
        r["set"] = name
        recs.append(r)
    return {
        "set": name, "n_img": len(imgs), "n_lbl": len(lbls),
        "img_no_lbl": sorted(img_stems - lbl_stems), "lbl_no_img": sorted(lbl_stems - img_stems),
        "nonimage_files": sorted(p.name for p in img_dir.iterdir() if p.suffix.lower() not in IMG_EXT)[:20],
        "n_nonimage_files": sum(1 for p in img_dir.iterdir() if p.suffix.lower() not in IMG_EXT),
        "records": recs,
    }


sets = []
sets.append(scan("raw:potholes", DS / "potholes" / "images", DS / "potholes" / "labels"))
sets.append(scan("raw:speed_bumps", DS / "speed_bumps" / "images", DS / "speed_bumps" / "labels"))
for s in ("train", "valid", "test"):
    sets.append(scan(f"raw:rf_{s}", DS / "roboflow" / s / "images", DS / "roboflow" / s / "labels"))
for s in ("train", "val", "test"):
    sets.append(scan(f"v2:{s}", V2 / "images" / s, V2 / "labels" / s))
OUT.write_text(json.dumps(sets))
for S in sets:
    print(S["set"], S["n_img"], S["n_lbl"], "img_no_lbl", len(S["img_no_lbl"]), "lbl_no_img", len(S["lbl_no_img"]), "nonimg", S["n_nonimage_files"])
