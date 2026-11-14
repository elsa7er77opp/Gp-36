"""Check a folder of candidate images against the protected GP36 evaluation sets, using hashes only.

    python tools/leak_check.py <image_dir> <out.csv> [--hashes review/new_data_r3/protected_hashes.npz]

protected_hashes.npz holds, for every image of road_hazards_v3a_r2 (train/val/test), the external BD87 test and
the val/test splits of every parts_r3 part: 64-bit dHash, 64-bit pHash, an id string, and all SHA-256 values.
No pixels. A candidate image is a HIT when its SHA-256 is known, or when (dHash over 8 flips/rotations <= 4
AND pHash <= 10, both under the SAME flip/rotation) for some protected image (the same rule as
tools/build_part.py). Until 2026-11-04 the pHash was compared unrotated only, so flipped copies were missed
(found by tests/test_leak_check.py; see review/new_data_r3/CLOUD_REPORT.md). Writes one row per image
with the closest protected id and distances, and prints how many hits fall on val/test/external sets.
It also flags file names of known re-upload / already-used families (KNOWN_FAMILIES), a cheap first filter
that works even when the pixels were re-encoded. Functions are importable (tests/test_leak_check.py).
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


KNOWN_FAMILIES = {
    # file-name families that are already used or are re-uploads of protected sets (CANDIDATES.md, task brief)
    "Image000xx / Image-N- (rf8 / sb15 family)": r"^[Ii]mage[-_ ]?\(?\d+",
    "MVI_15xx (rf8 video family)": r"^MVI_15\d\d",
    "VID_20190924 (rf8 video family)": r"^VID_20190924",
    "G00xxxxx (Nienaber GoPro = r2 val/test family)": r"^G00\d{5}",
    "newonetrwww (sub5 family)": r"^newonetrwww",
    "speedbreakerrefinedone (rejected family)": r"^speedbreakerrefinedone",
    "rdd_ (RDD2022, already held)": r"^rdd_|^(Japan|India|Czech|Norway|United_States|China_Drone|China_MotorBike)_\d+",
    "kg_/dz_ (part sr, already used)": r"^(kg|dz)_",
    "potholesN (andrewmvd / ghpot family)": r"^potholes\d+",
    "SpeedBreaker-N- (rf8 re-upload: yolov7-tipdu/speed-breaker-ffvo0, 59 rf8-val hits, session 5)": r"^SpeedBreaker-\d+-",
}


def family(name):
    """Name of the known family a file name belongs to, or None (Roboflow '_jpg.rf.<hash>' suffix ignored)."""
    import re
    stem = re.sub(r"(_(jpe?g|png|JPE?G|PNG))?\.rf\.[0-9a-f]{20,32}$", "", Path(name).stem)
    for k, rx in KNOWN_FAMILIES.items():
        if re.search(rx, stem):
            return k
    return None


def load_protected(path):
    z = np.load(path, allow_pickle=False)
    return z["dhash"], z["phash"], z["id"], set(z["sha256"].tolist())


def check_image(f, RD, RP, ids, shas):
    """One candidate image vs the protected hashes -> row dict (same rule as tools/build_part.py)."""
    sha = hashlib.sha256(Path(f).read_bytes()).hexdigest()
    with Image.open(f) as im:
        im.draft("RGB", (512, 512))
        im = im.convert("RGB")
        tr = [im if t is None else im.transpose(t) for t in DIHEDRAL]
        d8 = np.array([dhash(x) for x in tr], dtype=np.uint64)
        p8 = np.array([phash(x) for x in tr], dtype=np.uint64)
    # the SAME transform is applied to both hashes (a flipped copy keeps its dHash only under the flip,
    # and likewise its pHash): shape (8, n_protected)
    D = np.stack([np.bitwise_count(np.bitwise_xor(RD, v)) for v in d8])
    P = np.stack([np.bitwise_count(np.bitwise_xor(RP, v)) for v in p8])
    near8 = (D <= 4) & (P <= 10)
    near = near8.any(axis=0)
    t_best = np.argmin(D + P, axis=0)
    dd, pp = D[t_best, np.arange(D.shape[1])], P[t_best, np.arange(P.shape[1])]
    j = int(np.argmin(dd + pp))
    hit = sha in shas or bool(near.any())
    k = j
    if near.any():
        # report an EVAL hit when there is one: a duplicate of an r2 TRAIN image listed first must not hide it
        cand = np.nonzero(near)[0]
        ev = [c for c in cand if not str(ids[c]).startswith("train:")]
        k = int(ev[0] if ev else cand[0])
    return {"image": str(f), "hit": hit, "exact": sha in shas, "closest_id": str(ids[k]),
            "dhash": int(dd[k]), "phash": int(pp[k]), "family": family(Path(f).name) or ""}


def images_under(d):
    return sorted(p for p in Path(d).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image_dir")
    ap.add_argument("out_csv")
    ap.add_argument("--hashes", default=str(Path(__file__).resolve().parents[1] / "review/new_data_r3/protected_hashes.npz"))
    args = ap.parse_args()
    RD, RP, ids, shas = load_protected(args.hashes)
    rows, hits = [], {"eval": 0, "r2_train": 0}
    for f in images_under(args.image_dir):
        r = check_image(f, RD, RP, ids, shas)
        if r["hit"]:
            hits["r2_train" if r["closest_id"].startswith("train:") else "eval"] += 1
        rows.append(r)
    if not rows:
        sys.exit(f"no images under {args.image_dir}")
    with open(args.out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fams = {}
    for r in rows:
        if r["family"]:
            fams[r["family"]] = fams.get(r["family"], 0) + 1
    print(f"{len(rows)} images; hits on protected EVAL sets (val/test/external): {hits['eval']}; "
          f"hits on r2 train (duplicates, no value): {hits['r2_train']} -> {args.out_csv}")
    if fams:
        print("known re-upload families by file name:", fams)


if __name__ == "__main__":
    main()
