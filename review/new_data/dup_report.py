import json, re, collections
R=[json.loads(l) for l in open("hashes.jsonl")]
key=lambda r:r["p"].split(":")[0]
print(collections.Counter(key(r) for r in R))
def stem(p):
    n=p.rsplit("/",1)[-1]; m=re.match(r"(.+?)_(jpg|jpeg|png|JPG|JPEG|PNG)\.rf\.",n); return m.group(1) if m else n
# exact sha
by=collections.defaultdict(list)
for r in R: by[r["sha"]].append(r["p"])
ex=collections.Counter()
for v in by.values():
    ks=sorted({x.split(":")[0] for x in v})
    if len(v)>1: ex[tuple(ks)]+=len(v)
print("exact-dup clusters (sets involved -> images):",dict(ex))
# near dup by dhash
NEW=("bd","hump","kiz"); OLD=("sb15","rf8","ghsb")
pc=lambda a,b:bin(a^b).count("1")
for T in (4,8):
    pairs=collections.Counter(); hitimg=collections.defaultdict(set)
    news=[r for r in R if key(r) in NEW]
    for i,a in enumerate(news):
        for b in R:
            if b is a or b["p"]<=a["p"] and key(b) in NEW: continue
            if pc(a["dh"],b["dh"])<=T:
                ka,kb=key(a),key(b)
                if ka==kb and stem(a["p"])==stem(b["p"]): continue
                pairs[tuple(sorted((ka,kb)))]+=1; hitimg[ka].add(a["p"])
                if kb in NEW: hitimg[kb].add(b["p"])
    print(f"dhash<= {T}: pairs {dict(pairs)}; new images with a link {{k:len(v) for k,v in hitimg.items()}}".replace("{k:len(v) for k,v in hitimg.items()}",str({k:len(v) for k,v in hitimg.items()})))
# originals per set
for k in NEW:
    s={stem(r["p"]) for r in R if key(r)==k}; print(k,"images",sum(key(r)==k for r in R),"unique roboflow stems",len(s))
    print("  sample names:",[r["p"] for r in R if key(r)==k][:3])
