"""Final integrity verification of a built YOLO dataset folder.

Two modes (independent-audit fix 2026-10-30, issues 1 and 2):

* ``strict`` (default) - required for an integrity PASS. data.yaml must point at images/<split> for
  train/val/test; every split must have an images and a labels directory with at least one image;
  ``checksums.sha256`` and ``manifest.csv`` are required; every checksum record must be well formed,
  unique, inside the dataset root and match; every file in the folder must be covered by the checksum
  manifest (the only exceptions are listed in DERIVED_CACHE_RULES and are reported as warnings);
  manifest.csv must list exactly the images on disk, in the right split, with the right SHA-256.
* ``legacy`` - for historical datasets built before checksums/manifest existed. Missing checksum or
  manifest files and unlisted files become warnings, and the report says LEGACY so the result can
  never be mistaken for a strict PASS. Missing splits, malformed / duplicate / outside-root checksum
  records and hash mismatches are still errors in legacy mode.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath

import numpy as np
import yaml
from PIL import Image

from .hashing import dhash, hamming_to_all, phash
from .io_utils import IMG_EXT, inspect_image, pair_images_labels, PairingError
from .labels import parse_label_file
from .manifest import sha256_file

SPLITS = ("train", "val", "test")
MODES = ("strict", "legacy")
CHECKSUM_LINE = re.compile(r"^([0-9a-f]{64})  (\S.*)$")
# Files that may exist in a dataset without being in checksums.sha256:
#   - checksums.sha256 itself and build_info.json (written after the checksum list by build.py);
#   - Ultralytics training caches, which Ultralytics writes into the dataset folder during training:
#     images/<split>/<stem>.npy next to a listed image (cache=disk) and labels/<split>.cache.
NOT_CHECKSUMMED = {"checksums.sha256", "build_info.json"}


def _is_derived_cache(rel, listed):
    parts = PurePosixPath(rel).parts
    if len(parts) == 2 and parts[0] == "labels" and parts[1] in {f"{s}.cache" for s in SPLITS}:
        return True
    if len(parts) == 3 and parts[0] == "images" and parts[1] in SPLITS and rel.endswith(".npy"):
        stem = rel[:-4]
        return any(f"{stem}{e}" in listed for e in IMG_EXT)
    return False


def _inside(root, rel):
    """True when rel is a plain relative path that stays inside root (no absolute path, drive or '..')."""
    if rel.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", rel) or "\\" in rel:
        return False
    if any(part in ("..", "") for part in rel.split("/")):
        return False
    try:
        (root / rel).resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def verify_dataset(root, check_near_dups=True, dhash_max=4, phash_max=10, mode="strict", allow_unlisted=()):
    """Return {"mode", "errors", "warnings", "counts"}. An empty error list means PASS in that mode.

    allow_unlisted: extra top-level file names that may be absent from checksums.sha256 (used only by
    build.py for its own in-progress marker while it verifies the temporary folder).
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    strict = mode == "strict"
    root = Path(root)
    errors, warnings = [], []
    counts = {}
    soft = errors if strict else warnings  # checks that are errors in strict mode, warnings in legacy mode
    if not strict:
        warnings.append("LEGACY MODE: checksum/manifest completeness not enforced; this is not a strict integrity PASS")

    def result():
        return {"mode": mode, "errors": errors, "warnings": warnings, "counts": counts}

    if not root.is_dir():
        errors.append(f"dataset root {root} is not a directory")
        return result()
    try:
        data = yaml.safe_load((root / "data.yaml").read_text(encoding="utf-8"))
        names = data["names"]
        nc = len(names)
    except Exception as e:
        errors.append(f"data.yaml unreadable: {e}")
        return result()
    base = root / str(data.get("path") or ".")
    for split in SPLITS:
        if split not in data or not data[split]:
            soft.append(f"data.yaml: no '{split}' entry")
        elif not isinstance(data[split], str) or (base / data[split]).resolve() != (root / "images" / split).resolve():
            soft.append(f"data.yaml: '{split}' is {data[split]!r}, expected images/{split}")

    sha_of = {}  # relative posix path -> sha256 (each file hashed once)

    def sha(p):
        rel = p.relative_to(root).as_posix()
        if rel not in sha_of:
            sha_of[rel] = sha256_file(p)
        return sha_of[rel]

    sha_split = defaultdict(set)
    hashes = []  # (split, file, dhash, phash)
    disk_images = {}  # rel path -> split
    for split in SPLITS:
        img_dir, lbl_dir = root / "images" / split, root / "labels" / split
        missing = [str(d.relative_to(root).as_posix()) for d in (img_dir, lbl_dir) if not d.is_dir()]
        if missing:
            errors.append(f"{split}: required split directory missing: {', '.join(missing)}")
            continue
        try:
            pairs, no_label, orphans = pair_images_labels(img_dir, lbl_dir)
        except PairingError as e:
            errors.append(f"{split}: {e}")
            continue
        if not pairs and not no_label:
            errors.append(f"{split}: split has no images")
        errors += [f"{split}: image without label {p.name}" for p in no_label]
        errors += [f"{split}: label without image {p.name}" for p in orphans]
        n_obj = defaultdict(int)
        n_empty = 0
        for img, lbl in pairs:
            disk_images[img.relative_to(root).as_posix()] = split
            info = inspect_image(img)
            if not info["ok"]:
                errors.append(f"{split}: unreadable image {img.name}: {info['error']}")
                continue
            boxes, issues = parse_label_file(lbl)
            for i in issues:
                (errors if i.severity == "error" else warnings).append(f"{split}/{lbl.name}:{i.line} {i.code} {i.detail}")
            if not boxes and not issues:
                n_empty += 1  # explicitly supported: empty label file = verified negative image
            for b in boxes:
                if b.cls >= nc:
                    errors.append(f"{split}/{lbl.name}: class {b.cls} >= nc {nc}")
                n_obj[b.cls] += 1
            h = sha(img)
            if split in sha_split[h]:
                errors.append(f"{split}: duplicate image content {img.name}")
            sha_split[h].add(split)
            if check_near_dups:
                with Image.open(img) as im:
                    hashes.append((split, img.name, dhash(im), phash(im)))
        counts[split] = {"images": len(pairs), "objects": dict(n_obj), "empty_label_images": n_empty}

    for h, splits in sha_split.items():
        if len(splits) > 1:
            errors.append(f"identical image in splits {sorted(splits)} (sha {h[:12]})")

    if check_near_dups and hashes:
        D = np.array([h[2] for h in hashes], dtype=np.uint64)
        P = np.array([h[3] for h in hashes], dtype=np.uint64)
        for i in range(len(hashes) - 1):
            dd = hamming_to_all(int(D[i]), D[i + 1:])
            pd = hamming_to_all(int(P[i]), P[i + 1:])
            for j in np.nonzero((dd <= dhash_max) & (pd <= phash_max))[0]:
                a, b = hashes[i], hashes[i + 1 + int(j)]
                if a[0] != b[0]:
                    errors.append(f"near-duplicate across splits: {a[0]}/{a[1]} ~ {b[0]}/{b[1]}")

    # ---- checksum manifest ----
    ck = root / "checksums.sha256"
    listed = {}
    if not ck.is_file():
        soft.append("checksums.sha256 missing: file integrity NOT verified")
    else:
        try:
            lines = ck.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            lines = []
            errors.append(f"checksums.sha256 unreadable: {e}")
        for n, line in enumerate(lines, 1):
            if not line.strip():
                continue
            m = CHECKSUM_LINE.match(line)
            if not m:
                errors.append(f"checksum line {n}: malformed record {line[:80]!r}")
                continue
            digest, rel = m.groups()
            if not _inside(root, rel):
                errors.append(f"checksum line {n}: path outside dataset root or not a plain relative path: {rel}")
                continue
            if rel in listed:
                errors.append(f"checksum line {n}: duplicate record for {rel}")
                continue
            listed[rel] = digest
            p = root / rel
            if not p.is_file():
                errors.append(f"checksum: missing file {rel}")
            elif sha(p) != digest:
                errors.append(f"checksum: modified file {rel}")
        if not listed and not any("unreadable" in e for e in errors):
            errors.append("checksums.sha256 has no records")
        n_cache = 0
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if rel in listed or rel in NOT_CHECKSUMMED or rel in set(allow_unlisted):
                continue
            if _is_derived_cache(rel, listed):
                n_cache += 1
                continue
            soft.append(f"checksum: file not covered by checksums.sha256: {rel}")
        if n_cache:
            warnings.append(f"{n_cache} derived training-cache file(s) ignored (Ultralytics *.npy / labels/<split>.cache)")

    # ---- dataset manifest ----
    mf = root / "manifest.csv"
    if not mf.is_file():
        soft.append("manifest.csv missing: image provenance NOT verified")
    else:
        try:
            with open(mf, encoding="utf-8", newline="") as fh:  # closed before build.py renames the folder
                rows = list(csv.DictReader(fh))
        except Exception as e:
            rows = None
            errors.append(f"manifest.csv unreadable: {e}")
        if rows is not None:
            if rows and not {"split", "out_image"} <= set(rows[0]):
                errors.append("manifest.csv lacks the 'split'/'out_image' columns")
            else:
                seen = set()
                for k, r in enumerate(rows, 2):
                    rel, sp = r["out_image"], r["split"]
                    if rel in seen:
                        errors.append(f"manifest.csv line {k}: duplicate entry {rel}")
                        continue
                    seen.add(rel)
                    if rel not in disk_images:
                        errors.append(f"manifest.csv line {k}: listed image not in dataset: {rel}")
                    elif disk_images[rel] != sp or not rel.startswith(f"images/{sp}/"):
                        errors.append(f"manifest.csv line {k}: split {sp!r} does not match location {rel}")
                    elif r.get("out_sha256") and sha(root / rel) != r["out_sha256"]:
                        errors.append(f"manifest.csv line {k}: out_sha256 mismatch for {rel}")
                for rel in sorted(set(disk_images) - seen):
                    errors.append(f"manifest.csv: image on disk not listed: {rel}")
    return result()
