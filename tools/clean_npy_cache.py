"""Remove the Ultralytics disk cache (*.npy written by `cache=disk`) from the composed datasets. Dry-run by default.

    venv\\Scripts\\python -I tools\\clean_npy_cache.py            # dry run: counts and GB, deletes nothing
    venv\\Scripts\\python -I tools\\clean_npy_cache.py --delete   # deletes, and writes a log

A .npy file is removed only if ALL of these hold:
  - it is under road_hazards_*/images/<split>/ in this folder;
  - an image with the same stem (.jpg/.jpeg/.png/.bmp) sits next to it, so the cache is rebuildable;
  - it is NOT listed in that dataset's checksums.sha256 (so no dataset file is touched).
Images, labels, manifests, checksums, runs and weights are never touched. Ultralytics rebuilds the cache on the next
`cache=disk` training. Log: review/disk_cleanup_<date>.csv (path, bytes).
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--delete", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    total_n, total_b, rows = 0, 0, []
    for ds in sorted(root.glob("road_hazards_*")):
        if not (ds / "images").is_dir():
            continue
        listed = set()
        ck = ds / "checksums.sha256"
        if ck.exists():
            listed = {line.split()[-1].lstrip("*").replace("\\", "/") for line in ck.read_text(encoding="utf-8").splitlines() if line.strip()}
        n = b = skipped = 0
        for f in (ds / "images").rglob("*.npy"):
            rel = f.relative_to(ds).as_posix()
            if rel in listed or not any(f.with_suffix(e).exists() for e in IMG_EXT):
                skipped += 1
                continue
            sz = f.stat().st_size
            n, b = n + 1, b + sz
            rows.append((str(f.relative_to(root)), sz))
        total_n, total_b = total_n + n, total_b + b
        print(f"{ds.name:24s} {n:6d} cache files  {b / 1e9:6.1f} GB" + (f"  ({skipped} skipped)" if skipped else ""))
    print(f"{'TOTAL':24s} {total_n:6d} cache files  {total_b / 1e9:6.1f} GB")
    if not args.delete:
        print("dry run - nothing deleted. Add --delete to remove them.")
        return
    log = root / "review" / f"disk_cleanup_{datetime.now():%Y-%m-%d_%H%M}.csv"
    if log.exists():
        sys.exit(f"{log} exists - refusing to overwrite")
    with open(log, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "bytes"])
        for p, sz in rows:
            (root / p).unlink()
            w.writerow([p, sz])
    print(f"deleted {total_n} files, {total_b / 1e9:.1f} GB freed. Log: {log.relative_to(root)}")


if __name__ == "__main__":
    main()
