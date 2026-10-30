import json, sys, collections, re
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sets = json.load(open(sys.argv[1], encoding="utf-8"))
S = {s["set"]: s for s in sets}


def stats(name):
    s = S[name]
    recs = s["records"]
    bad_img = [r["path"] for r in recs if not r["ok"]]
    fmt = collections.Counter(r.get("format") for r in recs)
    sizes = collections.Counter(tuple(r["size"]) for r in recs if r["ok"])
    orient = collections.Counter(r.get("exif_orient") for r in recs)
    cls = collections.Counter()
    nbox = 0; empty = 0; poly = 0; bad = collections.Counter(); dup = 0; badfiles = []
    ws, hs, areas = [], [], []
    for r in recs:
        L = r["label"]
        for k, v in L["classes"].items():
            cls[int(k)] += v
        nbox += L["lines"]; poly += L["poly"]; dup += L.get("dup_lines", 0)
        if L["lines"] == 0:
            empty += 1
        for _, why in L["bad"]:
            bad[why] += 1
        if L["bad"]:
            badfiles.append(r["path"].split("\\")[-1])
        for c, xc, yc, w, h in L["boxes"]:
            ws.append(w); hs.append(h); areas.append(w * h)
    ws, hs, areas = map(np.array, (ws, hs, areas))
    print(f"\n## {name}: imgs={len(recs)} unreadable={len(bad_img)} formats={dict(fmt)}")
    print(f"   top sizes={sizes.most_common(4)} n_sizes={len(sizes)} exif_orient={dict(orient)}")
    print(f"   boxes={nbox} classes={dict(cls)} empty_label_imgs={empty} polygon_lines={poly} dup_lines={dup} bad={dict(bad)}")
    if len(ws):
        print(f"   w median={np.median(ws):.4f} p5={np.percentile(ws,5):.4f}  h median={np.median(hs):.4f} p5={np.percentile(hs,5):.4f}  area<0.0004(=~13px@640):{(np.sqrt(areas)<0.02).mean():.2%} tiny(<0.005 side):{((ws<0.005)|(hs<0.005)).sum()}")
    if badfiles:
        print("   bad files sample:", badfiles[:8])
    return recs


allrecs = {}
for n in S:
    allrecs[n] = stats(n)

# --- duplicates within raw and cross-source (SHA256)
raw = [r for n in S if n.startswith("raw:") for r in S[n]["records"] if r["ok"]]
by_sha = collections.defaultdict(list)
for r in raw:
    by_sha[r["sha256"]].append(r["set"] + "|" + r["path"].split("\\")[-1])
exact = [v for v in by_sha.values() if len(v) > 1]
print("\n## RAW exact duplicate groups (sha256):", len(exact), "images involved:", sum(len(v) for v in exact))
cross = [v for v in exact if len({x.split("|")[0] for x in v}) > 1]
print("   groups spanning >1 set/split:", len(cross))
for v in cross[:10]:
    print("    ", v)

# --- near duplicates via dHash, hamming <= T
def near_groups(recs, T):
    H = np.array([r["dhash"] for r in recs], dtype=np.uint64)
    tag = [r["set"] for r in recs]
    pairs = []
    for i in range(len(H)):
        x = np.bitwise_xor(H[i + 1:], H[i])
        # popcount
        d = np.zeros(len(x), dtype=np.int64)
        y = x.copy()
        for _ in range(64):
            d += (y & np.uint64(1)).astype(np.int64); y >>= np.uint64(1)
        for j in np.nonzero(d <= T)[0]:
            pairs.append((i, i + 1 + int(j), int(d[j])))
    return pairs

for T in (0, 4):
    pairs = near_groups(raw, T)
    cnt = collections.Counter()
    for i, j, d in pairs:
        a, b = raw[i]["set"], raw[j]["set"]
        cnt[tuple(sorted((a, b)))] += 1
    print(f"\n## RAW near-duplicate pairs dHash<= {T}: {len(pairs)}")
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print("   ", k, v)
    if T == 4:
        ex = [(raw[i]["path"].split("\\")[-1], raw[i]["set"], raw[j]["path"].split("\\")[-1], raw[j]["set"], d) for i, j, d in pairs if raw[i]["set"] != raw[j]["set"]]
        print("   cross-set examples:", ex[:12])
        json.dump([(raw[i]["path"], raw[j]["path"], d) for i, j, d in pairs], open(sys.argv[2], "w"))

