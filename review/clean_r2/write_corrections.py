"""All round-2 review decisions (31 Oct 2026) -> corrections.csv. One file, extended as the review goes on.
Index = position of the image in the flagged list of its split (label_error_ranking.csv, score order), as on the sheets."""
import csv
from collections import Counter
from pathlib import Path
HERE = Path(__file__).parent
ranked = list(csv.DictReader(open(HERE / "label_error_ranking.csv", encoding="utf-8")))

DEC = {
 "val": {
  "viewed": set(range(0, 108)) | set(range(132, 138)),
  "DROP_IMAGE": {4: "glare_reflection", 14: "glare_reflection", 20: "too_dark", 30: "sun_flare", 33: "sun_flare",
                 40: "finger_occlusion", 48: "sun_flare", 51: "finger_occlusion", 54: "sun_flare",
                 55: "ambiguous_mixed_boxes", 62: "sun_flare", 64: "sun_flare", 66: "motion_blur", 68: "too_dark",
                 69: "sun_flare", 80: "motion_blur"},
  "REMOVE_UNMATCHED_POTHOLE": {13: "FAR_TINY", 18: "D5_crack", 22: "D5_wet_patch", 23: "FAR_TINY", 24: "FAR_TINY",
                 25: "FAR_TINY", 26: "FAR_TINY", 27: "FAR_TINY", 34: "D4_one_box_per_defect", 36: "not_visibly_pothole",
                 43: "D4_one_box_per_defect", 45: "FAR_TINY", 82: "D5_crack", 98: "FAR_TINY", 99: "FAR_TINY",
                 100: "D5_crack", 104: "FAR_TINY", 105: "FAR_TINY", 107: "FAR_TINY", 132: "FAR_TINY",
                 133: "FAR_TINY", 134: "FAR_TINY"},
  "RECLASS_TO_SPEED_BUMP": {46: "painted_hump_D2", 47: "painted_hump_D2"},
 },
 "train": {
  "viewed": set(range(0, 54)) | set(range(108, 120)),
  "DROP_IMAGE": {1: "inconsistent_boxes_patch_area", 10: "raveled_surface_ambiguous", 24: "raveled_surface_ambiguous",
                 27: "finger_occlusion", 32: "rotation_wrong_label_misaligned", 43: "manhole_boxed_as_pothole_D5"},
  "REMOVE_UNMATCHED_POTHOLE": {2: "FAR_TINY", 3: "FAR_TINY", 4: "FAR_TINY", 5: "FAR_TINY", 6: "not_visibly_pothole",
                 7: "box_on_trees_sky", 8: "FAR_TINY", 9: "D5_crack", 11: "not_visibly_pothole", 13: "FAR_TINY",
                 14: "FAR_TINY", 15: "FAR_TINY", 16: "FAR_TINY", 17: "FAR_TINY", 18: "FAR_TINY", 19: "FAR_TINY",
                 20: "FAR_TINY", 21: "FAR_TINY", 22: "FAR_TINY", 23: "FAR_TINY", 28: "FAR_TINY", 29: "D5_crack",
                 31: "D5_crack", 37: "D5_crack", 50: "not_visibly_pothole", 53: "FAR_TINY"},
  "RECLASS_TO_SPEED_BUMP": {},
 },
}
# Box-level fixes found outside the flagged list (box index = line number in the v3a_r1 label file, from 0)
EXTRA = [
 ("val", "images/val/rf8__76b65a5a1892db22.jpg", "REMOVE_BOX", 0, "manhole_boxed_as_pothole_D5", "visual (rotated-photo sheet)"),
 ("val", "images/val/rf8__b5d0e1a3b2ae4c3b.jpg", "REMOVE_BOX", 2, "manhole_boxed_as_pothole_D5", "visual (rotated-photo sheet)"),
 ("train", "images/train/rf8__5ae13b701841194a.jpg", "REMOVE_BOX", 0, "manhole_boxed_as_pothole_D5", "visual (rotated-photo sheet)"),
 ("test", "images/test/rf8__e1f876f17049c87c.jpg", "DROP_IMAGE", "", "rotation_wrong_label_misaligned (build bug; needs owner OK, test set)", "visual (rotation check)"),
]

