"""Eye review of EVERY train image of a standardised dataset, then a clean dataset with only the accepted images.

    python -I tools/v4_review.py sheets --data road_hazards_v4_std --out review/std_v4/review_sheets
    python -I tools/v4_review.py apply  --data road_hazards_v4_std --review review/std_v4/review_sheets ^
                                        --out road_hazards_v4_clean --reviewed-by ahmed

sheets: writes sheet_0001.jpg ... (12 train images each, boxes drawn: orange = pothole, magenta = speed bump,
        "no hazard" written on empty images), sorted by source so one source is seen at a time, plus index.csv
        (sheet, cell, image, source) and an empty bad.txt.
review: the reviewer looks at every sheet and writes ONLY the bad cells in bad.txt, one line per sheet:
            0012: 3 7        cells 3 and 7 of sheet_0012 are bad
            SOURCE ens       every train image of source "ens" is bad
        A cell is bad if: a box is on something that is not a pothole / speed bump, a clear hazard has no box,
        a box is far too big / too small / shifted, the picture is a zoomed close-up or not a road view, or the
        picture is too dark / blurred to tell. When the last sheet is done, write the word DONE on the last line.
apply:  <out> = the dataset without the bad train images (val and test unchanged). A bad image is LEFT OUT, never
        "fixed": no box is added, moved or resized. Refuses to run if bad.txt has no DONE line. --reviewed-by is
        saved in build_info.json (use "claude" if an AI did the review; it must never be reported as human).
Files are hard-linked when possible. Refuses to overwrite.
"""
import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

COL = {0: (255, 165, 0), 1: (255, 0, 255)}
CW, CH, COLS, ROWS = 480, 360, 4, 3
PER = COLS * ROWS


