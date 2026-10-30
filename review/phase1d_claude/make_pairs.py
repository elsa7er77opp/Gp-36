"""Phase 1d helper (read-only on data): render zoomed side-by-side overlays of
byte-identical duplicate pairs whose labels conflict, for human review.
Writes only into review/phase1d_claude/pairs/. Safe to rerun (skips existing)."""
import csv, os, sys
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "mnt", "Desktop", "GP36_AI")
AUD = os.path.join(BASE, "review", "phase1c_2026-10-30", "ANNOTATION_AUDIT.csv")
OUT = os.path.join(BASE, "review", "phase1d_claude", "pairs")
FLAG = sys.argv[1] if len(sys.argv) > 1 else "EXACT_DUP_LABEL_CONFLICT"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
COL = {0: (255, 40, 40), 1: (40, 140, 255)}

def winpath(p):
    p = p.replace("C:\\Users\\ahmed\\Desktop", os.path.join(HOME, "mnt", "Desktop"))
    return p.replace("\\", "/")

def label_path(img):
    d, f = os.path.split(img)
    return os.path.join(os.path.dirname(d), "labels", f.rsplit(".", 1)[0] + ".txt")

def read_boxes(p):
    out = []
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8"):
        t = line.split()
        if not t:
            continue
        c = int(float(t[0])); v = [float(x) for x in t[1:]]
        if len(v) == 4:
            xc, yc, w, h = v
        else:
            xs, ys = v[0::2], v[1::2]
            xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, h = max(xs) - min(xs), max(ys) - min(ys)
        out.append((c, xc, yc, w, h))
    return out

rows = list(csv.DictReader(open(AUD, encoding="utf-8")))
groups = defaultdict(list)
for r in rows:
    if FLAG in r["auto_flags"].split(";") or FLAG in r["auto_flags"]:
        groups[r["sha256"]].append(r)
pairs = sorted(groups.items(), key=lambda kv: kv[1][0]["sample_id"])
font = ImageFont.load_default()
index = os.path.join(OUT, f"index_{FLAG}.csv")
with open(index, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["pair_no", "sha256", "copy", "sample_id", "boxes"])
    for i, (sha, rs) in enumerate(pairs, 1):
        for k, r in enumerate(rs):
            b = read_boxes(label_path(winpath(r["image"])))
            w.writerow([i, sha, "ABCD"[k], r["sample_id"], " | ".join(f"{c}:{xc:.3f},{yc:.3f},{bw:.3f},{bh:.3f}" for c, xc, yc, bw, bh in b)])
done = 0
for i, (sha, rs) in enumerate(pairs, 1):
    if i > LIMIT:
        break
    out = os.path.join(OUT, f"{FLAG[:14]}_{i:03d}.jpg")
    if os.path.exists(out):
        continue
    img_p = winpath(rs[0]["image"])
    im = Image.open(img_p); im.draft("RGB", (im.width // 2, im.height // 2)); im = im.convert("RGB")
    W, H = im.size
    allb = [read_boxes(label_path(winpath(r["image"]))) for r in rs]
    flat = [b for bs in allb for b in bs]
    if flat:
        x1 = min(b[1] - b[3] / 2 for b in flat); x2 = max(b[1] + b[3] / 2 for b in flat)
        y1 = min(b[2] - b[4] / 2 for b in flat); y2 = max(b[2] + b[4] / 2 for b in flat)
    else:
        x1, x2, y1, y2 = 0.2, 0.8, 0.4, 0.8
    pad = 0.12
    cx1, cx2 = max(0, x1 - pad), min(1, x2 + pad)
    cy1, cy2 = max(0, y1 - pad), min(1, y2 + pad)
    if cx2 - cx1 < 0.35:
        m = (cx1 + cx2) / 2; cx1, cx2 = max(0, m - 0.175), min(1, m + 0.175)
    if cy2 - cy1 < 0.25:
        m = (cy1 + cy2) / 2; cy1, cy2 = max(0, m - 0.125), min(1, m + 0.125)
    crop = im.crop((int(cx1 * W), int(cy1 * H), int(cx2 * W), int(cy2 * H)))
    PW = int(os.environ.get("PW", "700"))
    sc = PW / crop.width
    ph = int(crop.height * sc)
    thumb_w = 300
    th = im.resize((thumb_w, int(H * thumb_w / W)))
    canvas = Image.new("RGB", (PW * len(rs) + 20 * (len(rs) - 1), ph + 40 + th.height + 10), (30, 30, 30))
    d = ImageDraw.Draw(canvas)
    for k, (r, bs) in enumerate(zip(rs, allb)):
        panel = crop.resize((PW, ph))
        pd = ImageDraw.Draw(panel)
        for n, (c, xc, yc, bw, bh) in enumerate(bs, 1):
            bx1 = ((xc - bw / 2) - cx1) * W * sc; bx2 = ((xc + bw / 2) - cx1) * W * sc
            by1 = ((yc - bh / 2) - cy1) * H * sc; by2 = ((yc + bh / 2) - cy1) * H * sc
            pd.rectangle([bx1, by1, bx2, by2], outline=COL.get(c, (255, 255, 0)), width=3)
            pd.text((bx1 + 3, by1 + 2), str(n), fill=(255, 255, 0), font=font)
        x0 = k * (PW + 20)
        canvas.paste(panel, (x0, 40))
        tt = th.copy(); td = ImageDraw.Draw(tt)
        td.rectangle([cx1 * thumb_w, cy1 * tt.height, cx2 * thumb_w, cy2 * tt.height], outline=(255, 255, 0), width=2)
        canvas.paste(tt, (x0, 40 + ph + 10))
        npot = sum(1 for b in bs if b[0] == 0); nb = sum(1 for b in bs if b[0] == 1)
        d.text((x0 + 4, 4), f"#{i} copy {'ABCD'[k]}: {r['sample_id'][:70]}", fill=(255, 255, 255), font=font)
        d.text((x0 + 4, 20), f"P:{npot} B:{nb}  (red=pothole, blue=bump)", fill=(200, 200, 200), font=font)
    canvas.save(out, quality=85)
    done += 1
print("pairs:", len(pairs), "rendered now:", done, "index:", index)
