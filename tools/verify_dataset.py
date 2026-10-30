"""Verify a built dataset folder (pairing, labels, class range, cross-split duplicates, checksums).

    python tools/verify_dataset.py road_hazards_v3_clean
Exit code 0 = PASS, 1 = FAIL.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.verify import verify_dataset  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--no-near-dups", action="store_true")
    args = ap.parse_args()
    rep = verify_dataset(args.root, check_near_dups=not args.no_near_dups)
    print(json.dumps(rep["counts"], indent=1))
    for e in rep["errors"][:100]:
        print("ERROR", e)
    print(f"{len(rep['errors'])} errors, {len(rep['warnings'])} warnings ->", "PASS" if not rep["errors"] else "FAIL")
    sys.exit(1 if rep["errors"] else 0)


if __name__ == "__main__":
    main()
