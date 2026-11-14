"""Rank egm TRAIN-creator frames by model C's speed-bump / pothole score, to choose which frames get looked at.
Owner decision 7 Nov (STATUS Stage 37b). The output is ONLY a ranking: no label is written from it; every label is
drawn by looking at the frame (D1-D6). EVAL-creator frames are never run through any model (checked below).

    venv\\Scripts\\python -I tools\\egm_mine_candidates.py --tiles ..\\GP36_Dataset\\raw_v3\\egm
        --pool review\\new_data_r3\\items\\egm_pool.csv --weights runs\\detect\\v3b_C_11n_960_s0_r2\\weights\\best.pt
        --out review\\new_data_r3\\vet\\egm\\mine_C_train.csv

Writes one row per frame: image, id, sequence, creator, captured_at, lat, lon, max_bump, max_pothole, n_bump, n_pothole
(scores >= --conf). Frames: every non-panorama frame in the tiles whose creator is a TRAIN-pool creator.
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--pool", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--conf", type=float, default=0.05)
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    with open(a.pool, encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    train_c = {r["creator"] for r in pool if r["pool"] == "train"}
    eval_c = {r["creator"] for r in pool if r["pool"] == "eval"}
    assert not (train_c & eval_c)
    frames = []
    for js in sorted(Path(a.tiles).rglob("*.json")):
        img = js.with_suffix(".jpg")
        if "_tar" in js.parts or not img.exists():
            continue
        d = json.loads(js.read_text(encoding="utf-8"))
        cr = str((d.get("creator") or {}).get("id") or (d.get("creator") or {}).get("username") or "")
        if d.get("is_pano") or cr not in train_c:
            continue
        g = (d.get("geometry") or {}).get("coordinates") or [None, None]
        frames.append({"image": str(img), "id": str(d.get("id", js.stem)), "sequence": d.get("sequence") or "",
                       "creator": cr, "captured_at": d.get("captured_at") or 0, "lon": g[0], "lat": g[1]})
    assert all(f["creator"] not in eval_c for f in frames)
    print(f"train-creator frames to rank: {len(frames)} (eval creators excluded: {len(eval_c)})", flush=True)
    from ultralytics import YOLO
    model = YOLO(a.weights)
    names = model.names
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["image", "id", "sequence", "creator", "captured_at", "lat", "lon", "max_bump", "max_pothole", "n_bump", "n_pothole"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for k in range(0, len(frames), a.batch):
            chunk = frames[k:k + a.batch]
            res = model.predict([c["image"] for c in chunk], imgsz=a.imgsz, conf=a.conf, verbose=False, half=True)
            for c, r in zip(chunk, res):
                cls = r.boxes.cls.tolist()
                sc = r.boxes.conf.tolist()
                b = [s for s, q in zip(sc, cls) if names[int(q)] == "speed_bump"]
                p = [s for s, q in zip(sc, cls) if names[int(q)] == "pothole"]
                w.writerow({**c, "max_bump": round(max(b, default=0), 4), "max_pothole": round(max(p, default=0), 4),
                            "n_bump": len(b), "n_pothole": len(p)})
            if (k // a.batch) % 50 == 0:
                print(f"  {k + len(chunk)}/{len(frames)}", flush=True)
    print("done:", out)


if __name__ == "__main__":
    main()
