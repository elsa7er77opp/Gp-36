"""Helpers for labelling the egm pool by Claude (owner decision, STATUS Stage 37). No GP36 model is run here.

    python3 -I tools/egm_ai_label.py sheet  --pool eval --start 0 --n 6 --out <dir>   contact sheet of frames start..start+n
    python3 -I tools/egm_ai_label.py grid   --pool eval --idx 12 13 --out <dir>       one frame per file, 10 % grid
    python3 -I tools/egm_ai_label.py crop   --pool eval --idx 12 --box x1 y1 x2 y2 --out <dir>   zoom (relative coords)
    python3 -I tools/egm_ai_label.py write  --pool eval --idx 12 --status done --b "1 0.30 0.62 0.71 0.70" ...
    python3 -I tools/egm_ai_label.py overlay --pool eval --idx 12 13 --out <dir>      draw the saved labels

Order = the same as tools/egm_label.py (sequence, capture time, id), so idx is stable. Boxes in `write` are
"class x1 y1 x2 y2" relative to the EXIF-oriented image (0 = pothole, 1 = speed_bump). Labels go to
<labels-root>/<pool>/<id>.txt (YOLO), decisions append to review/new_data_r3/egm_labels/status_<pool>.csv with
labeller=claude. Paths in the pool CSV are Windows paths; --map rewrites the prefix for the Linux view.
"""
import argparse
import csv
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
COL = {0: (255, 165, 0), 1: (255, 0, 255)}


def rows_for(a):
    with open(a.csv, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["pool"] == a.pool]
    rows.sort(key=lambda r: (r["sequence"], float(r["captured_at"] or 0), r["id"]))
    return rows


def path_of(a, r):
    p = r["image"].replace("\\", "/")
    if a.map:
        src, dst = a.map.split("=", 1)
        if p.lower().startswith(src.lower()):
            p = dst + p[len(src):]
    return Path(p)


def load(a, r, width):
    im = Image.open(path_of(a, r))
    if width <= 1400:
        im.draft("RGB", (width * 2, width * 2))  # fast JPEG decode at reduced size; full size used by `crop`
    im = ImageOps.exif_transpose(im).convert("RGB")
    W, H = im.size
    return im.resize((width, round(H * width / W)), Image.BILINEAR), (W, H)


