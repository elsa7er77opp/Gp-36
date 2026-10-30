"""Make the split manifest for road_hazards_v3a_r1 (2026-10-30, owner-approved after the independent audit).

Same SELECTION as v3a (manifests/v3a_split_manifest.csv: same rows, same images, same labels).
Only the GROUPING changes, to remove the temporal leakage found in v3a (audit report, issue 7):
  groups = v3a groups (exact + near-duplicate with margin + sb15 time blocks)
         + rf8 GoPro frames (G00xxxxx) whose numbers differ by <= --gopro-gap
         + rf8 numeric-name families (123_jpg, Image00370, image28) whose numbers differ by <= --numeric-gap (10; gap 3 left 54 cross-split pairs at gap 4-10)
         + sb15 frames <= --sb15-dt seconds apart AND visually similar (dHash <= 12 OR pHash <= 20)
Group-aware 70/20/10 split, seed 0. Writes a NEW manifest; never overwrites.
"""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gp36data.hashing import hamming  # noqa: E402
from gp36data.sources import VIDEO_FRAME  # noqa: E402
from gp36data.split import group_split  # noqa: E402


def seq_key(sample_id):
    stem = sample_id.split("/")[-1]
    m = re.match(r"^(G)(\d{7})_JPG", stem, re.I) or re.match(r"^([A-Za-z]*?)(\d+)_(?:jpe?g|png)", stem, re.I)
    if not m:
        return None
    return ("gopro" if m.group(1) == "G" else "num:" + m.group(1)), int(m.group(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="manifests/v3a_split_manifest.csv")
    ap.add_argument("--built", default="road_hazards_v3a/manifest.csv", help="for per-image class counts")
    ap.add_argument("--sb15-cache", default="manifests/v3a_sb15_hash_cache.json")
    ap.add_argument("--out", default="manifests/v3a_r1_split_manifest.csv")
    ap.add_argument("--gopro-gap", type=int, default=10)
    ap.add_argument("--numeric-gap", type=int, default=10)
    ap.add_argument("--sb15-dt", type=float, default=5.0)
    ap.add_argument("--sb15-dhash", type=int, default=12)
    ap.add_argument("--sb15-phash", type=int, default=20)
    a = ap.parse_args()
    out = ROOT / a.out
    if out.exists():
        sys.exit(f"refusing: {out} exists (manifests are never overwritten)")
    rows = list(csv.DictReader(open(ROOT / a.base, encoding="utf-8")))
    built = {r["sample_id"]: r for r in csv.DictReader(open(ROOT / a.built, encoding="utf-8"))}
    cache = json.load(open(ROOT / a.sb15_cache))
    par = list(range(len(rows)))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(i, j):
        par[find(i)] = find(j)

    links = Counter()
    first = {}
    for i, r in enumerate(rows):
        union(i, first.setdefault(r["group_id"], i))
    fam = defaultdict(list)
    for i, r in enumerate(rows):
        if r["source"] == "rf8" and (k := seq_key(r["sample_id"])):
            fam[k[0]].append((k[1], i))
    for k, L in fam.items():
        gap = a.gopro_gap if k == "gopro" else a.numeric_gap
        L.sort()
        for (n1, i1), (n2, i2) in zip(L, L[1:]):
            if n2 - n1 <= gap:
                union(i1, i2); links["gopro" if k == "gopro" else "numeric"] += 1
    sb = []
    for i, r in enumerate(rows):
        if r["source"] == "sb15":
            m = VIDEO_FRAME.match(Path(r["sample_id"]).stem)
            sb.append((int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100, i, r["sample_id"]))
    sb.sort()
    for x in range(len(sb)):
        for y in range(x + 1, len(sb)):
            if sb[y][0] - sb[x][0] > a.sb15_dt:
                break
            ha, hb = cache[sb[x][2]], cache[sb[y][2]]
            if hamming(int(ha[0]), int(hb[0])) <= a.sb15_dhash or hamming(int(ha[1]), int(hb[1])) <= a.sb15_phash:
                union(sb[x][1], sb[y][1]); links["sb15"] += 1
    comp = [f"r1g{find(i)}" for i in range(len(rows))]
    groups = defaultdict(lambda: {"n": 0, "classes": Counter()})
    for r, g in zip(rows, comp):
        b = built[r["sample_id"]]
        groups[g]["n"] += 1
        groups[g]["classes"].update({0: int(b["n_pothole"]), 1: int(b["n_speed_bump"])})
    assign = group_split({k: {"n": v["n"], "classes": dict(v["classes"])} for k, v in groups.items()}, seed=0)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r, g in zip(rows, comp):
            w.writerow({**r, "split": assign[g], "group_id": g})
    tab = defaultdict(Counter)
    for r, g in zip(rows, comp):
        sp, b = assign[g], built[r["sample_id"]]
        tab[sp]["images"] += 1; tab[sp]["pothole"] += int(b["n_pothole"]); tab[sp]["speed_bump"] += int(b["n_speed_bump"])
        tab[sp][r["source"]] += 1; tab[sp]["negative"] += int(b["n_pothole"]) + int(b["n_speed_bump"]) == 0
    print("links added:", dict(links), "| groups:", len(groups), "| largest:", sorted((v["n"] for v in groups.values()), reverse=True)[:5])
    for sp in ("train", "val", "test"):
        print(sp, dict(tab[sp]))
    print("written", out)


if __name__ == "__main__":
    main()
