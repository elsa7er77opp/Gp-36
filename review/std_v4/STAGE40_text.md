
## Stage 40 — owner decision: nothing is removed; unify the resolution and FIX the labels (2026-11-11 ~20:10; written BEFORE any build or result)
- **Owner (Ahmed, 11 Nov, after Stage 39c):** he never asked for images to be removed. He wants all ~10,000 train images kept, one resolution, and wrong labels / boxes corrected (missing box drawn, wrong box moved or removed), then training on all of them.
- **This replaces, for the train split of v5 only,** the earlier rule "a bad image is left out, never fixed". Val and test labels are NOT changed (they are the cleaned r2 benchmark).
- **`road_hazards_v5_all`** (`tools/std_dataset_v2.py build --frame-rules none --no-dedup`; v2 = `std_dataset.py` plus the `--no-dedup` option): every image of `road_hazards_v3b_C` at exactly 960x720 (4:3 crop that keeps every box, letterbox when impossible; sb15 un-stretched to 16:9). No framing filter, no duplicate removal: train stays 10,562 images. Val/test come out the same as in v4.
- **A1 = `v5_all_11n_960_s0`:** C's exact arguments on `road_hazards_v5_all` (cache=False). It isolates the effect of the single resolution.
- **Label fixes** (`tools/v5_fix.py`): train images marked bad in Stage 39a (1,599) and train images never looked at (left out of v4_std) are looked at; a corrected, complete box list per image goes to `review/v5/fixes.jsonl`; `apply` builds `road_hazards_v5_fixed` (same 10,562 images, `fix_log.csv` keeps old and new boxes).
  - The boxes are drawn by Claude Code **by eye**: these are AI labels (`fixed_by=claude`), never described as human labels. No model is run on the images and no model output is shown while fixing (no pseudo-labels).
  - When an image cannot be judged (too dark, blurred), its label is left as it is; nothing is removed.
- **F1 = `v5_fixed_11n_960_s0`:** C's exact arguments on `road_hazards_v5_fixed`.
- **H-40a (written now):** A1 - C on the v5 val, mean AP50, is within -0.02 to +0.02 (one resolution alone, same images and labels).
- **H-40b (written now):** F1 - A1: pothole AP50 between 0.00 and +0.04, bump AP50 within -0.02 to +0.02. Earlier label work (Stage 36) gave no gain, so a large gain is not expected.
- **Accept rule (each of A1, F1 against C, v5 val, all 830 images):** delta mean AP50 >= +0.02, or one class >= +0.02 with the other >= -0.02. Less than 0.02 is not called an improvement (seed spread about 0.014).
- **Test:** no test use in this stage; one needs Ahmed's explicit OK and a ledger entry as a new benchmark.
- Nothing is deleted or overwritten; new folders only.
