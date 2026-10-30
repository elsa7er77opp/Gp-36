"""SHA-256 manifests of directory trees, and comparison of two manifests."""
import csv
import hashlib
import os
from pathlib import Path

CHUNK = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def iter_files(root, exclude_suffixes=()):
    """Yield files under root in a deterministic order (sorted relative POSIX paths)."""
    root = Path(root)
    exclude = {s.lower() for s in exclude_suffixes}
    found = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in exclude:
                continue
            found.append(p)
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())


def build_manifest(root, exclude_suffixes=()):
    """Return a list of {path, size, sha256} rows with paths relative to root."""
    root = Path(root)
    return [
        {"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": sha256_file(p)}
        for p in iter_files(root, exclude_suffixes)
    ]


def write_manifest(rows, out_csv):
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_csv.with_name(out_csv.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "size", "sha256"])
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, out_csv)


def read_manifest(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return [{"path": r["path"], "size": int(r["size"]), "sha256": r["sha256"]} for r in csv.DictReader(f)]


def compare_manifests(a, b):
    """Return {'missing': [...], 'extra': [...], 'changed': [...]} of b relative to a."""
    A = {r["path"]: r["sha256"] for r in a}
    B = {r["path"]: r["sha256"] for r in b}
    return {
        "missing": sorted(set(A) - set(B)),
        "extra": sorted(set(B) - set(A)),
        "changed": sorted(p for p in set(A) & set(B) if A[p] != B[p]),
    }
