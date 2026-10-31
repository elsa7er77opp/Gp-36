"""Inspect or safely extract a downloaded dataset zip into a NEW folder.

    python -I tools/intake_zip.py list    <zip>
    python -I tools/intake_zip.py extract <zip> <new_dir>

Extraction refuses an existing target, rejects absolute paths / drive letters / '..' entries
(zip-slip), extracts into a temp folder and renames it when complete, and writes a SHA-256 manifest
of the zip and of every extracted file next to the data (``_intake.json``).
"""
import collections
import datetime
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def unsafe(name):
    n = name.replace("\\", "/")
    return n.startswith("/") or ":" in n or ".." in PurePosixPath(n).parts


def list_zip(zp):
    z = zipfile.ZipFile(zp)
    names = z.namelist()
    files = [n for n in names if not n.endswith("/")]
    print("entries", len(names), "files", len(files), "unsafe", sum(unsafe(n) for n in names),
          "uncompressed_MB", round(sum(i.file_size for i in z.infolist()) / 1e6, 1))
    print(dict(collections.Counter("/".join(n.split("/")[:2]) for n in files)))
    for n in files:
        if "/" not in n and n.endswith((".yaml", ".txt")):
            print("---", n)
            print(z.read(n).decode("utf-8", "replace")[:1200])


def extract(zp, out):
    zp, out = Path(zp), Path(out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    z = zipfile.ZipFile(zp)
    bad = [n for n in z.namelist() if unsafe(n)]
    if bad:
        sys.exit(f"unsafe entries in zip: {bad[:5]}")
    tmp = out.with_name(out.name + ".extracting")
    if tmp.exists():
        shutil.rmtree(tmp)  # leftover of our own interrupted extraction (name is specific to this tool)
    z.extractall(tmp)
    files = sorted(p for p in tmp.rglob("*") if p.is_file())
    info = {"zip": str(zp), "zip_sha256": sha256(zp), "zip_bytes": zp.stat().st_size,
            "extracted_at": datetime.datetime.now().isoformat(timespec="seconds"), "n_files": len(files),
            "files": {p.relative_to(tmp).as_posix(): sha256(p) for p in files}}
    (tmp / "_intake.json").write_text(json.dumps(info, indent=0), encoding="utf-8")
    os.rename(tmp, out)
    print(f"extracted {len(files)} files -> {out}")


if __name__ == "__main__":
    if sys.argv[1] == "list":
        list_zip(sys.argv[2])
    elif sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3])
    else:
        sys.exit("usage: list <zip> | extract <zip> <new_dir>")
