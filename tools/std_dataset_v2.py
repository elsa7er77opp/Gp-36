"""Standardise a YOLO dataset to ONE pattern (STATUS Stage 39; supervisor notes of 8 Nov 2026):
same framing, same resolution, no duplicates. Self-contained (PIL + numpy only). Never edits the source dataset.

    python -I tools/std_dataset.py audit --src road_hazards_v3b_C --out review/std_v4/audit
    python -I tools/std_dataset.py build --src road_hazards_v3b_C --out road_hazards_v4_std

What "one pattern" means here (all values are options):
- GEOMETRY, every split: each image is cropped to the target aspect (default 4:3, the ESP32-CAM shape) with a window
  that keeps every labelled box, then resized to exactly --size (default 960x720). If the boxes do not fit in the
  window, or the crop would keep less than --min-keep of the image, the whole image is letterboxed instead (grey bars).
  --unstretch SOURCE=RATIO first undoes a known stretch (e.g. sb15=1.7778 for frames squeezed to 640x640).
- FRAMING flags (from the image shape and the labelled boxes only; nobody "looks" at the picture):
    portrait        the original is taller than wide (phone photo, not a forward road view)
    extreme_aspect  the 4:3 crop would keep less than --min-keep of the image
    closeup         a hazard box covers more than --max-box-area of the frame
    high_box        a hazard box centre is above --min-cy of the frame height (hazard where the sky should be)
    lowres          the kept window is less than half the target width (would be upscaled more than 2x)
  TRAIN images with a flag listed in --frame-rules are left out (drop_log.csv). VAL and TEST images are never
  left out: the full val/test stay comparable with older results, and the unflagged ones are also listed in
  val_stdframe.txt / test_stdframe.txt (data_stdframe.yaml) as the "standard framing" subset.
- DUPLICATES, train only: two train images with dHash <= --dhash AND pHash <= --phash (computed on the standardised
  image) are one cluster; one image per cluster is kept (most boxes, then name). A train image that matches a val or
  test image by the same rule is left out too.
Outputs in <out>: images/, labels/, data.yaml, data_stdframe.yaml, manifest.csv (source columns + std_* columns),
drop_log.csv, build_info.json, sheets/*.jpg (samples of kept and of each drop reason, boxes drawn, for an eye check).
Built in <out>.building and renamed at the end; refuses to overwrite.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

NAMES = {0: "pothole", 1: "speed_bump"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALL_RULES = ["portrait", "extreme_aspect", "closeup", "high_box", "lowres"]
COL = {0: (255, 165, 0), 1: (255, 0, 255)}


def read_rows(src):
    """Rows of the source dataset: dicts with at least out_image, split, source, group_id."""
    man = src / "manifest.csv"
    rows, fields = [], []
    if man.exists():
        with open(man, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            fields = list(rd.fieldnames or [])
            for m in rd:
                if m.get("out_image") and m.get("split") in ("train", "val", "test"):
                    m["out_image"] = m["out_image"].replace("\\", "/")
                    rows.append(m)
    if not rows:
        fields = ["out_image", "split", "source", "group_id"]
        for sp in ("train", "val", "test"):
            d = src / "images" / sp
            if d.is_dir():
                for p in sorted(d.iterdir()):
                    if p.suffix.lower() in IMG_EXT:
                        rows.append({"out_image": f"images/{sp}/{p.name}", "split": sp,
                                     "source": p.stem.split("__")[0] if "__" in p.stem else "unknown", "group_id": ""})
    return rows, fields


def label_path(src, out_image):
    p = Path(out_image)
    return src / "labels" / p.parent.name / (p.stem + ".txt")


def read_boxes(p):
    """[(cls, x1, y1, x2, y2)] normalised; a polygon line is turned into its bounding box."""
    out = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        v = line.split()
        if len(v) < 5:
            continue
        c = int(float(v[0]))
        t = [float(x) for x in v[1:]]
        if len(t) == 4:
            cx, cy, w, h = t
            x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        else:
            xs, ys = t[0::2], t[1::2]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
        out.append((c, max(0.0, x1), max(0.0, y1), min(1.0, x2), min(1.0, y2)))
    return out


def plan(W, H, boxes, a):
    """Decide the window. Returns (mode, (x0, y0, cw, ch), keep_fraction). mode = crop | pad."""
    A = a.tw / a.th
    if abs(W / H - A) < 0.01:
        return "crop", (0, 0, W, H), 1.0
    if W / H > A:  # too wide: cut the sides
        cw, ch = min(W, int(round(H * A))), H
        lo, hi, pref, span = 0.0, float(W - cw), (W - cw) / 2, 0.0
        if boxes:
            b0, b1 = min(b[1] for b in boxes) * W, max(b[3] for b in boxes) * W
            span, lo, hi = b1 - b0, max(lo, b1 - cw), min(hi, b0)
        if span > cw or lo > hi:
            return "pad", (0, 0, W, H), 1.0
        x0, y0 = int(round(min(max(pref, lo), hi))), 0
    else:  # too tall: cut top / bottom
        cw, ch = W, min(H, int(round(W / A)))
        lo, hi, pref, span = 0.0, float(H - ch), (H - ch) / 2, 0.0
        if boxes:
            b0, b1 = min(b[2] for b in boxes) * H, max(b[4] for b in boxes) * H
            span, lo, hi = b1 - b0, max(lo, b1 - ch), min(hi, b0)
        if span > ch or lo > hi:
            return "pad", (0, 0, W, H), 1.0
        x0, y0 = 0, int(round(min(max(pref, lo), hi)))
    x0, y0 = max(0, min(x0, W - cw)), max(0, min(y0, H - ch))
    keep = (cw * ch) / (W * H)
    if keep < a.min_keep:
        return "pad", (0, 0, W, H), keep
    return "crop", (x0, y0, cw, ch), keep


def map_boxes(boxes, W, H, mode, win, a):
    """Boxes in the standardised frame (normalised), plus the up-scale factor."""
    x0, y0, cw, ch = win
    out = []
    if mode == "crop":
        for c, x1, y1, x2, y2 in boxes:
            q = ((x1 * W - x0) / cw, (y1 * H - y0) / ch, (x2 * W - x0) / cw, (y2 * H - y0) / ch)
            q = tuple(min(1.0, max(0.0, v)) for v in q)
            if q[2] - q[0] > 1e-4 and q[3] - q[1] > 1e-4:
                out.append((c,) + q)
        return out, a.tw / cw
    s = min(a.tw / W, a.th / H)
    ox, oy = (a.tw - W * s) / 2, (a.th - H * s) / 2
    for c, x1, y1, x2, y2 in boxes:
        out.append((c, (x1 * W * s + ox) / a.tw, (y1 * H * s + oy) / a.th, (x2 * W * s + ox) / a.tw, (y2 * H * s + oy) / a.th))
    return out, s


def flags_of(W0, H0, mode, keep, scale, boxes_std, a):
    fl = []
    if H0 > W0 * 1.05:
        fl.append("portrait")
    if keep < a.min_keep:
        fl.append("extreme_aspect")
    if any((b[3] - b[1]) * (b[4] - b[2]) > a.max_box_area for b in boxes_std):
        fl.append("closeup")
    if any((b[2] + b[4]) / 2 < a.min_cy for b in boxes_std):
        fl.append("high_box")
    if scale > 2.0:
        fl.append("lowres")
    return fl


def render(im, mode, win, a):
    x0, y0, cw, ch = win
    if mode == "crop":
        c = im.crop((x0, y0, x0 + cw, y0 + ch))
        return c.resize((a.tw, a.th), Image.LANCZOS if cw >= a.tw else Image.BICUBIC)
    W, H = im.size
    s = min(a.tw / W, a.th / H)
    nw, nh = max(1, int(round(W * s))), max(1, int(round(H * s)))
    canvas = Image.new("RGB", (a.tw, a.th), (114, 114, 114))
    canvas.paste(im.resize((nw, nh), Image.LANCZOS if s < 1 else Image.BICUBIC), ((a.tw - nw) // 2, (a.th - nh) // 2))
    return canvas


def dhash(im):
    g = np.asarray(im.convert("L").resize((9, 8), Image.BILINEAR), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


_DCT = None


def phash(im):
    global _DCT
    n = 32
    if _DCT is None:
        k = np.arange(n)
        _DCT = np.cos(np.pi * (2 * k[None, :] + 1) * k[:, None] / (2 * n))
    g = np.asarray(im.convert("L").resize((n, n), Image.BILINEAR), dtype=np.float64)
    d = (_DCT @ g @ _DCT.T)[:8, :8].flatten()
    med = np.median(d[1:])
    return int("".join("1" if v > med else "0" for v in d), 2)


_POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def ham(a, b):
    """Hamming distances between uint64 vectors a (n,) and b (m,) -> (n, m) uint8."""
    x = a[:, None] ^ b[None, :]
    return _POP[x.view(np.uint8).reshape(x.shape + (8,))].sum(axis=2)


def near_pairs(d1, p1, d2, p2, td, tp, same):
    """Index pairs (i, j) with dHash <= td and pHash <= tp; if same, only j > i."""
    out = []
    for s in range(0, len(d1), 256):
        hd = ham(d1[s:s + 256], d2)
        ii, jj = np.nonzero(hd <= td)
        for i, j in zip(ii.tolist(), jj.tolist()):
            gi = s + i
            if same and j <= gi:
                continue
            if bin(int(p1[gi]) ^ int(p2[j])).count("1") <= tp:
                out.append((gi, j))
    return out


class Reservoir:
    def __init__(self, k, seed):
        self.k, self.n, self.items, self.rng = k, 0, [], random.Random(seed)

    def add(self, make):
        self.n += 1
        if len(self.items) < self.k:
            self.items.append(make())
        else:
            j = self.rng.randrange(self.n)
            if j < self.k:
                self.items[j] = make()


def thumb(im, boxes, text):
    t = im.resize((320, 240), Image.BILINEAR)
    d = ImageDraw.Draw(t)
    for c, x1, y1, x2, y2 in boxes:
        d.rectangle([x1 * 320, y1 * 240, x2 * 320, y2 * 240], outline=COL.get(c, (0, 255, 0)), width=2)
    d.rectangle([0, 0, 320, 12], fill=(0, 0, 0))
    d.text((2, 1), text[:52], fill=(255, 255, 0))
    return t


def save_sheet(items, path):
    if not items:
        return
    cols = 6
    rows = (len(items) + cols - 1) // cols
    sh = Image.new("RGB", (cols * 320, rows * 240), "black")
    for i, t in enumerate(items):
        sh.paste(t, ((i % cols) * 320, (i // cols) * 240))
    sh.save(path, quality=80)


def open_rgb(p, ratio):
    im = Image.open(p)
    W0, H0 = im.size
    im = im.convert("RGB")
    if ratio:
        im = im.resize((max(1, int(round(H0 * ratio))), H0), Image.BICUBIC)
    return im, W0, H0


def common(ap):
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="960x720", help="target WIDTHxHEIGHT; every output image has exactly this size")
    ap.add_argument("--min-keep", type=float, default=0.5)
    ap.add_argument("--max-box-area", type=float, default=0.35)
    ap.add_argument("--min-cy", type=float, default=0.30)
    ap.add_argument("--frame-rules", default=",".join(ALL_RULES), help="flags that remove a TRAIN image; 'none' = keep all")
    ap.add_argument("--unstretch", nargs="*", default=[], help="SOURCE=ASPECT, e.g. sb15=1.7778")
    ap.add_argument("--drop-sources", nargs="*", default=[], help="sources left out of TRAIN completely")


def prep(a):
    a.tw, a.th = (int(v) for v in a.size.lower().split("x"))
    a.rules = [] if a.frame_rules == "none" else [r for r in a.frame_rules.split(",") if r]
    bad = [r for r in a.rules if r not in ALL_RULES]
    if bad:
        sys.exit(f"unknown rule(s) {bad}; known: {ALL_RULES}")
    a.un = {}
    for s in a.unstretch:
        k, v = s.split("=", 1)
        a.un[k] = float(v)
    a.src, a.out = Path(a.src), Path(a.out)
    if not (a.src / "images").is_dir():
        sys.exit(f"{a.src}/images not found")
    if a.out.exists():
        sys.exit(f"{a.out} exists; refusing to overwrite")


def do_audit(a):
    rows, _ = read_rows(a.src)
    a.out.mkdir(parents=True)
    st = defaultdict(lambda: Counter())
    sizes = defaultdict(Counter)
    with open(a.out / "audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["out_image", "split", "source", "src_w", "src_h", "mode", "keep", "scale", "n_boxes", "flags"])
        for k, m in enumerate(rows):
            p = a.src / m["out_image"]
            with Image.open(p) as im:
                W0, H0 = im.size
            r = a.un.get(m.get("source", ""))
            W, H = (int(round(H0 * r)), H0) if r else (W0, H0)
            boxes = read_boxes(label_path(a.src, m["out_image"]))
            mode, win, keep = plan(W, H, boxes, a)
            bs, scale = map_boxes(boxes, W, H, mode, win, a)
            fl = flags_of(W, H0, mode, keep, scale, bs, a)
            key = (m.get("source", ""), m["split"])
            c = st[key]
            c["n"] += 1
            c["pad"] += mode == "pad"
            c["flagged"] += bool(set(fl) & set(a.rules))
            for x in fl:
                c[x] += 1
            sizes[m.get("source", "")][f"{W0}x{H0}"] += 1
            w.writerow([m["out_image"], m["split"], m.get("source", ""), W0, H0, mode, f"{keep:.3f}", f"{scale:.3f}", len(boxes), "|".join(fl)])
            if (k + 1) % 2000 == 0:
                print(f"  {k + 1}/{len(rows)}", flush=True)
    L = [f"# Pattern audit of {a.src} (target {a.tw}x{a.th}; nothing was written to the dataset)", "",
         f"Rules that would remove a TRAIN image: {a.rules or 'none'}. Thresholds: min-keep {a.min_keep}, max-box-area {a.max_box_area}, min-cy {a.min_cy}.", "",
         "| source | split | images | most common size | letterboxed | portrait | extreme_aspect | closeup | high_box | lowres | flagged (any rule) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (s, sp), c in sorted(st.items()):
        top = sizes[s].most_common(1)[0]
        L.append(f"| {s} | {sp} | {c['n']} | {top[0]} ({top[1]}) | {c['pad']} | {c['portrait']} | {c['extreme_aspect']} | {c['closeup']} | {c['high_box']} | {c['lowres']} | {c['flagged']} |")
    tot = Counter()
    for (s, sp), c in st.items():
        tot[sp + "_n"] += c["n"]
        tot[sp + "_flag"] += c["flagged"]
    L += ["", "| split | images | flagged | unflagged |", "|---|---|---|---|"]
    for sp in ("train", "val", "test"):
        L.append(f"| {sp} | {tot[sp + '_n']} | {tot[sp + '_flag']} | {tot[sp + '_n'] - tot[sp + '_flag']} |")
    L += ["", f"Different image sizes in the source: {len({k for c in sizes.values() for k in c})}.",
          "Flagged train images would be left out by `build`; flagged val/test images stay and are only left out of the *_stdframe lists."]
    (a.out / "audit.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def do_build(a):
    rows, fields = read_rows(a.src)
    tmp = a.out.with_name(a.out.name + ".building")
    if tmp.exists():
        sys.exit(f"{tmp} exists (an earlier build stopped); rename or remove it yourself, then run again")
    for sp in ("train", "val", "test"):
        (tmp / "images" / sp).mkdir(parents=True)
        (tmp / "labels" / sp).mkdir(parents=True)
    (tmp / "sheets").mkdir()
    res = defaultdict(lambda: Reservoir(24, 0))
    recs, drops, seen = [], [], set()
    for k, m in enumerate(rows):
        sp, src_name = m["split"], m.get("source", "")
        stem = Path(m["out_image"]).stem
        if (sp, stem) in seen:
            sys.exit(f"two images named {stem} in {sp}")
        seen.add((sp, stem))
        if sp == "train" and src_name in a.drop_sources:
            drops.append((m["out_image"], sp, src_name, "source_left_out", ""))
            continue
        im, W0, H0 = open_rgb(a.src / m["out_image"], a.un.get(src_name))
        W, H = im.size
        boxes = read_boxes(label_path(a.src, m["out_image"]))
        mode, win, keep = plan(W, H, boxes, a)
        bs, scale = map_boxes(boxes, W, H, mode, win, a)
        fl = flags_of(W, H0, mode, keep, scale, bs, a)
        out = render(im, mode, win, a)
        hit = [x for x in fl if x in a.rules]
        if sp == "train" and hit:
            drops.append((m["out_image"], sp, src_name, "framing:" + "|".join(hit), ""))
            res["dropped_" + hit[0]].add(lambda: thumb(out, bs, f"{src_name} {stem}"))
            continue
        rel = f"images/{sp}/{stem}.jpg"
        out.save(tmp / rel, quality=92)
        (tmp / "labels" / sp / f"{stem}.txt").write_text(
            "".join(f"{c} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}\n" for c, x1, y1, x2, y2 in bs), encoding="utf-8")
        recs.append({"m": m, "rel": rel, "split": sp, "source": src_name, "stem": stem, "boxes": bs, "flags": fl, "mode": mode,
                     "win": win, "src_wh": (W0, H0), "d": dhash(out), "p": phash(out), "alive": True})
        if sp == "train":
            res["kept_train"].add(lambda: thumb(out, bs, f"{src_name} {stem}"))
        if (k + 1) % 500 == 0:
            print(f"  {k + 1}/{len(rows)} images", flush=True)

    def kill(r, reason, other):
        r["alive"] = False
        os.remove(tmp / r["rel"])
        os.remove(tmp / "labels" / r["split"] / (r["stem"] + ".txt"))
        drops.append((r["m"]["out_image"], r["split"], r["source"], reason, other))

    tr = [r for r in recs if r["split"] == "train"]
    ev = [r for r in recs if r["split"] != "train"]
    if not a.no_dedup and tr and ev:
        d1, p1 = np.array([r["d"] for r in tr], dtype=np.uint64), [r["p"] for r in tr]
        d2, p2 = np.array([r["d"] for r in ev], dtype=np.uint64), [r["p"] for r in ev]
        for i, j in near_pairs(d1, p1, d2, p2, a.dhash, a.phash, False):
            if tr[i]["alive"]:
                kill(tr[i], "near_duplicate_of_val_test", ev[j]["rel"])
    tr = [r for r in tr if r["alive"]]
    n_clusters = 0
    if not a.no_dedup and len(tr) > 1:
        d1, p1 = np.array([r["d"] for r in tr], dtype=np.uint64), [r["p"] for r in tr]
        par = list(range(len(tr)))

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x
        for i, j in near_pairs(d1, p1, d1, p1, a.dhash, a.phash, True):
            par[find(i)] = find(j)
        cl = defaultdict(list)
        for i in range(len(tr)):
            cl[find(i)].append(i)
        for mem in cl.values():
            if len(mem) > 1:
                n_clusters += 1
                mem.sort(key=lambda i: (-len(tr[i]["boxes"]), tr[i]["stem"]))
                for i in mem[1:]:
                    kill(tr[i], "near_duplicate_in_train", tr[mem[0]]["rel"])

    alive = [r for r in recs if r["alive"]]
    extra = ["std_mode", "std_window", "std_src_w", "std_src_h", "std_flags"]
    base = fields if "out_image" in fields else ["out_image", "split", "source", "group_id"]
    for need in ("out_w", "out_h", "out_sha256", "n_pothole", "n_speed_bump"):
        if need not in base:
            base = base + [need]
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=base + extra, extrasaction="ignore")
        w.writeheader()
        for r in alive:
            m = dict(r["m"])
            m.update({"out_image": r["rel"], "out_w": a.tw, "out_h": a.th,
                      "out_sha256": hashlib.sha256((tmp / r["rel"]).read_bytes()).hexdigest(),
                      "n_pothole": sum(b[0] == 0 for b in r["boxes"]), "n_speed_bump": sum(b[0] == 1 for b in r["boxes"]),
                      "std_mode": r["mode"], "std_window": "%d,%d,%d,%d" % r["win"], "std_src_w": r["src_wh"][0],
                      "std_src_h": r["src_wh"][1], "std_flags": "|".join(r["flags"])})
            w.writerow(m)
    with open(tmp / "drop_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_image", "split", "source", "reason", "kept_instead"])
        w.writerows(drops)
    yaml_names = "names:\n" + "".join(f"  {k}: {v}\n" for k, v in NAMES.items())
    (tmp / "data.yaml").write_text("train: images/train\nval: images/val\ntest: images/test\n" + yaml_names, encoding="utf-8")
    info = {"src": str(a.src), "size": [a.tw, a.th], "frame_rules": a.rules, "min_keep": a.min_keep, "max_box_area": a.max_box_area,
            "min_cy": a.min_cy, "unstretch": a.un, "drop_sources": a.drop_sources, "dhash": a.dhash, "phash": a.phash, "no_dedup": a.no_dedup,
            "train_duplicate_clusters": n_clusters, "drops": dict(Counter(d[3].split(":")[0] for d in drops)), "splits": {}}
    for sp in ("val", "test"):
        ok = [r for r in alive if r["split"] == sp and not (set(r["flags"]) & set(ALL_RULES))]
        (tmp / f"{sp}_stdframe.txt").write_text("".join(f"./{r['rel']}\n" for r in ok), encoding="utf-8")
    (tmp / "data_stdframe.yaml").write_text("train: images/train\nval: val_stdframe.txt\ntest: test_stdframe.txt\n" + yaml_names, encoding="utf-8")
    for sp in ("train", "val", "test"):
        rs = [r for r in alive if r["split"] == sp]
        info["splits"][sp] = {"images": len(rs), "source_images": sum(m["split"] == sp for m in rows),
                              "pothole_boxes": sum(b[0] == 0 for r in rs for b in r["boxes"]),
                              "speed_bump_boxes": sum(b[0] == 1 for r in rs for b in r["boxes"]),
                              "negatives": sum(not r["boxes"] for r in rs), "letterboxed": sum(r["mode"] == "pad" for r in rs),
                              "standard_framing": sum(not (set(r["flags"]) & set(ALL_RULES)) for r in rs)}
    (tmp / "build_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    for name, rv in res.items():
        save_sheet(rv.items, tmp / "sheets" / f"{name}.jpg")
    tmp.rename(a.out)
    print(json.dumps(info, indent=1))
    print(f"\nbuilt {a.out}: every image is {a.tw}x{a.th}. Look at {a.out}/sheets/*.jpg before training.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    common(sub.add_parser("audit"))
    b = sub.add_parser("build")
    common(b)
    b.add_argument("--dhash", type=int, default=4)
    b.add_argument("--phash", type=int, default=10)
    b.add_argument("--no-dedup", action="store_true", help="keep every image (no duplicate removal)")
    a = ap.parse_args()
    prep(a)
    (do_audit if a.cmd == "audit" else do_build)(a)


if __name__ == "__main__":
    main()
