"""Per-sample scan: integrity, hashes and label summary (one full decode per image)."""
from pathlib import Path

from PIL import Image

from .hashing import dhash, phash
from .io_utils import inspect_image
from .labels import parse_label_file
from .manifest import sha256_file


def scan_sample(sample):
    """Return sample merged with image info, sha256, dhash, phash and raw label summary."""
    out = dict(sample)
    info = inspect_image(sample["image"])
    out.update(info)
    out["sha256"] = sha256_file(sample["image"])
    out["dhash"] = out["phash"] = 0
    if info["ok"]:
        with Image.open(sample["image"]) as im:
            im.load()
            out["dhash"], out["phash"] = dhash(im), phash(im)
    boxes, issues = parse_label_file(sample["label"]) if sample.get("label") and Path(sample["label"]).exists() else ([], [])
    out["boxes"] = [(b.cls, b.xc, b.yc, b.w, b.h) for b in boxes]
    out["n_poly"] = sum(1 for b in boxes if b.kind == "poly")
    out["label_errors"] = sorted({i.code for i in issues if i.severity == "error"})
    out["label_warnings"] = sorted({i.code for i in issues if i.severity == "warning"})
    if info["ok"] and boxes:
        out["min_box_px"] = min(min(b.w * info["width"], b.h * info["height"]) for b in boxes)
        # shortest box side after letterboxing the image to 960 px on its long side
        s = 960 / max(info["width"], info["height"])
        out["min_box_px_at960"] = out["min_box_px"] * s
    else:
        out["min_box_px"] = out["min_box_px_at960"] = None
    return out
