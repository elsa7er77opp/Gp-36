"""Resumable: sha256 + 64-bit dHash for new and existing speed-bump sources. Read-only on data."""
import hashlib, json, os, sys, time
from pathlib import Path
from PIL import Image
D = Path.home() / "mnt/GP36_Dataset"
SETS = {
 "bd":  D/"raw_v3/roboflow_bd_speedbreaker_v2", "hump": D/"raw_v3/roboflow_hump_marked_v2",
 "kiz": D/"raw_v3/roboflow_kizmoya_speedbump_v2", "sb15": D/"raw_v3/roboflow_speedbump_v15",
 "rf8": D/"roboflow", "ghsb": D/"speed_bumps",
}
cache = Path("hashes.jsonl"); seen = set()
if cache.exists():
    for l in cache.read_text().splitlines(): seen.add(json.loads(l)["p"])
t0 = time.time(); n = left = 0
with open(cache, "a") as f:
    for k, root in SETS.items():
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() not in (".jpg", ".jpeg", ".png"): continue
            rel = f"{k}:{p.relative_to(root).as_posix()}"
            if rel in seen: continue
            if time.time() - t0 > float(sys.argv[1] if len(sys.argv) > 1 else 160): left += 1; continue
            b = p.read_bytes()
            im = Image.open(p).convert("L").resize((9, 8), Image.LANCZOS); px = list(im.getdata())
            dh = 0
            for r in range(8):
                for c in range(8): dh = (dh << 1) | (px[r*9+c] > px[r*9+c+1])
            w, h = Image.open(p).size
            f.write(json.dumps({"p": rel, "sha": hashlib.sha256(b).hexdigest(), "dh": dh, "w": w, "h": h}) + "\n"); n += 1
print("hashed", n, "left", left)
