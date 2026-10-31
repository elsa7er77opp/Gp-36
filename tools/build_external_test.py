"""Build a separate EXTERNAL test benchmark (never part of the internal train/val/test).

    python -I tools/build_external_test.py --src <roboflow export> --splits valid test \
        --class-map 0:speed_bump --out external_tests/bd_speedbreaker_v2_orig87

Images and labels are copied into <out>/images/test and <out>/labels/test with content-addressed
names. Classes are mapped by NAME to the hazard ontology (pothole=0, speed_bump=1); an unmapped
source class is an error. data.yaml points both val and test at images/test so `yolo val split=test`
works. A manifest.csv (original path + SHA-256) and checksums.sha256 are written, and the build
refuses to run if any image is a near-duplicate (dihedral dHash<=4 and pHash<=10) or exact copy of an
image in the internal dataset given by --internal.
"""
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gp36data.hashing import dhash, phash  # noqa: E402
from gp36data.io_utils import inspect_image, pair_images_labels  # noqa: E402
from gp36data.labels import format_label, has_errors, map_classes, parse_label_file  # noqa: E402
from gp36data.manifest import sha256_file  # noqa: E402
from new_data_forensics import DIHEDRAL, load_small  # noqa: E402

TARGET = ("pothole", "speed_bump")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--splits", nargs="+", required=True)
    ap.add_argument("--class-map", nargs="+", required=True, help="src_id:target_name ...")
    ap.add_argument("--out", required=True)
    ap.add_argument("--internal", default="road_hazards_v3a_r2")
    args = ap.parse_args()
    out, src = Path(args.out), Path(args.src)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    cmap = {int(k): v for k, v in (x.split(":") for x in args.class_map)}

    items, problems = [], []
    for sp in args.splits:
        pairs, nl, ol = pair_images_labels(src / sp / "images", src / sp / "labels")
        problems += [f"{sp}: image without label {p.name}" for p in nl] + [f"{sp}: label without image {p.name}" for p in ol]
        for img, lbl in pairs:
            info = inspect_image(img)
            boxes, issues = parse_label_file(lbl)
            if not info["ok"] or has_errors(issues):
                problems.append(f"{sp}/{img.name}: {info['error'] or [i.code for i in issues]}")
                continue
            mapped, _ = map_classes(boxes, cmap, (), TARGET)
            items.append({"split": sp, "img": img, "lbl": lbl, "sha": sha256_file(img), "boxes": mapped})
    if problems:
        sys.exit("problems:\n" + "\n".join(problems[:30]))
    shas = [i["sha"] for i in items]
    if len(set(shas)) != len(shas):
        sys.exit("duplicate image content inside the external set")

    # leakage guard against the internal dataset
    internal = Path(args.internal)
    refs = []
    with open(internal / "manifest.csv", newline="", encoding="utf-8") as f:
        for m in csv.DictReader(f):
            im = load_small(internal / m["out_image"])
            refs.append((m["split"], m["sample_id"], m["out_sha256"], m["orig_sha256"], dhash(im), phash(im)))
    RD = np.array([r[4] for r in refs], dtype=np.uint64)
    RP = np.array([r[5] for r in refs], dtype=np.uint64)
    ref_sha = {r[2] for r in refs} | {r[3] for r in refs}
    hits = []
    for it in items:
        if it["sha"] in ref_sha:
            hits.append((it["img"].name, "exact"))
            continue
        with Image.open(it["img"]) as im:
            im = im.convert("RGB")
            d8 = np.array([dhash(im if t is None else im.transpose(t)) for t in DIHEDRAL], dtype=np.uint64)
            ph = phash(im)
        dd = np.min(np.stack([np.bitwise_count(np.bitwise_xor(RD, v)) for v in d8]), axis=0)
        pp = np.bitwise_count(np.bitwise_xor(RP, np.uint64(ph)))
        j = np.nonzero((dd <= 4) & (pp <= 10))[0]
        if len(j):
            hits.append((it["img"].name, [refs[k][1] for k in j[:3]]))
        it["min_dh_internal"] = int(dd.min())
    if hits:
        sys.exit(f"near/exact duplicates of {internal}: {hits[:10]}")

    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "images" / "test").mkdir(parents=True)
    (tmp / "labels" / "test").mkdir(parents=True)
    rows, lines = [], []
    for it in sorted(items, key=lambda x: x["sha"]):
        stem = f"ext__{it['sha'][:16]}"
        dst = tmp / "images" / "test" / f"{stem}{it['img'].suffix.lower()}"
        shutil.copyfile(it["img"], dst)
        (tmp / "labels" / "test" / f"{stem}.txt").write_text(format_label(it["boxes"]), encoding="utf-8")
        rows.append({"orig_split": it["split"], "orig_image": str(it["img"]), "orig_label": str(it["lbl"]),
                     "sha256": it["sha"], "out_image": dst.relative_to(tmp).as_posix(),
                     "n_pothole": sum(b.cls == 0 for b in it["boxes"]), "n_speed_bump": sum(b.cls == 1 for b in it["boxes"]),
                     "min_dhash_to_internal": it["min_dh_internal"]})
    # 'train' only satisfies Ultralytics' data-YAML check; an external test is never trained on
    (tmp / "data.yaml").write_text("train: images/test\nval: images/test\ntest: images/test\nnames:\n  0: pothole\n  1: speed_bump\n", encoding="utf-8")
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for p in sorted(tmp.rglob("*")):
        if p.is_file():
            lines.append(f"{sha256_file(p)}  {p.relative_to(tmp).as_posix()}")
    (tmp / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp / "build_info.json").write_text(json.dumps({
        "kind": "external_test", "src": str(src), "splits": args.splits, "class_map": cmap, "n_images": len(rows),
        "n_speed_bump": sum(r["n_speed_bump"] for r in rows), "n_pothole": sum(r["n_pothole"] for r in rows),
        "leakage_guard": f"0 exact / 0 near (dihedral dHash<=4 & pHash<=10) vs {internal} ({len(refs)} images)",
        "min_dhash_to_internal_overall": min(r["min_dhash_to_internal"] for r in rows)}, indent=1), encoding="utf-8")
    os.rename(tmp, out)
    print(f"{len(rows)} images -> {out}")


if __name__ == "__main__":
    main()
