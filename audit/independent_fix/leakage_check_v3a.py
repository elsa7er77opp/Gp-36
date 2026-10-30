"""ISSUE 7 - independent, read-only leakage checks on the BUILT road_hazards_v3a (and v3b manifests).
Uses hashes of the ORIGINAL images (inventory.csv for rf8/ghpot, sb15 cache) + the built manifest."""
import csv, json, re, sys, itertools
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from gp36data.hashing import hamming_to_all

man = list(csv.DictReader(open(R / "road_hazards_v3a/manifest.csv", encoding="utf-8")))
split = {r["sample_id"]: r["split"] for r in man}
print("v3a rows", len(man), Counter(split.values()))
# 1 exact (orig and out sha)
for col in ("orig_sha256", "out_sha256"):
    d = defaultdict(set)
    for r in man: d[r[col]].add(r["split"])
    print(f"[exact] {col}: shas in >1 split =", sum(1 for v in d.values() if len(v) > 1), "| same sha twice =", sum(1 for v in Counter(r[col] for r in man).values() if v > 1))
# hashes of originals
inv = {r["sample_id"]: r for r in csv.DictReader(open(R / "review/phase1c_2026-10-30/inventory.csv", encoding="utf-8"))}
cache = json.load(open(R / "manifests/v3a_sb15_hash_cache.json"))
H = []
for r in man:
    sid = r["sample_id"]
    if sid in inv: H.append((sid, int(inv[sid]["dhash"], 16), int(inv[sid]["phash"], 16)))
    elif sid in cache: H.append((sid, int(cache[sid][0]), int(cache[sid][1])))
print("hashes found", len(H), "/", len(man))
D = np.array([h[1] for h in H], dtype=np.uint64); P = np.array([h[2] for h in H], dtype=np.uint64)
rules = {"AND d<=4&p<=10 (verifier)": lambda d, p: (d <= 4) & (p <= 10), "AND d<=7&p<=14 (grouping)": lambda d, p: (d <= 7) & (p <= 14),
         "OR d<=4|p<=10": lambda d, p: (d <= 4) | (p <= 10), "d<=6 alone": lambda d, p: d <= 6, "p<=12 alone": lambda d, p: p <= 12}
cross = {k: [] for k in rules}
for i in range(len(H) - 1):
    dd = hamming_to_all(int(D[i]), D[i + 1:]); pp = hamming_to_all(int(P[i]), P[i + 1:])
    for k, f in rules.items():
        for j in np.nonzero(f(dd, pp))[0]:
            a, b = H[i][0], H[i + 1 + int(j)][0]
            if split[a] != split[b]: cross[k].append((a, b, int(dd[j]), int(pp[j])))
for k, v in cross.items():
    print(f"[near] {k:28s} cross-split pairs: {len(v)}", v[:3])
json.dump({k: v for k, v in cross.items()}, open(R / "audit/independent_fix/v3a_crosssplit_pairs.json", "w"), indent=0)
# 3 temporal: sb15 frames of the same video within 3 s in different splits
vf = re.compile(r"frame\d+-(\d+)-(\d+)-(\d+)(?:-(\d+)-)?_jpg")
fr = []
for r in man:
    if r["source"] == "sb15":
        m = vf.search(r["sample_id"]); t = int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 100
        fr.append((m.group(4) or "1", t, r["split"], r["sample_id"]))
fr.sort(); tc = Counter()
for (v1, t1, s1, a), (v2, t2, s2, b) in itertools.combinations(fr, 2) if False else []: pass
byv = defaultdict(list)
for v, t, s, sid in fr: byv[v].append((t, s))
for v, L in byv.items():
    L.sort()
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            if L[j][0] - L[i][0] > 3: break
            if L[i][1] != L[j][1]: tc["sb15 <=3s cross-split"] += 1
# rf8 GoPro sequences: same 'G00' prefix, frame numbers within 3, different split
gp = re.compile(r"/(G\d{7})_JPG")
g = []
for r in man:
    m = gp.search(r["sample_id"])
    if m: g.append((int(m.group(1)[1:]), r["split"], r["sample_id"]))
g.sort()
for i in range(len(g)):
    for j in range(i + 1, len(g)):
        if g[j][0] - g[i][0] > 3: break
        if g[i][1] != g[j][1]: tc["rf8 GoPro frame# within 3, cross-split"] += 1
print("[temporal]", dict(tc) or "0 cross-split temporal neighbours")
# 5 v3a vs v3b val/test identity
a = {(r["sample_id"], r["split"]) for r in csv.DictReader(open(R / "manifests/v3a_split_manifest.csv", encoding="utf-8")) if r["split"] != "train"}
for name in ("v3b_full_split_manifest.csv", "v3b_capped_split_manifest.csv"):
    b = {(r["sample_id"], r["split"]) for r in csv.DictReader(open(R / "manifests" / name, encoding="utf-8")) if r["split"] != "train"}
    print(f"[v3a vs {name}] val/test identical: {a == b} ({len(a)} vs {len(b)})")
# v3a built == v3a split manifest
sm = {r["sample_id"]: r["split"] for r in csv.DictReader(open(R / "manifests/v3a_split_manifest.csv", encoding="utf-8"))}
print("[manifest] built v3a matches split manifest:", sm == split)
