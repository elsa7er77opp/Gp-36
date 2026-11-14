"""Contact sheets of egm TRAIN-creator frames ranked by C's speed-bump score (STATUS Stage 37b). No boxes are drawn:
the ranking only chooses which frames are looked at. Writes <out>/cand_list.csv (rank, image, id, sequence, max_bump)
and sheets <out>/cand_<start>.jpg with 9 frames each (label = rank)."""
import argparse, csv, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ap = argparse.ArgumentParser()
ap.add_argument('--mine', required=True); ap.add_argument('--leak', required=True)
ap.add_argument('--out', required=True); ap.add_argument('--n', type=int, default=90)
ap.add_argument('--per-seq', type=int, default=3); ap.add_argument('--key', default='max_bump')
ap.add_argument('--root', default='')
a = ap.parse_args()
hit = {r['image'] for r in csv.DictReader(open(a.leak)) if r['hit'] == 'True'}
rows = [r for r in csv.DictReader(open(a.mine)) if r['image'] not in hit]
rows.sort(key=lambda r: -float(r[a.key]))
per, sel = {}, []
for r in rows:
    if per.get(r['sequence'], 0) >= a.per_seq: continue
    per[r['sequence']] = per.get(r['sequence'], 0) + 1
    sel.append(r)
    if len(sel) >= a.n: break
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
with open(out / 'cand_list.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['rank', 'image', 'id', 'sequence', a.key])
    for k, r in enumerate(sel): w.writerow([k, r['image'], r['id'], r['sequence'], r[a.key]])
try: fnt = ImageFont.truetype('DejaVuSans-Bold.ttf', 18)
except OSError: fnt = ImageFont.load_default()
def load(p):
    im = Image.open(Path(a.root) / p.replace('\\', '/')); im.draft('RGB', (1280, 1280))
    im = ImageOps.exif_transpose(im).convert('RGB'); W, H = im.size
    return im.resize((640, round(H * 640 / W)))
for s in range(0, len(sel), 9):
    tiles = [load(r['image']) for r in sel[s:s + 9]]
    th = max(t.size[1] for t in tiles)
    sh = Image.new('RGB', (1920, th * ((len(tiles) + 2) // 3)), (30, 30, 30)); d = ImageDraw.Draw(sh)
    for k, t in enumerate(tiles):
        x, y = 640 * (k % 3), th * (k // 3); sh.paste(t, (x, y))
        d.rectangle([x, y, x + 70, y + 26], fill=(0, 0, 0)); d.text((x + 4, y + 3), f'c{s + k}', fill=(255, 255, 0), font=fnt)
    sh.save(out / f'cand_{s:03d}.jpg', quality=85)
print(len(sel), 'selected; sheets in', out)
