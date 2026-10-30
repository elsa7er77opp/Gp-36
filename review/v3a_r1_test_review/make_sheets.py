"""Overlay sheets for the 100% visual review of the v3a_r1 TEST split (read-only on data).
Images/labels are read from road_hazards_v3a (same selection and build settings; only the split differs).
Red = pothole (P), blue = speed_bump (B). Each cell shows sheet-cell id and source."""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[2]
D = R / "road_hazards_v3a"
part, nparts = map(int, sys.argv[1].split("/")) if len(sys.argv) > 1 else (1, 1)
man = [r for r in csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")) if r["split"] == "test"]
built = {r["sample_id"]: r for r in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
def cls_of(r):
    b = built[r["sample_id"]]; return ("both" if int(b["n_pothole"]) and int(b["n_speed_bump"]) else "pothole" if int(b["n_pothole"]) else "speed_bump")
man.sort(key=lambda r: (r["source"], cls_of(r), r["sample_id"]))
PER, COLS, W, H = 12, 4, 420, 315
font = ImageFont.load_default()
idx_rows = []
sheets = [man[i:i + PER] for i in range(0, len(man), PER)]
for si, chunk in enumerate(sheets, 1):
    if (si - 1) % nparts != part - 1: continue
    sheet = Image.new("RGB", (COLS * W, ((len(chunk) + COLS - 1) // COLS) * (H + 16)), "white"); d = ImageDraw.Draw(sheet)
    for ci, r in enumerate(chunk):
        b = built[r["sample_id"]]
        im = Image.open(D / b["out_image"]).convert("RGB"); iw, ih = im.size
        sc = min(W / iw, H / ih); im = im.resize((max(1, int(iw * sc)), max(1, int(ih * sc))))
        dr = ImageDraw.Draw(im)
        lbl = D / b["out_image"].replace("images/", "labels/", 1).rsplit(".", 1)[0]
        for line in open(str(lbl) + ".txt", encoding="utf-8"):
            if not line.strip(): continue
            c, x, y, w, h = line.split()[:5]; x, y, w, h = (float(v) for v in (x, y, w, h))
            col = (255, 0, 0) if c == "0" else (0, 90, 255)
            box = [(x - w / 2) * im.width, (y - h / 2) * im.height, (x + w / 2) * im.width, (y + h / 2) * im.height]
            dr.rectangle(box, outline=col, width=3); dr.text((box[0] + 2, box[1] + 1), "P" if c == "0" else "B", fill=col, font=font)
        x0, y0 = (ci % COLS) * W, (ci // COLS) * (H + 16)
        sheet.paste(im, (x0, y0 + 16))
        cell = f"T{si:02d}-{ci + 1:02d}"
        d.text((x0 + 3, y0 + 2), f"{cell} {r['source']} {Path(r['sample_id']).name[:34]}", fill="black", font=font)
        idx_rows.append({"cell": cell, "sample_id": r["sample_id"], "source": r["source"], "class": cls_of(r),
                         "n_pothole": b["n_pothole"], "n_speed_bump": b["n_speed_bump"], "out_image": b["out_image"]})
    sheet.save(R / f"review/v3a_r1_test_review/sheets/T{si:02d}.jpg", quality=88)
with open(R / f"review/v3a_r1_test_review/sheet_index_part{part}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(idx_rows[0].keys())); w.writeheader(); w.writerows(idx_rows)
print("sheets", len(sheets), "part", part, "cells", len(idx_rows))
