"""Final integrity verification of a built YOLO dataset folder."""
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from .hashing import dhash, hamming_to_all, phash
from .io_utils import inspect_image, pair_images_labels, PairingError
from .labels import parse_label_file
from .manifest import sha256_file

SPLITS = ("train", "val", "test")


def verify_dataset(root, check_near_dups=True, dhash_max=4, phash_max=10):
    """Return {"errors": [...], "warnings": [...], "counts": {...}}. An empty error list means PASS."""
    root = Path(root)
    errors, warnings = [], []
    counts = {}
    try:
        data = yaml.safe_load((root / "data.yaml").read_text(encoding="utf-8"))
        names = data["names"]
        nc = len(names)
    except Exception as e:
        return {"errors": [f"data.yaml unreadable: {e}"], "warnings": [], "counts": {}}

    sha_split = defaultdict(set)
    hashes = []  # (split, file, dhash, phash)
    for split in SPLITS:
        img_dir, lbl_dir = root / "images" / split, root / "labels" / split
        if not img_dir.exists():
            continue
        try:
            pairs, no_label, orphans = pair_images_labels(img_dir, lbl_dir)
        except PairingError as e:
            errors.append(f"{split}: {e}")
            continue
        errors += [f"{split}: image without label {p.name}" for p in no_label]
        errors += [f"{split}: label without image {p.name}" for p in orphans]
        n_obj = defaultdict(int)
        for img, lbl in pairs:
            info = inspect_image(img)
            if not info["ok"]:
                errors.append(f"{split}: unreadable image {img.name}: {info['error']}")
                continue
            boxes, issues = parse_label_file(lbl)
            for i in issues:
                (errors if i.severity == "error" else warnings).append(f"{split}/{lbl.name}:{i.line} {i.code} {i.detail}")
            for b in boxes:
                if b.cls >= nc:
                    errors.append(f"{split}/{lbl.name}: class {b.cls} >= nc {nc}")
                n_obj[b.cls] += 1
            sha = sha256_file(img)
            if split in sha_split[sha]:
                errors.append(f"{split}: duplicate image content {img.name}")
            sha_split[sha].add(split)
            if check_near_dups:
                with Image.open(img) as im:
                    hashes.append((split, img.name, dhash(im), phash(im)))
        counts[split] = {"images": len(pairs), "objects": dict(n_obj)}

    for sha, splits in sha_split.items():
        if len(splits) > 1:
            errors.append(f"identical image in splits {sorted(splits)} (sha {sha[:12]})")

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

    ck = root / "checksums.sha256"
    if ck.exists():
        for line in ck.read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            p = root / rel
            if not p.exists():
                errors.append(f"checksum: missing file {rel}")
            elif sha256_file(p) != digest:
                errors.append(f"checksum: modified file {rel}")
    return {"errors": errors, "warnings": warnings, "counts": counts}
