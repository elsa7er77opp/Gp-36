"""Vet one candidate YOLO source before any items CSV is written (steps 1-5 of the r3 data gate, automated part).

    python -I tools/vet_source.py --name <short> --root <unzipped source dir> --out review/new_data_r3/vet/<short> \
        [--sheet <outside-git>/sheet_<short>.jpg] [--hashes review/new_data_r3/protected_hashes.npz]

It finds every image under --root and its YOLO label (same stem, in a sibling `labels` folder or next to it),
then writes <out>/vet.json and <out>/vet.md (no pixels) with:
  - images, labelled images, raw class-id counts, data.yaml class names if present, licence lines of README files;
  - Roboflow augmentation: images per base name after stripping `_jpg.rf.<hash>` (copies > 1 = augmented export);
  - within-source near-duplicate clusters (dihedral dHash <= 4 and pHash <= 10): originals ~= clusters;
  - file-name families already used or known re-uploads (tools/leak_check.py KNOWN_FAMILIES);
  - leak check vs every protected val/test/external image (hash-only, review/new_data_r3/protected_hashes.npz);
  - verdict hints: REJECT if any eval hit falls outside an excludable family, AUGMENTED if most bases have copies.
The contact sheet (20 random images with raw ids) is written to --sheet, which must be OUTSIDE git.
The human visual check (D1-D6) is still required; this tool only does the mechanical part.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leak_check import check_image, family, images_under, load_protected  # noqa: E402

RF = re.compile(r"(_(jpe?g|png|JPE?G|PNG))?\.rf\.[0-9a-f]{20,32}$")


def base_name(stem):
    return RF.sub("", stem)


def label_for(img):
    cands = [img.with_suffix(".txt")]
    parts = list(img.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            cands.insert(0, Path(*parts[:i], "labels", *parts[i + 1:]).with_suffix(".txt"))
            break
    for c in cands:
        if c.exists():
            return c
    return None


def clusters(rows):
    """Union-find over within-source near-duplicates; returns cluster id per row index."""
    D0 = np.array([r["_d8"][0] for r in rows], dtype=np.uint64)
    P = np.array([r["_ph"] for r in rows], dtype=np.uint64)
    par = list(range(len(rows)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, r in enumerate(rows):
        dd = np.min(np.bitwise_count(np.asarray(r["_d8"], dtype=np.uint64)[:, None] ^ D0[None, :]), axis=0)
        pp = np.bitwise_count(np.uint64(r["_ph"]) ^ P)
        for j in np.nonzero((dd <= 4) & (pp <= 10))[0]:
            if j != i:
                par[f(i)] = f(int(j))
    return [f(i) for i in range(len(rows))]


def hashes(path):
    from PIL import Image

    from gp36data.hashing import dhash, phash
    from new_data_forensics import DIHEDRAL
    with Image.open(path) as im:
        im.draft("RGB", (512, 512))
        im = im.convert("RGB")
        return [int(dhash(im if t is None else im.transpose(t))) for t in DIHEDRAL], int(phash(im))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--hashes", default=str(Path(__file__).resolve().parents[1] / "review/new_data_r3/protected_hashes.npz"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    root = Path(a.root)
    RD, RP, ids, shas = load_protected(a.hashes)
    rows = []
    for img in images_under(root):
        lbl = label_for(img)
        cls = []
        if lbl:
            cls = [ln.split()[0] for ln in lbl.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        lk = check_image(img, RD, RP, ids, shas)
        d8, ph = hashes(img)
        rows.append({"image": str(img.relative_to(root)), "label": bool(lbl), "cls": cls, "base": base_name(img.stem),
                     "family": family(img.name), "hit": lk["hit"], "closest": lk["closest_id"], "_d8": d8, "_ph": ph})
    if not rows:
        sys.exit(f"no images under {root}")
    cid = clusters(rows)
    per_base = Counter(r["base"] for r in rows)
    per_cl = Counter(cid)
    names = {}
    for y in root.rglob("data.yaml"):
        try:
            import yaml
            names[str(y.relative_to(root))] = yaml.safe_load(y.read_text(encoding="utf-8")).get("names")
        except Exception as e:  # noqa: BLE001
            names[str(y.relative_to(root))] = f"unreadable: {e}"
    lic = sorted({ln.strip() for p in root.rglob("README*") if p.is_file()
                  for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if "icen" in ln})[:10]
    hits = [r for r in rows if r["hit"]]
    ev = [r for r in hits if not r["closest"].startswith("train:")]
    rep = {"name": a.name, "root": str(root), "images": len(rows), "labelled": sum(r["label"] for r in rows),
           "class_id_counts": dict(Counter(c for r in rows for c in r["cls"])), "data_yaml_names": names,
           "licence_lines": lic,
           "roboflow_bases": len(per_base), "images_per_base": dict(Counter(per_base.values())),
           "near_dup_clusters": len(per_cl), "images_per_cluster": dict(Counter(per_cl.values())),
           "known_families": dict(Counter(r["family"] for r in rows if r["family"])),
           "leak_hits_eval": len(ev), "leak_hits_r2_train": len(hits) - len(ev),
           "leak_eval_by_protected_set": dict(Counter(r["closest"].split("/")[0] for r in ev)),
           "leak_eval_by_family": dict(Counter(r["family"] or base_name(r["image"].split("/")[-1])[:12] for r in ev))}
    rep["hint"] = ("REJECT or exclude the hit families (eval leak)" if ev else
                   "AUGMENTED export: keep one image per base/cluster" if rep["near_dup_clusters"] < 0.7 * len(rows) else
                   "mechanically clean; do the visual D1-D6 check")
    out.mkdir(parents=True)
    (out / "vet.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    md = [f"# Vet report — {a.name}", "", f"Tool: `tools/vet_source.py`; root `{root}`.", "", "| item | value |", "|---|---|"]
    md += [f"| {k} | {json.dumps(v, ensure_ascii=False)} |" for k, v in rep.items() if k not in ("name", "root")]
    (out / "vet.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    groups = defaultdict(list)
    for r, c in zip(rows, cid):
        groups[c].append(r["image"])
    with open(out / "clusters.csv", "w", encoding="utf-8") as fh:
        fh.write("cluster,image\n")
        for c, ims in groups.items():
            for im in ims:
                fh.write(f"{c},{im}\n")
    if a.sheet:
        import subprocess
        subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("sample_sheet.py")), str(root), str(root),
                        a.sheet], check=False)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
