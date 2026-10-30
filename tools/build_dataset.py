"""Build a dataset version from a reviewed split manifest (Phase 1e; not run in Phase 1c).

    python tools/build_dataset.py --split-manifest <csv> --out road_hazards_v3_clean --max-side 1920

The split manifest has one row per APPROVED sample with columns:
    sample_id, source, split, image, label, negative (0/1), group_id
    optional: allow_ignored_only (0/1), rotate_cw (0/90/180/270; pixels only, owner-approved)
`label` may point to a reviewed/corrected label file instead of the raw one. Class maps come from
configs/sources.yaml. The build is atomic and refuses to overwrite an existing version.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.build import BuildError, build_dataset  # noqa: E402
from gp36data.manifest import sha256_file  # noqa: E402
from gp36data.sources import load_sources  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/sources.yaml")
    ap.add_argument("--split-manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-side", type=int, default=None)
    ap.add_argument("--version", default="")
    args = ap.parse_args()
    cfg = load_sources(args.config)
    records = []
    with open(args.split_manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = cfg["sources"][row["source"]]
            records.append({"sample_id": row["sample_id"], "source": row["source"], "split": row["split"],
                            "image": row["image"], "label": row.get("label") or None,
                            "negative": row.get("negative", "0") == "1", "group_id": row.get("group_id", ""),
                            "class_map": src["class_map"], "ignore": src["ignore"],
                            "allow_ignored_only": row.get("allow_ignored_only", "0") == "1",
                            "rotate_cw": int(row.get("rotate_cw") or 0)})
    try:
        report = build_dataset(records, args.out, cfg["target_names"], max_side=args.max_side,
                               info={"version": args.version, "split_manifest": args.split_manifest,
                                     "split_manifest_sha256": sha256_file(args.split_manifest),
                                     "sources_config_sha256": sha256_file(args.config)})
    except BuildError as e:
        print("BUILD FAILED - nothing was written to", args.out)
        for p in e.problems[:50]:
            print("  ", p)
        sys.exit(1)
    print(json.dumps(report["counts"], indent=1), "\nwarnings:", len(report["warnings"]),
          "\nfingerprint:", report["fingerprint_sha256"], "\nBUILD PASS ->", args.out)


if __name__ == "__main__":
    main()