# --- Roboflow source-stem grouping across splits
def src_stem(fn):
    m = re.match(r"(.+?)_(jpg|jpeg|png|JPG|JPEG|PNG)\.rf\.[0-9a-f]+\.\w+$", fn)
    return m.group(1) if m else None
grp = collections.defaultdict(set); per = collections.defaultdict(int); nomatch = 0
for n in ("raw:rf_train", "raw:rf_valid", "raw:rf_test"):
    for r in S[n]["records"]:
        st = src_stem(r["path"].split("\\")[-1])
        if st is None:
            nomatch += 1; continue
        grp[st].add(n); per[(st, n)] += 1
multi = {k: v for k, v in grp.items() if len(v) > 1}
copies = collections.Counter(per.values())
print(f"\n## Roboflow: distinct source stems={len(grp)} unmatched names={nomatch}; stems in >1 split={len(multi)}; copies-per-stem-per-split histogram={dict(copies)}")
print("   examples:", list(multi.items())[:8])

# --- 60-char truncation collisions in prepare_dataset rf naming
for n in ("raw:rf_train", "raw:rf_valid", "raw:rf_test"):
    stems = [r["path"].split("\\")[-1].rsplit(".", 1)[0] for r in S[n]["records"]]
    trunc = collections.Counter(s[:60] for s in stems)
    longest = max(len(s) for s in stems)
    print(f"   {n}: longest stem={longest}, truncation collisions={sum(1 for v in trunc.values() if v>1)}, stems with >1 dot={sum(1 for s in stems if s.count('.')>0)}")

# --- v2 vs raw label consistency: compare v2 rf_ labels to raw labels (boxes identical after bbox conversion?)
rawlab = {}
for n in ("raw:rf_train", "raw:rf_valid", "raw:rf_test"):
    for r in S[n]["records"]:
        st = r["path"].split("\\")[-1].rsplit(".", 1)[0]
        rawlab["rf_" + st[:60]] = sorted(tuple(round(v, 4) for v in b) for b in r["label"]["boxes"] if b[0] in (0, 1))
for r in S["raw:potholes"]["records"]:
    st = r["path"].split("\\")[-1].rsplit(".", 1)[0]
    rawlab["pot_" + st] = sorted((0,) + tuple(round(v, 4) for v in b[1:]) for b in r["label"]["boxes"])
mismatch = []; checked = 0; srcmap = collections.Counter()
for n in ("v2:train", "v2:val", "v2:test"):
    for r in S[n]["records"]:
        st = r["path"].split("\\")[-1].rsplit(".", 1)[0]
        srcmap[(n, st.split("_")[0])] += 1
        if st in rawlab:
            checked += 1
            v = sorted(tuple(round(x, 4) for x in b) for b in r["label"]["boxes"])
            if v != rawlab[st]:
                mismatch.append(st)
print(f"\n## v2 label consistency vs raw (rf_ and pot_): checked={checked} mismatched={len(mismatch)} {mismatch[:5]}")
print("   v2 composition:", dict(srcmap))

# v2 split leakage: sha and dhash across v2 splits
v2 = [r for n in ("v2:train", "v2:val", "v2:test") for r in S[n]["records"]]
sha = collections.defaultdict(set)
for r in v2:
    sha[r["sha256"]].add(r["set"])
print("   v2 exact dup groups across splits:", sum(1 for v in sha.values() if len(v) > 1))
pairs = near_groups(v2, 4)
c = collections.Counter(tuple(sorted((v2[i]["set"], v2[j]["set"]))) for i, j, d in pairs)
print("   v2 near-dup pairs dHash<=4 by split pair:", dict(c))
tt = [(v2[i]["path"].split("\\")[-1], v2[j]["path"].split("\\")[-1], d) for i, j, d in pairs if {v2[i]["set"], v2[j]["set"]} == {"v2:train", "v2:test"}]
print("   train<->test examples:", tt[:15])
test_imgs = {v2[k]["path"].split("\\")[-1] for p in pairs for k in p[:2] if v2[k]["set"] == "v2:test" and {v2[p[0]]["set"], v2[p[1]]["set"]} & {"v2:train", "v2:val"}}
print("   distinct v2 TEST images with a near-dup (<=4) in train/val:", len(test_imgs), collections.Counter(x.split('_')[0] for x in test_imgs))
json.dump(sorted(test_imgs), open(sys.argv[3], "w"))
