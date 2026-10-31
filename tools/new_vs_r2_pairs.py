"""Sheets of new-image <-> r2 near-duplicate pairs, for visual confirmation of the dedup threshold.

    python -I tools/new_vs_r2_pairs.py --forensics review/new_data_r2b --set sub5 --splits val test
Writes <forensics>/pairs_<set>_<splits>.csv and sheets/pairs_<set>_<splits>_NN.jpg (does not overwrite).
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # tools/ (python -I drops the script dir)
from gp36data.hashing import dhash, phash  # noqa: E402
from gp36data.overlay import contact_sheet, tile  # noqa: E402
from new_data_forensics import DIHEDRAL, load_small  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forensics", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--splits", nargs="+", default=["val", "test"])
    ap.add_argument("--r2", default="road_hazards_v3a_r2")
    ap.add_argument("--dh", type=int, default=4)
    ap.add_argument("--ph", type=int, default=10)
    ap.add_argument("--per-sheet", type=int, default=8)
    args = ap.parse_args()
    fdir, r2 = Path(args.forensics), Path(args.r2)
    tag = f"{args.set}_{'_'.join(args.splits)}"
    out_csv = fdir / f"pairs_{tag}.csv"
    if out_csv.exists():
        sys.exit(f"{out_csv} exists")
    refs = []
    with open(r2 / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            if m["split"] in args.splits:
                im = load_small(r2 / m["out_image"])
                refs.append((m["split"], m["sample_id"], r2 / m["out_image"], dhash(im), phash(im)))
    RD = np.array([r[3] for r in refs], dtype=np.uint64)
    RP = np.array([r[4] for r in refs], dtype=np.uint64)
    pairs = []
    with open(fdir / "new_images.csv", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["set"] == args.set and r["ok"] == "True"
                and any(int(r[f"near_r2_{s}"] or 0) for s in args.splits)]
    for r in rows:
        with Image.open(r["image"]) as im:
            im = im.convert("RGB")
            d8 = np.array([dhash(im if t is None else im.transpose(t)) for t in DIHEDRAL], dtype=np.uint64)
            ph = phash(im)
        dd = np.min(np.stack([np.bitwise_count(np.bitwise_xor(RD, v)) for v in d8]), axis=0)
        pp = np.bitwise_count(np.bitwise_xor(RP, np.uint64(ph)))
        for j in np.nonzero((dd <= args.dh) & (pp <= args.ph))[0]:
            pairs.append((r["file"], r["image"], refs[j][0], refs[j][1], str(refs[j][2]), int(dd[j]), int(pp[j])))
    pairs.sort(key=lambda p: -(p[5] + p[6]))  # borderline first
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["new_file", "new_image", "r2_split", "r2_sample", "r2_image", "dhash", "phash"])
        w.writerows(pairs)
    sd = fdir / "sheets"
    sd.mkdir(exist_ok=True)
    for k in range(0, min(len(pairs), args.per_sheet * 4), args.per_sheet):
        tiles = []
        for p in pairs[k:k + args.per_sheet]:
            for path, cap in ((p[1], f"NEW {args.set}/{p[0][:40]}"), (p[4], f"r2 {p[2]}: {p[3][-44:]}")):
                with Image.open(path) as im:
                    tiles.append(tile(im.convert("RGB"), [cap, f"dh={p[5]} ph={p[6]}"], width=400))
        contact_sheet(tiles, cols=4, title=f"{tag}: new vs r2 near-duplicates, sheet {k // args.per_sheet + 1}").save(
            sd / f"pairs_{tag}_{k // args.per_sheet + 1:02d}.jpg", quality=85)
    print(len(rows), "new images with a match;", len(pairs), "pairs ->", out_csv)


if __name__ == "__main__":
    main()
