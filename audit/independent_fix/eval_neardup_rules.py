"""ISSUE 3 - controlled evaluation of near-duplicate decision rules (read-only; writes only into audit/independent_fix/).
Positives: exact copy, resize 0.5x, JPEG q30, brightness x0.75 / x1.25 (synthetic, from 120 v3a images),
           adjacent video frames: rf8 GoPro consecutive numbers (gap=1) and sb15 same-video dt<=0.5 s.
Negatives: random pairs from DIFFERENT sources (different scenes), and rf8 GoPro frames >=300 numbers apart (hard: same camera/area)."""
import csv, io, json, random, re, sys
from pathlib import Path
from PIL import Image, ImageEnhance
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R))
from gp36data.hashing import dhash, phash, hamming
from gp36data.sources import VIDEO_FRAME
random.seed(0)
D = R / "road_hazards_v3a"
man = list(csv.DictReader(open(D / "manifest.csv", encoding="utf-8")))
inv = {r["sample_id"]: r for r in csv.DictReader(open(R / "review/phase1c_2026-10-30/inventory.csv", encoding="utf-8"))}
cache = json.load(open(R / "manifests/v3a_sb15_hash_cache.json"))
def H(sid):
    if sid in inv: return int(inv[sid]["dhash"], 16), int(inv[sid]["phash"], 16)
    return int(cache[sid][0]), int(cache[sid][1])
rows = []  # (category, label, dd, pd, a, b)
def add(cat, lab, ha, hb, a, b): rows.append((cat, lab, hamming(ha[0], hb[0]), hamming(ha[1], hb[1]), a, b))
# synthetic transforms
for r in random.sample(man, 120):
    im = Image.open(D / r["out_image"]).convert("RGB"); h0 = (dhash(im), phash(im)); sid = r["sample_id"]
    add("exact_copy", 1, h0, (dhash(im.copy()), phash(im.copy())), sid, sid)
    s = im.resize((max(1, im.width // 2), max(1, im.height // 2))); add("resize_0.5", 1, h0, (dhash(s), phash(s)), sid, sid)
    b = io.BytesIO(); im.save(b, "JPEG", quality=30); j = Image.open(b); add("jpeg_q30", 1, h0, (dhash(j), phash(j)), sid, sid)
    for f in (0.75, 1.25):
        e = ImageEnhance.Brightness(im).enhance(f); add(f"brightness_x{f}", 1, h0, (dhash(e), phash(e)), sid, sid)
# adjacent video frames (original-image hashes, as used by the split)
gp = re.compile(r"/(G\d{7})_JPG", re.I)
g = sorted((int(m.group(1)[1:]), r["sample_id"]) for r in man if (m := gp.search(r["sample_id"])))
for (n1, a), (n2, b) in zip(g, g[1:]):
    if n2 - n1 == 1: add("adjacent_rf8_gopro_gap1", 1, H(a), H(b), a, b)
vid = {}
for r in man:
    if r["source"] == "sb15":
        m = VIDEO_FRAME.match(Path(r["sample_id"]).stem)
        vid.setdefault(m.group("vid") or "1", []).append((int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100, r["sample_id"]))
for L in vid.values():
    L.sort()
    for (t1, a), (t2, b) in zip(L, L[1:]):
        if t2 - t1 <= 0.5: add("adjacent_sb15_dt<=0.5s", 1, H(a), H(b), a, b)
# negatives
by_src = {}
for r in man: by_src.setdefault(r["source"], []).append(r["sample_id"])
srcs = list(by_src)
for _ in range(3000):
    s1, s2 = random.sample(srcs, 2); a, b = random.choice(by_src[s1]), random.choice(by_src[s2]); add("neg_different_source", 0, H(a), H(b), a, b)
far = [(x, y) for x in random.sample(g, 300) for y in random.sample(g, 10) if abs(x[0] - y[0]) >= 300][:2000]
for (n1, a), (n2, b) in far: add("neg_rf8_gopro_far(>=300)", 0, H(a), H(b), a, b)
w = csv.writer(open(R / "audit/independent_fix/neardup_eval_pairs.csv", "w", newline="", encoding="utf-8")); w.writerow(["category", "is_dup", "dhash_dist", "phash_dist", "a", "b"]); w.writerows(rows)
rules = {"AND d<=4 & p<=10 (verifier, current)": lambda d, p: d <= 4 and p <= 10,
         "AND d<=7 & p<=14 (split grouping margin)": lambda d, p: d <= 7 and p <= 14,
         "OR  d<=4 | p<=10": lambda d, p: d <= 4 or p <= 10,
         "OR  d<=7 | p<=14": lambda d, p: d <= 7 or p <= 14,
         "d<=10 alone": lambda d, p: d <= 10, "p<=16 alone": lambda d, p: p <= 16,
         "SUM d+p<=20": lambda d, p: d + p <= 20, "SUM d+p<=28": lambda d, p: d + p <= 28}
cats = sorted({c for c, *_ in rows}); out = []
hdr = f"{'rule':42s} " + " ".join(f"{c[:24]:>24s}" for c in cats); print(hdr); out.append(hdr)
for name, f in rules.items():
    cells = []
    for c in cats:
        sub = [(l, d, p) for cc, l, d, p, *_ in rows if cc == c]; hit = sum(f(d, p) for l, d, p in sub)
        cells.append(f"{hit:4d}/{len(sub):4d} {'TP' if sub[0][0] else 'FP'}")
    line = f"{name:42s} " + " ".join(f"{x:>24s}" for x in cells); print(line); out.append(line)
import statistics as st
for c in cats:
    ds = sorted(d for cc, l, d, p, *_ in rows if cc == c); ps = sorted(p for cc, l, d, p, *_ in rows if cc == c)
    line = f"{c:28s} n={len(ds):4d} dhash median {st.median(ds):5.1f} p05 {ds[len(ds)//20]:3d} p95 {ds[len(ds)*19//20]:3d} | phash median {st.median(ps):5.1f} p05 {ps[len(ps)//20]:3d} p95 {ps[len(ps)*19//20]:3d}"
    print(line); out.append(line)
open(R / "audit/independent_fix/neardup_eval_results.txt", "w").write("\n".join(out) + "\n")
