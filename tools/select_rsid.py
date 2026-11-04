"""Choose which RSID (Zenodo 18789662) images to fetch, and assign each sequence to train / val / test.

    python -I tools/select_rsid.py --labels ../GP36_Dataset/raw_v3/zenodo_rsid_labels --out review/new_data_r3/rsid_selection

Rules (written before any image was looked at):
- Family GOPRO (`G00xxxxx`, Nienaber South Africa) is EXCLUDED: same family as r2 val/test (rf8 group r1g1132).
- Family `other` (random-hash names, "random Roboflow datasets" per the README) is EXCLUDED: unknown provenance.
- Every image belongs to a sequence (drive/video); the split is by sequence, never by frame.
- Hazard frames (pothole or speed bump box) form runs: frames of one sequence <= --run-gap frame numbers apart.
  Up to --per-run frames per run are kept, evenly spaced (the rest are near-duplicate frames of the same object).
- Hard negatives: frames with only manhole boxes (manhole = background, rule D5) or no boxes, at least
  --neg-margin frames away from any hazard frame of the same sequence, spaced >= --neg-gap apart, at most
  --neg-cap per sequence (half manhole-only when available).
- Sequences are assigned to val / test / train greedily by number of bump runs, so val and test each hold about
  --hold fraction of all bump runs, and no sequence is split.
Writes <out>.csv (one row per selected image) and <out>_names.txt (archive member names: image + label).
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "Road-surface-irregularities-dataset/raw"
PATS = [
    (r"^G\d{7}", "GOPRO", None),
    (r"^(\d{10})_(\d+)_blurred", "VLNdash", 1),
    (r"^(\d{8})_(\d+)_blurred", "VLNphone", 1),
    (r"^HD1080_SN\d+_(\d\d-\d\d-\d\d)_flipped_frame_(\d+)", "ZED", 1),
    # dash-cam clips are 5-min pieces of one drive: group by recording DAY so adjacent clips stay together
    (r"^(?:FILE|EMER)(\d{6})-\d{6}[-_]MOV-(\d+)", "DASHKR", 1),
    (r"^(Bumps?_\d*_?[a-z]*)_?frame_(\d+)", "LTbump", 1),
    (r"^(Manholes?_\d*_?[a-z]*)_?frame_(\d+)", "LTmanhole", 1),
    (r"^(Vienas_dangtis_\w*?)_?fra?m?e?_(\d+)", "LTmanhole", 1),
]


def parse(stem):
    s = re.sub(r"\.rf\.[0-9a-f]{32}$", "", stem)
    for pat, fam, _ in PATS:
        m = re.match(pat, s)
        if m:
            if fam == "GOPRO":
                return fam, None, None
            return fam, f"{fam}:{m.group(1)}", int(m.group(2))
    return "other", None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-gap", type=int, default=30)
    ap.add_argument("--per-run", type=int, default=4)
    ap.add_argument("--neg-margin", type=int, default=60)
    ap.add_argument("--neg-gap", type=int, default=50)
    ap.add_argument("--neg-cap", type=int, default=30)
    ap.add_argument("--hold", type=float, default=0.15)
    args = ap.parse_args()
    out = Path(args.out)
    if out.with_suffix(".csv").exists():
        sys.exit(f"{out}.csv exists")
    base = Path(args.labels) / ROOT

    frames = defaultdict(list)  # seq -> [(frame, split, stem, kind, n_pot, n_bump, n_man)]
    excluded = defaultdict(int)
    for sp in ("train", "valid", "test"):
        for f in sorted((base / sp / "labels").glob("*.txt")):
            fam, seq, fr = parse(f.stem)
            if seq is None:
                excluded[fam] += 1
                continue
            cls = [int(l.split()[0]) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            npot, nman, nbump = cls.count(0), cls.count(1), cls.count(2)
            kind = "hazard" if npot or nbump else "neg_manhole" if nman else "neg_empty"
            frames[seq].append((fr, sp, f.stem, kind, npot, nbump, nman))

    rows, runs_per_seq = [], {}
    for seq, fl in frames.items():
        fl.sort()
        haz = [x for x in fl if x[3] == "hazard"]
        runs, cur = [], []
        for x in haz:
            if cur and x[0] - cur[-1][0] > args.run_gap:
                runs.append(cur)
                cur = []
            cur.append(x)
        if cur:
            runs.append(cur)
        runs_per_seq[seq] = runs
        for ri, r in enumerate(runs):
            k = min(args.per_run, len(r))
            idx = sorted({round(i * (len(r) - 1) / max(k - 1, 1)) for i in range(k)})
            for i in idx:
                rows.append((seq, r[i], f"run{ri}"))
        hfr = [x[0] for x in haz]
        negs = [x for x in fl if x[3] != "hazard" and all(abs(x[0] - h) >= args.neg_margin for h in hfr)]
        picked = {"neg_manhole": [], "neg_empty": []}
        for kind in ("neg_manhole", "neg_empty"):
            last = -10 ** 9
            for x in (n for n in negs if n[3] == kind):
                if x[0] - last >= args.neg_gap:
                    picked[kind].append(x)
                    last = x[0]
        cap_m = min(len(picked["neg_manhole"]), args.neg_cap // 2 if picked["neg_empty"] else args.neg_cap)
        cap_e = min(len(picked["neg_empty"]), args.neg_cap - cap_m)
        for kind, cap in (("neg_manhole", cap_m), ("neg_empty", cap_e)):
            L = picked[kind]
            sel = [L[round(i * (len(L) - 1) / max(cap - 1, 1))] for i in range(cap)] if cap else []
            for x in dict.fromkeys(sel):
                rows.append((seq, x, kind))

    # split by sequence: bump runs per sequence
    bump_runs = {s: sum(any(x[5] for x in r) for r in runs_per_seq[s]) for s in frames}
    total = sum(bump_runs.values())
    target = args.hold * total
    assign, got = {}, {"val": 0, "test": 0}
    for s in sorted(frames, key=lambda s: (-bump_runs[s], s)):
        if bump_runs[s] == 0:
            assign[s] = "train"
            continue
        # give a sequence to the held-out split that is furthest below target, if it does not overshoot by much
        need = min(("val", "test"), key=lambda k: got[k])
        if got[need] + bump_runs[s] <= target * 1.35 and bump_runs[s] <= 0.6 * target:
            assign[s] = need
            got[need] += bump_runs[s]
        else:
            assign[s] = "train"

    with open(out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member_image", "member_label", "seq", "frame", "orig_split", "kind", "run", "n_pothole",
                    "n_speed_bump", "n_manhole", "part_split"])
        names = []
        for seq, x, tag in rows:
            fr, sp, stem, kind, npot, nbump, nman = x
            img = f"{ROOT}/{sp}/images/{stem}.jpg"
            lbl = f"{ROOT}/{sp}/labels/{stem}.txt"
            w.writerow([img, lbl, seq, fr, sp, kind, tag if kind == "hazard" else "", npot, nbump, nman, assign[seq]])
            names.append(img)
    Path(str(out) + "_names.txt").write_text("\n".join(names) + "\n", encoding="utf-8")

    summ = defaultdict(lambda: defaultdict(int))
    for seq, x, tag in rows:
        k = assign[seq]
        summ[k]["images"] += 1
        summ[k][x[3]] += 1
        summ[k]["bump_boxes"] += x[5]
        summ[k]["pothole_boxes"] += x[4]
    print("excluded by family:", dict(excluded))
    print("bump runs total", total, "| val", got["val"], "| test", got["test"])
    print("held-out sequences:", {k: [s for s in assign if assign[s] == k] for k in ("val", "test")})
    for k in ("train", "val", "test"):
        print(k, dict(summ[k]))


if __name__ == "__main__":
    main()
