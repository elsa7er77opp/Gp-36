"""ISSUE 7 detail: temporal neighbours across splits in v3a (rf8 GoPro frame numbers, sb15 video time)."""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from gp36data.sources import VIDEO_FRAME
man = list(csv.DictReader(open(R / "road_hazards_v3a/manifest.csv", encoding="utf-8")))
gp = re.compile(r"/(G\d{7})_JPG", re.I)
g = sorted((int(m.group(1)[1:]), r["split"], r["sample_id"]) for r in man if (m := gp.search(r["sample_id"])))
print("rf8 GoPro-named images in v3a:", len(g), Counter(s for _, s, _ in g))
for K in (1, 2, 3, 5, 10):
    pairs = 0; imgs = defaultdict(set)
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            if g[j][0] - g[i][0] > K: break
            if g[i][1] != g[j][1]:
                pairs += 1; imgs[g[i][1]].add(g[i][2]); imgs[g[j][1]].add(g[j][2])
    print(f"  gap<={K:2d}: cross-split pairs {pairs:4d} | images involved: " + ", ".join(f"{s} {len(v)}" for s, v in sorted(imgs.items())))
# runs of consecutive numbers -> how many 'sequences'
seq = 0; prev = None
for n, _, _ in g:
    if prev is None or n - prev > 3: seq += 1
    prev = n
print("  sequences (gap>3 breaks):", seq)
# sb15
fr = defaultdict(list)
for r in man:
    if r["source"] != "sb15": continue
    m = VIDEO_FRAME.match(Path(r["sample_id"]).stem)
    t = int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100
    fr[m.group("vid") or "1"].append((t, r["split"], r["sample_id"]))
print("sb15 videos:", {k: len(v) for k, v in fr.items()})
for K in (1, 2, 3, 5):
    pairs = 0; imgs = defaultdict(set)
    for L in fr.values():
        L.sort()
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                if L[j][0] - L[i][0] > K: break
                if L[i][1] != L[j][1]: pairs += 1; imgs[L[i][1]].add(L[i][2]); imgs[L[j][1]].add(L[j][2])
    print(f"  dt<={K}s: cross-split pairs {pairs:3d} | images involved: " + ", ".join(f"{s} {len(v)}" for s, v in sorted(imgs.items())))
# write gap<=1 rf8 and dt<=1 sb15 examples for visual check
out = []
for i in range(len(g) - 1):
    if g[i + 1][0] - g[i][0] == 1 and g[i][1] != g[i + 1][1]: out.append(("rf8", g[i][2], g[i][1], g[i + 1][2], g[i + 1][1], 1))
for L in fr.values():
    for i in range(len(L) - 1):
        if L[i + 1][0] - L[i][0] <= 1 and L[i][1] != L[i + 1][1]: out.append(("sb15", L[i][2], L[i][1], L[i + 1][2], L[i + 1][1], round(L[i + 1][0] - L[i][0], 2)))
w = csv.writer(open(R / "audit/independent_fix/temporal_crosssplit_examples.csv", "w", newline="", encoding="utf-8"))
w.writerow(["source", "a", "split_a", "b", "split_b", "gap"]); w.writerows(out)
print("examples written:", len(out))
