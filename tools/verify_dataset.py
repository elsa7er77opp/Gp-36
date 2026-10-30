"""Verify a built dataset folder (pairing, labels, class range, cross-split duplicates, checksums).

    python tools/verify_dataset.py road_hazards_v3_clean            # strict (default)
    python tools/verify_dataset.py old_dataset --legacy              # historical datasets only
Exit code 0 = PASS, 1 = FAIL. Strict mode requires checksums.sha256 and manifest.csv; legacy mode
is printed as "LEGACY PASS" so it is never mistaken for a strict integrity PASS.
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
    ap.add_argument("--legacy", action="store_true",
                    help="historical datasets without checksums/manifest; result is labelled LEGACY")
    args = ap.parse_args()
    mode = "legacy" if args.legacy else "strict"
    rep = verify_dataset(args.root, check_near_dups=not args.no_near_dups, mode=mode)
    print(json.dumps(rep["counts"], indent=1))
    for e in rep["errors"][:100]:
        print("ERROR", e)
    for w in rep["warnings"][:20]:
        print("WARN ", w)
    verdict = "PASS" if not rep["errors"] else "FAIL"
    if mode == "legacy":
        verdict = f"LEGACY {verdict} (not a strict integrity result)"
    near = "" if not args.no_near_dups else " [near-duplicate check SKIPPED]"
    print(f"mode={mode}: {len(rep['errors'])} errors, {len(rep['warnings'])} warnings -> {verdict}{near}")
    sys.exit(1 if rep["errors"] else 0)


if __name__ == "__main__":
    main()
