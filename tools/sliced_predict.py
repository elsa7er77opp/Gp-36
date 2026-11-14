"""Sliced inference (full frame + overlapping tiles) for small / far hazards, writing an Ultralytics-style
predictions.json that tools/metrics_report.py scores exactly like `yolo val save_json=True`.

    python -I tools/sliced_predict.py --weights runs/detect/<run>/weights/best.pt --data <part or r2 dir> --split val \
        --tile 640 --overlap 0.25 --imgsz 960 --merge nms --out runs/detect/<run>_SLICED_val/predictions.json

Per image (images/<split>/*):
  1. the full frame is predicted at --imgsz (the normal path);
  2. the frame is cut into tiles of --tile px with --overlap (fraction) overlap; the grid always covers the right and
     bottom edges (the last tile is shifted back inside the image); each tile is predicted at --tile-imgsz
     (default = --tile); --rows-from 0.4 keeps only tiles whose bottom edge is below 0.4 H (sky / far rows are
     skipped, they hold no hazard on our forward view; set 0 to tile everything);
  3. tile boxes are shifted to frame coordinates; boxes cut by an INNER tile border (within --edge px of a border that
     is not the image border) are dropped, the neighbouring tile or the full frame sees them whole;
  4. full-frame and tile boxes are merged per class: --merge nms (class-wise greedy NMS, IoU --iou) or
     --merge wbf (tools/wbf_ensemble.fuse_boxes, every source weight 1, no agreement rescaling).
All predictions use conf 0.001 (as `yolo val`) so the PR curve is complete; the operating threshold is chosen on VAL
by metrics_report.py as for any model. Latency: <out>_latency.json holds per-image wall time (ms) of the whole sliced
pipeline and the number of tiles; the laptop measures it on the RTX 5050 (the cloud has no GPU).
Requires ultralytics (laptop). The pure functions (tile_grid, shift/edge filter, nms, merge) are unit-tested.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wbf_ensemble import fuse_boxes, iou_xywh  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def _starts(L, t, step):
    if L <= t:
        return [0]
    s = list(range(0, L - t, step))
    if s[-1] != L - t:
        s.append(L - t)
    return s


def tile_grid(W, H, tile, overlap, rows_from=0.0):
    """Tiles (x0, y0, x1, y1) covering the image; tiles whose bottom edge is above rows_from*H are skipped."""
    step = max(1, int(round(tile * (1 - overlap))))
    out = []
    for y in _starts(H, tile, step):
        for x in _starts(W, tile, step):
            x1, y1 = min(x + tile, W), min(y + tile, H)
            if y1 >= rows_from * H:
                out.append((x, y, x1, y1))
    return out


def shift_and_filter(dets, tile, W, H, edge=2.0):
    """dets in tile coords [(cls, score, [x, y, w, h])] -> frame coords; drop boxes touching an INNER tile border."""
    x0, y0, x1, y1 = tile
    out = []
    for c, s, (x, y, w, h) in dets:
        X, Y = x + x0, y + y0
        cut = ((x0 > 0 and X <= x0 + edge) or (y0 > 0 and Y <= y0 + edge) or
               (x1 < W and X + w >= x1 - edge) or (y1 < H and Y + h >= y1 - edge))
        if not cut:
            out.append((c, s, [X, Y, w, h]))
    return out


def nms(dets, iou_thr=0.5):
    """Class-wise greedy NMS on [(cls, score, [x, y, w, h])]."""
    keep = []
    for d in sorted(dets, key=lambda t: -t[1]):
        if all(k[0] != d[0] or iou_xywh(k[2], d[2]) <= iou_thr for k in keep):
            keep.append(d)
    return keep


def merge(dets, method="nms", iou_thr=0.5):
    if method == "nms":
        return nms(dets, iou_thr)
    out = []
    for c in sorted({d[0] for d in dets}):
        boxes = [(0, s, b) for cc, s, b in dets if cc == c]   # one "model": no agreement rescaling
        out += [(c, s, b) for s, b in fuse_boxes(boxes, [1.0], iou_thr, skip=0.0)]
    return out


def to_json(stem, dets):
    return [{"image_id": stem, "category_id": int(c) + 1, "bbox": [round(v, 3) for v in b], "score": round(float(s), 5)}
            for c, s, b in dets]


def _predict(model, img, imgsz, conf):
    r = model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    xyxy = r.boxes.xyxy.cpu().numpy()
    return [(int(c), float(s), [float(a), float(b), float(x2 - a), float(y2 - b)])
            for (a, b, x2, y2), s, c in zip(xyxy, r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy())]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True, help="dataset dir with images/<split>/")
    ap.add_argument("--split", required=True)
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--tile", type=int, default=640)
    ap.add_argument("--tile-imgsz", type=int)
    ap.add_argument("--overlap", type=float, default=0.25)
    ap.add_argument("--rows-from", type=float, default=0.4)
    ap.add_argument("--edge", type=float, default=2.0)
    ap.add_argument("--merge", choices=["nms", "wbf"], default="nms")
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--conf", type=float, default=0.001)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    from PIL import Image
    from ultralytics import YOLO
    model = YOLO(a.weights)
    imgs = sorted(p for p in (Path(a.data) / "images" / a.split).iterdir() if p.suffix.lower() in IMG_EXT)
    preds, lat = [], []
    for p in imgs:
        im = Image.open(p).convert("RGB")
        W, H = im.size
        t0 = time.perf_counter()
        dets = _predict(model, im, a.imgsz, a.conf)
        tiles = tile_grid(W, H, a.tile, a.overlap, a.rows_from)
        for t in tiles:
            dets += shift_and_filter(_predict(model, im.crop(t), a.tile_imgsz or a.tile, a.conf), t, W, H, a.edge)
        dets = merge(dets, a.merge, a.iou)
        lat.append({"image": p.stem, "ms": round((time.perf_counter() - t0) * 1000, 2), "tiles": len(tiles)})
        preds += to_json(p.stem, dets)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(preds), encoding="utf-8")
    ms = sorted(x["ms"] for x in lat)
    info = {"weights": a.weights, "data": a.data, "split": a.split, "args": vars(a), "images": len(lat),
            "ms_median": ms[len(ms) // 2] if ms else None, "ms_p95": ms[int(0.95 * (len(ms) - 1))] if ms else None,
            "per_image": lat}
    out.with_name(out.stem + "_latency.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in info.items() if k != "per_image"}))


if __name__ == "__main__":
    main()
