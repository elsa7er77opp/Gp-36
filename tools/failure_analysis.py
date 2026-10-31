"""Failure analysis of a detector on the VAL split (never test), from a saved predictions.json.

    python -I tools/failure_analysis.py --pred runs/detect/v3a_r2_11n_VAL_json/predictions.json \
        --data road_hazards_v3a_r2 --conf 0.35 --out review/clean_r2/failure_val_runA

predictions.json is what `yolo val save_json=True` writes (bbox = x, y, w, h in pixels; category_id = class + 1).
At one operating point (--conf, default 0.35 = perception fsm.hazard_min_conf, read only), predictions are
matched greedily by score to ground truth of the same class at IoU >= --iou. Every FP is typed:
  wrong_class   IoU >= iou with a GT box of the other class
  localization  0.1 <= IoU < iou with a GT box of the same class
  duplicate     IoU >= iou with a same-class GT box that was already matched
  background    anything else
FN and TP are broken down by class, box size (sqrt of the box area fraction) and source, and the groups
with the most misses are listed. Contact sheets show the worst images (GT solid, predictions thin).
Writes summary.json, per_image.csv and sheets/ under --out (refuses to overwrite).
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.labels import parse_label_file  # noqa: E402
from gp36data.overlay import COLORS, contact_sheet, draw_boxes, tile  # noqa: E402

NAMES = {0: "pothole", 1: "speed_bump"}
SIZES = ((0.0, 0.05, "tiny"), (0.05, 0.15, "small"), (0.15, 0.35, "medium"), (0.35, 9.0, "large"))


def size_bucket(w, h):
    s = (w * h) ** 0.5  # normalised w, h
    return next(name for lo, hi, name in SIZES if lo <= s < hi)


def iou(a, b):  # x1, y1, x2, y2 normalised
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def xyxy(xc, yc, w, h):
    return (xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="val", choices=["val", "train"])  # test is never analysed
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet-n", type=int, default=24)
    args = ap.parse_args()
    out, data = Path(args.out), Path(args.data)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")

    meta = {}
    with open(data / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            if m["split"] == args.split:
                meta[Path(m["out_image"]).stem] = m
    preds = defaultdict(list)
    for p in json.load(open(args.pred, encoding="utf-8")):
        if p["score"] < args.conf:
            continue
        m = meta.get(str(p["image_id"]))
        if m is None:
            sys.exit(f"prediction for an image not in {args.split}: {p['image_id']}")
        W, H = int(m["out_w"]), int(m["out_h"])
        x, y, w, h = p["bbox"]
        preds[str(p["image_id"])].append((p["category_id"] - 1, p["score"], (x / W, y / H, (x + w) / W, (y + h) / H)))

    rows, fp_types = [], Counter()
    tally = defaultdict(Counter)  # key -> Counter(tp, fn, fp)
    for stem, m in sorted(meta.items()):
        gts = [(b.cls, xyxy(b.xc, b.yc, b.w, b.h), b) for b in parse_label_file(data / "labels" / args.split / f"{stem}.txt")[0]]
        ps = sorted(preds.get(stem, []), key=lambda t: -t[1])
        matched = [False] * len(gts)
        n_fp = Counter()
        for cls, score, box in ps:
            best, bj = 0.0, -1
            for j, (gc, gb, _) in enumerate(gts):
                if gc == cls and not matched[j]:
                    v = iou(box, gb)
                    if v > best:
                        best, bj = v, j
            if best >= args.iou:
                matched[bj] = True
                g = gts[bj][2]
                for key in (("class", NAMES[cls]), ("size", f"{NAMES[cls]}/{size_bucket(g.w, g.h)}"),
                            ("source", f"{NAMES[cls]}/{m['source']}")):
                    tally[key]["tp"] += 1
                continue
            same = [iou(box, gb) for gc, gb, _ in gts if gc == cls]
            other = [iou(box, gb) for gc, gb, _ in gts if gc != cls]
            if other and max(other) >= args.iou:
                t = "wrong_class"
            elif same and max(same) >= args.iou:
                t = "duplicate"
            elif same and max(same) >= 0.1:
                t = "localization"
            else:
                t = "background"
            fp_types[(NAMES[cls], t)] += 1
            n_fp[t] += 1
            tally[("class", NAMES[cls])]["fp"] += 1
            tally[("source", f"{NAMES[cls]}/{m['source']}")]["fp"] += 1
        n_fn = Counter()
        for j, (gc, _, g) in enumerate(gts):
            if not matched[j]:
                n_fn[NAMES[gc]] += 1
                for key in (("class", NAMES[gc]), ("size", f"{NAMES[gc]}/{size_bucket(g.w, g.h)}"),
                            ("source", f"{NAMES[gc]}/{m['source']}")):
                    tally[key]["fn"] += 1
        rows.append({"stem": stem, "source": m["source"], "group_id": m["group_id"], "sample_id": m["sample_id"],
                     "n_gt": len(gts), "n_pred": len(ps), "tp": sum(matched),
                     "fn_pothole": n_fn["pothole"], "fn_speed_bump": n_fn["speed_bump"],
                     **{f"fp_{t}": n_fp[t] for t in ("background", "localization", "wrong_class", "duplicate")}})

    def table(kind):
        res = {}
        for (k, name), c in sorted(tally.items()):
            if k == kind:
                tp, fn, fp = c["tp"], c["fn"], c["fp"]
                res[name] = {"tp": tp, "fn": fn, "fp": fp,
                             "recall": round(tp / (tp + fn), 3) if tp + fn else None,
                             "precision": round(tp / (tp + fp), 3) if tp + fp else None}
        return res

    groups = Counter()
    for r in rows:
        groups[(r["source"], r["group_id"])] += r["fn_pothole"] + r["fn_speed_bump"]
    summary = {
        "pred": args.pred, "data": str(data), "split": args.split, "conf": args.conf, "iou": args.iou,
        "images": len(rows), "by_class": table("class"), "by_size": table("size"), "by_source": table("source"),
        "fp_types": {f"{c}/{t}": n for (c, t), n in sorted(fp_types.items())},
        "top_fn_groups": [{"source": s, "group_id": g, "fn": n} for (s, g), n in groups.most_common(15) if n],
        "size_buckets_sqrt_area": {name: [lo, hi] for lo, hi, name in SIZES},
    }
    (out / "sheets").mkdir(parents=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    with open(out / "per_image.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    def sheet(name, key):
        pick = sorted((r for r in rows if key(r) > 0), key=lambda r: -key(r))[:args.sheet_n]
        tiles = []
        for r in pick:
            m = meta[r["stem"]]
            with Image.open(data / m["out_image"]) as im:
                gt = [(b.cls, b.xc, b.yc, b.w, b.h) for b in parse_label_file(data / "labels" / args.split / f"{r['stem']}.txt")[0]]
                img = draw_boxes(im, gt, number=False)
            d = ImageDraw.Draw(img)
            W, H = img.size
            for cls, score, (x1, y1, x2, y2) in preds.get(r["stem"], []):
                d.rectangle([x1 * W, y1 * H, x2 * W, y2 * H], outline=(255, 255, 255), width=max(1, round(max(W, H) / 900)))
                d.text((x1 * W + 3, y2 * H - 14), f"{NAMES[cls][0]}{score:.2f}", fill=COLORS[cls])
            tiles.append(tile(img, [f"{r['source']} {r['sample_id'][-46:]}",
                                    f"FN p{r['fn_pothole']} b{r['fn_speed_bump']}  FP bg{r['fp_background']} "
                                    f"loc{r['fp_localization']} cls{r['fp_wrong_class']}"], width=420))
        if tiles:
            contact_sheet(tiles, cols=4, title=f"{name} (conf>={args.conf}; GT solid red/blue, pred white)").save(
                out / "sheets" / f"{name}.jpg", quality=85)

    sheet("fn_speed_bump", lambda r: r["fn_speed_bump"])
    sheet("fn_pothole", lambda r: r["fn_pothole"])
    sheet("fp_background", lambda r: r["fp_background"])
    print(json.dumps({k: summary[k] for k in ("by_class", "fp_types")}, indent=1))


if __name__ == "__main__":
    main()
