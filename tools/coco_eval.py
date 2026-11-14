"""Official COCO evaluation (pycocotools COCOeval, bbox) of saved predictions, next to tools/metrics_report.py.

    python -I tools/coco_eval.py --data road_hazards_v3a_r2 --split val \
        --pred C=runs/detect/v3b_C_11n_960_s0_r2_VALr2_json/predictions.json --pred D1=... --out review/metrics_r3/coco_val_r2

Ground truth and predictions are read with metrics_report.load (same files, same image list), converted to COCO json
in memory (image ids = 1..N over the sorted stems, category ids 1 = pothole, 2 = speed_bump, bbox in pixels of the
image size in manifest.csv) and scored with pycocotools 2.0.8 (requirements-lock.txt), unchanged defaults:
IoU 0.50:0.05:0.95, maxDets 100, area ranges small < 32^2 px, medium 32^2-96^2, large > 96^2 px.
Caveat written into every report: area ranges are in ORIGINAL pixels and our images range from 640 px wide to 4K,
so "small/medium/large" are not the same physical size across sources.
Reports per model: all-class stats (AP, AP50, AP75, APs, APm, APl, AR1, AR10, AR100, ARs, ARm, ARl) and the same per class.
The test split is refused unless --allow-test is given (use it only for a ledger-recorded final test, tools/test_ledger.py).
Writes <out>/report.json and <out>/report.md (refuses to overwrite).
"""
import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics_report as mr  # noqa: E402
from pycocotools.coco import COCO  # noqa: E402
from pycocotools.cocoeval import COCOeval  # noqa: E402

NAMES = ["pothole", "speed_bump"]
STATS = ["AP", "AP50", "AP75", "APs", "APm", "APl", "AR1", "AR10", "AR100", "ARs", "ARm", "ARl"]


def to_coco(meta, gt, pr):
    stems = sorted(meta)
    ids = {s: i + 1 for i, s in enumerate(stems)}
    images, anns, dets = [], [], []
    for s in stems:
        W, H = int(meta[s]["out_w"]), int(meta[s]["out_h"])
        images.append({"id": ids[s], "file_name": s, "width": W, "height": H})
        for c, (x1, y1, x2, y2), _ in gt[s]:
            w, h = (x2 - x1) * W, (y2 - y1) * H
            anns.append({"id": len(anns) + 1, "image_id": ids[s], "category_id": c + 1, "bbox": [x1 * W, y1 * H, w, h],
                         "area": w * h, "iscrowd": 0})
        for c, sc, (x1, y1, x2, y2) in pr.get(s, []):
            dets.append({"image_id": ids[s], "category_id": c + 1, "score": sc,
                         "bbox": [x1 * W, y1 * H, (x2 - x1) * W, (y2 - y1) * H]})
    gtj = {"images": images, "annotations": anns, "categories": [{"id": i + 1, "name": n} for i, n in enumerate(NAMES)]}
    return gtj, dets


def coco_stats(gtj, dets, cat_ids=None):
    with contextlib.redirect_stdout(io.StringIO()):
        g = COCO()
        g.dataset = gtj
        g.createIndex()
        d = g.loadRes(dets) if dets else COCO()
        e = COCOeval(g, d, "bbox")
        if cat_ids:
            e.params.catIds = cat_ids
        e.evaluate()
        e.accumulate()
        e.summarize()
    return {k: (None if v < 0 else round(float(v), 4)) for k, v in zip(STATS, e.stats)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--pred", action="append", required=True, help="name=path/to/predictions.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-test", action="store_true")
    args = ap.parse_args()
    if args.split == "test" and not args.allow_test:
        sys.exit("refusing the test split without --allow-test (final, ledger-recorded use only)")
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists - refusing to overwrite")
    data = Path(args.data)
    rep = {"data": str(data), "split": args.split, "tool": "pycocotools COCOeval bbox, default params", "models": {}}
    for spec in args.pred:
        name, path = spec.split("=", 1)
        meta, gt, pr = mr.load(data, args.split, Path(path))
        gtj, dets = to_coco(meta, gt, pr)
        r = {"pred": path, "n_images": len(gtj["images"]), "all": coco_stats(gtj, dets), "classes": {}}
        for i, n in enumerate(NAMES):
            n_gt = sum(a["category_id"] == i + 1 for a in gtj["annotations"])
            r["classes"][n] = {"n_gt": n_gt, **(coco_stats(gtj, dets, [i + 1]) if n_gt else {})}
        rep["models"][name] = r
    out.mkdir(parents=True)
    (out / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    f = lambda v: "—" if v is None else f"{v:.3f}"  # noqa: E731
    lines = [f"# COCO evaluation (pycocotools) — {data.name} / {args.split}", "",
             "Official COCOeval bbox, default parameters (IoU .50:.05:.95, maxDets 100). AP = mAP50-95, AP50 = mAP@0.5.",
             "Area ranges (small < 32², medium 32²–96², large > 96² px) are in original pixels; our sources range from "
             "640 px to 4K wide, so the size columns are not comparable across sources. Source: `report.json`.", "",
             "| model | class | n_gt | AP | AP50 | AP75 | APs | APm | APl | AR100 | ARs | ARm | ARl |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in rep["models"].items():
        rows = [("all", sum(c["n_gt"] for c in r["classes"].values()), r["all"])]
        rows += [(n, c["n_gt"], c) for n, c in r["classes"].items()]
        for cn, ng, s in rows:
            lines.append(f"| {name} | {cn} | {ng} | " + " | ".join(f(s.get(k)) for k in
                                                                    ("AP", "AP50", "AP75", "APs", "APm", "APl", "AR100", "ARs", "ARm", "ARl")) + " |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