def train_rows(data):
    with open(data / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = [m for m in csv.DictReader(f)]
    tr = [m for m in rows if m["split"] == "train"]
    tr.sort(key=lambda m: (m.get("source", ""), m.get("group_id", ""), m["out_image"]))
    return rows, tr


def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def do_sheets(a):
    data, out = Path(a.data), Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    _, tr = train_rows(data)
    out.mkdir(parents=True)
    with open(out / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet", "cell", "image", "source"])
        for s in range(0, len(tr), PER):
            sid = s // PER + 1
            sh = Image.new("RGB", (COLS * CW, ROWS * CH + 22), "black")
            d0 = ImageDraw.Draw(sh)
            chunk = tr[s:s + PER]
            d0.text((6, 5), f"sheet {sid:04d}   sources: {', '.join(sorted({m.get('source', '') for m in chunk}))}", fill=(255, 255, 255))
            for j, m in enumerate(chunk):
                p = Path(m["out_image"])
                im = Image.open(data / p).convert("RGB").resize((CW, CH), Image.BILINEAR)
                d = ImageDraw.Draw(im)
                n = 0
                lp = data / "labels" / "train" / (p.stem + ".txt")
                for line in (lp.read_text(encoding="utf-8").splitlines() if lp.exists() else []):
                    v = line.split()
                    if len(v) >= 5:
                        c = int(float(v[0]))
                        cx, cy, bw, bh = (float(x) for x in v[1:5])
                        d.rectangle([(cx - bw / 2) * CW, (cy - bh / 2) * CH, (cx + bw / 2) * CW, (cy + bh / 2) * CH], outline=COL.get(c, (0, 255, 0)), width=2)
                        n += 1
                d.rectangle([0, 0, 150, 15], fill=(0, 0, 0))
                d.text((3, 2), f"{j + 1}  {m.get('source', '')}" + ("" if n else "  no hazard"), fill=(255, 255, 0))
                sh.paste(im, ((j % COLS) * CW, 22 + (j // COLS) * CH))
                w.writerow([f"{sid:04d}", j + 1, m["out_image"], m.get("source", "")])
            sh.save(out / f"sheet_{sid:04d}.jpg", quality=85)
            if sid % 50 == 0:
                print(f"  sheet {sid}", flush=True)
    (out / "bad.txt").write_text("", encoding="utf-8")
    print(f"{out}: {(len(tr) + PER - 1) // PER} sheets for {len(tr)} train images. Write the bad cells in {out / 'bad.txt'}.")


def read_bad(review):
    idx = {}
    by_source = {}
    with open(review / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            idx[(r["sheet"], int(r["cell"]))] = r["image"]
            by_source.setdefault(r["source"], []).append(r["image"])
    bad, done = {}, False
    for ln, line in enumerate((review / "bad.txt").read_text(encoding="utf-8-sig").splitlines(), 1):
        t = line.split("#")[0].strip()
        if not t:
            continue
        if t.upper() == "DONE":
            done = True
            continue
        if t.upper().startswith("SOURCE "):
            s = t.split(None, 1)[1].strip()
            if s not in by_source:
                sys.exit(f"bad.txt line {ln}: unknown source {s!r}")
            for im in by_source[s]:
                bad[im] = f"source:{s}"
            continue
        if ":" not in t:
            sys.exit(f"bad.txt line {ln}: expected 'SHEET: cells', 'SOURCE name' or DONE, got {t!r}")
        sh, cells = t.split(":", 1)
        sh = sh.strip().zfill(4)
        for c in cells.replace(",", " ").split():
            if not c.isdigit() or (sh, int(c)) not in idx:
                sys.exit(f"bad.txt line {ln}: no cell {c!r} on sheet {sh}")
            bad[idx[(sh, int(c))]] = f"sheet {sh} cell {c}"
    return bad, done, len(idx)


def do_apply(a):
    data, review, out = Path(a.data), Path(a.review), Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    bad, done, n_idx = read_bad(review)
    if not done:
        sys.exit("bad.txt has no DONE line: the review is not finished")
    rows, tr = train_rows(data)
    if n_idx != len(tr):
        sys.exit(f"index.csv has {n_idx} images but the dataset has {len(tr)} train images: the sheets belong to another build")
    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        sys.exit(f"{tmp} exists (an earlier run stopped); rename or remove it yourself")
    kept = []
    for m in rows:
        if m["split"] == "train" and m["out_image"] in bad:
            continue
        p = Path(m["out_image"])
        link(data / p, tmp / p)
        link(data / "labels" / m["split"] / (p.stem + ".txt"), tmp / "labels" / m["split"] / (p.stem + ".txt"))
        kept.append(m)
    for name in ("data.yaml", "data_stdframe.yaml", "val_stdframe.txt", "test_stdframe.txt"):
        if (data / name).exists():
            shutil.copyfile(data / name, tmp / name)
    with open(tmp / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(kept)
    with open(tmp / "review_drop_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "where"])
        w.writerows(sorted(bad.items()))
    src_of = {m["out_image"]: m.get("source", "") for m in tr}
    info = {"from": str(data), "review": str(review), "reviewed_by": a.reviewed_by, "train_reviewed": len(tr),
            "train_left_out": len(bad), "left_out_by_source": dict(Counter(src_of[i] for i in bad)), "splits": {}}
    for sp in ("train", "val", "test"):
        rs = [m for m in kept if m["split"] == sp]
        info["splits"][sp] = {"images": len(rs), "pothole_boxes": sum(int(m.get("n_pothole") or 0) for m in rs),
                              "speed_bump_boxes": sum(int(m.get("n_speed_bump") or 0) for m in rs)}
    (tmp / "build_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    tmp.rename(out)
    print(json.dumps(info, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheets")
    s.add_argument("--data", required=True)
    s.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--data", required=True)
    p.add_argument("--review", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--reviewed-by", required=True, help="who looked at the sheets, e.g. ahmed or claude")
    a = ap.parse_args()
    (do_sheets if a.cmd == "sheets" else do_apply)(a)


if __name__ == "__main__":
    main()
