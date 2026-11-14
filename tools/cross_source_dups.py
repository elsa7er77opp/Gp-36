"""Rule-v2 near-duplicates ACROSS sources (parts) and against the protected eval hashes.

    python -I tools/cross_source_dups.py --parts parts_r3/dmd parts_r3/pol ... --out-pairs <pairs.csv> --out-drop <drop.csv>
        [--hashes review/new_data_r3/protected_hashes.npz] [--loose 10 16]

A pair (A in part P, B in part Q, P != Q) is a near-duplicate when dHash <= 4 AND pHash <= 10 under the SAME one of
the 8 flips/rotations (the rule of tools/leak_check.py / build_part.py). Pairs inside one part are ignored (handled
by that part's group split). --loose D P also reports looser pairs (dHash <= D and pHash <= P), flagged rule=loose,
for a visual check only; they do not enter the drop list.
Drop list: every val/test image of a part that has a rule-v2 partner in ANOTHER part (any split) or in the
protected eval hashes (id not starting with 'train:').
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gp36data.hashing import dhash, phash  # noqa: E402
from new_data_forensics import DIHEDRAL  # noqa: E402


def hashes(path):
    with Image.open(path) as im:
        im.draft("RGB", (512, 512))
        im = im.convert("RGB")
        tr = [im if t is None else im.transpose(t) for t in DIHEDRAL]
        return [dhash(x) for x in tr], [phash(x) for x in tr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", nargs="+", required=True)
    ap.add_argument("--out-pairs", required=True)
    ap.add_argument("--out-drop", required=True)
    ap.add_argument("--hashes", default=str(Path(__file__).resolve().parents[1] / "review/new_data_r3/protected_hashes.npz"))
    ap.add_argument("--loose", nargs=2, type=int, default=None)
    a = ap.parse_args()
    for o in (a.out_pairs, a.out_drop):
        if Path(o).exists():
            sys.exit(f"{o} exists; refusing to overwrite")
    rec = []
    for p in a.parts:
        pp = Path(p)
        for m in csv.DictReader(open(pp / "manifest.csv", newline="", encoding="utf-8")):
            d8, p8 = hashes(pp / m["out_image"])
            rec.append({"part": pp.name, "split": m["split"], "file": Path(m["orig_image"]).name, "d8": d8, "p8": p8})
    D = np.array([r["d8"] for r in rec], dtype=np.uint64)  # (n, 8)
    P = np.array([r["p8"] for r in rec], dtype=np.uint64)
    parts = np.array([r["part"] for r in rec])
    pairs, drop = [], {}
    lo = a.loose or (4, 10)
    for i in range(len(rec)):
        other = np.nonzero(parts[i + 1:] != parts[i])[0] + i + 1
        if not len(other):
            continue
        dd = np.bitwise_count(D[i][:, None] ^ D[other, 0][None, :])  # candidate i transformed vs others unrotated
        pq = np.bitwise_count(P[i][:, None] ^ P[other, 0][None, :])
        strict = ((dd <= 4) & (pq <= 10)).any(axis=0)
        loose = ((dd <= lo[0]) & (pq <= lo[1])).any(axis=0)
        for k in np.nonzero(strict | loose)[0]:
            j = other[k]
            t = int(np.argmin(dd[:, k] + pq[:, k]))
            rule = "v2" if strict[k] else "loose"
            pairs.append({"rule": rule, "part_a": rec[i]["part"], "split_a": rec[i]["split"], "file_a": rec[i]["file"],
                          "part_b": rec[j]["part"], "split_b": rec[j]["split"], "file_b": rec[j]["file"],
                          "dhash": int(dd[t, k]), "phash": int(pq[t, k])})
            if rule == "v2":
                for x, y in ((i, j), (j, i)):
                    if rec[x]["split"] in ("val", "test"):
                        drop.setdefault((rec[x]["part"], rec[x]["split"], rec[x]["file"]), f"near {rec[y]['part']}/{rec[y]['split']}/{rec[y]['file']}")
    z = np.load(a.hashes, allow_pickle=False)
    RD, RP, ids = z["dhash"], z["phash"], z["id"]
    ev = np.array([not str(s).startswith("train:") for s in ids])
    for r in rec:
        dd = np.bitwise_count(np.array(r["d8"], dtype=np.uint64)[:, None] ^ RD[None, :])
        pq = np.bitwise_count(np.array(r["p8"], dtype=np.uint64)[:, None] ^ RP[None, :])
        hit = ((dd <= 4) & (pq <= 10)).any(axis=0)
        for k in np.nonzero(hit)[0]:
            pairs.append({"rule": "v2_protected", "part_a": r["part"], "split_a": r["split"], "file_a": r["file"],
                          "part_b": "protected", "split_b": str(ids[k]).split(":")[0], "file_b": str(ids[k]),
                          "dhash": int(dd[:, k].min()), "phash": int(pq[:, k].min())})
            if ev[k] or r["split"] in ("val", "test"):
                drop.setdefault((r["part"], r["split"], r["file"]), f"near protected {ids[k]}")
    with open(a.out_pairs, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rule", "part_a", "split_a", "file_a", "part_b", "split_b", "file_b", "dhash", "phash"])
        w.writeheader()
        w.writerows(pairs)
    with open(a.out_drop, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["part", "split", "file", "reason"])
        for (p, s, fn), why in sorted(drop.items()):
            w.writerow([p, s, fn, why])
    from collections import Counter
    print(len(rec), "images;", Counter(p["rule"] for p in pairs), "; val/test drops:", len(drop))
    print(Counter((p["part_a"], p["part_b"]) for p in pairs if p["rule"] == "v2"))


if __name__ == "__main__":
    main()
