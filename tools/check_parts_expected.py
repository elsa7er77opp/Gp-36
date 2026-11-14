"""Compare laptop-built parts with the cloud's expected build_info (review/new_data_r3/vet/<p>/expected_build_info*.json).

    python -I tools/check_parts_expected.py

Gate (written before the builds ran, STATUS Stage 27):
- decision part-vals pol_v2, red_v2, ng8_v2, egy_v2: val and test counts (images, negatives, boxes per class) must match EXACTLY;
- every part's train counts may differ by at most 2 % per field (the cloud guarded against protected_hashes.npz,
  the laptop against the --guard list, so a few train images can differ).
Prints a table, writes review/new_data_r3/vet/laptop_build_check_<time>.md, exits 1 on any gate failure.
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VET = ROOT / "review/new_data_r3/vet"
FIELDS = ("images", "negatives", "pothole_boxes", "speed_bump_boxes")
CHECKS = [(p, VET / p / "expected_build_info.json", False) for p in ("dmd", "pol", "red", "ng8", "hmp", "egy", "ens", "bpo")]
CHECKS += [(f"{p}_v2", VET / p / f"expected_build_info_{p}_v2.json", True) for p in ("pol", "red", "ng8", "egy")]
TRAIN_TOL = 0.02


def main():
    lines, bad = ["| part | split | field | expected | laptop | ok |", "|---|---|---|---|---|---|"], []
    for part, exp_path, exact_valtest in CHECKS:
        got_path = ROOT / "parts_r3" / part / "build_info.json"
        if not got_path.exists() or not exp_path.exists():
            bad.append(f"{part}: missing {got_path if not got_path.exists() else exp_path}")
            continue
        exp = json.loads(exp_path.read_text(encoding="utf-8"))["splits"]
        got = json.loads(got_path.read_text(encoding="utf-8"))["splits"]
        for sp in ("train", "val", "test"):
            for f in FIELDS:
                e, g = exp.get(sp, {}).get(f, 0), got.get(sp, {}).get(f, 0)
                if sp == "train":
                    ok = abs(g - e) <= max(1, TRAIN_TOL * e)
                else:
                    ok = g == e or not exact_valtest
                lines.append(f"| {part} | {sp} | {f} | {e} | {g} | {'yes' if ok else '**NO**'} |")
                if not ok:
                    bad.append(f"{part} {sp} {f}: expected {e}, laptop {g}")
    hmpt = ROOT / "parts_r3/hmpt/build_info.json"
    if hmpt.exists():
        t = json.loads(hmpt.read_text(encoding="utf-8"))["splits"]["train"]
        lines.append(f"| hmpt | train | (no expected file) | — | {t} | info |")
    else:
        bad.append("hmpt: missing build_info.json")
    report = "\n".join(["# Laptop part builds vs cloud expected_build_info", "",
                        "Gate: decision part-vals (_v2) val/test exact; train within 2 % (STATUS Stage 27).", ""] + lines +
                       ["", "## Result", ""] + ([f"- FAIL: {b}" for b in bad] or ["- PASS"]))
    print(report)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    (VET / f"laptop_build_check_{stamp}.md").write_text(report + "\n", encoding="utf-8")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
