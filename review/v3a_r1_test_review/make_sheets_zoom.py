"""rf8 test images: each cell = full frame (left) + zoom on the labelled region (right), so far/tiny boxes can be judged.
Red = pothole (P), blue = speed_bump (B). Cell id Rxx-yy. Read-only on data."""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[2]; D = R / "road_hazards_v3a"
part, nparts = map(int, sys.argv[1].split("/"))
src = sys.argv[2] if len(sys.argv) > 2 else "rf8"
man = [r for r in csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")) if r["split"] == "test" and r["source"] == src]
built = {r["sample_id"]: r for r in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
man.sort(key=lambda r: r["sample_id"])
FW, FH, ZW, ZH, PER = 280, 210, 360, 270, 8
font = ImageFont.load_default(); rows = []
def boxes(b):
    p = D / (b["out_image"].replace("images/", "labels/", 1).rsplit(".", 1)[0] + ".txt")
    return [(l.split()[0], *map(float, l.split()[1:5])) for l in open(p, encoding="utf-8") if l.strip()]
def draw(im, bx, ox=0, oy=0, sc=1.0, w=2):
    d = ImageDraw.Draw(im)
    for c, x0, y0, x1, y1 in bx:
        col = (255, 0, 0) if c == "0" else (0, 90, 255)
        r = [(x0 - ox) * sc, (y0 - oy) * sc, (x1 - ox) * sc, (y1 - oy) * sc]
        d.rectangle(r, outline=col, width=w); d.text((r[0] + 2, r[1] + 1), "P" if c == "0" else "B", fill=col, font=font)
sheets = [man[i:i + PER] for i in range(0, len(man), PER)]
for si, chunk in enumerate(sheets, 1):
    if (si - 1) % nparts != part - 1: continue
    S = Image.new("RGB", (2 * (FW + ZW + 10), 4 * (ZH + 16)), "white"); dS = ImageDraw.Draw(S)
    for ci, r in enumerate(chunk):
        b = built[r["sample_id"]]; im = Image.open(D / b["out_image"]).convert("RGB"); W, H = im.size
        bx = [(c, (x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H) for c, x, y, w, h in boxes(b)]
        full = im.copy(); sc = min(FW / W, FH / H); full = full.resize((int(W * sc), int(H * sc))); draw(full, bx, sc=sc, w=2)
        if bx:
            x0 = min(b_[1] for b_ in bx); y0 = min(b_[2] for b_ in bx); x1 = max(b_[3] for b_ in bx); y1 = max(b_[4] for b_ in bx)
            cw = max((x1 - x0) * 1.6, 240); ch = max((y1 - y0) * 1.6, 180)
            cw, ch = max(cw, ch * 4 / 3), max(ch, cw * 3 / 4)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            l, t = max(0, min(W - cw, cx - cw / 2)), max(0, min(H - ch, cy - ch / 2))
            crop = im.crop((int(l), int(t), int(min(W, l + cw)), int(min(H, t + ch))))
            zs = min(ZW / crop.width, ZH / crop.height); crop = crop.resize((int(crop.width * zs), int(crop.height * zs)))
            draw(crop, bx, ox=l, oy=t, sc=zs, w=2)
        else:
            crop = Image.new("RGB", (ZW, ZH), (230, 230, 230))
        X = (ci % 2) * (FW + ZW + 10); Y = (ci // 2) * (ZH + 16)
        S.paste(full, (X, Y + 16)); S.paste(crop, (X + FW + 4, Y + 16))
        cell = f"R{si:02d}-{ci + 1}"
        dS.text((X + 2, Y + 2), f"{cell} {Path(r['sample_id']).name[:40]} P{b['n_pothole']} B{b['n_speed_bump']}", fill="black", font=font)
        rows.append({"cell": cell, "sample_id": r["sample_id"], "n_pothole": b["n_pothole"], "n_speed_bump": b["n_speed_bump"], "out_image": b["out_image"]})
    S.save(R / f"review/v3a_r1_test_review/sheets/R{si:02d}.jpg", quality=88)
with open(R / f"review/v3a_r1_test_review/zoom_index_part{part}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("sheets", len(sheets), "part", part, "cells", len(rows))
