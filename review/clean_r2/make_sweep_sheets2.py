"""Sweep sheets of the NOT-flagged val images (excluding the G00 GoPro set), to find systematic label errors the
model shares (manhole, crosswalk, patch boxed as hazard). Box number = line in the label file. Green = pothole, blue = bump."""
import csv, json
from pathlib import Path
from PIL import Image, ImageDraw
import sys
SPLIT, FAM = sys.argv[1], sys.argv[2]
FILTER = (lambda r: "/G00" not in r["sample_id"]) if FAM == "noG00" else (lambda r: r["sample_id"].split("/")[-1].startswith(FAM))
ROOT = Path(__file__).resolve().parents[2]; DS = ROOT / "road_hazards_v3a_r1"; HERE = Path(__file__).parent
flagged = {r["out_image"] for r in csv.DictReader(open(HERE / "label_error_ranking.csv", encoding="utf-8")) if float(r["score"]) > 0}
rows = [r for r in csv.DictReader(open(DS / "manifest.csv", encoding="utf-8"))
        if r["split"] == SPLIT and FILTER(r) and r["out_image"] not in flagged]
TW, COLS, PER = 300, 6, 24
index = []
for p in range(0, len(rows), PER):
    tiles = []
    for j, r in enumerate(rows[p:p + PER]):
        n = p + j
        im = Image.open(DS / r["out_image"]).convert("RGB"); w, h = im.size; im = im.resize((TW, int(h * TW / w))); d = ImageDraw.Draw(im)
        for k, l in enumerate((DS / "labels" / SPLIT / (Path(r["out_image"]).stem + ".txt")).read_text().split("\n")):
            t = l.split()
            if not t: continue
            c, x, y, bw, bh = int(t[0]), *map(float, t[1:])
            col = (0, 255, 0) if c == 0 else (0, 160, 255)
            d.rectangle([(x - bw/2)*TW, (y - bh/2)*im.height, (x + bw/2)*TW, (y + bh/2)*im.height], outline=col, width=2)
            d.text(((x - bw/2)*TW + 2, (y - bh/2)*im.height + 1), str(k), fill=col)
        d.rectangle([0, 0, TW, 12], fill=(0, 0, 0)); d.text((2, 0), f"S{n}", fill=(255, 255, 0))
        tiles.append(im); index.append({"S": n, "out_image": r["out_image"], "sample_id": r["sample_id"]})
    rh = min(max(t.height for t in tiles), 420)
    sh = Image.new("RGB", (COLS * TW, rh * ((len(tiles) + COLS - 1) // COLS)), (40, 40, 40))
    for i, t in enumerate(tiles): sh.paste(t.crop((0, 0, TW, min(t.height, rh))), ((i % COLS) * TW, (i // COLS) * rh))
    sh.save(HERE / "sheets" / f"sweep_{SPLIT}_{FAM}_{p:03d}.jpg", quality=70)
json.dump(index, open(HERE / f"sweep_{SPLIT}_{FAM}_index.json", "w"))
print(len(rows), "images,", (len(rows) + PER - 1) // PER, "sheets")