def font(sz):
    for f in ("DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def grid(im):
    d = ImageDraw.Draw(im)
    w, h = im.size
    f = font(14)
    for k in range(1, 10):
        x, y = w * k // 10, h * k // 10
        d.line([(x, 0), (x, h)], fill=(0, 255, 255), width=1)
        d.line([(0, y), (w, y)], fill=(0, 255, 255), width=1)
        d.text((x + 2, 2), f"{k / 10:.1f}", fill=(255, 255, 0), font=f)
        d.text((2, y + 2), f"{k / 10:.1f}", fill=(255, 255, 0), font=f)
    return im


def read_label(a, r):
    p = Path(a.labels_root) / a.pool / f"{r['id']}.txt"
    out = []
    if p.exists():
        for line in p.read_text().split("\n"):
            v = line.split()
            if len(v) == 5:
                c, cx, cy, w, h = int(v[0]), *map(float, v[1:])
                out.append((c, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sheet", "grid", "crop", "write", "overlay", "count"])
    ap.add_argument("--pool", default="eval")
    ap.add_argument("--csv", default=str(ROOT / "review/new_data_r3/items/egm_pool.csv"))
    ap.add_argument("--labels-root", default=str(ROOT.parent / "GP36_Dataset/labels_egm"))
    ap.add_argument("--status-dir", default=str(ROOT / "review/new_data_r3/egm_labels"))
    ap.add_argument("--map", default="")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--idx", type=int, nargs="*", default=[])
    ap.add_argument("--id", default="", help="write by image id (e.g. train candidates from mine_C_train.csv) instead of pool index")
    ap.add_argument("--box", type=float, nargs=4)
    ap.add_argument("--status", choices=["done", "unsure", "unusable"])
    ap.add_argument("--b", action="append", default=[])
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    rows = rows_for(a)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "count":
        print(len(rows)); return
    if a.cmd == "sheet":
        sel = list(range(a.start, min(a.start + a.n, len(rows))))
        tiles = [load(a, rows[i], 640)[0] for i in sel]
        th = max(t.size[1] for t in tiles)
        cols = 3 if len(tiles) > 4 else 2
        sheet = Image.new("RGB", (640 * cols, th * ((len(tiles) + cols - 1) // cols)), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for k, (i, t) in enumerate(zip(sel, tiles)):
            x, y = 640 * (k % cols), th * (k // cols)
            sheet.paste(t, (x, y))
            d.rectangle([x, y, x + 70, y + 26], fill=(0, 0, 0))
            d.text((x + 4, y + 3), f"#{i}", fill=(255, 255, 0), font=font(18))
        f = out / f"sheet_{a.pool}_{a.start:04d}.jpg"
        sheet.save(f, quality=85)
        print(f, [(i, rows[i]["id"], rows[i]["sequence"][:8]) for i in sel])
    elif a.cmd in ("grid", "overlay"):
        for i in a.idx:
            im, _ = load(a, rows[i], a.width)
            if a.cmd == "grid":
                grid(im)
            d = ImageDraw.Draw(im)
            W, H = im.size
            for c, x1, y1, x2, y2 in read_label(a, rows[i]):
                d.rectangle([x1 * W, y1 * H, x2 * W, y2 * H], outline=COL[c], width=3)
            f = out / f"{a.cmd}_{a.pool}_{i:04d}.jpg"
            im.save(f, quality=88)
            print(f)
    elif a.cmd == "crop":
        i = a.idx[0]
        im = ImageOps.exif_transpose(Image.open(path_of(a, rows[i]))).convert("RGB")
        W, H = im.size
        x1, y1, x2, y2 = a.box
        c = im.crop((int(x1 * W), int(y1 * H), int(x2 * W), int(y2 * H)))
        c = c.resize((1024, max(1, round(c.size[1] * 1024 / c.size[0]))), Image.BILINEAR)
        # grid in the crop's own frame mapped back to full-image coordinates
        d = ImageDraw.Draw(c)
        for k in range(1, 10):
            xx, yy = c.size[0] * k // 10, c.size[1] * k // 10
            d.line([(xx, 0), (xx, c.size[1])], fill=(0, 255, 255))
            d.line([(0, yy), (c.size[0], yy)], fill=(0, 255, 255))
            d.text((xx + 2, 2), f"{x1 + (x2 - x1) * k / 10:.3f}", fill=(255, 255, 0), font=font(12))
            d.text((2, yy + 2), f"{y1 + (y2 - y1) * k / 10:.3f}", fill=(255, 255, 0), font=font(12))
        f = out / f"crop_{a.pool}_{i:04d}.jpg"
        c.save(f, quality=88)
        print(f)
    elif a.cmd == "write":
        assert a.status and (len(a.idx) == 1 or a.id)
        r = {"id": a.id} if a.id else rows[a.idx[0]]
        lines = []
        for b in (a.b if a.status != "unusable" else []):
            v = b.split()
            c = int(v[0])
            x1, x2 = sorted((float(v[1]), float(v[3])))
            y1, y2 = sorted((float(v[2]), float(v[4])))
            assert c in (0, 1) and 0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1, b
            lines.append(f"{c} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}")
        p = Path(a.labels_root) / a.pool / f"{r['id']}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines) + ("\n" if lines else ""))
        sp = Path(a.status_dir) / f"status_{a.pool}.csv"
        new = not sp.exists()
        sp.parent.mkdir(parents=True, exist_ok=True)
        with open(sp, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "pool", "status", "n_pothole", "n_bump", "time", "labeller"])
            if new:
                w.writeheader()
            w.writerow({"id": r["id"], "pool": a.pool, "status": a.status,
                        "n_pothole": sum(l.startswith("0 ") for l in lines), "n_bump": sum(l.startswith("1 ") for l in lines),
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"), "labeller": "claude"})
        print(a.id or a.idx[0], r["id"], a.status, lines)


if __name__ == "__main__":
    main()
