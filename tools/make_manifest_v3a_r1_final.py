"""Apply the owner-approved review decisions (2026-10-30) to the v3a_r1 split -> manifests/v3a_r1_final_split_manifest.csv.
  * test: keep proposed_decision == OK, plus ROTATION_MISMATCH images (rotated); all other test rows excluded
    (NOT moved to train/val: their groups belong to test).
  * all splits: rotate_cw=90 for ROTATE_CW rows of ROTATION_REVIEW.csv; UNSURE rotation rows excluded.
Writes a NEW manifest plus an exclusions list; never overwrites."""
import csv, sys
from collections import Counter
from pathlib import Path
R = Path(__file__).resolve().parents[1]
RV = R / "review/v3a_r1_test_review"
out = R / "manifests/v3a_r1_final_split_manifest.csv"; exc = R / "manifests/v3a_r1_final_excluded.csv"
for p in (out, exc):
    if p.exists(): sys.exit(f"refusing: {p} exists")
rows = list(csv.DictReader(open(R / "manifests/v3a_r1_split_manifest.csv", encoding="utf-8")))
test = {r["sample_id"]: r for r in csv.DictReader(open(RV / "TEST_REVIEW.csv", encoding="utf-8"))}
rot = {r["sample_id"]: r for r in csv.DictReader(open(RV / "ROTATION_REVIEW.csv", encoding="utf-8"))}
keep, excl = [], []
for r in rows:
    sid = r["sample_id"]; why = None
    if r["split"] == "test":
        t = test[sid]
        if not (t["proposed_decision"] == "OK" or "ROTATION_MISMATCH" in t["codes"]):
            why = f"test review {t['proposed_decision']}: {t['codes']}"
    v = rot.get(sid, {}).get("verdict")
    if v == "UNSURE":
        why = why or "rotation unsure"
    if why:
        excl.append({"sample_id": sid, "split": r["split"], "reason": why}); continue
    keep.append({**r, "rotate_cw": 90 if v == "ROTATE_CW" else 0, "review": "reviewed_test" if r["split"] == "test" else r["review"]})
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(keep[0].keys())); w.writeheader(); w.writerows(keep)
with open(exc, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["sample_id", "split", "reason"]); w.writeheader(); w.writerows(excl)
print("kept", Counter(r["split"] for r in keep), "| rotated", Counter(r["split"] for r in keep if r["rotate_cw"]), "| excluded", Counter(r["split"] for r in excl))
