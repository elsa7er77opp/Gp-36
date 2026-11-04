"""Per-class check of the COCO detector of the pipeline on labelled ROAD images (not COCO val).

    python -I tools/coco_road_eval.py --images ../GP36_Dataset/yolo-automotive-dataset/bdd100k --out runs/coco_road_eval_bdd

Ground truth: the BDD100k subset of yolo-automotive-dataset (Favelli et al. 2024, MIT). Its class ids were
identified empirically (review/new_data_r3, Stage 10 of STATUS): 0 = vehicle (car, truck and bus merged),
24 = person; the other ids are traffic lights / signs / riders and are not scored. So only two per-class rows
are possible: `person` (COCO person) and `vehicle` (COCO car + truck + bus merged into one class). Bicycle,
motorcycle and dog have no labels here: only the COCO-benchmark number exists for them.
Detector settings come from perception/config.yaml (coco: weights, imgsz, iou); conf 0.001 is used to get the
full PR curve, and P/R are reported at the deployed conf (0.35) and at the F1-optimal threshold.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics_report import ap101, match  # noqa: E402

GT_MAP = {0: "vehicle", 24: "person"}
PRED_MAP = {"car": "vehicle", "truck": "vehicle", "bus": "vehicle", "person": "person"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default="perception/config.yaml")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists")
    cc = yaml.safe_load(open(args.config, encoding="utf-8"))["coco"]
    from ultralytics import YOLO
    m = YOLO(cc["weights"])
    fs = sorted(Path(args.images).glob("*.jpg"))
    per = {c: {"scores": [], "tp": [], "n_gt": 0} for c in ("vehicle", "person")}
    for f in fs:
        g = {c: [] for c in per}
        for line in f.with_suffix(".txt").read_text(encoding="utf-8").splitlines():
            a = line.split()
            if a and int(a[0]) in GT_MAP:
                x, y, w, h = map(float, a[1:5])
                g[GT_MAP[int(a[0])]].append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        r = m.predict(str(f), imgsz=cc["imgsz"], conf=0.001, iou=cc["iou"], device=args.device, verbose=False)[0]
        P, C, S = r.boxes.xyxyn.cpu().numpy(), r.boxes.cls.cpu().numpy().astype(int), r.boxes.conf.cpu().numpy()
        for c in per:
            preds = [(float(s), tuple(b)) for b, k, s in zip(P, C, S) if PRED_MAP.get(m.names[k]) == c]
            tp, _ = match(preds, np.array(g[c]) if g[c] else np.zeros((0, 4)), 0.5)
            per[c]["scores"] += [p[0] for p in preds]
            per[c]["tp"] += list(tp)
            per[c]["n_gt"] += len(g[c])
    res = {"images": len(fs), "source": args.images, "config": args.config, "weights": cc["weights"], "classes": {}}
    for c, d in per.items():
        s, t, n = np.array(d["scores"]), np.array(d["tp"], bool), d["n_gt"]
        o = np.argsort(-s, kind="stable")
        s, t = s[o], t[o]
        ctp, cfp = np.cumsum(t), np.cumsum(~t)
        f1 = 2 * ctp / (ctp + cfp + n)
        k = int(np.argmax(f1))

        def at(th):
            i = np.searchsorted(-s, -th, side="right")
            tp, fp = int(ctp[i - 1]) if i else 0, int(cfp[i - 1]) if i else 0
            return {"thr": th, "P": tp / max(tp + fp, 1), "R": tp / max(n, 1), "BoxAcc": tp / max(tp + fp + (n - tp), 1)}
        res["classes"][c] = {"n_gt": n, "AP50": ap101(s, t, n), "f1_opt": at(float(s[k])), "deploy": at(float(cc["conf"]))}
    out.mkdir(parents=True)
    (out / "report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
