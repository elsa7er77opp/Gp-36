"""Build a model YAML with Ultralytics on CPU (no data, no weights needed) and print params, GFLOPs, strides.

    python -I tools/check_model_yaml.py models/yolo11n-p2.yaml [--ref yolo11n.yaml] [--imgsz 640 960] [--weights yolo11n.pt]
        [--out review/metrics_r3/model_check_p2.json]

For each YAML: number of parameters, GFLOPs at each --imgsz (thop, as in Ultralytics' model.info()), the Detect
strides, and the shapes of one forward pass on a zero image. With --weights, it also reports how many tensors of
the pretrained checkpoint transfer into the new model by name and shape (what `YOLO(yaml).load(pt)` does).
"""
import argparse
import json
import sys
from pathlib import Path


def flops(model, imgsz):
    import copy

    import torch
    from ultralytics.utils.torch_utils import get_flops
    try:
        return round(get_flops(model, imgsz), 3)
    except Exception:  # noqa: BLE001  older/newer signature
        import thop
        m = copy.deepcopy(model).eval()
        x = torch.zeros(1, 3, imgsz, imgsz)
        return round(thop.profile(m, inputs=[x], verbose=False)[0] / 1e9 * 2, 3)


def build(cfg, nc, imgszs):
    import torch
    from ultralytics.nn.tasks import DetectionModel
    m = DetectionModel(cfg, ch=3, nc=nc, verbose=False).eval()
    det = m.model[-1]
    with torch.no_grad():
        y = m(torch.zeros(1, 3, imgszs[-1], imgszs[-1]))
    feats = y[1] if isinstance(y, (list, tuple)) and len(y) > 1 else None
    if isinstance(feats, dict):  # Ultralytics >= 8.4 returns {"boxes", "scores", "feats"}
        feats = feats.get("feats")
    shapes = [list(t.shape) for t in feats] if isinstance(feats, (list, tuple)) else None
    return m, {"yaml": str(cfg), "nc": nc, "params": int(sum(p.numel() for p in m.parameters())),
               "gflops": {str(s): flops(m, s) for s in imgszs}, "strides": [int(s) for s in det.stride.tolist()],
               "n_detect_layers": int(det.nl), "forward_feature_shapes": shapes}


def transfer(model, weights):
    import torch
    # Ultralytics checkpoints pickle the model object, so weights_only=False is needed: use ONLY trusted
    # checkpoints (the official yolo11n.pt, SHA-256 checked on the laptop).
    ck = torch.load(weights, map_location="cpu", weights_only=False)
    src = (ck.get("ema") or ck["model"]).float().state_dict()
    dst = model.state_dict()
    ok = [k for k, v in src.items() if k in dst and dst[k].shape == v.shape]
    return {"weights": str(weights), "src_tensors": len(src), "dst_tensors": len(dst), "transferred": len(ok)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml")
    ap.add_argument("--ref", default="yolo11n.yaml", help="reference YAML (Ultralytics built-in name or path)")
    ap.add_argument("--nc", type=int, default=2)
    ap.add_argument("--imgsz", type=int, nargs="+", default=[640, 960])
    ap.add_argument("--weights")
    ap.add_argument("--out")
    a = ap.parse_args()
    import ultralytics
    rep = {"ultralytics": ultralytics.__version__, "device": "cpu"}
    m, rep["model"] = build(a.yaml, a.nc, a.imgsz)
    if a.ref:
        _, rep["reference"] = build(a.ref, a.nc, a.imgsz)
    if a.weights:
        rep["transfer"] = transfer(m, a.weights)
    txt = json.dumps(rep, indent=1)
    print(txt)
    if a.out:
        out = Path(a.out)
        if out.exists():
            sys.exit(f"{out} exists; refusing to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
