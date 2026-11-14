"""Labelling pool from the Egyptian Mapillary mirror (`egm`): Egyptian forward-view street frames, UNLABELLED.

    python -I tools/make_egm_pool.py --tiles <dir with extracted tile folders> --out review/new_data_r3/items/egm_pool.csv \
        [--min-gap-m 15] [--max-per-seq 40] [--eval-every 3]

Source: Kaggle `yassienwasfy/egyptian-streets-dashcam` = Hugging Face `masterofaudio2077/egyptian-streets`
(mirror of Mapillary images; the mirror says Apache-2.0, Mapillary images themselves are CC BY-SA 4.0 -> keep
attribution, see review/new_data_r3/vet/egm/README.md). Files: data/<x>_<y>/r*.tar with <id>.jpg + <id>.json;
tile x ~ floor(12.5 * lon), y ~ floor(12.5 * lat) (fitted on 3 tiles, cloud session 5): Cairo/Giza = 390_375, 391_375;
Alexandria = 374_390.

These frames have NO labels. They are never used as positives or as "hazard-free" negatives until a person has
labelled every frame by D1-D6 (no pseudo-labels). The pool only decides WHICH frames get labelled and how they are
split, BEFORE anyone looks at them:
  1. drop panoramas (is_pano) and frames without a sequence id;
  2. per sequence, sorted by capture time, keep a frame only if it is >= --min-gap-m metres from the last kept frame
     (consecutive phone frames are near-duplicates) and at most --max-per-seq frames;
  3. split by CREATOR (one driver / phone = one group, so the same streets and camera never sit on both sides):
     creators sorted by (-kept frames, creator id); i % --eval-every == --eval-every - 1 -> pool "eval" (a future
     Egyptian benchmark, labelled completely, never trained on), else pool "train".
Output CSV columns: image, id, sequence, creator, pool, lat, lon, captured_at, width, height, tile. No pixels are
written. A summary is printed (frames per pool, sequences, creators).
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def haversine_m(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def read_meta(tiles):
    rows = []
    for js in sorted(Path(tiles).rglob("*.json")):
        img = js.with_suffix(".jpg")
        if not img.exists():
            continue
        d = json.loads(js.read_text(encoding="utf-8"))
        g = (d.get("geometry") or {}).get("coordinates") or [None, None]
        rows.append({"image": str(img), "id": str(d.get("id", js.stem)), "sequence": d.get("sequence") or "",
                     "creator": str((d.get("creator") or {}).get("id") or (d.get("creator") or {}).get("username") or ""),
                     "is_pano": bool(d.get("is_pano")), "lon": g[0], "lat": g[1],
                     "captured_at": d.get("captured_at") or 0, "width": d.get("width"), "height": d.get("height"),
                     "tile": js.parent.name})
    return rows


def thin(rows, min_gap_m=15.0, max_per_seq=40):
    """Per sequence: time order, keep frames >= min_gap_m apart (from the last kept), at most max_per_seq."""
    by = defaultdict(list)
    for r in rows:
        if r["is_pano"] or not r["sequence"]:
            continue
        by[r["sequence"]].append(r)
    out = []
    for seq in sorted(by):
        last, n = None, 0
        for r in sorted(by[seq], key=lambda x: (x["captured_at"], x["id"])):
            if n >= max_per_seq:
                break
            pos = (r["lon"], r["lat"])
            if last is not None and None not in pos and None not in last and haversine_m(last, pos) < min_gap_m:
                continue
            out.append(r)
            last, n = pos, n + 1
    return out


def split_by_creator(rows, eval_every=3):
    cnt = defaultdict(int)
    for r in rows:
        cnt[r["creator"]] += 1
    order = sorted(cnt, key=lambda c: (-cnt[c], c))
    pool = {c: "eval" if i % eval_every == eval_every - 1 else "train" for i, c in enumerate(order)}
    for r in rows:
        r["pool"] = pool[r["creator"]]
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-gap-m", type=float, default=15.0)
    ap.add_argument("--max-per-seq", type=int, default=40)
    ap.add_argument("--eval-every", type=int, default=3)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    meta = read_meta(a.tiles)
    rows = split_by_creator(thin(meta, a.min_gap_m, a.max_per_seq), a.eval_every)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["image", "id", "sequence", "creator", "pool", "lat", "lon", "captured_at", "width", "height", "tile"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    summ = {p: {"frames": sum(r["pool"] == p for r in rows), "sequences": len({r["sequence"] for r in rows if r["pool"] == p}),
                "creators": len({r["creator"] for r in rows if r["pool"] == p})} for p in ("train", "eval")}
    print(json.dumps({"frames_read": len(meta), "panos_dropped": sum(r["is_pano"] for r in meta), "kept": len(rows),
                      "pools": summ, "out": str(out)}, indent=1))


if __name__ == "__main__":
    main()
