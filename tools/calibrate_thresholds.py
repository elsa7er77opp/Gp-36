"""Choose a per-class confidence threshold from saved VAL predictions and write it as a JSON proposal.

    python -I tools/calibrate_thresholds.py --data road_hazards_v3a_r2 --split val \
        --pred runs/detect/v3b_A_11n_960_VALr2_json/predictions.json --model D1 \
        --mode f1 | recall:0.80 | precision:0.90 \
        --out review/metrics_r3/thresholds_D1_f1.json [--min-conf 0.05] [--bootstrap 200]

Inputs are the same as tools/metrics_report.py (predictions.json from `yolo val save_json=True conf=0.001`,
ground truth from <data>/labels/<split>, sizes from <data>/manifest.csv). Matching is the same greedy IoU>=0.5
matching (imported from metrics_report.py), so P/R here equal the metrics report at the same threshold.

Modes (per class, chosen independently):
  f1             the threshold that maximises F1 (the Stage 7.2 operating point);
  recall:R       the HIGHEST threshold whose recall >= R (most precise point that still reaches R);
  precision:P    the LOWEST threshold whose precision >= P (highest recall that still keeps P).
If a target cannot be reached, the class gets "reached": false and the closest point is reported.
Only thresholds >= --min-conf are considered (the live pipeline never runs below it).
With --bootstrap N, images are resampled N times (seed 0) and the 5/50/95 % quantiles of the chosen threshold
and of P/R at the chosen threshold are reported, to show how stable the choice is.

Rules: the split must be val (thresholds are never chosen on test; the tool refuses --split test). The output is
a PROPOSAL for perception/: this tool never edits perception/config.yaml. The deployed pipeline has ONE value
(fsm.hazard_min_conf); per-class values need a reviewed change of perception/ by the owner.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics_report import NAMES, load, match  # noqa: E402


def per_image(stems, gt, pr, c):
    """For class c: list of (scores array, tp flags array, n_gt) per image, IoU 0.5."""
    out = []
    for s in stems:
        g = [b for b in gt[s] if b[0] == c]
        p = [(sc, bx) for cl, sc, bx in pr.get(s, []) if cl == c]
        G = np.array([b[1] for b in g]) if g else np.zeros((0, 4))
        tp, _ = match(p, G, 0.5)
        out.append((np.array([x[0] for x in p], float), tp, len(g)))
    return out


def curve(imgs, min_conf):
    """Return thresholds (descending, distinct score boundaries >= min_conf) and P, R, F1 at each."""
    sc = np.concatenate([i[0] for i in imgs]) if imgs else np.zeros(0)
    tp = np.concatenate([i[1] for i in imgs]).astype(bool) if imgs else np.zeros(0, bool)
    n_gt = int(sum(i[2] for i in imgs))
    o = np.argsort(-sc, kind="stable")
    sc, tp = sc[o], tp[o]
    keep = sc >= min_conf
    sc, tp = sc[keep], tp[keep]
    ctp, cfp = np.cumsum(tp), np.cumsum(~tp)
    last = np.r_[sc[1:] != sc[:-1], True] if len(sc) else np.zeros(0, bool)
    thr, ctp, cfp = sc[last], ctp[last], cfp[last]
    P = ctp / np.maximum(ctp + cfp, 1)
    R = ctp / max(n_gt, 1)
    F1 = np.where(P + R > 0, 2 * P * R / np.maximum(P + R, 1e-12), 0.0)
    return thr, P, R, F1, ctp, cfp, n_gt


def choose(thr, P, R, F1, mode):
    """Index into the curve for the mode, and whether the target was reached."""
    if len(thr) == 0:
        return None, False
    if mode == "f1":
        return int(np.argmax(F1)), True
    kind, _, val = mode.partition(":")
    t = float(val)
    if kind == "recall":
        ok = np.nonzero(R >= t)[0]  # thresholds are descending -> first index = highest threshold
        return (int(ok[0]), True) if len(ok) else (int(np.argmax(R)), False)
    if kind == "precision":
        ok = np.nonzero(P >= t)[0]  # last index = lowest threshold that still keeps P
        return (int(ok[-1]), True) if len(ok) else (int(np.argmax(P)), False)
    raise ValueError(mode)


def calibrate(imgs, mode, min_conf):
    thr, P, R, F1, ctp, cfp, n_gt = curve(imgs, min_conf)
    k, reached = choose(thr, P, R, F1, mode)
    if k is None:
        return {"n_gt": n_gt, "conf": None, "reached": False, "note": "no predictions above min_conf"}
    return {"n_gt": n_gt, "conf": round(float(thr[k]), 4), "reached": bool(reached), "P": round(float(P[k]), 4),
            "R": round(float(R[k]), 4), "F1": round(float(F1[k]), 4), "tp": int(ctp[k]), "fp": int(cfp[k]),
            "fn": int(n_gt - ctp[k])}


def bootstrap(imgs, mode, min_conf, n, seed=0):
    rng = np.random.default_rng(seed)
    vals = {"conf": [], "P": [], "R": []}
    for _ in range(n):
        idx = rng.integers(0, len(imgs), len(imgs))
        r = calibrate([imgs[i] for i in idx], mode, min_conf)
        if r["conf"] is not None:
            for key in vals:
                vals[key].append(r[key])
    return {key: [round(float(q), 4) for q in np.quantile(v, [0.05, 0.5, 0.95])] if v else None
            for key, v in vals.items()} | {"n": n, "quantiles": [0.05, 0.5, 0.95]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--pred", required=True, help="predictions.json (save_json, conf 0.001)")
    ap.add_argument("--model", required=True, help="name of the model, recorded in the JSON")
    ap.add_argument("--mode", nargs="+", default=["f1"],
                    help="one mode for all classes, or one per class in class order (pothole speed_bump)")
    ap.add_argument("--min-conf", type=float, default=0.05)
    ap.add_argument("--bootstrap", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.split != "val":
        sys.exit("thresholds are chosen on val only (Stage 7.2); refusing --split " + a.split)
    modes = a.mode * len(NAMES) if len(a.mode) == 1 else a.mode
    if len(modes) != len(NAMES):
        sys.exit(f"--mode needs 1 or {len(NAMES)} values")
    for m in modes:
        choose(np.ones(1), np.ones(1), np.ones(1), np.ones(1), m)  # validates the mode string
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    data = Path(a.data)
    meta, gt, pr = load(data, a.split, a.pred)
    stems = sorted(meta)
    rep = {"kind": "per-class confidence threshold PROPOSAL (not applied)", "model": a.model, "data": str(data),
           "split": a.split, "pred": a.pred, "iou": 0.5, "min_conf": a.min_conf, "n_images": len(stems),
           "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "tool": "tools/calibrate_thresholds.py",
           "note": "perception/config.yaml is NOT edited. The live FSM uses one value fsm.hazard_min_conf; "
                   "per-class values need an owner-reviewed perception/ change. Re-check on the frozen test once, "
                   "with these thresholds fixed (tools/metrics_report.py --thresholds).",
           "classes": {}}
    for (c, cn), mode in zip(NAMES.items(), modes):
        imgs = per_image(stems, gt, pr, c)
        r = {"mode": mode, **calibrate(imgs, mode, a.min_conf)}
        if a.bootstrap:
            r["bootstrap"] = bootstrap(imgs, mode, a.min_conf, a.bootstrap)
        rep["classes"][cn] = r
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
