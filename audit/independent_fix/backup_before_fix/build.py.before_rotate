"""Atomic, non-destructive dataset builder.

The builder
  1. validates every record first (readable image, EXIF orientation, label syntax, class mapping,
     no duplicate content) and refuses to write anything if one record fails;
  2. writes into a hidden temporary folder next to the target;
  3. verifies the temporary folder with verify.verify_dataset;
  4. renames it to the target only when verification passes.
It never deletes or overwrites an existing dataset version, and never modifies its inputs.
"""
import csv
import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path

import yaml
from PIL import Image

from . import __version__
from .io_utils import inspect_image, output_name
from .labels import format_label, has_errors, map_classes, parse_label_file
from .manifest import iter_files, sha256_file
from .io_utils import IMG_EXT
from .verify import verify_dataset

MARKER = ".gp36_build_in_progress"
MARKER_OWNER = "gp36data.build"
_TOP_LEVEL = {MARKER, "images", "labels", "data.yaml", "manifest.csv", "checksums.sha256", "build_info.json"}
_SPLITS = ("train", "val", "test")


def _write_marker(tmp, target_name):
    (tmp / MARKER).write_text(json.dumps({"owner": MARKER_OWNER, "target": target_name,
                                          "created": datetime.datetime.now().isoformat()}), encoding="utf-8")


def stale_temp_problems(tmp, target_name):
    """Return the reasons why ``tmp`` may NOT be deleted (empty list = provably our own stale build folder).

    A leftover temp folder is deleted only when ALL of these hold (independent-audit fix, issue 4):
    it is a real directory (not a symlink); its marker is a JSON ownership record written by this builder
    for this same target; and it contains nothing but the builder's own layout (images/<split>/*.<img>,
    labels/<split>/*.txt and the builder's top-level files), with no symlinks anywhere. Anything else is
    treated as possible user data and the build refuses instead of guessing.
    """
    problems = []
    if tmp.is_symlink() or not tmp.is_dir():
        return [f"{tmp} is not a plain directory"]
    try:
        m = json.loads((tmp / MARKER).read_text(encoding="utf-8"))
        if m.get("owner") != MARKER_OWNER or m.get("target") != target_name:
            problems.append(f"marker does not prove ownership for target {target_name!r}: {m}")
    except FileNotFoundError:
        return [f"{tmp} has no builder marker"]
    except Exception as e:
        problems.append(f"marker is not a valid ownership record ({e})")
    for p in sorted(tmp.rglob("*")):
        rel = p.relative_to(tmp).parts
        if p.is_symlink():
            problems.append(f"symlink inside temp folder: {p.relative_to(tmp).as_posix()}")
        elif len(rel) == 1:
            if rel[0] not in _TOP_LEVEL or (rel[0] in ("images", "labels")) != p.is_dir():
                problems.append(f"unexpected entry: {rel[0]}")
        elif len(rel) == 2:
            if rel[0] not in ("images", "labels") or rel[1] not in _SPLITS or not p.is_dir():
                problems.append(f"unexpected entry: {'/'.join(rel)}")
        elif len(rel) == 3 and rel[0] in ("images", "labels") and p.is_file():
            ok = p.suffix.lower() in IMG_EXT if rel[0] == "images" else p.suffix.lower() == ".txt"
            if not ok:
                problems.append(f"unexpected file: {'/'.join(rel)}")
        else:
            problems.append(f"unexpected entry: {'/'.join(rel)}")
    return problems


class BuildError(Exception):
    def __init__(self, problems):
        self.problems = problems if isinstance(problems, list) else [problems]
        super().__init__(f"{len(self.problems)} problem(s); first: {self.problems[0]}")


def _prepare(records, target_names):
    """Validate all records. Returns a list of prepared items or raises BuildError with every problem."""
    problems, items, seen = [], [], {}
    ids = set()
    for r in records:
        sid = r["sample_id"]
        if sid in ids:
            problems.append(f"{sid}: duplicate sample_id")
            continue
        ids.add(sid)
        img = Path(r["image"])
        info = inspect_image(img)
        if not info["ok"]:
            problems.append(f"{sid}: unreadable image ({info['error']})")
            continue
        if info["exif_orientation"] not in (1,):
            problems.append(f"{sid}: EXIF orientation {info['exif_orientation']} needs explicit handling")
            continue
        sha = sha256_file(img)
        if sha in seen:
            problems.append(f"{sid}: same content as {seen[sha]} (deduplicate first)")
            continue
        seen[sha] = sid
        if r.get("label"):
            boxes, issues = parse_label_file(r["label"])
            if has_errors(issues):
                problems.append(f"{sid}: label errors {[(i.line, i.code) for i in issues if i.severity == 'error']}")
                continue
        elif r.get("negative"):
            boxes, issues = [], []
        else:
            problems.append(f"{sid}: no label file and not marked as a verified negative")
            continue
        try:
            mapped, ignored = map_classes(boxes, r["class_map"], r.get("ignore", ()), target_names)
        except Exception as e:
            problems.append(f"{sid}: {e}")
            continue
        if ignored and not mapped and not r.get("allow_ignored_only"):
            # e.g. an RDD2022 image with cracks only: it is NOT a clean negative (the cracks are still there)
            problems.append(f"{sid}: only ignored-class objects {ignored}; not a verified negative")
            continue
        items.append({**r, "sha256": sha, "info": info, "boxes": mapped, "ignored": ignored,
                      "warnings": [f"{i.line}:{i.code}" for i in issues if i.severity == "warning"]})
    if problems:
        raise BuildError(problems)
    return items


