"""rf8 IMG_* phone photos: show each as stored and rotated 90 deg CW, with the SAME normalized boxes drawn on both.
If the boxes only land on damage in the rotated view, the stored pixels are sideways relative to the labels."""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[2]; D = R / "road_hazards_v3a"
split = sys.argv[1]
man = [r for r in csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")) if r["split"] == split and "/IMG_" in r["sample_id"]]
man.sort(key=lambda r: r["sample_id"]); built = {r["sample_id"]: r for r in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
P, PER = 230, 12; font = ImageFont.load_default(); idx = []
for si in range(0, len(man), PER):
    chunk = man[si:si + PER]; S = Image.new("RGB", (4 * (P + 6), 3 * (P + 16)), "white"); dS = ImageDraw.Draw(S)
    for ci, r in enumerate(chunk):
        b = built[r["sample_id"]]; im = Image.open(D / b["out_image"]).convert("RGB")
        lb = [l.split() for l in open(D / (b["out_image"].replace("images/", "labels/", 1).rsplit(".", 1)[0] + ".txt")) if l.strip()]
        for k, img in enumerate((im, im.rotate(-90, expand=True))):
            t = img.copy(); t.thumbnail((P, P)); d = ImageDraw.Draw(t)
            for c, x, y, w, h in lb:
                x, y, w, h = map(float, (x, y, w, h)); d.rectangle([(x - w / 2) * t.width, (y - h / 2) * t.height, (x + w / 2) * t.width, (y + h / 2) * t.height], outline=(255, 0, 0) if c == "0" else (0, 90, 255), width=3)
            X = ((ci % 2) * 2 + k) * (P + 6); Y = (ci // 2) * (P + 16) if False else (ci // 2 % 3) * (P + 16)
            S.paste(t, (X, Y + 14))
        cell = f"{split[0].upper()}ROT{si // PER + 1:02d}-{ci + 1:02d}"
        dS.text(((ci % 2) * 2 * (P + 6) + 2, (ci // 2 % 3) * (P + 16) + 1), f"{cell} {Path(r['sample_id']).name[:12]}  [stored | 90CW]", fill="black", font=font)
        idx.append({"cell": cell, "sample_id": r["sample_id"], "split": split})
        if ci == 5:
            S.save(R / f"review/v3a_r1_test_review/sheets/{split}_ROT{si // PER + 1:02d}a.jpg", quality=85)
            S = Image.new("RGB", (4 * (P + 6), 3 * (P + 16)), "white"); dS = ImageDraw.Draw(S)
    S.save(R / f"review/v3a_r1_test_review/sheets/{split}_ROT{si // PER + 1:02d}b.jpg", quality=85)
with open(R / f"review/v3a_r1_test_review/rotation_index_{split}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["cell", "sample_id", "split"]); w.writeheader(); w.writerows(idx)
print(split, len(man))
