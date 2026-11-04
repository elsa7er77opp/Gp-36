"""Per-class metrics report from saved predictions (definitions: STATUS_for_claude.md, Stage 7.2).

    python -I tools/metrics_report.py --data road_hazards_v3a_r2 --split val \
        --pred v1=runs/detect/v3a_r1_11n_VALr2_json/predictions.json \
        --pred runA_s0=runs/detect/v3a_r2_11n_VAL_json/predictions.json \
        --out review/metrics_r3/val_r2 [--by source] [--thresholds <val report.json>]

predictions.json = `yolo val save_json=True` output (image_id = file stem, bbox = x,y,w,h px, category_id = class+1),
made with the default val conf (0.001) so the full PR curve is available. Ground truth comes from
<data>/labels/<split>/<stem>.txt; image sizes and grouping columns come from <data>/manifest.csv.

Per model and class it reports:
  AP50, AP50-95  all-point COCO-style 101-point interpolated AP, our own implementation, so every model is
                 scored identically (Ultralytics' printout may differ in the 3rd decimal)
  thr            operating confidence = argmax F1 on VAL; for another split pass --thresholds <val report.json>
  P, R, F1       at thr, IoU >= 0.5
  BoxAcc         TP / (TP + FP + FN) at thr
  ImgAcc         share of images whose "class present" == "class predicted at thr"; n_neg images reported with it
  NearR          A1: recall at thr over GT with bottom edge y2 >= 0.60 H and sqrt(area fraction) >= 0.05
  P@R50          A3: interpolated precision at recall 0.50
and the same P/R/F1/BoxAcc/ImgAcc at the deployed conf 0.35 (perception/config.yaml fsm.hazard_min_conf).
With --by <manifest column>, AP50, P, R at thr are also given per value of that column.
Writes <out>/report.json and <out>/report.md (refuses to overwrite).
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.labels import parse_label_file  # noqa: E402

NAMES = {0: "pothole", 1: "speed_bump"}
DEPLOY_CONF = 0.35
IOUS = np.round(np.arange(0.5, 0.96, 0.05), 2)


def iou_matrix(a, b):  # a: (n,4) b: (m,4) xyxy normalised
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    ix = np.clip(np.minimum(a[:, None, 2], b[None, :, 2]) - np.maximum(a[:, None, 0], b[None, :, 0]), 0, None)
    iy = np.clip(np.minimum(a[:, None, 3], b[None, :, 3]) - np.maximum(a[:, None, 1], b[None, :, 1]), 0, None)
    inter = ix * iy
    area = lambda x: (x[:, 2] - x[:, 0]) * (x[:, 3] - x[:, 1])  # noqa: E731
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-12)


def match(preds, gts, thr_iou):
    """Greedy by score. preds: list of (score, box); gts: (m,4). Returns tp flags (n,), matched gt index or -1."""
    order = np.argsort([-p[0] for p in preds], kind="stable")
    tp = np.zeros(len(preds), bool)
    gi = -np.ones(len(preds), int)
    if len(preds) == 0 or len(gts) == 0:
        return tp, gi
    M = iou_matrix(np.array([preds[k][1] for k in order]), gts)
    used = np.zeros(len(gts), bool)
    for r, k in enumerate(order):
        cand = np.where(~used & (M[r] >= thr_iou))[0]
        if len(cand):
            j = cand[np.argmax(M[r, cand])]
            used[j] = True
            tp[k], gi[k] = True, j
    return tp, gi


def ap101(scores, tp, n_gt):
    if n_gt == 0:
        return None
    if len(scores) == 0:
        return 0.0
    o = np.argsort(-np.asarray(scores), kind="stable")
    t = np.asarray(tp)[o]
    ctp, cfp = np.cumsum(t), np.cumsum(~t)
    rec = ctp / n_gt
    prec = ctp / np.maximum(ctp + cfp, 1e-12)
    prec = np.maximum.accumulate(prec[::-1])[::-1]
    pts = np.linspace(0, 1, 101)
    idx = np.searchsorted(rec, pts, side="left")
    return float(np.mean([prec[i] if i < len(prec) else 0.0 for i in idx]))


def load(data, split, pred_path):
    meta = {}
    with open(data / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            if m["split"] == split:
                meta[Path(m["out_image"]).stem] = m
    gt = {}
    for stem, m in meta.items():
        boxes = parse_label_file(data / "labels" / split / f"{stem}.txt")[0]
        gt[stem] = [(b.cls, (b.xc - b.w / 2, b.yc - b.h / 2, b.xc + b.w / 2, b.yc + b.h / 2), b.w * b.h) for b in boxes]
    pr = defaultdict(list)
    for p in json.load(open(pred_path, encoding="utf-8")):
        stem = str(p["image_id"])
        if stem not in meta:
            sys.exit(f"{pred_path}: prediction for an image not in {split}: {stem}")
        W, H = int(meta[stem]["out_w"]), int(meta[stem]["out_h"])
        x, y, w, h = p["bbox"]
        pr[stem].append((p["category_id"] - 1, float(p["score"]), (x / W, y / H, (x + w) / W, (y + h) / H)))
    return meta, gt, pr


def evaluate(stems, gt, pr, c, thr=None):
    """All metrics for class c over the image list stems. thr=None -> choose argmax-F1 threshold."""
    scores, flags = [], []
    flags_by_iou = {t: [] for t in IOUS}
    n_gt = 0
    per_img = []  # (stem, gt boxes of c, preds of c with tp flag and gt index at IoU 0.5)
    for s in stems:
        g = [b for b in gt[s] if b[0] == c]
        p = [(sc, bx) for cl, sc, bx in pr.get(s, []) if cl == c]
        G = np.array([b[1] for b in g]) if g else np.zeros((0, 4))
        n_gt += len(g)
        tp50, gi = match(p, G, 0.5)
        for t in IOUS:
            flags_by_iou[t] += list(match(p, G, t)[0]) if t != 0.5 else list(tp50)
        scores += [x[0] for x in p]
        flags += list(tp50)
        per_img.append((s, g, p, tp50, gi))
    ap50 = ap101(scores, flags, n_gt)
    ap5095 = None if n_gt == 0 else float(np.mean([ap101(scores, flags_by_iou[t], n_gt) for t in IOUS]))

    o = np.argsort(-np.asarray(scores), kind="stable")
    sc_sorted = np.asarray(scores)[o]
    t_sorted = np.asarray(flags, bool)[o]
    ctp, cfp = np.cumsum(t_sorted), np.cumsum(~t_sorted)
    if thr is None:
        if len(sc_sorted) and n_gt:
            f1 = 2 * ctp / (ctp + cfp + n_gt)
            # only thresholds at a score boundary (last index of each distinct score)
            last = np.r_[sc_sorted[1:] != sc_sorted[:-1], True]
            k = int(np.argmax(np.where(last, f1, -1)))
            thr = float(sc_sorted[k])
        else:
            thr = 1.0
    rec = ctp / max(n_gt, 1)
    prec = ctp / np.maximum(ctp + cfp, 1e-12)
    penv = np.maximum.accumulate(prec[::-1])[::-1] if len(prec) else prec
    i50 = np.searchsorted(rec, 0.5, side="left")
    p_at_r50 = float(penv[i50]) if n_gt and i50 < len(penv) else 0.0

    def at(th):
        tp = fp = fn = 0
        img_ok = n_img = n_neg = 0
        near_tp = near_n = 0
        for s, g, p, tp50, gi in per_img:
            keep = np.array([x[0] >= th for x in p], bool)
            t = int(np.sum(tp50 & keep))
            f = int(np.sum(~tp50 & keep))
            matched = set(gi[tp50 & keep].tolist())
            tp += t
            fp += f
            fn += len(g) - t
            present, predicted = len(g) > 0, bool(keep.any())
            img_ok += present == predicted
            n_img += 1
            n_neg += not present
            for j, (_, bx, af) in enumerate(g):
                if bx[3] >= 0.60 and af ** 0.5 >= 0.05:
                    near_n += 1
                    near_tp += j in matched
        P = tp / (tp + fp) if tp + fp else 0.0
        R = tp / (tp + fn) if tp + fn else 0.0
        return {"thr": round(th, 4), "tp": tp, "fp": fp, "fn": fn, "P": P, "R": R,
                "F1": 2 * P * R / (P + R) if P + R else 0.0, "BoxAcc": tp / (tp + fp + fn) if tp + fp + fn else 0.0,
                "ImgAcc": img_ok / n_img if n_img else 0.0, "n_img": n_img, "n_neg": n_neg,
                "NearR": near_tp / near_n if near_n else None, "n_near": near_n}

    return {"n_gt": n_gt, "AP50": ap50, "AP50_95": ap5095, "P_at_R50": p_at_r50, "op": at(thr), "deploy": at(DEPLOY_CONF)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--pred", action="append", required=True, help="name=path/to/predictions.json")
    ap.add_argument("--thresholds", help="val report.json whose operating thresholds are reused (for test)")
    ap.add_argument("--by", action="append", default=[], help="manifest column for subset reports")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out, data = Path(args.out), Path(args.data)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    fixed = json.load(open(args.thresholds, encoding="utf-8")) if args.thresholds else None
    if args.split == "test" and fixed is None:
        sys.exit("test needs --thresholds from a val report (thresholds are never chosen on test)")

    rep = {"data": str(data), "split": args.split, "definitions": "STATUS_for_claude.md Stage 7.2",
           "thresholds_from": args.thresholds or "argmax F1 on this split (val)", "models": {}}
    for spec in args.pred:
        name, path = spec.split("=", 1)
        meta, gt, pr = load(data, args.split, path)
        stems = sorted(meta)
        r = {"pred": path, "classes": {}, "by": {}}
        for c, cn in NAMES.items():
            thr = fixed["models"][name]["classes"][cn]["op"]["thr"] if fixed else None
            r["classes"][cn] = evaluate(stems, gt, pr, c, thr)
            for col in args.by:
                groups = defaultdict(list)
                for s in stems:
                    groups[meta[s].get(col, "")].append(s)
                th = r["classes"][cn]["op"]["thr"]
                for gv, ss in sorted(groups.items()):
                    e = evaluate(ss, gt, pr, c, th)
                    if e["n_gt"] or e["op"]["fp"]:
                        r["by"].setdefault(f"{col}={gv}", {})[cn] = {
                            "n_img": len(ss), "n_gt": e["n_gt"], "AP50": e["AP50"], "P": e["op"]["P"], "R": e["op"]["R"],
                            "fp": e["op"]["fp"], "ImgAcc": e["op"]["ImgAcc"]}
        rep["models"][name] = r
    out.mkdir(parents=True)
    (out / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")

    f = lambda v: "—" if v is None else f"{v:.3f}"  # noqa: E731
    L = [f"# Metrics report — {data} / {args.split}", "",
         f"Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: {rep['thresholds_from']}. IoU 0.5. Source: `report.json`.", "",
         "| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in rep["models"].items():
        for cn, e in r["classes"].items():
            o, d = e["op"], e["deploy"]
            L.append(f"| {name} | {cn} | {e['n_gt']} | {f(e['AP50'])} | {f(e['AP50_95'])} | {o['thr']:.3f} | {f(o['P'])} | {f(o['R'])} | "
                     f"{f(o['F1'])} | {f(o['BoxAcc'])} | {f(o['ImgAcc'])} ({o['n_neg']}) | {f(o['NearR'])} ({o['n_near']}) | "
                     f"{f(e['P_at_R50'])} | {f(d['P'])} / {f(d['R'])} / {f(d['ImgAcc'])} |")
    for name, r in rep["models"].items():
        if r["by"]:
            L += ["", f"## {name}: subsets (at the operating threshold)", "",
                  "| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |", "|---|---|---|---|---|---|---|---|---|"]
            for k, v in r["by"].items():
                for cn, e in v.items():
                    L.append(f"| {k} | {cn} | {e['n_img']} | {e['n_gt']} | {f(e['AP50'])} | {f(e['P'])} | {f(e['R'])} | {e['fp']} | {f(e['ImgAcc'])} |")
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
