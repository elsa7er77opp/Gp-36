"""Check a folder of candidate images against the protected GP36 evaluation sets, using hashes only.

    python tools/leak_check.py <image_dir> <out.csv> [--hashes review/new_data_r3/protected_hashes.npz]

protected_hashes.npz holds, for every image of road_hazards_v3a_r2 (train/val/test), the external BD87 test and
the val/test splits of every parts_r3 part: 64-bit dHash, 64-bit pHash, an id string, and all SHA-256 values.
No pixels. A candidate image is a HIT when its SHA-256 is known, or when (dHash over 8 flips/rotations <= 4
AND pHash <= 10) for some protected image (the same rule as tools/build_part.py). Writes one row per image
with the closest protected id and distances, and prints how many hits fall on val/test/external sets.
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gp36data.hashing import dhash, phash  # noqa: E402
from new_data_forensics import DIHEDRAL  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image_dir")
    ap.add_argument("out_csv")
    ap.add_argument("--hashes", default=str(Path(__file__).resolve().parents[1] / "review/new_data_r3/protected_hashes.npz"))
    args = ap.parse_args()
    z = np.load(args.hashes, allow_pickle=False)
    RD, RP, ids, shas = z["dhash"], z["phash"], z["id"], set(z["sha256"].tolist())
    rows, hits = [], {"eval": 0, "r2_train": 0}
    for f in sorted(p for p in Path(args.image_dir).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")):
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        with Image.open(f) as im:
            im.draft("RGB", (512, 512))
            im = im.convert("RGB")
            d8 = np.array([dhash(im if t is None else im.transpose(t)) for t in DIHEDRAL], dtype=np.uint64)
            ph = np.uint64(phash(im))
        dd = np.min(np.stack([np.bitwise_count(np.bitwise_xor(RD, v)) for v in d8]), axis=0)
        pp = np.bitwise_count(np.bitwise_xor(RP, ph))
        j = int(np.argmin(dd + pp))
        hit = sha in shas or bool(np.any((dd <= 4) & (pp <= 10)))
        k = int(np.nonzero((dd <= 4) & (pp <= 10))[0][0]) if hit and sha not in shas else j
        where = str(ids[k])
        if hit:
            hits["r2_train" if where.startswith("train:") else "eval"] += 1
        rows.append({"image": str(f), "hit": hit, "exact": sha in shas, "closest_id": where,
                     "dhash": int(dd[k]), "phash": int(pp[k])})
    with open(args.out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} images; hits on protected EVAL sets (val/test/external): {hits['eval']}; "
          f"hits on r2 train (duplicates, no value): {hits['r2_train']} -> {args.out_csv}")


if __name__ == "__main__":
    main()
