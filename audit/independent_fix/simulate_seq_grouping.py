"""Dry run (no files written except this report): how big do groups get if v3a groups are merged with
sequence links? rf8 GoPro gap<=K, rf8 numeric families gap<=K, sb15 dt<=T s AND weak visual similarity."""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R))
from gp36data.sources import VIDEO_FRAME
from gp36data.hashing import hamming
man = list(csv.DictReader(open(R / "manifests/v3a_split_manifest.csv", encoding="utf-8")))
cache = json.load(open(R / "manifests/v3a_sb15_hash_cache.json"))
idx = {r["sample_id"]: i for i, r in enumerate(man)}
def seq_key(sid):
    stem = sid.split("/")[-1]
    m = re.match(r"^(G)(\d{7})_JPG", stem, re.I) or re.match(r"^([A-Za-z]*?)(\d+)_(?:jpe?g|png)", stem, re.I)
    return (("gopro" if m.group(1) == "G" else "num:" + m.group(1)), int(m.group(2))) if m else None
def run(Kg, Kn, T, dmax, pmax):
    par = list(range(len(man)))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def u(a, b): par[f(a)] = f(b)
    first = {}
    for i, r in enumerate(man):  # existing v3a groups
        g = r["group_id"]; u(i, first.setdefault(g, i))
    fam = defaultdict(list)
    for i, r in enumerate(man):
        if r["source"] == "rf8" and (k := seq_key(r["sample_id"])): fam[k[0]].append((k[1], i))
    for k, L in fam.items():
        K = Kg if k == "gopro" else Kn
        L.sort()
        for (n1, i1), (n2, i2) in zip(L, L[1:]):
            if n2 - n1 <= K: u(i1, i2)
    sb = []
    for i, r in enumerate(man):
        if r["source"] == "sb15":
            m = VIDEO_FRAME.match(Path(r["sample_id"]).stem)
            sb.append((int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100, i, r["sample_id"]))
    sb.sort(); nsb = 0
    for a in range(len(sb)):
        for b in range(a + 1, len(sb)):
            if sb[b][0] - sb[a][0] > T: break
            ha, hb = cache[sb[a][2]], cache[sb[b][2]]
            if hamming(int(ha[0]), int(hb[0])) <= dmax or hamming(int(ha[1]), int(hb[1])) <= pmax: u(sb[a][1], sb[b][1]); nsb += 1
    comp = Counter(f(i) for i in range(len(man)))
    sizes = sorted(comp.values(), reverse=True)
    return len(comp), sizes[:5], nsb
print("v3a now: groups", len(set(r["group_id"] for r in man)), "largest", sorted(Counter(r["group_id"] for r in man).values(), reverse=True)[:5])
for Kg, Kn, T, d, p in [(3, 1, 5, 12, 20), (10, 1, 5, 12, 20), (10, 3, 5, 12, 20), (20, 3, 10, 12, 20), (10, 3, 5, 16, 24)]:
    n, top, nsb = run(Kg, Kn, T, d, p)
    print(f"gopro<= {Kg:2d} numeric<= {Kn} sb15 dt<={T}s & (d<={d}|p<={p}) [{nsb} sb15 links]: groups {n}, largest {top}  (total {len(man)})")

# ---- dry-run split with the proposed rule (gopro<=10, numeric<=3, sb15 dt<=5s & (d<=12|p<=20)); nothing written ----
from gp36data.split import group_split
def comps(Kg=10, Kn=3, T=5, dmax=12, pmax=20):
    par = list(range(len(man)))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def u(a, b): par[f(a)] = f(b)
    first = {}
    for i, r in enumerate(man): u(i, first.setdefault(r["group_id"], i))
    fam = defaultdict(list)
    for i, r in enumerate(man):
        if r["source"] == "rf8" and (k := seq_key(r["sample_id"])): fam[k[0]].append((k[1], i))
    for k, L in fam.items():
        K = Kg if k == "gopro" else Kn; L.sort()
        for (n1, i1), (n2, i2) in zip(L, L[1:]):
            if n2 - n1 <= K: u(i1, i2)
    sb = sorted((int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100, i, r["sample_id"]) for i, r in enumerate(man) if r["source"] == "sb15" and (m := VIDEO_FRAME.match(Path(r["sample_id"]).stem)))
    for a in range(len(sb)):
        for b in range(a + 1, len(sb)):
            if sb[b][0] - sb[a][0] > T: break
            ha, hb = cache[sb[a][2]], cache[sb[b][2]]
            if hamming(int(ha[0]), int(hb[0])) <= dmax or hamming(int(ha[1]), int(hb[1])) <= pmax: u(sb[a][1], sb[b][1])
    return [f(i) for i in range(len(man))]
c = comps()
big = Counter(c).most_common(3)
for root, n in big:
    print("component", n, Counter(man[i]["source"] for i in range(len(man)) if c[i] == root))
built = {r["sample_id"]: r for r in csv.DictReader(open(R / "road_hazards_v3a/manifest.csv", encoding="utf-8"))}
groups = defaultdict(lambda: {"n": 0, "classes": Counter()})
for i, r in enumerate(man):
    b = built[r["sample_id"]]; g = groups[c[i]]; g["n"] += 1; g["classes"].update({0: int(b["n_pothole"]), 1: int(b["n_speed_bump"])})
assign = group_split({k: {"n": v["n"], "classes": dict(v["classes"])} for k, v in groups.items()}, seed=0)
tab = defaultdict(Counter)
for i, r in enumerate(man):
    sp = assign[c[i]]; b = built[r["sample_id"]]
    tab[sp]["images"] += 1; tab[sp]["pothole"] += int(b["n_pothole"]); tab[sp]["bump"] += int(b["n_speed_bump"]); tab[sp][r["source"]] += 1
    tab[sp]["neg"] += int(b["n_pothole"]) + int(b["n_speed_bump"]) == 0
for sp in ("train", "val", "test"): print(sp, dict(tab[sp]))
