"""Pascal VOC (XML) -> YOLO label conversion, strict and non-destructive.

Used for RDD2022 (Road Damage Dataset). Object names are mapped to *source* class IDs by an
explicit ``names`` list (e.g. ["D00", "D10", "D20", "D40"]); the project ontology mapping
(e.g. D40 -> pothole, cracks -> ignore) is done later by configs/sources.yaml, never here.

Rules
* An object name that is not in ``names`` is an error (never silently dropped or renamed).
* Coordinates are VOC pixel corners. Normalised: x / width, y / height.
* The XML <size> must be positive. When the real image size is given it must match the XML.
* Boxes may exceed the image by at most CLIP_TOL (normalised) and are then clipped with a warning;
  more than that, or xmin >= xmax / ymin >= ymax, is an error.
* A file with any error yields no label (the caller must not write a partial label).
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .labels import CLIP_TOL, EPS, Box, Issue


@dataclass
class VocResult:
    filename: str = ""
    width: int = 0
    height: int = 0
    boxes: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)  # name -> count (valid boxes only)

    @property
    def ok(self):
        return not any(i.severity == "error" for i in self.issues)


def _num(el, tag):
    t = el.find(tag)
    if t is None or t.text is None or not t.text.strip():
        raise ValueError(f"missing <{tag}>")
    return float(t.text.strip())


def parse_voc(xml_text, names, image_size=None):
    """Parse one VOC annotation. ``names``: ordered list of accepted object names (index = class id)."""
    res = VocResult()
    name_to_id = {n: i for i, n in enumerate(names)}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        res.issues.append(Issue(0, "XML_PARSE", "error", str(e)[:80]))
        return res
    res.filename = (root.findtext("filename") or "").strip()
    size = root.find("size")
    try:
        if size is None:
            raise ValueError("missing <size>")
        w, h = int(_num(size, "width")), int(_num(size, "height"))
        if w <= 0 or h <= 0:
            raise ValueError(f"size {w}x{h}")
    except ValueError as e:
        res.issues.append(Issue(0, "BAD_SIZE", "error", str(e)))
        return res
    if image_size is not None and tuple(image_size) != (w, h):
        res.issues.append(Issue(0, "SIZE_MISMATCH", "error", f"xml {w}x{h} vs image {image_size[0]}x{image_size[1]}"))
        return res
    res.width, res.height = w, h
    for k, obj in enumerate(root.findall("object"), start=1):
        name = (obj.findtext("name") or "").strip()
        if name not in name_to_id:
            res.issues.append(Issue(k, "UNKNOWN_NAME", "error", repr(name)))
            continue
        bb = obj.find("bndbox")
        try:
            if bb is None:
                raise ValueError("missing <bndbox>")
            x1, y1, x2, y2 = (_num(bb, t) for t in ("xmin", "ymin", "xmax", "ymax"))
        except ValueError as e:
            res.issues.append(Issue(k, "BAD_BNDBOX", "error", str(e)))
            continue
        if x2 - x1 <= EPS or y2 - y1 <= EPS:
            res.issues.append(Issue(k, "NONPOSITIVE_WH", "error", f"{x1},{y1},{x2},{y2}"))
            continue
        nx1, ny1, nx2, ny2 = x1 / w, y1 / h, x2 / w, y2 / h
        over = max(-nx1, -ny1, nx2 - 1, ny2 - 1)
        if over > CLIP_TOL:
            res.issues.append(Issue(k, "EXCEEDS_IMAGE", "error", f"by {over:.4f}"))
            continue
        if over > EPS:
            res.issues.append(Issue(k, "CLIPPED", "warning", f"by {over:.4f}"))
            nx1, ny1, nx2, ny2 = max(nx1, 0.0), max(ny1, 0.0), min(nx2, 1.0), min(ny2, 1.0)
        res.boxes.append(Box(name_to_id[name], (nx1 + nx2) / 2, (ny1 + ny2) / 2, nx2 - nx1, ny2 - ny1, "bbox"))
        res.counts[name] = res.counts.get(name, 0) + 1
    return res


def scan_names(xml_texts):
    """Count every object name across files (to discover the real vocabulary before choosing ``names``)."""
    out = {}
    for t in xml_texts:
        try:
            root = ET.fromstring(t)
        except ET.ParseError:
            out["<XML_PARSE_ERROR>"] = out.get("<XML_PARSE_ERROR>", 0) + 1
            continue
        for obj in root.findall("object"):
            n = (obj.findtext("name") or "").strip()
            out[n] = out.get(n, 0) + 1
    return out