def _write_image(item, dst_stem, max_side, quality):
    src, info = Path(item["image"]), item["info"]
    w, h = info["width"], info["height"]
    dst = dst_stem.with_name(dst_stem.name + ".jpg")
    if info["format"] == "JPEG" and (max_side is None or max(w, h) <= max_side):
        shutil.copyfile(src, dst)  # keep original bytes
        return dst, w, h
    with Image.open(src) as im:
        im = im.convert("RGB")
        if max_side is not None and max(w, h) > max_side:
            s = max_side / max(w, h)
            im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
        im.save(dst, "JPEG", quality=quality)
        return dst, im.width, im.height


def build_dataset(records, out_dir, target_names=("pothole", "speed_bump"), max_side=None, jpeg_quality=95,
                  info=None, check_near_dups=True):
    """Build a YOLO dataset at out_dir from records.

    record keys: sample_id, source, split (train/val/test), image, label (path) or negative=True,
    class_map {src_id: target_name}, optional ignore [src_ids], optional orig fields kept in manifest.
    Returns the verification report.
    """
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise BuildError(f"target {out_dir} already exists; dataset versions are never overwritten")
    tmp = out_dir.parent / f".{out_dir.name}.building"
    if tmp.exists() or tmp.is_symlink():
        problems = stale_temp_problems(tmp, out_dir.name)
        if problems:
            raise BuildError([f"{tmp} exists and cannot be proven to be a disposable builder temp folder; "
                              f"nothing was deleted. Inspect and remove it manually."] + problems)
        shutil.rmtree(tmp)  # proven: our own leftover of an interrupted build of this same target
    for r in records:
        if r["split"] not in ("train", "val", "test"):
            raise BuildError(f"{r['sample_id']}: unknown split {r['split']!r}")

    items = _prepare(records, target_names)

    tmp.mkdir(parents=True)
    _write_marker(tmp, out_dir.name)
    for s in ("train", "val", "test"):
        (tmp / "images" / s).mkdir(parents=True)
        (tmp / "labels" / s).mkdir(parents=True)
    rows = []
    for it in sorted(items, key=lambda x: x["sample_id"]):
        stem = output_name(it["source"], it["sha256"])
        dst, w, h = _write_image(it, tmp / "images" / it["split"] / stem, max_side, jpeg_quality)
        (tmp / "labels" / it["split"] / f"{stem}.txt").write_text(format_label(it["boxes"]), encoding="utf-8")
        per_class = [sum(1 for b in it["boxes"] if b.cls == k) for k in range(len(target_names))]
        rows.append({"sample_id": it["sample_id"], "source": it["source"], "split": it["split"],
                     "orig_image": str(it["image"]), "orig_label": str(it.get("label") or ""),
                     "orig_sha256": it["sha256"], "out_image": dst.relative_to(tmp).as_posix(),
                     "out_sha256": sha256_file(dst), "out_w": w, "out_h": h,
                     **{f"n_{n}": k for n, k in zip(target_names, per_class)},
                     "ignored": json.dumps(it["ignored"]), "label_warnings": ";".join(it["warnings"]),
                     "group_id": it.get("group_id", "")})

    (tmp / "data.yaml").write_text(yaml.safe_dump(
        {"train": "images/train", "val": "images/val", "test": "images/test",
         "names": {i: n for i, n in enumerate(target_names)}}, sort_keys=False), encoding="utf-8")
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["sample_id"])
        w.writeheader()
        w.writerows(rows)
    files = [p for p in iter_files(tmp) if p.name not in (MARKER, "checksums.sha256", "build_info.json")]
    lines = [f"{sha256_file(p)}  {p.relative_to(tmp).as_posix()}" for p in files]
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fingerprint = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    (tmp / "build_info.json").write_text(json.dumps({
        "gp36data_version": __version__, "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "fingerprint_sha256": fingerprint, "n_samples": len(rows), "max_side": max_side,
        "jpeg_quality": jpeg_quality, "target_names": list(target_names), **(info or {})}, indent=1), encoding="utf-8")

    report = verify_dataset(tmp, check_near_dups=check_near_dups, mode="strict", allow_unlisted=(MARKER,))
    if report["errors"]:
        raise BuildError(["verification failed"] + report["errors"])
    if out_dir.exists() or out_dir.is_symlink():  # appeared while we were building: never replace it
        raise BuildError(f"target {out_dir} appeared during the build; it was not touched. Built copy left in {tmp}")
    (tmp / MARKER).unlink()
    os.rename(tmp, out_dir)
    report["fingerprint_sha256"] = fingerprint
    return report
