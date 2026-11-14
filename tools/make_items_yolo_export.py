"""Items CSV (input of tools/build_part.py) for a Roboflow / Kaggle YOLO export that has no drive or video ids.

    python -I tools/make_items_yolo_export.py --root <unzipped export> --part <short> \
        --cmap '{"0": "speed_bump", "1": "speed_bump", "2": "ignore"}' --out review/new_data_r3/items/items_<short>.csv \
        [--all-train] [--exclude-family-hits review/new_data_r3/vet/<short>/vet.json] [--max-per-group 4]

Rules (the same as make_items_sr.py, written down before any model sees the data):
1. class map is explicit; every source id must appear (build_part.py exits on an unmapped id).
   Rumble strips -> "ignore" (D6); flat zebra crossings / manholes / cracks / patches -> "ignore" (D1, D5);
   raised crossings, humps, marked or unmarked bumps -> "speed_bump" (D2).
2. Roboflow augmented copies: images are grouped by base name (stem without `_jpg.rf.<hash>`); ONE copy per base
   is kept (the lexicographically first, so the choice is reproducible).
3. Known re-upload families (tools/leak_check.py KNOWN_FAMILIES) are dropped by file name.
4. Group key = numeric block of the name when names end in a frame/photo number (`..._123` -> block of 25),
   joined (union-find) with within-source near-duplicates under the leak rule (dHash <= 4 and pHash <= 10 under
   the same flip/rotation), so copies of one picture never straddle splits. Groups, not frames, are split.
   (Looser thresholds chained low-texture road frames into one giant group: tried and rejected 2026-11-04.)
5. Split: groups sorted by (-hazard boxes, id); every 6th group -> val, the next -> test, rest train
   (~2/3 train), like make_items_sr.py. --all-train sends everything to train (use it for single-location sets).
6. --max-per-group caps the images kept per group (most hazard boxes first), so one place does not dominate.
8. --group-regex: group key from the name (e.g. the video id), before the numeric-block fallback; --block sets
   the numeric block size (default 25).
7. --include / --exclude: regular expressions on the base name (full match) to keep one family only, e.g.
   --include "[0-9]{3,}" keeps bare numeric names >= 100.
The source's own train/valid/test split is ignored (Roboflow splits are by image, so copies leak across them).
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leak_check import family, images_under  # noqa: E402
from vet_source import base_name, hashes, label_for  # noqa: E402


def cluster(H, P8, dthr=4, pthr=10):
    """Group key: near-duplicates under the same flip/rotation (looser thresholds than the leak rule)."""
    D0 = np.array([h[0] for h in H], dtype=np.uint64)
    P0 = np.array([p[0] for p in P8], dtype=np.uint64)
    par = list(range(len(H)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, h in enumerate(H):
        dd = np.bitwise_count(np.asarray(h, dtype=np.uint64)[:, None] ^ D0[None, :])
        pp = np.bitwise_count(np.asarray(P8[i], dtype=np.uint64)[:, None] ^ P0[None, :])
        for j in np.nonzero(((dd <= dthr) & (pp <= pthr)).any(axis=0))[0]:
            if j != i:
                par[f(i)] = f(int(j))
    return [f(i) for i in range(len(H))]


def assign_splits(group_haz, all_train=False):
    if all_train:
        return {g: "train" for g in group_haz}
    order = sorted(group_haz, key=lambda k: (-group_haz[k], k))
    return {g: "val" if i % 6 == 2 else "test" if i % 6 == 5 else "train" for i, g in enumerate(order)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--cmap", required=True, help='JSON {src_id: "pothole"|"speed_bump"|"ignore"}')
    ap.add_argument("--out", required=True)
    ap.add_argument("--all-train", action="store_true")
    ap.add_argument("--max-per-group", type=int, default=0)
    ap.add_argument("--keep-family", action="append", default=[], help="known family to keep anyway (rare)")
    ap.add_argument("--group-regex", help="regex whose first capture group (re.search on the base name) is the group "
                    "key, e.g. a video id; images without a match fall back to the numeric name block")
    ap.add_argument("--block", type=int, default=25, help="numeric name block size for the fallback group key")
    ap.add_argument("--include", help="regex: keep only images whose Roboflow BASE name matches (re.fullmatch)")
    ap.add_argument("--exclude", help="regex: drop images whose base name matches (re.fullmatch)")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    cmap = json.loads(a.cmap)
    bad = {v for v in cmap.values()} - {"pothole", "speed_bump", "ignore"}
    if bad:
        sys.exit(f"bad target names {bad}")
    by_base, dropped_fam = {}, 0
    for img in images_under(a.root):
        fam = family(img.name)
        if fam and fam not in a.keep_family:
            dropped_fam += 1
            continue
        b = base_name(img.stem)
        if (a.include and not re.fullmatch(a.include, b)) or (a.exclude and re.fullmatch(a.exclude, b)):
            continue
        if b not in by_base or str(img) < str(by_base[b]):
            by_base[b] = img
    rows = []
    for b, img in sorted(by_base.items()):
        lbl = label_for(img)
        ids = [ln.split()[0] for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()] if lbl else []
        unknown = set(ids) - set(cmap)
        if unknown:
            sys.exit(f"{lbl}: ids {unknown} not in --cmap")
        haz = sum(cmap[i] != "ignore" for i in ids)
        d8, ph = hashes(img)
        m = re.search(r"(\d+)$", b)
        g = re.search(a.group_regex, b) if a.group_regex else None
        rows.append({"img": img, "lbl": lbl, "haz": haz, "d8": d8, "ph": ph,
                     "block": f"re:{g.group(1)}" if g else
                     f"{re.sub(r'[0-9]+$', '', b)}{int(m.group(1)) // a.block}" if m else b})
    if not rows:
        sys.exit("no images left")
    cid = cluster([r["d8"] for r in rows], [r["ph"] for r in rows])
    # merge near-dup clusters with name blocks (union over both keys)
    par = {}

    def f(x):
        while par.setdefault(x, x) != x:
            x = par[x]
        return x
    for r, c in zip(rows, cid):
        par[f(("c", c))] = f(("b", r["block"]))
    for r, c in zip(rows, cid):
        r["group"] = f(("c", c))
    # deterministic group names: numbered by the first image path of each group
    first = {}
    for r in sorted(rows, key=lambda x: str(x["img"])):
        first.setdefault(r["group"], len(first))
    for r in rows:
        r["group"] = f"{a.part}_g{first[r['group']]:05d}"
    if a.max_per_group:
        g = defaultdict(list)
        for r in rows:
            g[r["group"]].append(r)
        rows = [x for v in g.values() for x in sorted(v, key=lambda x: (-x["haz"], str(x["img"])))[:a.max_per_group]]
    gh = defaultdict(int)
    for r in rows:
        gh[r["group"]] += r["haz"]
    split = assign_splits(gh, a.all_train)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
        w.writeheader()
        for r in sorted(rows, key=lambda x: str(x["img"])):
            w.writerow({"image": str(r["img"]), "label": str(r["lbl"] or Path(r["img"]).with_suffix(".txt")),
                        "class_map": json.dumps(cmap), "group": r["group"], "part_split": split[r["group"]],
                        "meta": f"family={a.part}"})
    summ = {s: {"images": sum(split[r["group"]] == s for r in rows), "hazard_boxes": sum(r["haz"] for r in rows if split[r["group"]] == s),
                "groups": sum(v == s for v in split.values())} for s in ("train", "val", "test")}
    from collections import Counter
    gs = Counter(r["group"] for r in rows)
    print(json.dumps({"out": str(out), "bases": len(by_base), "dropped_known_family": dropped_fam, "groups": len(gs),
                      "largest_groups": gs.most_common(3), "splits": summ}, indent=1))


if __name__ == "__main__":
    main()
