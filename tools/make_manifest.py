"""Write a SHA-256 manifest of a directory, or verify a directory against an existing manifest.

    python tools/make_manifest.py --root ../GP36_Dataset --out manifests/raw_GP36_Dataset.csv
    python tools/make_manifest.py --root road_hazards_v2 --out manifests/road_hazards_v2.csv --exclude .npy .cache
    python tools/make_manifest.py --root <dir> --verify manifests/<file>.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.manifest import build_manifest, compare_manifests, read_manifest, write_manifest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", help="manifest CSV to write (must not exist)")
    ap.add_argument("--verify", help="existing manifest CSV to check --root against")
    ap.add_argument("--exclude", nargs="*", default=[], help="file suffixes to skip, e.g. .npy .cache")
    args = ap.parse_args()
    rows = build_manifest(args.root, args.exclude)
    if args.verify:
        diff = compare_manifests(read_manifest(args.verify), rows)
        bad = sum(len(v) for v in diff.values())
        for k, v in diff.items():
            print(f"{k}: {len(v)} {v[:5]}")
        print("VERIFY", "PASS" if bad == 0 else "FAIL", f"({len(rows)} files)")
        sys.exit(1 if bad else 0)
    if not args.out:
        ap.error("--out or --verify is required")
    if Path(args.out).exists():
        sys.exit(f"refusing to overwrite existing manifest {args.out}")
    write_manifest(rows, args.out)
    print(f"{len(rows)} files, {sum(r['size'] for r in rows) / 1e9:.2f} GB -> {args.out}")


if __name__ == "__main__":
    main()
