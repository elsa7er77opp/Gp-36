"""Numbered crop sheets for a box audit (context crop with the box drawn + a full-frame thumbnail), 40 per sheet.

    python -I tools/audit_crop_sheets.py <export root> <class ids, e.g. 0,1> <out dir OUTSIDE git> [per_sheet] [file list]

Writes <out>/index.csv (idx, file, split, label_sha256, line, class_id, box) and sheet_NNN.jpg. YOLO polygon lines are
converted to their bounding box (bug before 2026-11-04: polygons were read as xc yc w h; see VALTEST_AUDIT_S4.md).
"""
"""Numbered crop sheets for a box audit: each tile = context crop (box x3) with the box drawn, + small full frame."""
import csv, hashlib, sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root, cls_keep, out, per = Path(sys.argv[1]), set(sys.argv[2].split(',')), Path(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 40
only = set(Path(sys.argv[5]).read_text().split()) if len(sys.argv) > 5 else None
out.mkdir(parents=True, exist_ok=True)
rows = []
for lbl in sorted(root.glob('*/labels/*.txt')):
    img = next((lbl.parent.parent / 'images' / (lbl.stem + e) for e in ('.jpg', '.jpeg', '.png') if (lbl.parent.parent / 'images' / (lbl.stem + e)).exists()), None)
    if only is not None and img.name not in only:
        continue
    data = lbl.read_bytes(); sha = hashlib.sha256(data).hexdigest()
    for i, ln in enumerate(data.decode().splitlines()):
        p = ln.split()
        if p and p[0] in cls_keep:
            if len(p) == 5:
                xc, yc, w, h = map(float, p[1:5])
            else:  # YOLO polygon -> its bounding box (same as gp36data.labels)
                xs, ys = list(map(float, p[1::2])), list(map(float, p[2::2]))
                xc, yc, w, h = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)
            rows.append({'idx': len(rows), 'file': img.name, 'split': lbl.parent.parent.name, 'label_sha256': sha, 'line': i, 'class_id': p[0],
                         'xc': xc, 'yc': yc, 'w': w, 'h': h, 'img': str(img), 'poly': len(p) > 5})
with open(out / 'index.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
font = ImageFont.load_default(size=14)
T = 220
for s in range(0, len(rows), per):
    chunk = rows[s:s + per]; cols = 8; rws = math.ceil(len(chunk) / cols)
    sheet = Image.new('RGB', (cols * T, rws * (T + 70)), (40, 40, 40)); d = ImageDraw.Draw(sheet)
    for k, r in enumerate(chunk):
        im = Image.open(r['img']).convert('RGB'); W, H = im.size
        bw, bh = r['w'] * W, r['h'] * H; cx, cy = r['xc'] * W, r['yc'] * H
        side = max(bw, bh) * 2.2 + 40
        x0, y0 = max(0, cx - side / 2), max(0, cy - side / 2); x1, y1 = min(W, cx + side / 2), min(H, cy + side / 2)
        crop = im.crop((int(x0), int(y0), int(x1), int(y1))); sc = T / max(crop.size); crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))))
        dc = ImageDraw.Draw(crop); dc.rectangle([(cx - bw / 2 - x0) * sc, (cy - bh / 2 - y0) * sc, (cx + bw / 2 - x0) * sc, (cy + bh / 2 - y0) * sc], outline=(255, 40, 40), width=2)
        gx, gy = (k % cols) * T, (k // cols) * (T + 70)
        sheet.paste(crop, (gx, gy))
        th = im.copy(); th.thumbnail((90, 60)); dt = ImageDraw.Draw(th); f = th.width / W
        dt.rectangle([(cx - bw / 2) * f, (cy - bh / 2) * f, (cx + bw / 2) * f, (cy + bh / 2) * f], outline=(255, 255, 0))
        sheet.paste(th, (gx + T - th.width, gy + T + 4))
        d.text((gx + 3, gy + T + 4), f"#{r['idx']}", fill=(255, 255, 0), font=font)
        d.text((gx + 3, gy + T + 22), r['file'][:24], fill=(200, 200, 200), font=ImageFont.load_default(size=10))
        d.text((gx + 3, gy + T + 36), f"{r['split']} {int(bw)}x{int(bh)}px", fill=(200, 200, 200), font=ImageFont.load_default(size=10))
    sheet.save(out / f'sheet_{s // per:03d}.jpg', quality=85)
print(len(rows), 'boxes', math.ceil(len(rows) / per), 'sheets')
