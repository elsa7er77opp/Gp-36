"""Contact sheet of N random images of a candidate YOLO source, with its RAW class ids drawn, for the visual check.

    python -I tools/sample_sheet.py <images_dir> <labels_dir> <out.jpg> [--n 20] [--seed 0] [--cols 5]

Labels are matched by file stem anywhere under labels_dir (so a Roboflow export root works for both). Raw source ids are drawn (0 red, 1 blue, others
yellow) with the id written in the caption, so the class map can be decided from what is seen. Sheets are review
images: keep them out of git (only the written description goes into CANDIDATES.md).
"""
import argparse
import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.overlay import contact_sheet, draw_boxes, tile  # noqa: E402

COL = {0: (255, 40, 40), 1: (30, 144, 255), 2: (0, 200, 0), 3: (255, 0, 255)}


def read(lbl):
    out = []
    if lbl.exists():
        for ln in lbl.read_text(encoding="utf-8", errors="replace").splitlines():
            p = ln.split()
            if len(p) == 5:
                out.append((int(float(p[0])), *map(float, p[1:])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images")
    ap.add_argument("labels")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cols", type=int, default=5)
    a = ap.parse_args()
    fs = sorted(p for p in Path(a.images).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    pick = random.Random(a.seed).sample(fs, min(a.n, len(fs)))
    lab = {p.stem: p for p in Path(a.labels).rglob("*.txt")}
    tiles = []
    for f in pick:
        b = read(lab.get(f.stem, Path("/nonexistent")))
        with Image.open(f) as im:
            tiles.append(tile(draw_boxes(im, b, class_colors=COL),
                              [f.name[:60], f"{im.size[0]}x{im.size[1]} ids={[x[0] for x in b]}"]))
    contact_sheet(tiles, cols=a.cols, title=f"{a.images} (n={len(pick)}, seed {a.seed})").save(a.out, quality=88)
    print(a.out, len(pick))


if __name__ == "__main__":
    main()
