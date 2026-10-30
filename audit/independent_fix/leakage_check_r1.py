"""Leakage check of manifests/v3a_r1_split_manifest.csv (before building). Uses original-image hashes."""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R))
from gp36data.hashing import hamming_to_all, hamming
from gp36data.sources import VIDEO_FRAME
sys.path.insert(0, str(R / "tools")); from make_split_v3a_r1 import seq_key
man = list(csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")))
split = {r["sample_id"]: r["split"] for r in man}
built = {r["sample_id"]: r for r in csv.DictReader(open(R / "road_hazards_v3a/manifest.csv", encoding="utf-8"))}
inv = {r["sample_id"]: r for r in csv.DictReader(open(R / "review/phase1c_2026-10-30/inventory.csv", encoding="utf-8"))}
cache = json.load(open(R / "manifests/v3a_sb15_hash_cache.json"))
d = defaultdict(set)
for r in man: d[built[r["sample_id"]]["orig_sha256"]].add(r["split"])
print("[exact] sha in >1 split:", sum(len(v) > 1 for v in d.values()))
H = [(r["sample_id"], *((int(inv[r["sample_id"]]["dhash"], 16), int(inv[r["sample_id"]]["phash"], 16)) if r["sample_id"] in inv else (int(cache[r["sample_id"]][0]), int(cache[r["sample_id"]][1])))) for r in man]
D = np.array([h[1] for h in H], dtype=np.uint64); P = np.array([h[2] for h in H], dtype=np.uint64)
c = Counter()
for i in range(len(H) - 1):
    dd = hamming_to_all(int(D[i]), D[i + 1:]); pp = hamming_to_all(int(P[i]), P[i + 1:])
    for name, m in (("AND 4/10", (dd <= 4) & (pp <= 10)), ("AND 7/14", (dd <= 7) & (pp <= 14))):
        for j in np.nonzero(m)[0]:
            if split[H[i][0]] != split[H[i + 1 + int(j)][0]]: c[name] += 1
print("[near] cross-split:", dict(c) or 0)
fam = defaultdict(list)
for r in man:
    if r["source"] == "rf8" and (k := seq_key(r["sample_id"])): fam[k[0]].append((k[1], r["split"]))
t = Counter()
for k, L in fam.items():
    L.sort()
    for x in range(len(L)):
        for y in range(x + 1, len(L)):
            if L[y][0] - L[x][0] > 10: break
            if L[x][1] != L[y][1]: t[("gopro" if k == "gopro" else "numeric") + f" gap<={L[y][0]-L[x][0]}"] += 1
print("[temporal rf8] cross-split pairs within 10 numbers:", dict(sorted(t.items())) or 0)
sb = sorted((int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100, r["split"], r["sample_id"]) for r in man if r["source"] == "sb15" and (m := VIDEO_FRAME.match(Path(r["sample_id"]).stem)))
print("[sb15] splits:", Counter(s for _, s, _ in sb))
print("[selection] same rows as v3a:", {r["sample_id"] for r in man} == {r["sample_id"] for r in csv.DictReader(open(R / "manifests/v3a_split_manifest.csv", encoding="utf-8"))})
