"""Weighted Boxes Fusion (WBF) of >= 2 Ultralytics `save_json` predictions.json files (own implementation).

    python -I tools/wbf_ensemble.py --pred runs/detect/A_val/predictions.json --pred runs/detect/B_val/predictions.json:2 \
        --iou 0.55 --skip 0.001 --out runs/detect/wbf_AB_val/predictions.json

Input / output format: list of {"image_id", "category_id", "bbox": [x, y, w, h] px, "score"} (Ultralytics save_json).
The output is scored with tools/metrics_report.py exactly like a single model (same GT, same thresholds rule:
the operating threshold of the WBF model is chosen on VAL, never on test).

Algorithm (Solovyev, Wang, Gabruseva 2021, "Weighted boxes fusion"), per image and class:
  1. keep boxes with score >= --skip; each model m has weight w_m (default 1; `path:w` sets it);
  2. sort all boxes by score * w_m (descending);
  3. for each box, find the cluster whose CURRENT fused box has the highest IoU with it; if that IoU > --iou the box
     joins the cluster, otherwise it starts a new cluster; the fused box is recomputed after every insert:
       coords = sum(score_i * w_i * coord_i) / sum(score_i * w_i)
  4. fused score = sum(score_i * w_i) / sum(w_i)  (weighted mean, stays in [0, 1]), then rescaled by
       min(sum of the weights of the DISTINCT models in the cluster, W) / W,   W = sum of all model weights,
     so a box found by only one of two equal models keeps half its score (the paper's conf_type="avg" rescaling,
     but counted per distinct model so two boxes of one model cannot fake agreement).
Images present in any input appear in the output. Nothing is printed except a summary.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def iou_xywh(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0.0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    u = a[2] * a[3] + b[2] * b[3] - inter
    return inter / u if u > 0 else 0.0


def fuse_boxes(boxes, weights, iou_thr=0.55, skip=0.001):
    """boxes: list of (model_index, score, [x, y, w, h]) for ONE image and ONE class.
    weights: list of model weights. Returns list of (score, [x, y, w, h])."""
    W = float(sum(weights))
    items = sorted(((m, s, b) for m, s, b in boxes if s >= skip), key=lambda t: -t[1] * weights[t[0]])
    clusters = []  # each: {"members": [(m, s, b)], "box": fused box [x, y, w, h]}
    for m, s, b in items:
        best, best_iou = None, iou_thr
        for c in clusters:
            v = iou_xywh(c["box"], b)
            if v > best_iou:
                best, best_iou = c, v
        if best is None:
            clusters.append({"members": [(m, s, b)], "box": list(b)})
            continue
        best["members"].append((m, s, b))
        tw = sum(sc * weights[mm] for mm, sc, _ in best["members"])
        x1 = sum(sc * weights[mm] * bb[0] for mm, sc, bb in best["members"]) / tw
        y1 = sum(sc * weights[mm] * bb[1] for mm, sc, bb in best["members"]) / tw
        x2 = sum(sc * weights[mm] * (bb[0] + bb[2]) for mm, sc, bb in best["members"]) / tw
        y2 = sum(sc * weights[mm] * (bb[1] + bb[3]) for mm, sc, bb in best["members"]) / tw
        best["box"] = [x1, y1, x2 - x1, y2 - y1]
    out = []
    for c in clusters:
        score = sum(s * weights[m] for m, s, _ in c["members"]) / sum(weights[m] for m, _, _ in c["members"])
        models = {m for m, _, _ in c["members"]}
        score *= min(sum(weights[m] for m in models), W) / W
        out.append((score, c["box"]))
    return out


def fuse_files(pred_lists, weights, iou_thr=0.55, skip=0.001):
    by = defaultdict(list)  # (image_id, category_id) -> [(m, score, bbox)]
    images = set()
    for m, preds in enumerate(pred_lists):
        for p in preds:
            images.add(p["image_id"])
            by[(p["image_id"], p["category_id"])].append((m, float(p["score"]), [float(v) for v in p["bbox"]]))
    out = []
    for (img, cat), boxes in sorted(by.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        for s, b in fuse_boxes(boxes, weights, iou_thr, skip):
            out.append({"image_id": img, "category_id": cat, "bbox": [round(v, 3) for v in b], "score": round(s, 5)})
    return out, images


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", action="append", required=True, help="predictions.json[:weight], at least 2")
    ap.add_argument("--iou", type=float, default=0.55)
    ap.add_argument("--skip", type=float, default=0.001)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if len(a.pred) < 2:
        sys.exit("WBF needs at least 2 --pred files")
    paths, weights = [], []
    for spec in a.pred:
        path, _, w = spec.rpartition(":") if spec.rsplit(":", 1)[-1].replace(".", "", 1).isdigit() else (spec, "", "1")
        paths.append(Path(path))
        weights.append(float(w))
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    lists = [json.load(open(p, encoding="utf-8")) for p in paths]
    fused, images = fuse_files(lists, weights, a.iou, a.skip)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fused), encoding="utf-8")
    meta = {"inputs": [str(p) for p in paths], "weights": weights, "iou": a.iou, "skip": a.skip,
            "boxes_in": [len(x) for x in lists], "boxes_out": len(fused), "images": len(images)}
    out.with_name(out.stem + "_wbf_info.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
