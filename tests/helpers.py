import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def smooth_image(seed, size=(320, 240)):
    """A smooth random image whose perceptual hashes survive re-encoding and resizing."""
    rng = np.random.default_rng(seed)
    small = Image.fromarray(rng.integers(0, 256, (6, 8, 3), dtype=np.uint8))
    return small.resize(size, Image.BICUBIC)


def save(im, path, fmt="JPEG", **kw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, fmt, **kw)
    return path


def write_label(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