# Full sweep of the 486 not-flagged val images outside the GoPro set (sheets sweep_val_*.jpg, index sweep_val_index.json)
import json
_sw = {d["S"]: d["out_image"] for d in json.load(open(HERE / "sweep_val_index.json"))}
SWEEP_DROP = {44: "sun_flare", 45: "sun_flare", 51: "sun_flare", 63: "too_dark", 125: "glare_reflection",
              127: "glare_reflection", 145: "sun_flare", 182: "sun_flare", 183: "sun_flare", 373: "too_dark",
              376: "too_dark", 377: "too_dark", 379: "too_dark", 397: "too_dark", 428: "glare_reflection",
              429: "glare_reflection", 430: "glare_reflection", 431: "glare_reflection", 437: "sun_flare",
              438: "sun_flare", 439: "sun_flare", 448: "sun_flare", 478: "too_dark", 481: "too_dark"}
SWEEP_BOX = {54: (0, "patch_boxed_as_pothole_D5"), 217: (0, "manhole_boxed_as_pothole_D5")}
for k, why in SWEEP_DROP.items():
    EXTRA.append(("val", _sw[k], "DROP_IMAGE", "", why, f"visual (sweep S{k})"))
for k, (b, why) in SWEEP_BOX.items():
    EXTRA.append(("val", _sw[k], "REMOVE_BOX", b, why, f"visual (sweep S{k})"))

# Sweep of the 199 train IMG_ (Moroccan phone) images (sheets sweep_train_IMG__*.jpg, index sweep_train_IMG__index.json)
_st = {d["S"]: d["out_image"] for d in json.load(open(HERE / "sweep_train_IMG__index.json"))}
TSWEEP_DROP = {66: "occlusion_not_road_view", 180: "occlusion_not_road_view"}
TSWEEP_BOX = {13: (1, "manhole_boxed_as_pothole_D5"), 169: (1, "manhole_boxed_as_pothole_D5"),
              141: (0, "manhole_grate_boxed_as_pothole_D5"),
              80: (0, "crosswalk_not_bump_D1"), 81: (0, "crosswalk_not_bump_D1"), 82: (0, "crosswalk_not_bump_D1"),
              83: (0, "crosswalk_not_bump_D1"), 110: (0, "crosswalk_not_bump_D1"), 111: (0, "crosswalk_not_bump_D1"),
              182: (0, "crosswalk_not_bump_D1"), 183: (0, "crosswalk_not_bump_D1"), 193: (0, "crosswalk_not_bump_D1")}
for k, why in TSWEEP_DROP.items():
    EXTRA.append(("train", _st[k], "DROP_IMAGE", "", why, f"visual (train sweep S{k})"))
for k, (b, why) in TSWEEP_BOX.items():
    EXTRA.append(("train", _st[k], "REMOVE_BOX", b, why, f"visual (train sweep S{k})"))

out = []
for split, d in DEC.items():
    rows = [r for r in ranked if r["split"] == split and float(r["score"]) > 0]
    for i, r in enumerate(rows):
        flags = r["flags"].split()
        box = ""
        for act in ("DROP_IMAGE", "REMOVE_UNMATCHED_POTHOLE", "RECLASS_TO_SPEED_BUMP"):
            if i in d[act]:
                a, why, basis = act, d[act][i], "visual"
                break
        else:
            if i in d["viewed"]:
                a, why, basis = "KEEP", "plausible_or_unverifiable", "visual"
            elif flags and r["source"] == "rf8" and all(
                    f.startswith("UNMATCHED_GT:pothole:area=") and float(f.split("=")[1]) < 0.004 for f in flags):
                a, why, basis = "REMOVE_UNMATCHED_POTHOLE", "FAR_TINY", "rule (pattern confirmed on viewed sheets)"
            else:
                a, why, basis = "KEEP", "plausible_or_unverifiable", "rule"
        out.append({"split": split, "idx": i, "out_image": r["out_image"], "source": r["source"],
                    "sample_id": r["sample_id"], "action": a, "box": box, "reason": why, "basis": basis,
                    "reviewer": "claude", "date": "2026-10-31", "flags": r["flags"]})
for split, img, a, box, why, basis in EXTRA:
    out.append({"split": split, "idx": "", "out_image": img, "source": "rf8", "sample_id": "", "action": a, "box": box,
                "reason": why, "basis": basis, "reviewer": "claude", "date": "2026-10-31", "flags": ""})
with open(HERE / "corrections.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
c = Counter((o["split"], o["action"]) for o in out if o["action"] != "KEEP")
for k in sorted(c): print(k, c[k])
print("KEEP", sum(o["action"] == "KEEP" for o in out))
