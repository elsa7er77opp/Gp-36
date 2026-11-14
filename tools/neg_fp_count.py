"""False alarms on a hazard-free VAL set (STATUS Stage 38, accept rule 3).

    python -I tools/neg_fp_count.py --data parts_r3/egm --split val \
        --model C runs/detect/PARTVAL_egm_C/predictions.json review/metrics_r3/thr_C_f1.json \
        --model E3 ... --out review/metrics_r3/negfp_egm_E3

Every image of <data>/labels/<split> must have an EMPTY label (the tool refuses otherwise), so every kept
prediction is a false alarm. A prediction is kept when its score >= that model's per-class threshold
(the "conf" of each class in the calibrate_thresholds.py JSON, chosen on r2 val, never here).
Writes report.json and report.md; refuses to overwrite --out. Test splits are refused.
"""
import argparse, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--split", default="val")
ap.add_argument("--model", nargs=3, action="append", metavar=("NAME", "PREDICTIONS", "THRESHOLDS"), required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
if a.split == "test":
    sys.exit("test split refused")
out = Path(a.out)
if out.exists():
    sys.exit(f"{out} exists; refusing to overwrite")
lab = Path(a.data) / "labels" / a.split
stems = sorted(p.stem for p in lab.glob("*.txt"))
img_dir = Path(a.data) / "images" / a.split
stems_img = sorted(p.stem for p in img_dir.iterdir() if p.is_file())
if set(stems) != set(stems_img):
    sys.exit("labels and images differ")
for s in stems:
    if (lab / f"{s}.txt").read_text().strip():
        sys.exit(f"{s}: label not empty - this tool is for hazard-free sets only")
names = {1: "pothole", 2: "speed_bump"}
rep = {"data": a.data, "split": a.split, "n_images": len(stems), "models": {}}
for name, pred, thr in a.model:
    t = json.loads(Path(thr).read_text(encoding="utf-8"))["classes"]
    th = {c: float(t[n]["conf"]) for c, n in names.items()}
    P = json.loads(Path(pred).read_text(encoding="utf-8"))
    fp = {n: 0 for n in names.values()}
    imgs = {n: set() for n in names.values()}
    for p in P:
        s, c = str(p["image_id"]), int(p["category_id"])
        if s not in set(stems) or c not in th:
            continue
        if p["score"] >= th[c]:
            fp[names[c]] += 1
            imgs[names[c]].add(s)
    n = max(len(stems), 1)
    rep["models"][name] = {"thresholds": {names[c]: th[c] for c in th},
                           "fp_boxes": fp, "fp_boxes_total": sum(fp.values()),
                           "fp_per_image": round(sum(fp.values()) / n, 4),
                           "images_with_fp": {k: len(v) for k, v in imgs.items()},
                           "images_with_any_fp": len(imgs["pothole"] | imgs["speed_bump"])}
out.mkdir(parents=True)
(out / "report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
L = [f"# False alarms on {a.data} {a.split} ({len(stems)} hazard-free images)", "",
     "| model | thr pothole | thr bump | FP pothole | FP bump | FP / image | images with any FP |", "|---|---|---|---|---|---|---|"]
for k, v in rep["models"].items():
    L.append(f"| {k} | {v['thresholds']['pothole']:.3f} | {v['thresholds']['speed_bump']:.3f} | {v['fp_boxes']['pothole']} | "
             f"{v['fp_boxes']['speed_bump']} | {v['fp_per_image']:.3f} | {v['images_with_any_fp']} |")
(out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
