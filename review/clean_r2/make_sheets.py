"""Contact sheets for the ranked images: labelled boxes in GREEN (G#), v1 predictions conf>=0.25 in RED (P#).
Usage: python make_sheets.py <split> <start> <count> [per_sheet]"""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "road_hazards_v3a_r1"; PRED = ROOT / "runs/detect/runs/clean"
NM = {0: "pot", 1: "bump"}
split, start, count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
per = int(sys.argv[4]) if len(sys.argv) > 4 else 6
rows = [r for r in csv.DictReader(open(Path(__file__).with_name("label_error_ranking.csv"), encoding="utf-8"))
        if r["split"] == split and float(r["score"]) > 0][start:start + count]
out = Path(__file__).with_name("sheets"); out.mkdir(exist_ok=True)
def boxes(p, conf):
    r = []
    if p.exists():
        for l in p.read_text().split("\n"):
            t = l.split()
            if t and (not conf or float(t[5]) >= 0.25):
                r.append((int(t[0]), *map(float, t[1:5]), float(t[5]) if conf else None))
    return r
TW = 620
for s in range(0, len(rows), per):
    chunk = rows[s:s + per]; tiles = []
    for i, r in enumerate(chunk):
        im = Image.open(DS / r["out_image"]).convert("RGB"); w, h = im.size
        sc = TW / w; im = im.resize((TW, int(h * sc))); d = ImageDraw.Draw(im)
        stem = Path(r["out_image"]).stem
        for k, (c, x, y, bw, bh, _) in enumerate(boxes(DS / "labels" / split / f"{stem}.txt", False)):
            d.rectangle([(x - bw/2)*TW, (y - bh/2)*im.height, (x + bw/2)*TW, (y + bh/2)*im.height], outline=(0,255,0), width=3)
            d.text(((x - bw/2)*TW + 3, (y - bh/2)*im.height + 2), f"G{k}{NM[c]}", fill=(0,255,0))
        for k, (c, x, y, bw, bh, cf) in enumerate(boxes(PRED / f"pred_{split}_r1/labels/{stem}.txt", True)):
            d.rectangle([(x - bw/2)*TW, (y - bh/2)*im.height, (x + bw/2)*TW, (y + bh/2)*im.height], outline=(255,0,0), width=2)
            d.text(((x + bw/2)*TW - 60, (y + bh/2)*im.height - 12), f"P{k}{NM[c]}{cf:.2f}", fill=(255,60,60))
        d.rectangle([0, 0, TW, 28], fill=(0,0,0)); d.text((3, 1), f"#{start+s+i} {r['source']} {stem}", fill=(255,255,0)); d.text((3, 14), r['flags'][:110], fill=(200,200,200))
        tiles.append(im)
    cols = 2; rh = max(t.height for t in tiles)
    sheet = Image.new("RGB", (cols * TW, rh * ((len(tiles) + cols - 1) // cols)), (40,40,40))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * TW, (i // cols) * rh))
    p = out / f"{split}_{start+s:04d}.jpg"; sheet.save(p, quality=72); print(p.name, p.stat().st_size)
