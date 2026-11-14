"""Hand-labelling tool for the egm pool (Egyptian Mapillary frames). Local only: no upload, no model, no pseudo-labels.

    venv\\Scripts\\python -I tools\\egm_label.py --pool eval      (label the eval pool first: it must be labelled COMPLETELY)
    venv\\Scripts\\python -I tools\\egm_label.py --pool train

Reads review/new_data_r3/items/egm_pool.csv. Frames are shown in a fixed order (sequence, capture time), one at a time.
Labels follow D1-D6 (audit/CLASS_MAPPING.md):
  speed_bump = any raised bump/hump across the road, INCLUDING unmarked asphalt humps; painted flat crosswalk = background;
  pothole = a real hole; patch, manhole, crack, shadow, wet patch = background; rumble strip = not a bump.
  Box each defect once, tight. Far, tiny things you cannot really see: do not box them, press U (unsure) instead.

Keys:  1 = class pothole   2 = class speed_bump   (draw with the mouse: press, drag, release)
       Z = undo last box   C = clear all boxes on this frame
       SPACE / ENTER / N = save and next   (no boxes = you confirm the frame is hazard-free)
       U = unsure (saved, but the frame is never used as a negative or in eval scoring)
       X = not usable (not a forward road view: sky, inside the car, blurred, panorama)
       B = back one frame      Q / ESC = save and quit (resume later from the same place)
       + / - = zoom the view 1.25x around the mouse     0 = fit to window

Outputs (nothing is overwritten except the label file of the frame you are on):
  labels:  <labels-root>/<pool>/<id>.txt        YOLO: class cx cy w h (0 = pothole, 1 = speed_bump), relative to the image
  status:  review/new_data_r3/egm_labels/status_<pool>.csv   one row per decision (append-only; the last row per id wins)
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLS = {0: ("pothole", (0, 165, 255)), 1: ("speed_bump", (255, 0, 255))}
WIN = "egm label"


def load_pool(path, pool):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["pool"] == pool]
    rows.sort(key=lambda r: (r["sequence"], float(r["captured_at"] or 0), r["id"]))
    return rows


def load_status(path):
    st = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                st[r["id"]] = r
    return st


def append_status(path, row):
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "pool", "status", "n_pothole", "n_bump", "time", "labeller"])
        if new:
            w.writeheader()
        w.writerow(row)


def read_boxes(p, W, H):
    out = []
    if p.exists():
        for line in p.read_text().split("\n"):
            v = line.split()
            if len(v) == 5:
                c, cx, cy, w, h = int(v[0]), *map(float, v[1:])
                out.append([c, (cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H])
    return out


def write_boxes(p, boxes, W, H):
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for c, x1, y1, x2, y2 in boxes:
        x1, x2 = sorted((max(0, min(W, x1)), max(0, min(W, x2))))
        y1, y2 = sorted((max(0, min(H, y1)), max(0, min(H, y2))))
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        lines.append(f"{c} {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}")
    p.write_text("\n".join(lines) + ("\n" if lines else ""))
    return lines


class View:
    def __init__(self, img, win_w, win_h):
        self.img, self.H, self.W = img, img.shape[0], img.shape[1]
        self.ww, self.wh = win_w, win_h
        self.fit()

    def fit(self):
        self.s = min(self.ww / self.W, self.wh / self.H)
        self.ox, self.oy = 0.0, 0.0

    def zoom(self, f, mx, my):
        ix, iy = self.to_img(mx, my)
        self.s = max(min(self.ww / self.W, self.wh / self.H), min(self.s * f, 8.0))
        self.ox, self.oy = ix - mx / self.s, iy - my / self.s

    def to_img(self, x, y):
        return self.ox + x / self.s, self.oy + y / self.s

    def to_win(self, x, y):
        return int((x - self.ox) * self.s), int((y - self.oy) * self.s)

    def render(self):
        M = np.float32([[self.s, 0, -self.ox * self.s], [0, self.s, -self.oy * self.s]])
        return cv2.warpAffine(self.img, M, (self.ww, self.wh), flags=cv2.INTER_AREA, borderValue=(40, 40, 40))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", choices=["eval", "train"], required=True)
    ap.add_argument("--csv", default=str(ROOT / "review/new_data_r3/items/egm_pool.csv"))
    ap.add_argument("--labels-root", default=str(ROOT.parent / "GP36_Dataset/labels_egm"))
    ap.add_argument("--status-dir", default=str(ROOT / "review/new_data_r3/egm_labels"))
    ap.add_argument("--win", default="1600x900")
    a = ap.parse_args()
    rows = load_pool(a.csv, a.pool)
    if not rows:
        sys.exit(f"no rows for pool {a.pool} in {a.csv}")
    st_path = Path(a.status_dir) / f"status_{a.pool}.csv"
    status = load_status(st_path)
    lab_dir = Path(a.labels_root) / a.pool
    ww, wh = map(int, a.win.lower().split("x"))
    i = next((k for k, r in enumerate(rows) if r["id"] not in status), len(rows))
    if i == len(rows):
        print(f"all {len(rows)} frames of pool {a.pool} already have a decision"); return
    cv2.namedWindow(WIN, cv2.WINDOW_AUTOSIZE)
    st = {"cls": 1, "drag": None, "mouse": (0, 0)}

    def on_mouse(ev, x, y, flags, _):
        st["mouse"] = (x, y)
        if ev == cv2.EVENT_LBUTTONDOWN:
            st["drag"] = (x, y, x, y)
        elif ev == cv2.EVENT_MOUSEMOVE and st["drag"]:
            st["drag"] = (*st["drag"][:2], x, y)
        elif ev == cv2.EVENT_LBUTTONUP and st["drag"]:
            x0, y0 = st["drag"][:2]
            st["drag"] = None
            p0, p1 = view.to_img(x0, y0), view.to_img(x, y)
            if abs(p1[0] - p0[0]) > 3 and abs(p1[1] - p0[1]) > 3:
                boxes.append([st["cls"], p0[0], p0[1], p1[0], p1[1]])

    cv2.setMouseCallback(WIN, on_mouse)
    while 0 <= i < len(rows):
        r = rows[i]
        img = cv2.imread(r["image"], cv2.IMREAD_COLOR)  # applies EXIF orientation, like Ultralytics
        if img is None:
            print("cannot read", r["image"]); i += 1; continue
        H, W = img.shape[:2]
        lp = lab_dir / f"{r['id']}.txt"
        boxes = read_boxes(lp, W, H)
        view = View(img, ww, wh)
        decided = None
        while decided is None:
            canvas = view.render()
            for c, x1, y1, x2, y2 in boxes:
                cv2.rectangle(canvas, view.to_win(x1, y1), view.to_win(x2, y2), CLS[c][1], 2)
                cv2.putText(canvas, CLS[c][0], view.to_win(x1, y1 - 4 / view.s), 0, 0.6, CLS[c][1], 2)
            if st["drag"]:
                cv2.rectangle(canvas, st["drag"][:2], st["drag"][2:], CLS[st["cls"]][1], 1)
            done = sum(1 for x in rows if x["id"] in status)
            bar = (f"[{a.pool}] {i + 1}/{len(rows)}  done {done}  seq {r['sequence'][:10]}  class: {CLS[st['cls']][0]}  "
                   f"boxes {len(boxes)}   1/2 class  SPACE next  U unsure  X unusable  Z undo  B back  +/- zoom  Q quit")
            cv2.rectangle(canvas, (0, 0), (ww, 24), (0, 0, 0), -1)
            cv2.putText(canvas, bar, (6, 17), 0, 0.5, (255, 255, 255), 1)
            cv2.imshow(WIN, canvas)
            k = cv2.waitKey(30) & 0xFF
            if k == 255:
                if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
                    decided = "quit"
                continue
            ch = chr(k).lower() if k < 128 else ""
            if ch == "1": st["cls"] = 0
            elif ch == "2": st["cls"] = 1
            elif ch == "z" and boxes: boxes.pop()
            elif ch == "c": boxes.clear()
            elif ch in ("+", "="): view.zoom(1.25, *st["mouse"])
            elif ch in ("-", "_"): view.zoom(0.8, *st["mouse"])
            elif ch == "0": view.fit()
            elif k in (32, 13) or ch == "n": decided = "done"
            elif ch == "u": decided = "unsure"
            elif ch == "x": decided = "unusable"
            elif ch == "b": decided = "back"
            elif ch == "q" or k == 27: decided = "quit"
        if decided in ("done", "unsure", "unusable"):
            lines = write_boxes(lp, boxes if decided != "unusable" else [], W, H)
            row = {"id": r["id"], "pool": a.pool, "status": decided,
                   "n_pothole": sum(l.startswith("0 ") for l in lines), "n_bump": sum(l.startswith("1 ") for l in lines),
                   "time": time.strftime("%Y-%m-%d %H:%M:%S"), "labeller": "human"}
            append_status(st_path, row)
            status[r["id"]] = row
            i += 1
        elif decided == "back":
            i = max(0, i - 1)
        elif decided == "quit":
            if boxes:
                write_boxes(lp, boxes, W, H)
                print("boxes of the current frame saved, but the frame has no decision yet (it will open again)")
            break
    cv2.destroyAllWindows()
    vals = [status[x["id"]] for x in rows if x["id"] in status]
    print(f"pool {a.pool}: {len(vals)}/{len(rows)} decided | done {sum(v['status'] == 'done' for v in vals)} "
          f"unsure {sum(v['status'] == 'unsure' for v in vals)} unusable {sum(v['status'] == 'unusable' for v in vals)} | "
          f"bump boxes {sum(int(v['n_bump']) for v in vals)} pothole boxes {sum(int(v['n_pothole']) for v in vals)}")


if __name__ == "__main__":
    main()
