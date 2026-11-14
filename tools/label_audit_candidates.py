"""Label-audit candidates on a TRAIN split from a model's predictions, plus crop sheets for visual review (STATUS Stage 34).

    python -I tools/label_audit_candidates.py find --data road_hazards_v3b_C --split train \
        --pred runs/detect/AUDIT_C_on_v3bC_train/predictions.json --out review/label_audit_r3/candidates.csv
    python -I tools/label_audit_candidates.py sheets --data road_hazards_v3b_C --cands review/label_audit_r3/candidates.csv \
        --source bpo --kind unfit --out review/label_audit_r3/sheets/bpo_unfit

Candidate kinds (rules written in STATUS Stage 34 before any result):
  unfit    a GT box with no same-class prediction of score >= 0.05 at IoU >= 0.3 (a label the model refuses to learn)
  missing  a prediction of score >= 0.5 with IoU < 0.1 to every GT box of either class (possible unlabelled hazard)
  loose    a GT box whose best same-class prediction with score >= 0.3 has IoU in [0.1, 0.4)
GT boxes are numbered by their line in the label file (the composed datasets write one clean box per line), so a
verdict maps back to exactly one line. Sheets: 12 tiles per page, each the box on 2x its size of context (min 160 px),
GT in green, model box in red, tile title = cand_id, source, class, score. The val/test splits are refused.
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics_report as mr  # noqa: E402

NAMES = {0: "pothole", 1: "speed_bump"}
FIELDS = ["cand_id", "kind", "source", "stem", "out_image", "cls", "gt_line", "x1", "y1", "x2", "y2", "score", "iou",
          "px1", "py1", "px2", "py2"]


def find(args):
    if args.split != "train":
        sys.exit("label audit runs on the train split only")
    data = Path(args.data)
    meta, gt, pr = mr.load(data, args.split, Path(args.pred))
    rows = []
    for stem in sorted(meta):
        m = meta[stem]
        g = gt[stem]
        p = pr.get(stem, [])
        gb = np.array([b for _, b, _ in g]) if g else np.zeros((0, 4))
        pb = np.array([b for _, _, b in p]) if p else np.zeros((0, 4))
        M = mr.iou_matrix(gb, pb)  # (n_gt, n_pred)
        base = {"source": m["source"], "stem": stem, "out_image": m["out_image"]}
        for i, (c, b, _) in enumerate(g):
            same = [j for j, (pc, _, _) in enumerate(p) if pc == c]
            ok = [j for j in same if p[j][1] >= 0.05 and M[i, j] >= 0.3]
            best = max(same, key=lambda j: M[i, j] * (p[j][1] >= 0.3), default=None)
            if not ok:
                bj = max(same, key=lambda j: (M[i, j], p[j][1]), default=None)
                rows.append({**base, "kind": "unfit", "cls": c, "gt_line": i, "box": b,
                             "score": p[bj][1] if bj is not None else 0.0, "iou": M[i, bj] if bj is not None else 0.0,
                             "pbox": p[bj][2] if bj is not None and M[i, bj] > 0 else None})
            elif best is not None and p[best][1] >= 0.3 and 0.1 <= M[i, best] < 0.4:
                rows.append({**base, "kind": "loose", "cls": c, "gt_line": i, "box": b, "score": p[best][1],
                             "iou": M[i, best], "pbox": p[best][2]})
        for j, (pc, sc, b) in enumerate(p):
            if sc >= 0.5 and (len(g) == 0 or M[:, j].max() < 0.1):
                rows.append({**base, "kind": "missing", "cls": pc, "gt_line": -1, "box": b, "score": sc,
                             "iou": float(M[:, j].max()) if len(g) else 0.0, "pbox": b})
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists - refusing to overwrite")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for k, r in enumerate(rows):
            pb = r["pbox"] or (None,) * 4
            w.writerow({"cand_id": f"{r['kind'][0]}{k:05d}", "kind": r["kind"], "source": r["source"], "stem": r["stem"],
                        "out_image": r["out_image"], "cls": NAMES[r["cls"]], "gt_line": r["gt_line"],
                        **{n: f"{v:.6f}" for n, v in zip(("x1", "y1", "x2", "y2"), r["box"])},
                        "score": f"{r['score']:.4f}", "iou": f"{r['iou']:.3f}",
                        **{n: ("" if v is None else f"{v:.6f}") for n, v in zip(("px1", "py1", "px2", "py2"), pb)}})
    n_gt = {}
    for stem in meta:
        for c, _, _ in gt[stem]:
            n_gt[(meta[stem]["source"], c)] = n_gt.get((meta[stem]["source"], c), 0) + 1
    print(f"{len(rows)} candidates -> {out}")
    print(f"{'source':8s} {'gt_pot':>6s} {'gt_bump':>7s} {'unfit':>6s} {'loose':>6s} {'missing':>7s}")
    for s in sorted({m['source'] for m in meta.values()}):
        cnt = {k: sum(1 for r in rows if r["source"] == s and r["kind"] == k) for k in ("unfit", "loose", "missing")}
        print(f"{s:8s} {n_gt.get((s, 0), 0):6d} {n_gt.get((s, 1), 0):7d} {cnt['unfit']:6d} {cnt['loose']:6d} {cnt['missing']:7d}")


def sheets(args):
    data, out = Path(args.data), Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists - refusing to overwrite")
    rows = [r for r in csv.DictReader(open(args.cands, encoding="utf-8"))
            if (not args.source or r["source"] in args.source.split(",")) and (not args.kind or r["kind"] == args.kind)
            and (not args.cls or r["cls"] == args.cls)]
    if args.kind == "missing":
        rows.sort(key=lambda r: -float(r["score"]))
    else:
        rows.sort(key=lambda r: float(r["score"]))
    rows = rows[: args.limit] if args.limit else rows
    out.mkdir(parents=True)
    T, cols, per = 420, 4, 12
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for s in range(0, len(rows), per):
        page = Image.new("RGB", (cols * T, (per // cols) * (T + 22)), "white")
        d = ImageDraw.Draw(page)
        for k, r in enumerate(rows[s:s + per]):
            im = Image.open(data / r["out_image"]).convert("RGB")
            W, H = im.size
            x1, y1, x2, y2 = (float(r[n]) for n in ("x1", "y1", "x2", "y2"))
            bw, bh = (x2 - x1) * W, (y2 - y1) * H
            side = max(bw, bh) * 2.0 + 80
            side = max(side, 160)
            cx, cy = (x1 + x2) / 2 * W, (y1 + y2) / 2 * H
            L, Tp = max(0, cx - side / 2), max(0, cy - side / 2)
            R, B = min(W, cx + side / 2), min(H, cy + side / 2)
            crop = im.crop((int(L), int(Tp), int(R), int(B)))
            sc = T / max(crop.size)
            crop = crop.resize((max(1, int(crop.size[0] * sc)), max(1, int(crop.size[1] * sc))))
            cd = ImageDraw.Draw(crop)
            tr = lambda X, Y: ((X - L) * sc, (Y - Tp) * sc)  # noqa: E731
            if r["kind"] != "missing":
                cd.rectangle([*tr(x1 * W, y1 * H), *tr(x2 * W, y2 * H)], outline=(0, 230, 0), width=3)
            if r["px1"]:
                p = [float(r[n]) for n in ("px1", "py1", "px2", "py2")]
                cd.rectangle([*tr(p[0] * W, p[1] * H), *tr(p[2] * W, p[3] * H)], outline=(255, 30, 30), width=2)
            ox, oy = (k % cols) * T, (k // cols) * (T + 22)
            page.paste(crop, (ox, oy + 22))
            d.text((ox + 4, oy + 3), f"{r['cand_id']} {r['source']} {r['cls'][:4]} s={float(r['score']):.2f} "
                                     f"y2={y2:.2f}", fill="black", font=font)
        page.save(out / f"sheet_{s // per:03d}.jpg", quality=88)
    with open(out / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["sheet"] if rows else FIELDS)
        w.writeheader()
        for k, r in enumerate(rows):
            w.writerow({**r, "sheet": k // per})
    print(f"{len(rows)} tiles, {(len(rows) + per - 1) // per} sheets -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["find", "sheets"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--pred")
    ap.add_argument("--cands")
    ap.add_argument("--source", help="comma-separated sources")
    ap.add_argument("--kind", choices=["unfit", "missing", "loose"])
    ap.add_argument("--cls", choices=["pothole", "speed_bump"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    find(args) if args.cmd == "find" else sheets(args)


if __name__ == "__main__":
    main()
