"""Compact rotation check for rf8 IMG_* in a split: 12 images per sheet, each as [stored | rotated 90 CW] with the same boxes."""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[2]; D = R / "road_hazards_v3a"
split = sys.argv[1]
man = sorted((r for r in csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")) if r["split"] == split and "/IMG_" in r["sample_id"]), key=lambda r: r["sample_id"])
built = {r["sample_id"]: r for r in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
P, PER, COLS = 190, 12, 3; font = ImageFont.load_default(); idx = []
for si in range(0, len(man), PER):
    chunk = man[si:si + PER]; S = Image.new("RGB", (COLS * (2 * P + 14), 4 * (P + 14)), "white"); dS = ImageDraw.Draw(S)
    for ci, r in enumerate(chunk):
        b = built[r["sample_id"]]; im = Image.open(D / b["out_image"]).convert("RGB"); im.thumbnail((600, 600))
        lb = [l.split() for l in open(D / (b["out_image"].replace("images/", "labels/", 1).rsplit(".", 1)[0] + ".txt")) if l.strip()]
        X0, Y0 = (ci % COLS) * (2 * P + 14), (ci // COLS) * (P + 14)
        for k, img in enumerate((im, im.rotate(-90, expand=True))):
            t = img.copy(); t.thumbnail((P, P)); d = ImageDraw.Draw(t)
            for c, x, y, w, h in lb:
                x, y, w, h = map(float, (x, y, w, h)); d.rectangle([(x - w / 2) * t.width, (y - h / 2) * t.height, (x + w / 2) * t.width, (y + h / 2) * t.height], outline=(255, 0, 0) if c == "0" else (0, 90, 255), width=3)
            S.paste(t, (X0 + k * (P + 4), Y0 + 12))
        cell = f"{split[:2].upper()}{si // PER + 1:02d}-{ci + 1:02d}"
        dS.text((X0 + 2, Y0), f"{cell} {Path(r['sample_id']).name[:8]}", fill="black", font=font)
        idx.append({"cell": cell, "sample_id": r["sample_id"], "split": split})
    S.save(R / f"review/v3a_r1_test_review/sheets/rot_{split}_{si // PER + 1:02d}.jpg", quality=85)
with open(R / f"review/v3a_r1_test_review/rotation_index_{split}_all.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["cell", "sample_id", "split"]); w.writeheader(); w.writerows(idx)
print(split, len(man), "sheets", (len(man) + PER - 1) // PER)
