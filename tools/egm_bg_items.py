"""Items CSV for part `egm` (STATUS Stage 38): eye-checked egm TRAIN-creator frames only.

    python -I tools/egm_bg_items.py --out review/new_data_r3/items/items_egm.csv

- Reads review/new_data_r3/egm_labels/status_train.csv; for each id the LAST row wins. Only status=done is used
  (unsure / unusable are left out). Label = GP36_Dataset/labels_egm/train/<id>.txt (empty = background); it must exist.
- Image paths come from items/egm_pool.csv or, for frames outside the pool, vet/egm/mine_C_train.csv.
- Refuses any frame of an eval-pool creator and any leak hit in vet/egm/leak_egm.csv.
- group = sequence; sequences are split train/val at random (seed 0, --val-frac of the sequences), so the part val
  holds different sequences from the part train. meta = labeller=<..>;creator=<..>.
- Refuses to overwrite --out.
"""
import argparse, csv, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "review/new_data_r3"
DS = ROOT.parent / "GP36_Dataset"
WIN_DS = r"C:\Users\ahmed\Desktop\GP36_Dataset"


def win(p):  # "..\GP36_Dataset\raw_v3\..." -> absolute Windows path
    p = p.replace("/", "\\")
    pre = "..\\GP36_Dataset"
    if not p.startswith(pre):
        sys.exit(f"unexpected path {p}")
    return WIN_DS + p[len(pre):]


ap = argparse.ArgumentParser()
ap.add_argument("--status", default=str(R / "egm_labels/status_train.csv"))
ap.add_argument("--out", required=True)
ap.add_argument("--val-frac", type=float, default=1 / 3)
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
out = Path(a.out)
if out.exists():
    sys.exit(f"{out} exists; refusing to overwrite")

pool = {r["id"]: r for r in csv.DictReader(open(R / "items/egm_pool.csv", encoding="utf-8"))}
eval_creators = {r["creator"] for r in pool.values() if r["pool"] == "eval"}
mine = {r["id"]: r for r in csv.DictReader(open(R / "vet/egm/mine_C_train.csv", encoding="utf-8"))}
hits = {r["image"] for r in csv.DictReader(open(R / "vet/egm/leak_egm.csv", encoding="utf-8")) if r["hit"] == "True"}

last = {}
for r in csv.DictReader(open(a.status, encoding="utf-8")):
    if r["pool"] != "train":
        sys.exit(f"status row with pool={r['pool']}: only train frames may be used")
    last[r["id"]] = r

rows, skipped = [], {}
for i, s in last.items():
    if s["status"] != "done":
        skipped[s["status"]] = skipped.get(s["status"], 0) + 1
        continue
    src = pool.get(i) or mine.get(i)
    if src is None:
        sys.exit(f"{i}: not in egm_pool.csv nor mine_C_train.csv")
    if src["creator"] in eval_creators or (i in pool and pool[i]["pool"] != "train"):
        sys.exit(f"{i}: eval creator - never used for training")
    if src["image"] in hits:
        skipped["leak_hit"] = skipped.get("leak_hit", 0) + 1
        continue
    lbl = DS / "labels_egm/train" / f"{i}.txt"
    if not lbl.exists():
        sys.exit(f"{lbl} missing (write the decision first)")
    rows.append({"image": win(src["image"]), "label": WIN_DS + "\\labels_egm\\train\\" + f"{i}.txt",
                 "class_map": json.dumps({"0": "pothole", "1": "speed_bump"}), "group": src["sequence"],
                 "creator": src["creator"], "labeller": s["labeller"]})

seqs = sorted({r["group"] for r in rows})
rng = random.Random(a.seed)
rng.shuffle(seqs)
n_val = round(len(seqs) * a.val_frac)
val_seqs = set(seqs[:n_val])
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["image", "label", "class_map", "group", "part_split", "meta"])
    for r in sorted(rows, key=lambda r: (r["group"], r["image"])):
        w.writerow([r["image"], r["label"], r["class_map"], r["group"], "val" if r["group"] in val_seqs else "train",
                    f"labeller={r['labeller']};creator={r['creator']}"])
ntr = sum(r["group"] not in val_seqs for r in rows)
print(f"{out}: {len(rows)} frames ({ntr} train / {len(rows) - ntr} val), {len(seqs)} sequences ({n_val} val), skipped {skipped}")
