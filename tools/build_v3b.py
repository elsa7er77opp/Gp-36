"""Compose a training dataset version = frozen base (r2, all splits unchanged) + TRAIN splits of curated parts.

    python -I tools/build_v3b.py --out road_hazards_v3b_A --parts parts_r3/rsid parts_r3/bucko parts_r3/rdd_ji:800

Rules:
- val and test are the base's val and test, byte-identical (frozen r2 benchmark). Parts only add TRAIN images
  (rule: new sources go to train or to a separate external test, never into internal val/test).
- `part:N` takes a random subset (seed 0) of N train images of that part; the chosen list is in the manifest.
- Files are HARD-LINKED (same NTFS volume), not copied: no source file is ever modified, and the new folder
  is a complete dataset of its own (its own labels cache, manifest, checksums, strict verify).
- Built in <out>.building, strictly verified (gp36data.verify, near-dup check off as in r2), then renamed.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gp36data.manifest import sha256_file  # noqa: E402
from gp36data.verify import verify_dataset  # noqa: E402


def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="road_hazards_v3a_r2")
    ap.add_argument("--parts", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    base, out = Path(args.base), Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)

    base_rows = list(csv.DictReader(open(base / "manifest.csv", newline="", encoding="utf-8")))
    rows = []
    for r in base_rows:
        stem = Path(r["out_image"]).stem
        sp = r["split"]
        link(base / r["out_image"], tmp / r["out_image"])
        link(base / "labels" / sp / f"{stem}.txt", tmp / "labels" / sp / f"{stem}.txt")
        rows.append({**r, "part": "r2"})
    used = {}
    for spec in args.parts:
        pdir, _, cap = spec.partition(":")
        pdir = Path(pdir)
        prow = [r for r in csv.DictReader(open(pdir / "manifest.csv", newline="", encoding="utf-8")) if r["split"] == "train"]
        if cap:
            random.Random(0).shuffle(prow)
            prow = sorted(prow[:int(cap)], key=lambda r: r["out_image"])
        for r in prow:
            stem = Path(r["out_image"]).stem
            if (tmp / r["out_image"]).exists():
                sys.exit(f"name clash {r['out_image']}")
            link(pdir / r["out_image"], tmp / r["out_image"])
            link(pdir / "labels" / "train" / f"{stem}.txt", tmp / "labels" / "train" / f"{stem}.txt")
            rows.append(r)
        used[str(pdir)] = {"cap": int(cap) if cap else None, "train_images": len(prow),
                           "pothole_boxes": sum(int(r["n_pothole"]) for r in prow),
                           "speed_bump_boxes": sum(int(r["n_speed_bump"]) for r in prow),
                           "negatives": sum(int(r["n_pothole"]) + int(r["n_speed_bump"]) == 0 for r in prow),
                           "part_build_info_sha256": sha256_file(pdir / "build_info.json")}

    (tmp / "data.yaml").write_text("train: images/train\nval: images/val\ntest: images/test\nnames:\n  0: pothole\n  1: speed_bump\n",
                                   encoding="utf-8")
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    lines = []
    for p in sorted(tmp.rglob("*")):
        if p.is_file():
            rel = p.relative_to(tmp).as_posix()
            lines.append(f"{sha256_file(p)}  {rel}")
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fp = hashlib.sha256("\n".join(sorted(f"{r['split']},{r['out_image']},{r['out_sha256']}" for r in rows)).encode()).hexdigest()
    tr = [r for r in rows if r["split"] == "train"]
    (tmp / "build_info.json").write_text(json.dumps({
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"), "base": str(base),
        "base_fingerprint": json.load(open(base / "build_info.json"))["fingerprint_sha256"], "parts": used,
        "fingerprint_sha256": fp, "n_samples": len(rows),
        "train": {"images": len(tr), "pothole_boxes": sum(int(r["n_pothole"]) for r in tr),
                  "speed_bump_boxes": sum(int(r["n_speed_bump"]) for r in tr),
                  "negatives": sum(int(r["n_pothole"]) + int(r["n_speed_bump"]) == 0 for r in tr)},
        "val_test": "identical to base (frozen r2 benchmark)"}, indent=1), encoding="utf-8")
    rep = verify_dataset(tmp, check_near_dups=False, mode="strict")
    if rep["errors"]:
        print("\n".join(rep["errors"][:30]))
        sys.exit(f"verification FAILED; left in {tmp}")
    os.rename(tmp, out)
    print(json.dumps(json.load(open(out / "build_info.json")), indent=1))
    print(f"strict verify PASS ({len(rep['warnings'])} warnings)")


if __name__ == "__main__":
    main()
