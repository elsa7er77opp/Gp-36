"""Strict YOLO label parsing, validation and class mapping.

A label line is either a bounding box ``cls xc yc w h`` or a polygon ``cls x1 y1 x2 y2 x3 y3 ...``
(at least 3 points), all coordinates normalised to [0, 1]. Problems are reported as issues; nothing
is silently fixed. Only boxes that exceed the image edge by at most ``CLIP_TOL`` may be clipped, and
that is reported as a warning.
"""
import math
from dataclasses import dataclass

CLIP_TOL = 0.01  # normalised; ~1 % of the image side
EPS = 1e-6


@dataclass(frozen=True)
class Box:
    cls: int
    xc: float
    yc: float
    w: float
    h: float
    kind: str = "bbox"  # "bbox" or "poly" (converted to its bounding box)

    def xyxy(self):
        return self.xc - self.w / 2, self.yc - self.h / 2, self.xc + self.w / 2, self.yc + self.h / 2


@dataclass(frozen=True)
class Issue:
    line: int
    code: str
    severity: str  # "error" or "warning"
    detail: str = ""


def _box_from_xyxy(cls, x1, y1, x2, y2, kind):
    return Box(cls, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, kind)


def parse_label_text(text):
    """Parse label text. Returns (boxes, issues). Lines with errors produce no box."""
    boxes, issues, seen = [], [], set()
    for i, line in enumerate(text.splitlines(), start=1):
        tok = line.split()
        if not tok:
            continue
        try:
            vals = [float(t) for t in tok]
        except ValueError:
            issues.append(Issue(i, "NONNUMERIC", "error", line.strip()[:80]))
            continue
        if not all(math.isfinite(v) for v in vals):
            issues.append(Issue(i, "NONFINITE", "error"))
            continue
        c = vals[0]
        if c != int(c):
            issues.append(Issue(i, "NONINT_CLASS", "error", tok[0]))
            continue
        if c < 0:
            issues.append(Issue(i, "NEGATIVE_CLASS", "error", tok[0]))
            continue
        c = int(c)
        coords = vals[1:]
        if len(tok) == 5:
            xc, yc, w, h = coords
            if w <= EPS or h <= EPS:
                issues.append(Issue(i, "NONPOSITIVE_WH", "error", f"w={w} h={h}"))
                continue
            if not (0 <= xc <= 1 and 0 <= yc <= 1):
                issues.append(Issue(i, "CENTER_OUT_OF_RANGE", "error", f"xc={xc} yc={yc}"))
                continue
            box = Box(c, xc, yc, w, h, "bbox")
        elif len(tok) >= 7 and len(tok) % 2 == 1:
            xs, ys = coords[0::2], coords[1::2]
            if any(v < -CLIP_TOL or v > 1 + CLIP_TOL for v in xs + ys):
                issues.append(Issue(i, "POLY_OUT_OF_RANGE", "error"))
                continue
            box = _box_from_xyxy(c, min(xs), min(ys), max(xs), max(ys), "poly")
            if box.w <= EPS or box.h <= EPS:
                issues.append(Issue(i, "POLY_DEGENERATE", "error"))
                continue
        else:  # note: a 2-point polygon has 5 tokens and is indistinguishable from a bbox
            issues.append(Issue(i, "BAD_TOKEN_COUNT", "error", f"{len(tok)} tokens"))
            continue
        x1, y1, x2, y2 = box.xyxy()
        over = max(-x1, -y1, x2 - 1, y2 - 1)
        if over > CLIP_TOL:
            issues.append(Issue(i, "EXCEEDS_IMAGE", "error", f"by {over:.4f}"))
            continue
        if over > EPS:
            issues.append(Issue(i, "CLIPPED", "warning", f"by {over:.4f}"))
            box = _box_from_xyxy(c, max(x1, 0), max(y1, 0), min(x2, 1), min(y2, 1), box.kind)
        key = (box.cls, round(box.xc, 5), round(box.yc, 5), round(box.w, 5), round(box.h, 5))
        if key in seen:
            issues.append(Issue(i, "DUPLICATE_BOX", "warning"))
            continue
        seen.add(key)
        boxes.append(box)
    return boxes, issues


def parse_label_file(path):
    with open(path, encoding="utf-8") as f:
        return parse_label_text(f.read())


class ClassMappingError(Exception):
    pass


def map_classes(boxes, class_map, ignore=(), target_names=("pothole", "speed_bump")):
    """Map source class IDs to target class IDs by *name*.

    class_map: {source_id: target_name}. ``ignore`` lists source IDs that are deliberately excluded
    (they are counted and returned, never silently dropped). Any other unmapped ID raises.
    Returns (mapped_boxes, ignored_count_by_source_id).
    """
    name_to_id = {n: i for i, n in enumerate(target_names)}
    for src, name in class_map.items():
        if name not in name_to_id:
            raise ClassMappingError(f"source class {src} maps to unknown target {name!r}")
    out, ignored = [], {}
    for b in boxes:
        if b.cls in ignore:
            ignored[b.cls] = ignored.get(b.cls, 0) + 1
            continue
        if b.cls not in class_map:
            raise ClassMappingError(f"source class {b.cls} has no mapping and is not in ignore list")
        out.append(Box(name_to_id[class_map[b.cls]], b.xc, b.yc, b.w, b.h, b.kind))
    return out, ignored


def format_label(boxes):
    return "".join(f"{b.cls} {b.xc:.6f} {b.yc:.6f} {b.w:.6f} {b.h:.6f}\n" for b in boxes)


def has_errors(issues):
    return any(i.severity == "error" for i in issues)


def iou(a, b):
    ax1, ay1, ax2, ay2 = a.xyxy()
    bx1, by1, bx2, by2 = b.xyxy()
    iw, ih = max(0.0, min(ax2, bx2) - max(ax1, bx1)), max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union > 0 else 0.0


def compare_box_sets(a, b, same_iou=0.9, match_iou=0.5):
    """Compare two annotations of the same image.

    Returns "same" (same classes, every box matched with IoU >= same_iou), "minor" (every box
    matched with IoU >= match_iou) or "conflict" (different count/classes or unmatched boxes).
    Matching is greedy by IoU within each class.
    """
    if len(a) != len(b) or sorted(x.cls for x in a) != sorted(x.cls for x in b):
        return "conflict"
    pairs = sorted(((iou(x, y), i, j) for i, x in enumerate(a) for j, y in enumerate(b) if x.cls == y.cls), reverse=True)
    used_a, used_b, ious = set(), set(), []
    for v, i, j in pairs:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        ious.append(v)
    if len(ious) != len(a) or (ious and min(ious) < match_iou):
        return "conflict"
    return "same" if not ious or min(ious) >= same_iou else "minor"
