"""Load configs/sources.yaml and enumerate raw samples."""
import re
from pathlib import Path

import yaml

from .io_utils import pair_images_labels

# Roboflow speed-bump v15 video frames: frame0-MM-SS-cc[-N-]_jpg.rf.<hash>  (N = video number, absent = video 1)
VIDEO_FRAME = re.compile(r"^frame\d+-(?P<m>\d+)-(?P<s>\d+)-(?P<cs>\d+)(?:-(?P<vid>\d+)-)?_jpg(?:\.rf\.[0-9a-f]{32})?$", re.IGNORECASE)
RF_NAME = re.compile(r"^(?P<orig>.+?)_(?P<ext>jpe?g|png|bmp|webp)\.rf\.[0-9a-f]{32}$", re.IGNORECASE)


def load_sources(config_path):
    config_path = Path(config_path).resolve()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    for s in cfg["sources"].values():
        for sp in s["splits"].values():
            sp["images"] = (base / sp["images"]).resolve()
            sp["labels"] = (base / sp["labels"]).resolve()
        s["class_map"] = {int(k): v for k, v in s["class_map"].items()}
        s["ignore"] = [int(k) for k in s.get("ignore", [])]
    return cfg


def group_key(source_id, rule, image_path):
    """Metadata grouping key, or '' when the rule gives none."""
    if rule == "single_sequence":
        return f"{source_id}:sequence"
    if rule == "roboflow_stem":
        m = RF_NAME.match(Path(image_path).stem)
        return f"{source_id}:stem:{m.group('orig').lower()}" if m else ""
    if rule.startswith("video_timeblock"):
        # "video_timeblock:<seconds>": frames of the same video within the same time block share one group,
        # so near-identical consecutive frames can never be split across train/val/test
        block = float(rule.split(":", 1)[1]) if ":" in rule else 20.0
        m = VIDEO_FRAME.match(Path(image_path).stem)
        if not m:
            raise ValueError(f"{image_path}: name does not match the video-frame pattern")
        t = int(m.group("m")) * 60 + int(m.group("s")) + int(m.group("cs")) / 100
        return f"{source_id}:video{m.group('vid') or '1'}:block{int(t // block)}"
    if rule == "none":
        return ""
    raise ValueError(f"unknown group_rule {rule!r}")


def enumerate_samples(cfg):
    """Yield one dict per raw image, plus problems (orphans) as a separate list."""
    samples, problems = [], []
    for sid, s in cfg["sources"].items():
        for split, sp in s["splits"].items():
            pairs, no_label, orphans = pair_images_labels(sp["images"], sp["labels"])
            problems += [{"source": sid, "split": split, "file": str(p), "problem": "image_without_label"} for p in no_label]
            problems += [{"source": sid, "split": split, "file": str(p), "problem": "label_without_image"} for p in orphans]
            for img, lbl in pairs:
                samples.append({"sample_id": f"{sid}/{split}/{img.name}", "source": sid, "orig_split": split,
                                "image": str(img), "label": str(lbl),
                                "group_key": group_key(sid, s["group_rule"], img)})
    return samples, problems
