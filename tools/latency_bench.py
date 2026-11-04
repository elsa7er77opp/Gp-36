"""Per-frame latency (p50/p95/p99) of the hazard and COCO detectors on the same frames.

    python -I tools/latency_bench.py --frames road_hazards_v3a_r2/images/val --n 300 \
        --hazard runs/detect/v3a_r2_11n_960_s0/weights/best.pt runs/detect/v3a_r1_11n_960_s0/weights/best.pt \
        --out runs/latency_2026-11-01.json

Detector settings (imgsz, conf, iou, classes) are read from perception/config.yaml and are not changed;
only the hazard weights are swapped. Timings come from NamespacedDetector.predict (pre- + inference +
post-processing, one frame at a time, batch 1). Each model gets --warmup untimed frames first. "pipeline"
is hazard + COCO run back to back on one frame, as detect_stream.py does. Frames are val images only.
"""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

import cv2
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perception.detectors import NamespacedDetector  # noqa: E402
from perception.latency import summarize  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--hazard", nargs="+", required=True)
    ap.add_argument("--config", default="perception/config.yaml")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    paths = sorted(p for p in Path(args.frames).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))[:args.n]
    frames = [cv2.imread(str(p)) for p in paths]
    if any(f is None for f in frames):
        sys.exit("unreadable frame")

    hc, cc = cfg["hazard"], cfg["coco"]
    coco = NamespacedDetector(cc["weights"], "coco", imgsz=cc["imgsz"], conf=cc["conf"], iou=cc["iou"],
                              classes=cc.get("classes"))
    import torch
    res = {"frames_dir": args.frames, "n_frames": len(frames), "warmup": args.warmup, "config": args.config,
           "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
           "torch": torch.__version__, "python": platform.python_version(),
           "frame_sizes": sorted({f"{f.shape[1]}x{f.shape[0]}" for f in frames}),
           "note": "dev laptop GPU, not pod hardware; one frame at a time, fp32", "models": {}}

    def timed(det):
        for f in frames[:args.warmup]:
            det.predict(f)
        return [det.predict(f)[1] for f in frames]

    res["models"]["coco"] = summarize(timed(coco))
    for w in args.hazard:
        haz = NamespacedDetector(w, "hazard", imgsz=hc["imgsz"], conf=hc["conf"], iou=hc["iou"],
                                 expect_names=hc.get("expect_names"))
        res["models"][f"hazard:{w}"] = summarize(timed(haz))
        pipe = []
        for f in frames:
            t0 = time.perf_counter()
            haz.predict(f)
            coco.predict(f)
            pipe.append((time.perf_counter() - t0) * 1000.0)
        res["models"][f"pipeline:{w}+coco"] = summarize(pipe)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
