"""Write the val review decisions (31 Oct) into corrections.csv.
Index = position in the val part of label_error_ranking.csv (flagged rows, score order), as on the sheets."""
import csv
from pathlib import Path
HERE = Path(__file__).parent
rows = [r for r in csv.DictReader(open(HERE / "label_error_ranking.csv", encoding="utf-8"))
        if r["split"] == "val" and float(r["score"]) > 0]
VIEWED = set(range(0, 108)) | set(range(132, 138))
DROP = {4: "glare_reflection", 14: "glare_reflection", 20: "too_dark", 30: "sun_flare", 33: "sun_flare",
        40: "finger_occlusion", 48: "sun_flare", 51: "finger_occlusion", 54: "sun_flare", 55: "ambiguous_mixed_boxes",
        62: "sun_flare", 64: "sun_flare", 66: "motion_blur", 68: "too_dark", 69: "sun_flare", 80: "motion_blur"}
REMOVE = {13: "FAR_TINY", 18: "D5_crack", 22: "D5_wet_patch", 23: "FAR_TINY", 24: "FAR_TINY", 25: "FAR_TINY",
          26: "FAR_TINY", 27: "FAR_TINY", 34: "D4_one_box_per_defect", 36: "not_visibly_pothole",
          43: "D4_one_box_per_defect", 45: "FAR_TINY", 82: "D5_crack", 98: "FAR_TINY", 99: "FAR_TINY",
          100: "D5_crack", 104: "FAR_TINY", 105: "FAR_TINY", 107: "FAR_TINY", 132: "FAR_TINY", 133: "FAR_TINY",
          134: "FAR_TINY"}
RECLASS = {46: "painted_hump_D2", 47: "painted_hump_D2"}
out = []
for i, r in enumerate(rows):
    flags = r["flags"].split()
    if i in DROP:
        a, why, basis = "DROP_IMAGE", DROP[i], "visual"
    elif i in REMOVE:
        a, why, basis = "REMOVE_UNMATCHED_POTHOLE", REMOVE[i], "visual"
    elif i in RECLASS:
        a, why, basis = "RECLASS_TO_SPEED_BUMP", RECLASS[i], "visual"
    elif i in VIEWED:
        a, why, basis = "KEEP", "label_plausible_or_unverifiable", "visual"
    else:
        tiny_pot_only = flags and all(f.startswith("UNMATCHED_GT:pothole:area=") and float(f.split("=")[1]) < 0.004
                                      for f in flags) and r["source"] == "rf8"
        if tiny_pot_only:
            a, why, basis = "REMOVE_UNMATCHED_POTHOLE", "FAR_TINY", "rule (pattern confirmed on viewed sheets)"
        else:
            a, why, basis = "KEEP", "label_plausible_or_unverifiable", "rule"
    out.append({"split": "val", "idx": i, "out_image": r["out_image"], "source": r["source"],
                "sample_id": r["sample_id"], "action": a, "reason": why, "basis": basis,
                "reviewer": "claude", "date": "2026-10-31", "flags": r["flags"]})
with open(HERE / "corrections.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter((o["action"], o["basis"].split()[0]) for o in out))
