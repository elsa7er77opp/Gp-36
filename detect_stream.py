"""GP36 live perception stream.

The same frame goes to the hazard model (YOLO11n baseline v1: pothole, speed_bump)
and to the pretrained COCO YOLO11n. Both outputs are merged into one namespaced
list (hazard:*, coco:*) and a state machine gives SAFE / WARNING / STOP.

Examples (Windows, from the GP36_AI folder):
    venv\\Scripts\\python detect_stream.py --source 0 --name webcam_try1
    venv\\Scripts\\python detect_stream.py --source D:\\clips\\street.mp4 --name street1 --save-video
    venv\\Scripts\\python detect_stream.py --source http://<esp32-cam-ip>:81/stream --name esp32_try1

Every run writes a NEW folder runs/stream/<name>_<timestamp>/ with:
    frames.csv      one row per frame: latency per stage, counts, state, reasons
    detections.csv  one row per detection
    summary.json    config, weight hashes, latency p50/p95/p99, state counts
    stream.mp4      only with --save-video

Do not run this on images or videos from train/val/test or from the held-out
unseen-road / unseen-country lists: the FSM thresholds are tuned on what this
script sees, and those sets must stay untouched.
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import yaml

from perception.detectors import NamespacedDetector
from perception.fsm import LEVEL, PerceptionFSM, FsmConfig
from perception.latency import summarize
from perception.overlay import draw
from perception.types import COCO_NS, HAZARD_NS

ROOT = Path(__file__).resolve().parent


def sha256_short(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def new_run_dir(name):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    d = ROOT / "runs" / "stream" / f"{name}_{stamp}"
    d.mkdir(parents=True, exist_ok=False)  # never reuse or overwrite a folder
    return d


def open_source(src):
    cap = cv2.VideoCapture(int(src)) if src.isdigit() else cv2.VideoCapture(src)
    if not cap.isOpened():
        sys.exit(f"cannot open source {src!r}")
    return cap


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="webcam index (0), video file, or stream URL")
    ap.add_argument("--name", default="run", help="prefix of the output folder")
    ap.add_argument("--config", default=str(ROOT / "perception" / "config.yaml"))
    ap.add_argument("--device", default=None, help="e.g. 0 or cpu (default: Ultralytics picks)")
    ap.add_argument("--max-frames", type=int, default=0, help="stop after N frames (0 = no limit)")
    ap.add_argument("--no-show", action="store_true", help="do not open a window")
    ap.add_argument("--save-video", action="store_true", help="also write the annotated video")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    fsm_cfg = FsmConfig.from_dict(cfg["fsm"])
    hz, cc = cfg["hazard"], cfg["coco"]
    hz_w, cc_w = ROOT / hz["weights"], ROOT / cc["weights"]

    hazard = NamespacedDetector(hz_w, HAZARD_NS, hz["imgsz"], hz["conf"], hz["iou"],
                                expect_names=hz.get("expect_names"), device=args.device)
    coco = NamespacedDetector(cc_w, COCO_NS, cc["imgsz"], cc["conf"], cc["iou"],
                              classes=cc.get("classes"), device=args.device)
    fsm = PerceptionFSM(fsm_cfg)
    warmup = int(cfg.get("stream", {}).get("warmup_frames", 10))

    cap = open_source(args.source)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or None
    out = new_run_dir(args.name)
    print(f"output: {out}")

    fcsv = open(out / "frames.csv", "w", newline="", encoding="utf-8")
    dcsv = open(out / "detections.csv", "w", newline="", encoding="utf-8")
    fw, dw = csv.writer(fcsv), csv.writer(dcsv)
    fw.writerow(["frame", "t_s", "hazard_ms", "coco_ms", "fsm_ms", "total_ms", "n_hazard", "n_coco", "state",
                 "reasons"])
    dw.writerow(["frame", "label", "uid", "conf", "x1", "y1", "x2", "y2", "frame_w", "frame_h"])

    writer = None
    lat = {"hazard_ms": [], "coco_ms": [], "fsm_ms": [], "total_ms": []}
    states = {"SAFE": 0, "WARNING": 0, "STOP": 0}
    worst = "SAFE"
    t_start = time.perf_counter()
    n = 0
    read_failures = 0
    try:
        while True:
            ok, frame = cap.read()
            now = time.perf_counter() - t_start
            if not ok:
                if src_fps and not args.source.isdigit() and not args.source.startswith("http"):
                    break  # end of a video file
                read_failures += 1
                state, reasons = fsm.tick(now)  # live source dropped a frame: fail-safe check
                if read_failures > 50:
                    print("source stopped delivering frames")
                    break
                continue
            read_failures = 0
            t0 = time.perf_counter()
            h_dets, h_ms = hazard.predict(frame)
            c_dets, c_ms = coco.predict(frame)
            t1 = time.perf_counter()
            dets = h_dets + c_dets
            state, reasons = fsm.update(dets, now)
            f_ms = (time.perf_counter() - t1) * 1000.0
            total = (time.perf_counter() - t0) * 1000.0

            fw.writerow([n, f"{now:.3f}", f"{h_ms:.2f}", f"{c_ms:.2f}", f"{f_ms:.3f}", f"{total:.2f}",
                         len(h_dets), len(c_dets), state, " | ".join(reasons)])
            for d in dets:
                dw.writerow([n, d.label, d.uid, f"{d.conf:.4f}", *(f"{v:.1f}" for v in d.xyxy), *d.frame_wh])
            if n >= warmup:
                lat["hazard_ms"].append(h_ms)
                lat["coco_ms"].append(c_ms)
                lat["fsm_ms"].append(f_ms)
                lat["total_ms"].append(total)
            states[state] += 1
            if LEVEL[state] > LEVEL[worst]:
                worst = state

            vis = draw(frame, dets, state, reasons, fsm_cfg.corridor_x, f"{1000.0 / max(total, 1e-6):.1f} FPS")
            if args.save_video:
                if writer is None:
                    hh, ww = vis.shape[:2]
                    writer = cv2.VideoWriter(str(out / "stream.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                             src_fps or 15, (ww, hh))
                writer.write(vis)
            if not args.no_show:
                cv2.imshow("GP36 perception (q to quit)", vis)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            n += 1
            if args.max_frames and n >= args.max_frames:
                break
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()
        fcsv.close()
        dcsv.close()

    summary = {
        "source": args.source, "source_fps": src_fps, "frames": n, "warmup_frames_excluded": warmup,
        "git_commit": git_commit(),
        "weights": {"hazard": {"path": hz["weights"], "sha256_16": sha256_short(hz_w)},
                    "coco": {"path": cc["weights"], "sha256_16": sha256_short(cc_w)}},
        "config": cfg, "latency_ms": {k: summarize(v) for k, v in lat.items()},
        "state_frames": states, "worst_state": worst,
        "note": "Latency measured on this machine for this run only. FSM thresholds are placeholders.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"frames": n, "latency_ms": summary["latency_ms"], "state_frames": states}, indent=2))


if __name__ == "__main__":
    main()
