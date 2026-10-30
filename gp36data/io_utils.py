"""Image discovery, deterministic image<->label pairing and image integrity inspection.

Historical bug (CODE_AUDIT 1.1): Roboflow names such as ``103_jpg.rf.<hash>.jpg`` contain several
dots. Any code that rebuilds a name with ``Path.with_suffix`` on a stem treats ``.<hash>`` as the
extension and collapses different images onto one name. Here a stem is always the file name minus
its *final* suffix (``Path.stem``), and output names never derive from the original stem at all
(see ``output_name``).
"""
from pathlib import Path

from PIL import ExifTags, Image

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ORIENTATION_TAG = next(k for k, v in ExifTags.TAGS.items() if v == "Orientation")


class PairingError(Exception):
    pass


def list_images(img_dir):
    img_dir = Path(img_dir)
    return sorted((p for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT), key=lambda p: p.name)


def pair_images_labels(img_dir, lbl_dir):
    """Pair every image with ``<stem>.txt``.

    Returns (pairs, images_without_label, labels_without_image). ``pairs`` holds (image, label) for
    images that have a label file. Raises PairingError when two images map to the same label
    (e.g. ``a.jpg`` and ``a.PNG``), because the pairing would then be ambiguous.
    """
    img_dir, lbl_dir = Path(img_dir), Path(lbl_dir)
    by_stem = {}
    for p in list_images(img_dir):
        key = p.stem.lower()  # Windows file systems are case-insensitive
        if key in by_stem:
            raise PairingError(f"ambiguous label for {by_stem[key].name} and {p.name}")
        by_stem[key] = p
    labels = {p.stem.lower(): p for p in lbl_dir.glob("*.txt")} if lbl_dir.exists() else {}
    pairs = [(by_stem[k], labels[k]) for k in sorted(by_stem) if k in labels]
    missing_label = [by_stem[k] for k in sorted(by_stem) if k not in labels]
    orphan_labels = [labels[k] for k in sorted(labels) if k not in by_stem]
    return pairs, missing_label, orphan_labels


def inspect_image(path):
    """Fully decode an image and report its real format, size and EXIF orientation.

    Returns a dict with ``ok`` False and ``error`` set when the file cannot be decoded completely
    (corrupt or truncated). The extension is compared with the real format.
    """
    path = Path(path)
    info = {"ok": False, "error": "", "format": "", "width": 0, "height": 0, "mode": "", "exif_orientation": 1,
            "ext_matches_format": False}
    try:
        with Image.open(path) as im:
            info["format"] = im.format or ""
            try:
                info["exif_orientation"] = int(im.getexif().get(ORIENTATION_TAG, 1))
            except Exception:  # malformed EXIF is reported, not fatal
                info["exif_orientation"] = -1
            im.load()  # raises on truncated data
            info["width"], info["height"] = im.size
            info["mode"] = im.mode
        info["ok"] = info["width"] > 0 and info["height"] > 0
        if not info["ok"]:
            info["error"] = "zero-size image"
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    expected = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".bmp": "BMP", ".webp": "WEBP"}
    info["ext_matches_format"] = expected.get(path.suffix.lower()) == info["format"]
    return info


def output_name(source, sha256):
    """Collision-free, dot-free output stem: ``<source>__<first 16 hex of sha256>``.

    Two outputs can only share a name if they are byte-identical, which the builder rejects as a
    duplicate. The original file name is preserved in the dataset manifest instead.
    """
    if not source.replace("_", "").isalnum():
        raise ValueError(f"source id must be alphanumeric/underscore: {source!r}")
    return f"{source}__{sha256[:16]}"
