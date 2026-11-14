# STATUS for Claude — GP36 clean round 2 and after

Labels: VERIFIED (read from an output file, named) · PROVISIONAL (computed, still to be confirmed) · UNRESOLVED · BLOCKED.
Working rules: handoff files + owner overrides §13/§14 (31 Oct). Full autonomy, except the 4 NEVER rules: no deleting or overwriting; test once per model per benchmark version, final candidates only; no FSM/perception threshold changes for metrics; new data never goes into internal val/test.

## Test-set use log
| # | Date/time | Model | Benchmark | Output file | Why |
|---|---|---|---|---|---|
| 1 | 2026-10-31 21:47 | Run A `v3a_r2_11n_960_s0` best.pt | internal r2 test (323 img) | `runs/v3a_r2_11n_960_s0_TEST.txt` | final r2 candidate, selected on val in Stage 3 before this run |
| — | 2026-10-31 21:48 | Run A and v1 | external BD87 | `runs/EXT_bd87_v3a_r{2,1}_11n_960_s0.txt` | **not a use**: Ultralytics stopped at the YAML check ('train' key missing) before reading any image. The empty run folders stay as they are |
| 2 | 2026-10-31 21:49 | Run A `v3a_r2_11n_960_s0` best.pt | external BD87 (`bd_speedbreaker_v2_orig87_eval.yaml`) | `runs/EXT_bd87_v3a_r2_11n_960_s0_b.txt` | final candidate on the external test |
| 3 | 2026-10-31 21:49 | v1 `v3a_r1_11n_960_s0` best.pt (frozen) | external BD87 | `runs/EXT_bd87_v3a_r1_11n_960_s0_b.txt` | deployed-baseline reference on the external test |

## Stage 1 — state check (2026-10-31 ~18:35)
- **road_hazards_v3a_r2 exists — VERIFIED.** `road_hazards_v3a_r2/build_info.json`: fingerprint `4d7ca5f29ca86f0c425f70982ecca6f39469c55f8f1d05a39153a6fb2d757176`, built 2026-10-31T17:49:00, n_samples 4188, `test_image_dropped: true`. Summary in the same file:
  - train: −103 pothole boxes, −9 bump boxes, 8 images dropped, 16 images now background
  - val: −58 pothole boxes, 2 boxes reclassed to bump, 40 images dropped, 10 images now background
  - test: 1 image dropped
- **Bat step 2 (strict verify) — PROVISIONAL.** The bat only reaches step 3 when step 2 returns 0, and step 3 ran, so it passed. Its printout was not saved to a file. To re-run with saved output after Run A (it is I/O-heavy and RAM is tight).
- **Bat step 3 (v1 on corrected val) — ran, but the numbers are UNRESOLVED.** `runs/detect/v3a_r1_11n_VAL_on_r2/` holds only plots (created 17:59–18:00). The mAP printout went to the bat window and was not saved. Plan: re-run as `v3a_r1_11n_VAL_on_r2_log` with stdout saved to `runs/v3a_r1_11n_VAL_on_r2.txt` after Run A finishes. This uses val only, never test.
- **Bat step 4, Run A (`v3a_r2_11n_960_s0`) — RUNNING.** PID 5728, started 18:00:11 (process list). Args in `runs/detect/v3a_r2_11n_960_s0/args.yaml`: yolo11n.pt, epochs 150, imgsz 960, batch 8, workers 2, cache disk, patience 30, seed 0, deterministic. Progress in `results.csv`: epoch 13 at 2025.6 s (≈156 s/epoch). Best val mAP50 so far 0.426 (epoch 12). Early-epoch numbers mean little.
- Resources (18:35): free RAM **0.39 GB** while training (Win32_OperatingSystem); C: free 105.7 GB. So only light single-process work runs in parallel with training.

## Stage 2 — new speed-bump data intake (in progress)
Four zips from `Downloads` extracted read-only by `tools/intake_zip.py` (zip-slip checks, temp folder + rename, per-file SHA-256 in `_intake.json`). Counts are VERIFIED (tool output):
| Zip | Folder in `GP36_Dataset/raw_v3/` | Files | README facts |
|---|---|---|---|
| speed-unmarked-bumb.v5i.yolov8 | `roboflow_speed_unmarked_bumb_v5` | 4,501 | 2,249 images, train only; classes Manhole, Open Manhole, Pothole, Speed Bump, Unmarked Bump; 640 Stretch; no augmentation; CC BY 4.0 |
| Unmarked-Bumps.v1i.yolov8 | `roboflow_qassim_unmarked_bumps_v1` | 2,369 | 1,183 images = 2 augmented versions per source (h/v flip, 90° rotations); Manhole, Pothole, Unmarked Bump; CC BY 4.0 |
| Unmarked-Bumps2.v1i.yolov8 | `roboflow_qassim_unmarked_bumps2_v1` | 1,643 | 820 images, no augmentation; same 3 classes; CC BY 4.0 |
| Bumps.v1i.yolov8-obb | `roboflow_qu_bumps_v1_obb` | 603 (the zip lists data.yaml 3 times) | 300 images, oriented boxes; Manhole, Pothole, Speed Bump, Unmarked Bump; CC BY 4.0 |

### Validation result — VERIFIED (details: `review/new_data_r2b/VALIDATION_REPORT.md`)
Numbers are from `review/new_data_r2b/summary.json` and `pairs_sub5_val_test.csv`.
- **sub5 (speed-unmarked-bumb v5): FAIL as bulk data.**
  - 140 of its images are near-duplicates of r2 val images and 8 of r2 test images (strict: dHash≤4 and pHash≤10).
  - The pairs are the same places as rf8 (Indian campus `Image00xxx`; Egyptian videos `MVI_15xx` / `VID_20190924` / `VIDEO0012`). The whole families must therefore be excluded.
  - What is left is ≈185 originals (one motorcycle ride, `imgge`, `newonetrwww`) with grayscale/rotated copies and D1 conflicts.
  - The preliminary "~856 usable" is **not confirmed**.
- **qub1: REJECT** (augmented copy of qub2). **qub2: REJECT** (same families as sub5, rotated/inverted, oversized boxes).
- **qubo: NEEDS_REVIEW.** Varied Saudi humps, but 77 images have POLY_OUT_OF_RANGE, 66 have empty labels, and some D1/D5 issues.
- **Decision: no v3a_r2b / Run B from this data now.** Hypothesis test failed: ≈150–185 originals from 2–3 scenes cannot give a val gain larger than single-seed noise, and the seed variance is still unknown. Kept for a later manual relabel: qubo + ≈185 sub5 originals.

### External test BD — built (VERIFIED), with a caveat
- `external_tests/bd_speedbreaker_v2_orig87/` (`tools/build_external_test.py`): BD valid+test originals, **87 images, 88 speed_bump boxes** (`build_info.json`). The augmented train copies are not used.
- Leakage guard: 0 exact and 0 near-duplicates (dihedral dHash≤4 & pHash≤10) vs all 4,188 r2 images; minimum dHash 5.
- **Caveat (visual, sheet `review/new_data_r2b/sheets/bd_closest_r2.jpg`):** some BD photos show the **same locations** as rf8 at a different moment. `img--38` is the same power-line road as an r2 *train* image, `img--132` the same curved road and red wall as an r2 *val* image. So BD is an **independent-annotation, partly-seen-location** test, **not** an unseen-region test. Report it that way.

## Plan after Run A (written before any run starts)
Steps run in order, one GPU job at a time, with every console output saved under `runs/` as `*.txt`:
1. **Strict verify of r2 with saved output** → `review/clean_r2/verify_r2_strict.txt` (closes the step-2 gap).
2. **v1 on the corrected val, logged** → name `v3a_r1_11n_VAL_on_r2_log`, stdout `runs/v3a_r1_11n_VAL_on_r2.txt` (val only).
3. **Run A on the corrected val** → name `v3a_r2_11n_VAL`, stdout `runs/v3a_r2_11n_VAL.txt`.
4. **Selection on val only:** v1 vs Run A (mAP50, mAP50-95, per-class P/R). The selected model is the final candidate for this benchmark version.
5. **Test once:**
   - the selected candidate on the r2 test → `runs/<name>_TEST.txt`, logged in the test-use table;
   - the same candidate, plus frozen v1 as the deployed baseline, once each on the external BD test (`external_tests/bd_speedbreaker_v2_orig87`), with the caveat above.
6. **Run S1/S2: seeds 1 and 2 of the Run A config** (`v3a_r2_11n_960_s1`, `_s2`).
   - **Hypothesis H-seed:** the val mAP50 seed std of this config is ≥0.01. If so, the v1-vs-Run-A val difference must exceed about 2×std before it is called real. Without this, no single-seed comparison in this project can be interpreted.
   - Cost: ≈2×4–5 GPU-hours. Val only; no extra test use, except the one test of the final candidate if the selection changes.
7. **Latency benchmark** p50/p95/p99, hazard + COCO models on the same frames (GPU idle between trainings).
8. **Failure analysis on val** (FP/FN by size, source, bump type). Test is never used for this.

## Stage 3 — Run A finished, verify, val comparison (2026-10-31 21:40–21:50)
- **Run A finished — VERIFIED.** It stopped early at epoch 100 of 150 (patience 30). `results.csv` has 100 rows.
  - `best.pt` is the **epoch 70** checkpoint (`train_metrics` inside `best.pt`): P 0.75858, R 0.55634, mAP50 0.66282, mAP50-95 0.30427, fitness 0.30427.
  - Ultralytics 8.4.192 uses **fitness = mAP50-95 alone**. The highest mAP50 in training was 0.68295 at epoch 98 (`results.csv`), but that epoch was not selected. mAP50 was still rising slowly when training stopped.
  - Note for later runs: with this fitness, patience 30 can stop a run that is still improving in mAP50. This is not changed for S1/S2, because they must use the same config as Run A.
- **Strict verify of r2 — VERIFIED PASS.** `review/clean_r2/verify_r2_strict.txt`:
  - "mode=strict: 0 errors, 1 warnings -> PASS [near-duplicate check SKIPPED]". The warning is the 3,867 Ultralytics cache files, which the verifier ignores.
  - Counts: train 3,035 images (pothole 2,570 / bump 1,404 boxes, 703 empty); val 830 (691 / 378, 10 empty); test 323 (285 / 160, 0 empty). This closes the step-2 gap from Stage 1.
- **Corrected val (road_hazards_v3a_r2, 830 images, 1,069 boxes) — VERIFIED:**

| Model | File | all P | all R | all mAP50 | all mAP50-95 | pothole mAP50 / 50-95 | speed_bump mAP50 / 50-95 |
|---|---|---|---|---|---|---|---|
| v1 `v3a_r1_11n_960_s0` (r1 labels) | `runs/v3a_r1_11n_VAL_on_r2.txt` | 0.695 | 0.620 | 0.671 | 0.303 | 0.629 / 0.259 | 0.712 / 0.347 |
| Run A `v3a_r2_11n_960_s0` (r2 labels) | `runs/v3a_r2_11n_VAL.txt` | 0.753 | 0.558 | 0.665 | 0.305 | 0.606 / 0.253 | 0.723 / 0.356 |

  The Stage 1 UNRESOLVED item (v1 on the corrected val) is now resolved: the row above, from `runs/v3a_r1_11n_VAL_on_r2.txt`.
- **Reading (val only):**
  - The two models are **tied**: Δ mAP50 −0.006, Δ mAP50-95 +0.002.
  - Run A is better on speed_bump (+0.011 / +0.009) and worse on pothole (−0.023 / −0.006). It has higher precision and lower recall at its max-F1 point.
  - With one seed each, none of these differences can be called real; H-seed (S1/S2) is what will size the noise. So the label correction did **not** give a measurable val gain. It did make the val/train labels consistent with D1–D6.
  - Both models selected their best epoch on (nearly) this same val, so the comparison is fair in that respect.
- **Selection (decided here, BEFORE any test use): final candidate for benchmark r2 = Run A `v3a_r2_11n_960_s0/weights/best.pt`.** Reasons:
  1. The val metrics are tied, and Run A is ≥ v1 on the primary metric (mAP50-95, Ultralytics fitness).
  2. It is trained on labels that follow the agreed ontology D1–D6, while v1 learned from labels later found wrong.
  3. It is better on speed_bump, the weaker class on the r1 test.

  S1/S2 are for **variance only**. They will **not** replace the candidate, so there is no best-of-N selection on val and no second test use on r2.

## Stage 4 — one-time test uses and the start of H-seed (2026-10-31 21:47–21:55)
- **Internal r2 test, Run A (test use #1) — VERIFIED.** `runs/v3a_r2_11n_960_s0_TEST.txt`, 323 images, 445 boxes:

| class | P | R | mAP50 | mAP50-95 |
|---|---|---|---|---|
| all | 0.505 | 0.453 | **0.462** | 0.189 |
| pothole | 0.549 | 0.681 | 0.631 | 0.269 |
| speed_bump | 0.461 | 0.225 | **0.294** | 0.108 |

  - **Context, not a comparison claim:** v1 on the r1 test gave all 0.507, pothole 0.660, bump 0.354 (handoff / `runs/v3a_r1_RESULTS.csv`).
    - The r1 and r2 tests differ by 1 image (`build_info.json`: test_image_dropped). Without seed variance, a −0.045 difference cannot be attributed to the label fix.
    - v1 is **not** re-tested on r2 (handoff rule). Nothing is chosen or tuned on these numbers.
  - **Main finding:** the speed_bump val→test gap is large. Val bump mAP50 is 0.723 (`runs/v3a_r2_11n_VAL.txt`); test is 0.294 with recall 0.225. The sequence-aware split puts unseen scenes/videos in test, so bumps generalise poorly to new scenes. Potholes hold up (0.606 val → 0.631 test).
- **External BD87 test (uses #2 and #3) — VERIFIED.** 87 images, 88 speed_bump boxes. Caveat from Stage 2: independent annotation, partly-seen locations.

| Model | File | P | R | mAP50 | mAP50-95 |
|---|---|---|---|---|---|
| Run A | `runs/EXT_bd87_v3a_r2_11n_960_s0_b.txt` | 0.531 | 0.318 | **0.367** | 0.127 |
| v1 | `runs/EXT_bd87_v3a_r1_11n_960_s0_b.txt` | 0.406 | 0.397 | **0.328** | 0.117 |

  - This agrees with the internal test: out of the training scenes, speed_bump mAP50 is about 0.3–0.37, against about 0.72 on val.
  - 88 boxes is a small sample, so the Run A vs v1 difference (+0.039) is within noise.
- **Fix during this stage:**
  - `external_tests/bd_speedbreaker_v2_orig87/data.yaml` had no `train:` key, which Ultralytics requires. The dataset folder was **not** edited, so its checksums stay valid. A new eval-only wrapper `external_tests/bd_speedbreaker_v2_orig87_eval.yaml` was added instead.
  - `tools/build_external_test.py` now writes the `train:` key for future builds.
  - Side effect: Ultralytics writes `labels/test.cache` inside the external folder. This is a derived cache, which the verifier ignores.
- **Failure-analysis input (val only):** `runs/detect/v3a_r2_11n_VAL_json/predictions.json`, from `runs/v3a_r2_11n_VAL_json.txt`. It reproduces all mAP50 0.665 exactly, so evaluation is deterministic.
- **H-seed started — RUNNING.**
  - `run_r2_seeds.bat` runs seed 1, then seed 2, one after the other, with the same config as Run A. Each run is followed by a val-only eval → `runs/v3a_r2_11n_960_s{1,2}_VAL.txt`.
  - The first launch failed without training: cmd could not find the bat by its bare name. Its log is `runs/v3a_r2_seeds.log`; nothing was created under `runs/detect`.
  - The relaunch with the full path started seed 1 at 21:53:41 (`runs/v3a_r2_seeds_run.log`). Run A took 13,077 s (`results.csv`), so expect roughly 7–8 h for both seeds.
  - No test use is planned for these runs.
- **What this means for the project (PROVISIONAL, waiting for H-seed):**
  - The bottleneck is **speed_bump generalisation to new scenes**, not label noise. The label fix did not move val.
  - The highest-value next step is **more varied bump data**: EGY_PDD, plus a manual relabel of qubo and the ≈185 sub5 originals. It is not more training of the same data.
  - Every new source goes to train only, or to a separate external test (rule 4).

## Stage 5 — failure analysis of Run A on val (2026-10-31 ~22:10, CPU only, test never used)
Tool: `tools/failure_analysis.py`. Output: `review/clean_r2/failure_val_runA/` (`summary.json`, `per_image.csv`, `sheets/fn_speed_bump.jpg`, `fn_pothole.jpg`, `fp_background.jpg`). Log: `review/clean_r2/failure_val_runA_run2.log`; the first attempt crashed before writing anything, see `failure_val_runA.log`.
Operating point: conf ≥ 0.35. This is `perception/config.yaml` fsm.hazard_min_conf, read only and not changed. Matching is at IoU ≥ 0.5. The GT totals match the verifier (691 / 378).
- **Totals — VERIFIED (`summary.json`):**
  - pothole: TP 364, FN 327, FP 154 → R 0.527, P 0.703;
  - speed_bump: TP 210, FN 168, FP 24 → R 0.556, P 0.897.
  - Bump precision is high and recall is the problem.
  - FP types: pothole background 67, localization 68, duplicate 19; bump background 3, localization 11, duplicate 10; 0 wrong-class.
  - Note: the per-size "precision 1.0" rows in `by_size` are an artefact, because FPs are not assigned a size. Only recall is meaningful there.
- **The misses are concentrated in a few scenes — VERIFIED (`top_fn_groups` and `per_image.csv`).** 830 images, 1,069 GT boxes:
  - `r1g2418`: 89 images, 91 GT, TP 12, **77 bump FN**. Egyptian windscreen dashcam (`623_jpg…`).
  - `r1g589`: 75 images, 75 GT, TP 11, **64 bump FN**. Same type of Egyptian dashcam footage.
  - Together these two groups are **141 of the 168 bump misses**. Sheet `fn_speed_bump.jpg`: low-contrast unmarked humps across Egyptian city streets, often barely visible in a single frame.
  - `r1g1132`: 132 images, 264 GT, TP 139, **124 pothole FN**. GoPro fisheye dashcam (`G00xxxxx`); `r1g939` (same series) adds 26 more.
  - Sheet `fn_pothole.jpg`: mostly **many small, far-away potholes** (5–15 m ahead). Pothole size breakdown: tiny bucket recall 0.555, with 198 of the 327 pothole FN.
- **Reading (PROVISIONAL):**
  1. **Speed_bump recall fails on exactly the deployment domain**: unmarked Egyptian street humps seen from a dashcam. Marked or painted bumps elsewhere are mostly found. This matches the low test (0.294) and BD87 (0.367) bump numbers. More training on the same data will not fix it.
  2. Many pothole misses are far-field and tiny. They matter less for a slow pod whose FSM acts at ≤2 m (`range_warn_m: 2.0`), so val mAP understates near-range usefulness.
     - A near-range metric (GT boxes whose bottom edge is in the lower part of the frame) would measure what the FSM uses. This is a reporting change, not a threshold change.
  3. Also to check visually: some bump GT boxes in `r1g2418` / `r1g589` cover road with no visible hump in that frame. Part of this "miss" may be label ambiguity.
- **Next steps, ranked:**
  - (a) Get varied **Egyptian unmarked-hump** data: EGY_PDD, plus a relabel of qubo / sub5 originals. Train only, never internal val/test.
  - (b) Owner review of 30 `r1g2418` / `r1g589` frames: is a hump visible? If not, the label must be fixed in a new version r3, never in place.
  - (c) After H-seed: add a near-range recall metric to reporting.
  - (d) Latency benchmark when the GPU is idle after S2.

## Stage 6 — H-seed result, a double-training incident, and latency (2026-11-01 ~04:00)
### Incident: two s1 trainings ran at the same time on one folder (31 Oct 23:05 to ~23:31) — VERIFIED
- At 23:03 someone outside this agent's process edited `run_r2_seeds.bat` (its new comment says: "seed 1 was interrupted at epoch 30 (window closed)") and started `yolo train resume` on `v3a_r2_11n_960_s1` at 23:05.
- **The original s1 was NOT interrupted.** It was running in the background and had no window. Evidence:
  - `runs/v3a_r2_seeds_run.log` shows one s1 start and EarlyStopping at epoch 89 / 119 epochs (3.332 h).
  - `results.csv` time column of the original run rises without a break to 11,996 s.
- So **two trainings ran at once** (against the one-at-a-time rule).
- s1 `results.csv` has **122 rows for 119 epochs**: three extra rows (epochs 30–32, time 628–1,551 s) come from the resume process, which then stopped. `args.yaml` (23:05) and `labels.jpg` were rewritten by that resume.
- Effect on the result: none found.
  - The original process keeps its model in memory and wrote `best.pt` at 00:45 (epoch 89) and `last.pt` at 01:14, after the resume process had stopped.
  - `best.pt` `train_metrics` (P 0.71821, R 0.63637, mAP50 0.68519, mAP50-95 0.30695) match exactly the original-run row of epoch 89 in `results.csv` (time 10,210 s).
  - **s1 is therefore kept as valid, with this note.** Its `args.yaml` is not the original; the original arguments are printed at the top of `runs/v3a_r2_seeds_run.log` (seed=1, same config as Run A).
- Side effects:
  - The bat being edited while cmd was running it caused the final "'overwrite' is not recognized" line and exit code 1. This came after both seeds and both val evals had finished.
  - The edited bat now skips seeds that have a `_VAL.txt`, so running it again does nothing. Left as is.
- **Lesson:** do not start or resume a training without first checking the process list (`Get-Process yolo,python`) and the `results.csv` time stamp.

### H-seed — CONFIRMED (VERIFIED, `runs/v3a_r2_seed_summary.txt`)
- s2: EarlyStopping, best epoch 113 of 143 (`runs/v3a_r2_seeds_run.log`); `best.pt` train_metrics mAP50 0.67119 / mAP50-95 0.2999.
- Val (`runs/v3a_r2_11n_VAL.txt`, `runs/v3a_r2_11n_960_s1_VAL.txt`, `runs/v3a_r2_11n_960_s2_VAL.txt`):

| metric (val) | s0 | s1 | s2 | mean | std (n−1) | v1 | v1 − mean |
|---|---|---|---|---|---|---|---|
| all mAP50 | 0.665 | 0.686 | 0.673 | 0.6747 | **0.0106** | 0.671 | −0.0037 |
| all mAP50-95 | 0.305 | 0.308 | 0.300 | 0.3043 | 0.0040 | 0.303 | −0.0013 |
| pothole mAP50 | 0.606 | 0.634 | 0.628 | 0.6227 | 0.0147 | 0.629 | +0.0063 |
| speed_bump mAP50 | 0.723 | 0.739 | 0.717 | 0.7263 | 0.0114 | 0.712 | −0.0143 |
| speed_bump R | 0.571 | 0.688 | 0.664 | 0.6410 | 0.0618 | 0.624 | −0.0170 |

- **H-seed holds:** the seed std of val mAP50 is 0.0106 (≥ 0.01). A single-seed difference therefore needs about **> 0.02** to be called real.
- **v1 vs the Run A config: no measurable difference.**
  - v1 lies inside the seed range on every mAP row.
  - The largest gap is speed_bump mAP50, −0.014 ≈ 1.3 std, which is not significant.
  - So the r2 label correction gave no measurable val change. Its value is label consistency with D1–D6, not a metric gain.
- s0 (the selected r2 candidate) is the lowest of the three seeds on val mAP50. As pre-registered in Stage 3, the candidate is **not** replaced (no best-of-N on val) and **no** new test use is made.
  - The one r2 test number (0.462) is a single-seed value. Its seed spread is likely of the same order as on val, about ±0.01–0.02. This is PROVISIONAL: it is inferred from val and test was not re-run.

### Latency — VERIFIED (`runs/latency_2026-11-01.json`, `tools/latency_bench.py`)
- Setup:
  - 300 r2 **val** images (sizes vary from 350×263 to 1920×750), 20 warm-up frames, batch 1, fp32.
  - Settings read from `perception/config.yaml` and not changed: hazard imgsz 960 / conf 0.25; COCO imgsz 640 / conf 0.35.
  - Device: the dev laptop RTX 5050, **not pod hardware**.
- Times include pre- and post-processing (`NamespacedDetector.predict`):

| model | p50 ms | p95 ms | p99 ms | max ms |
|---|---|---|---|---|
| COCO yolo11n | 17.42 | 25.04 | 59.83 | 68.33 |
| hazard Run A | 18.10 | 26.85 | 60.71 | 76.13 |
| hazard v1 | 18.09 | 24.89 | 27.19 | 34.76 |
| pipeline Run A + COCO | 35.80 | 47.42 | 50.35 | 54.35 |
| pipeline v1 + COCO | 35.48 | 45.73 | 50.68 | 52.84 |

- Run A and v1 are the same architecture, so the same speed is expected and seen (p50 18.1 ms each).
- The first two models' p99 of about 60 ms are probably warm-up or OS jitter: the later runs on the same frames do not show them. This is PROVISIONAL.
- The full pipeline runs at about **36 ms/frame p50 (≈ 28 FPS)** and 47 ms p95 on this laptop. It must be measured again on the pod's own computer.

### Where the project stands (after Stage 6)
- The Run A config ≈ v1 on val. One-time numbers for the r2 benchmark are recorded, and seed noise is now known.
- **No more training on the current data is justified.** No hypothesis predicts a gain greater than 0.02 from same-data changes.
- The open bottleneck is still Egyptian unmarked speed bumps (Stage 5). Next steps need **new data or owner input**:
  - EGY_PDD email;
  - owner review of `r1g2418` / `r1g589` bump boxes;
  - qubo / sub5 relabel.
- Optional low-cost next items:
  - add a near-range recall metric to reporting;
  - measure latency on the pod computer.

# PHASE "target ≥ 0.90" (prompt `PROMPT_target90.md`, 2026-11-02; deadline ~8 Nov)

## Stage 7 — plan, metric definitions and expected gains (written 2026-11-02, before any new measurement)
### 7.1 Environment facts (checked 2026-11-02)
- No Kaggle token: `%USERPROFILE%\.kaggle\kaggle.json` is absent, and no Kaggle env var is set.
- `ROBOFLOW_API_KEY` is **not set** at User, Machine or Process level.
- So downloads use public URLs only: Kaggle's public dataset download endpoint, Zenodo, Mendeley, Figshare, Hugging Face and GitHub. A source that needs a login is marked BLOCKED in `review/new_data_r3/CANDIDATES.md`.
- Disk C: 130 GB free. No GPU job running.
- Throughput, from Run A `results.csv`: 3,035 train + 830 val images ≈ 130 s/epoch at imgsz 960, batch 8, YOLO11n. That is ≈ **26 train img/s ≈ 90k image-epochs per hour**.
  - A 3.5 h budget ≈ 300k image-epochs. That is ~3,000 images × 100 epochs, or ~7,500 images × 40 epochs.
  - YOLO11s is ≈ 2× slower, so at most ~4,000 images × 40 epochs in the same budget.

### 7.2 Metric definitions (fixed now; used unchanged everywhere)
Per class (pothole, speed_bump), never only the average:
- **P, R, F1, mAP50, mAP50-95.** P, R and F1 are given at the per-class operating threshold below; the mAPs come from the same predictions (COCO-style 101-point interpolation, computed by our tool so all models are scored the same way).
- **Operating threshold:** for each model and class, the confidence that maximises F1 on **val**. The same threshold is then used on test.
  - The deployed config value (conf 0.35, `perception/config.yaml`) is also reported as a second row.
- **Box-level Accuracy** = TP / (TP + FP + FN), at the operating threshold, IoU ≥ 0.5, per class.
- **Image-level Accuracy** (per class c) = share of evaluated images where "c present" (≥ 1 GT box of c) equals "c predicted" (≥ 1 prediction of c at the operating threshold).
  - Reported only on evaluation sets that contain hazard-free images. The current r2 val has only 10 empty images (`verify_r2_strict.txt`), so on r2 it is reported **with that caveat**.
  - The new val parts will include hazard-free frames.
- **Pre-registered alternative metrics** (defined now, values not looked at yet):
  - **A1 near-range recall** (per class): recall at the operating threshold over GT boxes whose bottom edge is in the lower 40 % of the frame (y2 ≥ 0.60·H) and whose sqrt(area fraction) ≥ 0.05. Rationale: a forward camera sees the road within a few metres in the lower part of the frame. The FSM acts at ≤ 2 m (`range_warn_m`).
  - **A2 image-level Accuracy** (as above), on evaluation sets with hazard-free frames.
  - **A3 precision at recall 0.50** (per class), read from the val PR curve.
- **The 0.90 claim counts only for** per-class mAP50 or the pre-registered A1–A3, on a leak-free, sequence-aware evaluation set. It does not count if it came from test tuning, dropped hard images or a random frame split.

### 7.3 Steps, in order, with expected gain (honest estimates, PROVISIONAL)
| # | Step | Cost | Expected effect (val mAP50) |
|---|---|---|---|
| 1 | `tools/metrics_report.py`: re-score v1 and Run A s0/s1/s2 on r2 val per class with all metrics above (val predictions only) | CPU + 4 short val runs | 0 (measurement). Gives the baseline table |
| 2 | Wide data search (Kaggle first) → `review/new_data_r3/CANDIDATES.md`, with re-upload detection | hours, no GPU | enables steps 3–5 |
| 3 | **Part A = potholes at scale**: RDD2022 Japan + India D40 (already extracted), filtered by D5/FAR_TINY and box size, capped per source, near-dups vs r2 removed, train only. Plus other large documented pothole sets found in step 2 | build only | pothole **+0.00 to +0.05**: val is rf8/ghpot dashcam, while RDD is a different camera/region |
| 4 | **Part B = speed bumps**: new independent forward-view bump sets that pass validation. Train + their own sequence-aware val/test split, never the frozen r2 test | build only | bump on r2 val **+0.00 to +0.04**. The main hope is new-scene recall (Egyptian dashcam groups), measured per subset |
| 5 | **Part N = hard negatives**: hazard-free road frames and crosswalk/manhole/patch frames → train background, plus a held-out negative subset for the new val/test | build only | precision **+0.01 to +0.03**; makes image-level Accuracy measurable |
| 6 | Label fixes from the val FP review (missing pothole boxes) → corrections file → new version `v3b_*`. Old versions untouched | review + build | pothole P **+0.01 to +0.03** (val only; measurement-correctness, not a model gain) |
| 7 | Training (one GPU job at a time, ≤ 3.5 h each): r2 + A; then + B (+N); a step is kept only if val improves by more than 2× seed std (0.02) or is positive on the target subset | 3–4 runs | as rows 3–5 |
| 8 | Single-class vs 2-class (pothole-only, bump-only, same data/settings) | 2 runs | ±0.02 (literature: little difference at this scale) |
| 9 | Model size YOLO11s (and 11m only if pipeline p50 ≤ 50 ms) | 1–2 runs | **+0.02 to +0.05** |
| 10 | imgsz 1280 or P2 head for small/far targets | 1 run | +0.00 to +0.03 (mainly tiny potholes) |
| 11 | Final: frozen r2 test and BD87 **once** per final candidate; package `supervisor_2026-11-08/` | short | — |

**Honest prior:**
- The best combination of the steps above might take val mAP50 from 0.675 (`runs/v3a_r2_seed_summary.txt`) to about 0.72–0.78.
- Per-class mAP50 ≥ 0.90 on a leak-free, sequence-aware set by 8 Nov is **very unlikely**, because:
  - test is 0.462 with bump 0.294 (`runs/v3a_r2_11n_960_s0_TEST.txt`), so the val→test gap shows the limit is scene diversity, not fitting;
  - 141/168 missed val bumps come from two Egyptian dashcam groups (Stage 5).
- If 0.90 is not reached, the report will show which of A1–A3 reach it, using the definitions above.

## Stage 8 — baselines with the new metrics, data search started, GPU experiment S (2026-11-02 evening)
### 8.1 Per-class baseline (VERIFIED, `review/metrics_r3/val_r2_baselines/report.md`, tool `tools/metrics_report.py`)
- Check of the tool: our AP50 matches Ultralytics within 0.002. Example: v1 pothole 0.628 vs 0.629 in `runs/v3a_r1_11n_VAL_on_r2.txt`. Run A s0 at conf 0.35 gives P/R 0.703/0.527 (pothole) and 0.897/0.556 (bump), the same as Stage 5.
- r2 val, at the per-class argmax-F1 threshold:

| model | class | AP50 | P | R | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 |
|---|---|---|---|---|---|---|---|---|
| v1 | pothole | 0.628 | 0.664 | 0.616 | 0.470 | 0.914 (380) | 0.577 (142) | 0.771 |
| v1 | speed_bump | 0.710 | 0.712 | 0.653 | 0.517 | 0.880 (454) | 0.363 (157) | 0.836 |
| Run A s0 | pothole | 0.605 | 0.617 | 0.603 | 0.439 | 0.900 (380) | 0.563 (142) | 0.730 |
| Run A s0 | speed_bump | 0.725 | 0.864 | 0.571 | 0.524 | 0.823 (454) | 0.191 (157) | 0.950 |
| Run A s1 | pothole | 0.632 | 0.657 | 0.595 | 0.454 | 0.899 (380) | 0.613 (142) | 0.763 |
| Run A s1 | speed_bump | 0.736 | 0.791 | 0.683 | 0.578 | 0.894 (454) | 0.401 (157) | 0.908 |
| Run A s2 | pothole | 0.628 | 0.682 | 0.602 | 0.470 | 0.898 (380) | 0.577 (142) | 0.760 |
| Run A s2 | speed_bump | 0.715 | 0.749 | 0.656 | 0.538 | 0.886 (454) | 0.376 (157) | 0.883 |

- **Caveats:**
  - On r2 val, the "negatives" for ImgAcc are mostly images of the *other* class: only 10 images are hazard-free. So ImgAcc ≈ 0.88–0.91 here is **not yet** the pre-registered A2 number. A2 needs the new evaluation sets with hazard-free frames.
  - NearR (A1) for bumps is low: 0.19–0.40. The near bumps that are missed are in the Egyptian dashcam groups (Stage 5).
  - P@R50 (A3) is the only metric already near 0.9 (bump 0.88–0.95). It is not claimed as "the 0.90" until it is measured on the final candidate with the frozen thresholds.

### 8.2 Data access facts (VERIFIED by request results)
- **Kaggle:** the public listing API works without login, so a candidate list was made (`review/new_data_r3/CANDIDATES.md`). Downloads return **HTTP 404 without a token** → **BLOCKED until Ahmed adds `%USERPROFILE%\.kaggle\kaggle.json`**.
- **Roboflow:** no API key on this machine → BLOCKED.
- **Zenodo:** the server gives about 5–40 KB/s per connection and limits the request rate.
  - Instead of the full 13.2 GB RSID zip, `tools/remote_zip.py` reads the central directory and fetches only chosen members in contiguous blocks.
  - The partial full-zip download (2.4 MB) is left in `GP36_Dataset/_downloads/zenodo_18789662_RSID/` and not used.
- **Figshare:** ≈ 3 MB/s, but the connection resets. It is resumed with `curl -C -`.

### 8.3 GPU experiment S (model size) — hypothesis written before the run
- **H-size:** YOLO11s with exactly the Run A config raises r2-val mAP50 by ≥ 0.02 over the YOLO11n 3-seed mean 0.6747 (`runs/v3a_r2_seed_summary.txt`).
  - Config: data r2, imgsz 960, batch 8, workers 2, cache disk, epochs 150, patience 30, seed 0, deterministic.
  - Literature and Ultralytics COCO tables suggest about +0.02–0.05 for n→s.
- Run name `v3a_r2_11s_960_s0`. Weights: `yolo11s.pt` downloaded from huggingface.co/Ultralytics/YOLO11, SHA-256 `85a76fe8…502d5`, 9.46 M params.
- Why now: the GPU is idle while the data downloads run. The model-size effect will later be re-checked on the new data version.
- Budget check: if one epoch takes > 200 s (≈ 8 h for 150 epochs), the run is stopped and noted. A stopped run is kept, not deleted.

## Stage 9 — data parts r3 (2026-11-02 night)
Tools:
- `tools/remote_zip.py`: range-reads a remote zip, fetches contiguous blocks in parallel; `records/…?download=1` with 16 connections reaches ≈ 1–4 MB/s.
- `tools/select_rsid.py`, `tools/make_items_r3.py`, `tools/build_part.py`.
- `tools/build_v3b.py`: base r2 (val/test frozen) + part TRAIN splits, hard-linked, strict verify.

All parts pass these gates in `build_part.py`:
- class map by id with explicit `ignore`;
- FAR_TINY: sqrt(w·h) < 0.02 → box removed; an image whose hazard boxes are all removed is dropped;
- EXIF rotation check;
- leakage guard vs r2 (all splits; exact + dihedral dHash ≤ 4 & pHash ≤ 10), cache `review/new_data_r3/r2_hashes.npz`;
- train vs held-out near-dups inside the part.

| part | source | train | val | test | notes (VERIFIED: `parts_r3/<part>/build_info.json`) |
|---|---|---|---|---|---|
| `rdd_ji` | RDD2022 Japan + India D40 | 2,920 img / 5,428 pothole boxes | — | — | 2 FAR_TINY boxes removed; 3,791 crack/manhole/repair boxes ignored (D5); 0 leak hits |
| `rdd_cz` | RDD2022 Czech D40 | — | — | 154 img / 197 pothole | unseen-country external test; 0 leak hits |
| `bucko` | Bučko et al. 2022, Slovakia dashcam | 282 (103 neg) / 357 pothole | 125 (42 neg) / 186 | 120 (23 neg) / 232 | group = location (Ca, Pd → train; Pr → val/test). Every 4th frame. 4 images only_far_tiny |

- **Bučko class 1 (442 boxes, not in its README) is mapped to `ignore`: PROVISIONAL.**
  - The visual check `review/new_data_r3/bucko_class1_check.jpg` shows it on manhole covers (clear case: `Vid_1_Ca_00000081`), so D5 → background.
  - Some blue boxes in the rain videos are unclear, and the labels file is kept, so this can be revisited.
- **`rsid`: Zenodo RSID, VGTU Vilnius.**
  - Selection: `review/new_data_r3/rsid_selection_v2.csv`. Dashcam clips are grouped by recording day, Vilnius drives by sequence, and ZED by session.
  - Families excluded: GoPro `G00…` (5,215 images, the same family as r2 val/test) and the random-name "other" (235, unknown provenance).
  - Up to 4 frames per hazard run, plus hard negatives (manhole-only and empty frames ≥ 60 frames away from any hazard).
  - Planned counts: train 776 (425 bump boxes, 210 manhole-only + 108 empty negatives), val 253 (140 bump), test 235 (142 bump).
  - Images are being fetched now.
- Pothole/bump balance: r2 train has 2,570 pothole and 1,404 bump boxes. Adding all of `rdd_ji` would make it about 6:1, so `rdd_ji` will be **capped** in the composed versions (prompt: near 1:1). Bumps are the scarce class; only RSID adds bumps (Kaggle/Roboflow are BLOCKED).
- **Val label issue noted but not fixed yet:** `review/clean_r2/failure_val_runA/sheets/fp_background.jpg` shows that many "background FPs" are real unlabelled potholes (e.g. `ghpot/pothole_100`, `rf8 64_JPG`, `rf8 49_JPG`). Others are D4 one-box-vs-many differences, and one is a true manhole FP (`rf8 13_JPG`).
  - Fixing val labels would change the benchmark (it needs a new version, and all models re-scored). It is planned only if time allows after the data runs. Until then, val **under-states** pothole precision.
- GPU: experiment S (`v3a_r2_11s_960_s0`) is running. Epochs 1–6 took 425, 196, …, 123 s, under the 200 s stop rule (`results.csv`).

## Stage 10 — hypotheses for the data runs (written before they start, 2026-11-03 ~00:00)
### Composition `road_hazards_v3b_A` (`tools/build_v3b.py`)
- Contents: r2 (all splits frozen) + `rsid` train + `bucko` train + `rdd_ji` train capped at **500** images (seed 0).
- Why the cap is 500: bumps can only come from RSID (~425 boxes). With the cap, train pothole:bump stays ≈ 2:1 (r2 alone is 1.8:1), instead of ~4.5:1 with all of RDD.
- Expected train size: ≈ 4,600 images.

### Run D1 `v3b_A_11n_960_s0`
- Config: yolo11n.pt, imgsz 960, batch 8, workers 2, cache disk, seed 0, deterministic, **epochs 70, patience 20**.
- Why 70 epochs: at ≈ 4,600 images an epoch is ≈ 200 s, so 150 epochs would be ≈ 8 h, over the 3–4 h budget. Run A's own best epoch was 70 (Stage 3).
- Confound, stated: the epoch budget differs from Run A (150 with early stop). If D1 shows no gain, this run cannot separate "no data effect" from "fewer epochs".
- **H-D1a (no harm):** r2-val mAP50 ≥ 0.654, i.e. Run A seed mean 0.6747 − 2·0.0106 (`runs/v3a_r2_seed_summary.txt`).
- **H-D1b (bump transfer):** on the RSID part-val (held-out sequences/days), speed_bump AP50 rises by ≥ 0.10 over Run A s0.
- **H-D1c (pothole transfer):** on the Bučko part-val (location Pr, night/evening included), pothole AP50 rises by ≥ 0.05 over Run A s0.
- Selection rule: D1 replaces Run A as the candidate only if H-D1a holds, plus H-D1b or H-D1c. Test sets are not touched.

### COCO classes on road images
- Labelled road images available on disk: the BDD100k subset of `yolo-automotive-dataset` (2,902 images).
- Its class ids were inferred by matching yolo11n COCO predictions on 300 images (CPU): id 0 = vehicle (car 1,055 / truck 59 / bus 27 of 1,225 matched), id 24 = person (121 of 155). Ids 1–4 are traffic lights and 23 signs.
- So per-class road numbers are possible only for **person** and **vehicle (car+truck+bus merged)**. Tool: `tools/coco_road_eval.py`.
- Bicycle, motorcycle and dog: only the COCO-benchmark figure exists (stated as such).

### 10.1 COCO detector per class on road images — VERIFIED (`runs/coco_road_eval_bdd/report.json`, log `runs/coco_road_eval_bdd.txt`)
Setup: 1,451 BDD100k road images (yolo-automotive-dataset); yolo11n COCO with the `perception/config.yaml` settings (imgsz 640); CPU.

| class | n_gt | AP50 | P / R @ deployed conf 0.35 | P / R @ F1-opt (thr) | BoxAcc @0.35 |
|---|---|---|---|---|---|
| vehicle (car+truck+bus) | 6,110 | **0.880** | 0.754 / 0.866 | 0.846 / 0.799 (0.455) | 0.675 |
| person | 632 | **0.705** | 0.678 / 0.704 | 0.744 / 0.672 (0.399) | 0.528 |

- Caveat: we do not know how completely this subset labels small or far objects. Unlabelled far cars would count as FP, so precision may be understated.
- Bicycle, motorcycle and dog: no road labels → only the COCO benchmark figure applies.

## Stage 11 — experiment S crashed, parts done, v3b_A built, D1 started (2026-11-03 ~01:00)
- **Experiment S (`v3a_r2_11s_960_s0`) CRASHED at epoch 15.**
  - Error: `cv2.resize SystemError` in the dataloader (`runs/v3a_r2_11s_960_s0_train.log`) = RAM exhausted.
  - Cause: my concurrent CPU/RAM jobs (part building with full-resolution hashing, the COCO CPU eval, downloads). Free RAM had been 0.65 GB.
  - Its `best.pt` is an early epoch (r2 val mAP50 0.415, `runs/v3a_r2_11s_960_s0_VAL_json.txt`). It is **not a result** and is kept only as a record.
  - Decision: H-size will be re-tested later on the final data version, not resumed on r2. Data comes first (prompt §5).
  - **Rule from now on:** no heavy CPU/RAM job while a training runs.
- **Part `rsid` built — VERIFIED (`parts_r3/rsid/build_info.json`).**
  - train 773 (318 neg; 421 bump, 76 pothole boxes); val 252 (81 neg; 140 bump, 42 pothole); test 234 (72 neg; 141 bump, 30 pothole).
  - 0 leakage hits vs r2; 5 images only_far_tiny; 787 manhole boxes ignored.
  - Visual check `review/new_data_r3/rsid_bump_check.jpg`: RSID bump boxes include **zebra crossings** (e.g. `rsid__c0005f…`, `rsid__57eadbf…`), very likely raised crossings (D2 = speed_bump). A raised profile cannot be confirmed from one frame. **D1-conflict risk, PROVISIONAL**; it is watched through r2-val bump precision.
  - It also has unmarked low-contrast humps (e.g. `rsid__e38d039…`), the same kind we miss in Egypt.
- **Run A and v1 on the part vals (pre-D1 baselines) — VERIFIED (`review/metrics_r3/partval_{rsid,bucko}_baselines/report.md`):**
  - RSID val speed_bump AP50: v1 0.028, Run A **0.035**. Run A recall at conf 0.35 ≈ 0.11 (`runs/PARTVAL_rsid_runA_s0.txt`). **The current models do not transfer to new-country bumps at all.**
    - Part of this may be the ontology difference above: RSID zebra/raised crossings vs our D1 background.
  - Bučko val pothole AP50: v1 0.399, Run A 0.422.
- **`road_hazards_v3b_A` — VERIFIED (`road_hazards_v3b_A/build_info.json`):**
  - Contents: r2 + rsid + bucko + rdd_ji:500, hard-linked; strict verify PASS, 0 warnings; fingerprint `f4abed4b…3d3`.
  - Train: 4,590 images, 3,930 pothole / 1,825 bump boxes (2.15 : 1), 1,124 negatives. Val/test = r2 (frozen).
- **D1 `v3b_A_11n_960_s0` started** (hypotheses in Stage 10). After training it is evaluated on r2 val and both part vals (val only).

## Stage 12 — queue after D1 (hypotheses written 2026-11-03 ~01:30, before any of these runs)
- D1 speed: epoch 1 271 s, epoch 2 at 384 s, so ≈ 113 s/epoch (`runs/detect/v3b_A_11n_960_s0/results.csv`); 70 epochs ≈ 2.3 h.
- The queue below runs strictly one job at a time (`run_r3_queue1.bat`, log `runs/r3_queue1.log`). It starts only after D1 and its evaluations have finished.
- Every queued run uses the D1 settings: data v3b_A, imgsz 960, batch 8, workers 2, cache disk, seed 0, deterministic, epochs 70, patience 20.
- Every queued run is then evaluated, val only, with `save_json`, on r2 val, the rsid part-val and the bucko part-val.

| run | change vs D1 (one thing) | hypothesis (val only) |
|---|---|---|
| `v3b_A_11n_960_bumponly_s0` | `classes=[1]` (single-class speed-bump model; potholes become background) | **H-1cls-bump:** r2-val speed_bump AP50 ≥ D1's + 0.02 (2 × seed std of bump AP50 ≈ 0.011) |
| `v3b_A_11n_960_potonly_s0` | `classes=[0]` (single-class pothole model) | **H-1cls-pot:** r2-val pothole AP50 ≥ D1's + 0.02 (pothole seed std 0.015 → this is within noise unless ≥ 0.03) |
| `v3b_A_11s_960_s0` | YOLO11s instead of YOLO11n | **H-size:** r2-val mAP50 (all) ≥ D1's + 0.02; pipeline p50 must stay ≤ 50 ms (measured afterwards with `tools/latency_bench.py`) |

- Selection after the queue (val only):
  - per class, the best of {2-class D1, single-class, 11s}, if its gain exceeds the stated noise;
  - otherwise the simpler model (2-class 11n) is kept.
- Test sets are used once, only for the final candidate(s), at the end.
- Queue launch note: the first launch (`runs/r3_queue1.log`) spun without waiting, because Git's coreutils `timeout` shadowed the Windows one inside cmd. It was stopped after a few seconds; no run was started. The relaunch uses `ping` as the sleep (`runs/r3_queue1_run2.log`).

## Stage 13 — D1 result (VERIFIED, 2026-11-03 ~01:20)
- D1 `v3b_A_11n_960_s0`: all 70 epochs ran, 1.948 h (`runs/v3b_A_11n_960_s0_train.log`). No early stop: the last epoch is ≤ 70.
- Ultralytics val numbers (files named per row):

| eval set (val only) | Run A s0 | D1 | file (D1) |
|---|---|---|---|
| r2 val, all mAP50 / mAP50-95 | 0.665 / 0.305 | **0.655** / 0.289 | `runs/v3b_A_11n_960_s0_VALr2_json.txt` |
| r2 val, pothole AP50 | 0.606 | 0.597 | same |
| r2 val, speed_bump AP50 | 0.723 | 0.712 | same |
| RSID part-val, speed_bump AP50 | 0.035 | **0.663** | `runs/PARTVAL_rsid_v3bA_s0.txt` |
| RSID part-val, pothole AP50 | 0.047 | 0.257 | same |
| Bučko part-val, pothole AP50 | 0.421 | **0.572** | `runs/PARTVAL_bucko_v3bA_s0.txt` |

- Per-class with our metric tool (`review/metrics_r3/val_r2_D1/report.md`, `partval_rsid_D1`, `partval_bucko_D1`):
  - r2 val: D1 bump P/R at its F1-opt threshold is 0.727/0.619, vs Run A s0 0.864/0.571. Bump precision is lower, but Run A's own seeds span 0.749–0.864 (Stage 8.1), so this is not clearly outside noise.
  - Bučko val: ImgAcc pothole 0.848 (42 hazard-free images), NearR 0.688.
  - RSID val: bump ImgAcc 0.758 (116 images without a bump), bump NearR 0.544.
- **Hypotheses:**
  - **H-D1a holds narrowly:** 0.655 ≥ 0.654. r2 val does not change beyond seed noise.
  - **H-D1b holds:** bump on new-country held-out sequences 0.035 → 0.663.
  - **H-D1c holds:** pothole on a new-country held-out location incl. night/evening 0.421 → 0.572.
- **Selection (pre-registered rule, Stage 10): D1 becomes the current candidate.**
  - Meaning: adding curated new-country data leaves the old benchmark unchanged, within noise, and makes the model work on new countries where it previously failed.
  - Remaining caveats:
    1. D1 used 70 epochs vs Run A's 150 + early stop (confound stated in Stage 10).
    2. Single seed.
    3. The RSID bump labels include raised zebra crossings (D1/D2 ambiguity).
- The queue started at 01:18 with `v3b_A_11n_960_bumponly_s0` (`runs/r3_queue1_run2.log`).

## Stage 14 — single-class speed-bump model (VERIFIED, 2026-11-03 03:15)
- Run `v3b_A_11n_960_bumponly_s0` (`classes=[1]`): 70 epochs in 1.887 h (`runs/v3b_A_11n_960_bumponly_s0_train.log`).
- r2-val speed_bump AP50 **0.650** vs D1 2-class 0.712 (`runs/v3b_A_11n_960_bumponly_s0_VALr2_json.txt`).
- RSID part-val bump AP50 0.596 vs D1 0.663 (`runs/PARTVAL_rsid_v3b_A_11n_960_bumponly_s0.txt`).
- **H-1cls-bump REJECTED:** the single-class bump model is worse, by −0.06 on both sets, more than 2× the seed std. Keep the bump class in the 2-class model.

## Stage 15 — single-class pothole model (VERIFIED, 2026-11-03 04:41)
- Run `v3b_A_11n_960_potonly_s0` (`classes=[0]`): early stop at epoch 50, best at epoch 30, 1.376 h (`runs/v3b_A_11n_960_potonly_s0_train.log`).
- Pothole AP50 vs the D1 2-class model:

| eval set | single-class | D1 2-class | file (single-class) |
|---|---|---|---|
| r2 val | **0.554** | 0.597 | `runs/v3b_A_11n_960_potonly_s0_VALr2_json.txt` |
| Bučko part-val | 0.527 | 0.572 | `runs/PARTVAL_bucko_v3b_A_11n_960_potonly_s0.txt` |
| RSID part-val | 0.161 | 0.257 | `runs/PARTVAL_rsid_v3b_A_11n_960_potonly_s0.txt` |

- **H-1cls-pot REJECTED:** the single-class model is worse on all three sets.
- **Conclusion (Stages 14–15):** one 2-class model is better per class than two single-class models on the same data. It also needs only one hazard model in the live pipeline. The `perception/` setup stays as it is: 1 hazard model + 1 COCO model.
- Queue: `v3b_A_11s_960_s0` started at 04:41.

## Stage 16 — model size (YOLO11s) on v3b_A (VERIFIED, run finished 2026-11-03 07:33)
- Run `v3b_A_11s_960_s0`: 70 epochs in 2.803 h (`runs/v3b_A_11s_960_s0_train.log`).

| eval set (val) | D1 11n | 11s | Δ | file (11s) |
|---|---|---|---|---|
| r2 all mAP50 | 0.655 | 0.660 | +0.005 | `runs/v3b_A_11s_960_s0_VALr2_json.txt` |
| r2 pothole AP50 | 0.597 | 0.626 | +0.029 | same |
| r2 speed_bump AP50 | 0.712 | 0.694 | −0.018 | same |
| RSID bump AP50 | 0.663 | 0.638 | −0.025 | `runs/PARTVAL_rsid_v3b_A_11s_960_s0.txt` |
| Bučko pothole AP50 | 0.572 | 0.607 | +0.035 | `runs/PARTVAL_bucko_v3b_A_11s_960_s0.txt` |

- **H-size REJECTED** on its pre-registered criterion: all mAP50 +0.005 < +0.02.
  - Per class the signs differ: potholes about +0.03, bumps about −0.02. Each is within ≈ 2× seed std with one seed, so neither is established.
- **Latency on 2026-11-04 is NOT comparable with Stage 6** (`runs/latency_2026-11-04_11s.json`).
  - The same COCO model measured p50 95.7 ms today vs 17.4 ms on 1 Nov. The laptop was on mains, Balanced plan, GPU P4, but other apps (MATLAB, VM, browsers) were loading the CPU, and pre/post-processing runs on the CPU.
  - Only the ratio under identical conditions is used: hazard p50 11s 62.7 ms vs 11n 54.5 ms (+15 %).
  - Latency is re-measured for the final candidate on an idle machine.
- **Decision:** keep YOLO11n. It is simpler and faster, and the size gain is not shown.

## Stage 17 — queue 2 (hypotheses written 2026-11-04 ~13:50, before the runs)
- Both runs use the D1 settings unless stated. Each is followed by val-only evals (r2 val, rsid part-val, bucko part-val).
- Script `run_r3_queue2.bat`, log `runs/r3_queue2.log`.

| run | change vs D1 | hypothesis |
|---|---|---|
| `v3b_A_11n_960_s1` | seed 1 (variance of the D1 config) | **H-seed-D1:** r2-val mAP50 stays within 0.655 ± 0.021 (2 × Run A seed std), AND RSID bump AP50 ≥ 0.55, AND Bučko pothole AP50 ≥ 0.50. Confirms that the D1 gains are not a seed artefact |
| `v3b_A_11n_1280_s0` | imgsz 1280 (training and eval), batch 8 | **H-1280:** r2-val pothole AP50 ≥ D1 + 0.03 (many misses are tiny/far potholes, Stage 5) AND all mAP50 ≥ D1 − 0.01. The latency must then be checked: at 1280 the hazard model costs ≈ 1.8× |
- Queue 2 started 2026-11-04 13:44 (`runs/r3_queue2.log`).
  - Note: its "no yolo running" guard did not work, because Git's `find` shadowed the Windows one. Its first lines are `find: '/i': No such file or directory`. No yolo process was running at that time (checked just before with `Get-Process`), so no double training happened.
  - Future scripts must call `%SystemRoot%\System32\find.exe` explicitly. The same shadowing affected the second guard line in queue 1, where D1 had already finished.
- Per-class val reports for all candidates so far:
  - `review/metrics_r3/val_r2_all_2026-11-04/report.md`
  - `review/metrics_r3/partval_rsid_all_2026-11-04/report.md`
  - `review/metrics_r3/partval_bucko_all_2026-11-04/report.md`

## Stage 18 — Kaggle data (token added by Ahmed 2026-11-04), part `sr`, v3b_B, D2 hypothesis
- **Kaggle access works.** `tools/kaggle_dl.py` reads `%USERPROFILE%\.kaggle\access_token` and never prints it. Triage of 13 Kaggle sets: `review/new_data_r3/CANDIDATES.md` §D.
- **Owner update (Ahmed, 2026-11-04):** the supervisor says EGY_PDD is not needed and that much more data exists online. EGY_PDD is removed from the plan.
- **Part `sr`** (Kaggle speedregulator, CC BY-SA 4.0, a merged set; `tools/make_items_sr.py`, `parts_r3/sr/build_info.json`):

| family | what it is | used? |
|---|---|---|
| `kg_` | Italian dashcam (shop signs `Onoranze Funebri`, `Hertz`): potholes, cracks, manholes | yes; group = recording date |
| `dz_` | Algerian phone dash videos: speed bumps + potholes | yes; group = video |
| `rad_` | Indian dashcam (RAD) | **built but kept OUT of training (PROVISIONAL)**: sheet `review/new_data_r3/sr_bump_check.jpg` shows many "speed bump" boxes on sand or dirt road edges with no visible hump (`sr__e445eed…`, `sr__86d385e…`, `sr__850dd86…`) |
| `rdd_`, `rf_`, `night_` (= Bučko frames), `aug_` | duplicates of data we hold, rejected families, augmented copies | excluded |

  - Part counts: train 2,436 (1,488 negatives = crack/manhole-only hard negatives; 1,125 pothole, 247 bump boxes); val 164; test 183. 37 / 8 / 8 groups.
  - **Leakage guard extended:** r2 (all splits) **+ BD87 + rsid/bucko val,test + rdd_cz test** → **0 hits**. Drops: 11 only_far_tiny, 3 label errors, 5 exact duplicates inside the part.
  - Spot check `review/new_data_r3/sr_pothole_check.jpg`: pothole boxes are plausible.
- **`road_hazards_v3b_B`** = v3b_A + sr (kg + dz) (`road_hazards_v3b_B/build_info.json`, strict PASS, fingerprint `f927a9df…aeb6`):
  - train 6,893 images; 5,055 pothole / 1,925 bump boxes (2.6 : 1); 2,612 negatives;
  - val/test = r2.
- **Run D2 `v3b_B_11n_960_s0`** (same settings as D1, data v3b_B):
  - **H-D2:** r2-val mAP50 ≥ D1 − 0.02, AND sr part-val pothole AP50 ≥ D1's + 0.10 (new country, Italy), AND r2-val pothole precision at the F1-opt threshold does not drop by more than 0.03 (the hard negatives should, if anything, raise it).
  - Queued after queue 2: `run_r3_queue3.bat`, log `runs/r3_queue3.log`.

## Stage 19 — runs moved to a visible window (2026-11-04 ~15:10, Ahmed's request)
- Ahmed asked that the next trainings run in a visible window, with full per-class results (P, R, mAP50, Accuracy), not only plots.
- The background scripts `run_r3_queue2.bat` and `run_r3_queue3.bat` were stopped (their cmd.exe only). The running D1-seed-1 training (yolo PID 44792) kept running.
- New `run_r3_visible.bat` runs in a console window titled "GP36 training". In order:
  1. it waits for D1 seed 1 to finish, then runs its val-only evals;
  2. D1 s0 and Run A on the sr part-val (baselines for H-D2);
  3. **D2** (v3b_B);
  4. **imgsz 1280** (v3b_A).
- Order change: D2 now runs before 1280 (data first). The hypotheses of Stages 17–18 are unchanged.
- After each run the window prints the Ultralytics per-class P/R/mAP50/mAP50-95 lines. `tools/metrics_report.py` adds BoxAcc, ImgAcc, F1, NearR and P@R50 per class (`review/metrics_r3/val_r2_D1_seeds`, `val_r2_D2`, `partval_*_D2`, `val_r2_1280`).

## Stage 20 — owner: "we must get higher numbers" (2026-11-04 ~15:20). Plan of LEGITIMATE levers (written before any of them is run)
Nothing below uses test data for a choice, drops hard images, or splits by random frame.

| # | Lever | Why it is legitimate | Evidence / expected effect (PROVISIONAL) | Cost |
|---|---|---|---|---|
| L1 | **Longer training**: 150 epochs, patience 30, on the best data version | Same protocol as Run A; only D1 was capped at 70 | D1 mAP50 still rising at the end: 0.621 (ep 40) → 0.637 (50) → 0.654 (60) → 0.658 (70) (`runs/detect/v3b_A_11n_960_s0/results.csv`). Expected **+0.01–0.03** | ≈ 5 h for 11n on v3b_B |
| L2 | **YOLO11s with L1** | Larger model; pothole was +0.03 in Stage 16 (1 seed) | potholes +0.02–0.04; bumps uncertain | ≈ 7 h |
| L3 | **Val/test label audit → benchmark version r3** (missing pothole boxes, D4 one-box-per-defect, D1/D5 errors), as a corrections file + new folder; r2 stays frozen; **all** models re-scored on r3; test audited by the same rules **before** any r3 test use | Measurement correction, applied equally to every model. It changes the benchmark, not the model | Stage 9/11: many "background FPs" in `fp_background.jpg` are real unlabelled potholes. Expected measured pothole AP50 **+0.03–0.08** for all models | review work, no GPU |
| L4 | **Test-time augmentation** (`augment=True`: flips + scales) at evaluation | Standard inference option; reported as a separate row with its latency cost | Typical **+0.01–0.03** AP50, about 2–3× slower inference | minutes |
| L5 | **Pod-range metric** (pre-registered A1, Stage 7.2): hazards in the lower 40 % of the frame and sqrt(area) ≥ 0.05, which is what the FSM acts on (≤ 2 m) | Defined on 2026-11-02, before its values were seen; reported **next to**, never instead of, full mAP50 | — | CPU |
| L6 | **More bump data** (cloud session, Task 1) | Data was the only lever that worked (Stage 13) | unknown until the PR arrives | laptop builds parts |

**Order:**
1. The visible window keeps running D1 s1 → D2 → 1280.
2. L3 is done on the CPU in parallel (no heavy RAM: sheets only).
3. After D2: the best data version gets L1 (11n, 150 epochs), then L2 if time allows.
4. L4 and L5 are applied to the final candidates on val.
5. Final candidates: one test use per benchmark version.

## Stage 21 — cloud PR #1 reviewed and applied locally (2026-11-04 ~16:00)
- PR: branch `claude/tender-faraday-43rjjv` in github.com/Darkdesert070/Gp-36. Report: `review/new_data_r3/CLOUD_REPORT.md`.
- The cloud VM could reach only GitHub and PyPI; Kaggle, Zenodo, HF, Roboflow, Figshare and Mendeley were blocked by its network policy.
- **Real bug found by the cloud session (VERIFIED by its tests and by my reading of the code): leak rule v1 compared pHash unrotated only.**
  - A flipped re-encoded copy could have dHash 2 under the flip but pHash 32 unrotated, and so pass.
  - On a rejected Roboflow re-export, rule v1 found 229 eval hits and rule v2 found 328 (`review/new_data_r3/vet/cloud_leak_summary.csv`).
  - Rule v2 compares both hashes under the same one of the 8 transforms (`tools/leak_check.py`, `tools/build_part.py` `near8`).
- **Two further fixes made by me while reviewing:**
  1. `leak_check.check_image` reported the FIRST near hit. If an r2-train duplicate came first, an eval hit on the same image was not counted. It now reports an eval hit when one exists.
  2. `build_part.guard_hashes` split `C:\…` at the drive colon. It was found by the PR's `test_guard_protects_extra_eval_set`. My earlier calls all used relative `dir:val,test` paths, so no built part was affected.
- Tests after both fixes: **139 run, OK, 1 skipped** (symlink) (`venv\Scripts\python -I -m unittest discover -s tests`).
- **Re-check of everything used in training with rule v2: RUNNING.**
  - Scope: all parts (train/val/test) vs the protected eval sets, and r2 train vs r2 val/test.
  - Output: `review/new_data_r3/recheck_rule_v2_all.csv`.
  - Until it finishes, D1/D2 numbers are **PROVISIONAL with respect to flipped-copy leakage**.
- New from the PR (not yet used):
  - part `dmd` (dm-druid China campus bumps, 277 images / 319 boxes, train only);
  - `models/yolo11n-p2.yaml`;
  - `tools/calibrate_thresholds.py`, `vet_source.py`, `make_items_yolo_export.py`;
  - supervisor drafts `supervisor_2026-11-08/README.md`, `METRICS.md`.

## Stage 22 — D1 seed 1, and the rule-v2 re-check (VERIFIED, 2026-11-04 evening)
- **D1 seed 1 `v3b_A_11n_960_s1`.** Val:

| eval set | D1 s0 | D1 s1 | file (s1) |
|---|---|---|---|
| r2 all mAP50 | 0.655 | 0.641 | `runs/v3b_A_11n_960_s1_VALr2_json.txt` |
| r2 pothole / bump AP50 | 0.597 / 0.712 | 0.595 / 0.687 | same |
| RSID bump AP50 | 0.663 | 0.630 | `runs/PARTVAL_rsid_v3b_A_11n_960_s1.txt` |
| Bučko pothole AP50 | 0.572 | 0.576 | `runs/PARTVAL_bucko_v3b_A_11n_960_s1.txt` |

  - **H-seed-D1 holds:** 0.641 is within 0.655 ± 0.021; RSID bump 0.630 ≥ 0.55; Bučko 0.576 ≥ 0.50. The D1 gains on new countries are not a seed artefact.
- **Rule-v2 re-check — VERIFIED** (`review/new_data_r3/recheck_rule_v2_all.csv`; script in the session scratchpad, logic described here):
  - every image of r2 train and of every part's train split, against every protected eval image (r2 val/test, BD87, all part val/test): **0 EVAL hits**;
  - r2 train vs r2 train: 1,491 images have a near-duplicate inside r2 train (video frames), which is harmless;
  - part val/test images vs r2 train: **0 hits**;
  - the only eval-vs-eval matches are inside the same split (consecutive frames inside one val or one test set), plus 4 Bučko val↔test pairs (same location Pr, documented in Stage 9);
  - so the rule-v1 bug did **not** leak anything into training or into the r2 benchmark. D1 results stand.
  - Still running: part val/test vs all part TRAIN images, cross-part (`review/new_data_r3/recheck_rule_v2_heldout_vs_train.csv`).
- **Held-out vs train re-check (rule v2) — VERIFIED, 0 hits** (`review/new_data_r3/recheck_rule_v2_heldout_vs_train.csv`, header only).
  - Every val/test image of rsid, bucko, sr and rdd_cz was compared with every TRAIN image of rsid, bucko, rdd_ji and sr, cross-part included.
  - Together with the Stage 22 checks: **no leakage into any training set or evaluation set used so far.**
- D2 (`v3b_B_11n_960_s0`) started at 15:49 in the visible window. The disk cache for v3b_B was built (7,723 .npy files).

## Stage 23 — cloud PR #2 reviewed (2026-11-04 ~17:30), order change written BEFORE D2 results
- **Received:** branch `claude/r3-cloud-data2` (3 commits). Applied to the working tree with `git checkout <branch> -- <files>`. None of these files had local changes.
  - Files: `CANDIDATES.md` §F, `CLOUD_REPORT.md` §0/§3/§5, `review/new_data_r3/vet/{dmd,pol,red,ng8,hmp,ens,egy}/`, `tools/make_items_egyrdd.py`, `tools/rf_download.py`, and changes to `make_items_yolo_export.py`, `vet_source.py` (rule-v2 clustering) and `sample_sheet.py`.
- **Checks done here (VERIFIED):**
  - No key or token strings and no images in the diff (grep of the diff; only .py/.md/.csv/.json files).
  - Tool code read: one copy per Roboflow base; group split by video or name block; rule-v2 clustering; refuses to overwrite; zip-slip guard in `rf_download.py`.
  - I added to `rf_download.py` a key-file fallback (`~/.roboflow/api_key`, outside the repo; never printed).
- **Proposed parts:** dmd, pol, red, ng8, hmp, ens and egy. The counts are from the cloud build and must be reproduced here: `CLOUD_REPORT.md` §0.3 and `vet/<part>/expected_build_info.json`. That is 1,973 new train bump boxes (1,551 without ens) and 835 Egyptian pothole boxes.
- **Gates still open before any new part is used (decided now, before any result):**
  1. **Cross-source duplicates.** Roboflow sets often re-upload each other. After the build, every new part's val/test must be checked against ALL train images of the composition: r2 train, the existing parts' train, and the other new parts' train. Rule v2, the same script as the Stage 22 held-out vs train check. Hits are removed from that part's val/test (new part version); the train side is kept.
  2. **egy label audit (all splits, not only val/test).** Manhole covers are labelled as potholes, and pothole is our weakest class. Wrong pothole boxes in train teach "manhole = pothole", which is an FSM false-positive risk. So the cloud audits every egy pothole box (~950) and writes a box-level corrections file. egy is used only after the corrections are applied (part version egy_v2).
  3. **ens sequence check** (laptop; needs the rf8 images): the 40 pairs in `vet/ens/sequence_check_pairs.csv`. One pair is a near-copy of an r2 TRAIN image (no eval risk).
  4. **hmp:** label quality is uncertain. The cloud audits a sample before hmp val is used for any decision.
- **Composition of v3b_C is NOT taken from the cloud recipe yet.** The cloud drops `rdd_ji` for a ~1.3:1 balance. Pothole is the weakest class (r2 val 0.597), so removing pothole data for balance alone is not justified a priori. H-D2 is the test of whether more pothole data helps. The v3b_C recipe will be fixed after the D2 val result and written here before v3b_C trains.
- **Order change, written before D2 results:**
  - The imgsz-1280 run on v3b_A (H-1280, Stage 17) is postponed. New curated data is the only lever that has worked so far (Stage 13), and 1280 costs about 1.8× compute per image (a latency risk for the pod).
  - 1280 will be re-run later on the best data version, under a new name.
  - Mechanism: the placeholder folder `runs/detect/v3b_A_11n_1280_s0/` (with `SKIPPED_README.txt`). It makes `run_r3_visible.bat` stop cleanly after D2 and its evals; the batch file is not edited while it runs.
- RAM during D2: ~0.8 GB free. So the part builds (CPU/RAM) wait until D2 ends. Only downloads run now (dm-druid clone started).
- dm-druid cloned (VERIFIED): `../GP36_Dataset/raw_v3/github_dmdruid_speedbumps`, depth 1, commit 8b6c16b95f5b828a756baa06209b8eb38098d565 (2018-06-27), 1.4 GB on disk. Its items and part build wait for D2 to end (RAM).
- Roboflow key: the owner's first attempt showed the key in chat (not used, not stored by me). The owner was asked to regenerate it and save the new one in `~/.roboflow/api_key` via Notepad.
- Roboflow downloads (VERIFIED, `tools/rf_download.py`, key file outside the repo): polisi 1,000, reductor 438, ng8ne 710, egyrdd 1,372, ensam 884, humps 5,000 images. All six equal the cloud's expected counts (CLOUD_REPORT §3 step 1). Folders are `../GP36_Dataset/raw_v3/rf_*/x`.
- **ens sequence check (gate 3) — done, VERIFIED by eye** (sheets in the session scratchpad, not kept: no project images in the repo).
  - Compared: the 25 pairs of `vet/ens/sequence_check_pairs.csv` whose nearest protected image is EVAL (r2 val/test or part val/test), plus 10 random ens images next to 10 random rf8 numeric-name images from r2 val/test.
  - **No pair shows the same frame, street or scene.** All distances are above the leak rule (pHash 8–20).
  - The ens campus (Indian campus, painted humps, yellow-black curbs) looks LIKE the rf8 `Image003xx` family in r2 val (Indian campus, painted humps), but the streets differ. The same campus cannot be excluded.
  - The rf8 numeric-name images in r2 val/test are mostly Egyptian / MENA city streets, so they are not the ens family.
  - The raw ens export also has `Image000xx` and `newonetrwww` files (rf8 / sub5 families). The cloud's `--include "[0-9]{3,}"` filter removes them; this must be confirmed in the built manifest.
  - **Decision: ens ACCEPTED as train-only**, with one condition. Any r2-val bump gain of a model trained with ens is also reported per source group (`metrics_report.py --by source`). A gain only on the rf8 `Image003xx` group would be flagged as possible location overlap.

## Stage 24 — cloud PR #3 reviewed (2026-11-04 evening); v3b_C recipe FIXED here, before the D2 result
- **Received:** branch `claude/r3-cloud-data3` (5 commits), applied with `git checkout <branch> -- <files>`. No local conflicts. No key strings and no images in the diff (grep).
  - egy box audit: 954 boxes, two passes. 400 are not potholes; 270 of those are manholes or grates.
  - `tools/apply_box_corrections.py` and its tests. Code read: it checks label SHA-256 and class id, matches each box by coordinates, writes a NEW folder, and stops with a hard error on any mismatch.
  - hmp audit: test box errors 35.3 %, and half of val is stock or rotated photos → train-only part `hmpt`.
  - Cross-source duplicates: 2 train/train pairs; empty val/test drop list (gate 1 passed for the cloud's 7 parts, cloud side).
  - New part `bpo` (BharatPotHole, India dashcam potholes): 1,413 / 214 / 202 pothole boxes.
  - The 7k-image dashcam pothole set `d7k` is not vetted (laptop task).
- **Correction to the cloud recipe:** `rdd_ji:500` is in BOTH v3b_A (D1) and v3b_B (D2) (`road_hazards_v3b_B/build_info.json`). D2 = D1 + `sr` (minus rad) only, so D2 says nothing about rdd_ji. Dropping rdd_ji would be an untested change to the baseline, so **rdd_ji:500 stays**.
- **v3b_C recipe (fixed now, before D2 ends):** base r2 + rsid + bucko + rdd_ji:500 + **[sr minus rad, only if H-D2's guard conditions hold: r2-val mAP50 ≥ D1 − 0.02 AND r2 pothole precision drop ≤ 0.03]** + dmd + pol + red + ng8 + hmpt + ens + egy_v2 + bpo.
  - Not used: hmp (replaced by hmpt), egy (replaced by egy_v2), d7k (until vetted).
- **Hypotheses for v3b_C (val only; baseline B* = D1 or D2, whichever has the higher r2-val mAP50):**
  - H-C1: r2-val mAP50 ≥ B* − 0.02, AND RSID part-val bump ≥ B* − 0.03, AND Bučko pothole ≥ B* − 0.03.
  - H-C3: bump AP50 on pol val ≥ B* + 0.15 and on ng8 val ≥ B* + 0.10; ng8 ImgAcc ≥ B*; bpo-val pothole AP50 ≥ B* + 0.10 (after its sample audit).
  - H-C4: r2-val bump +0.00 to +0.04, and pothole +0.00 to +0.04. Any r2 gain is also reported `--by source` (ens / rf8 location note, Stage 23).
  - egy_v2 val (30 boxes) and test (23 boxes) are too small for decisions; reported only.

## Stage 25 — cloud PR #4 reviewed (2026-11-04 late); recipe and part-vals updated BEFORE the D2 result
- **Received:** branch `claude/r3-cloud-data4` (4 commits), applied locally. No conflicts and no keys or images in the diff.
  - `tests/test_apply_box_corrections.py`: 8 tests OK here (unittest discover).
- **Cloud self-correction:** the session-3 hmp audit had misread polygon labels as boxes. The real hmp test error rate is 0 % (5.9 % counting uncertain boxes), not 35.3 %. hmpt (train-only) stays, for the other reasons (stock/rotated photos in val, same scenes across splits). Part builds were never affected.
- **Val/test audits** (`review/new_data_r3/vet/VALTEST_AUDIT_S4.md`):
  - pol, red: 0 % errors.
  - ng8: 0 % box errors; 1 test image dropped for an unlabelled pothole → ng8_v2.
  - **bpo: val 12.0 % / test 19.4 % definite errors (≈ 55–60 % with uncertain) → bpo is TRAIN-ONLY.** Its train split is used as built; its val/test are never used.
- **d7k** is the upstream of bpo (same drives; `vet/d7k/PRECHECK.md`), so it is not a new source. Not used together with bpo. Its download on the laptop is kept for reference only.
- **v3b_C recipe, updated (replaces the Stage 24 line):** r2 + rsid + bucko + rdd_ji:500 + [sr minus rad, if the H-D2 guard holds] + dmd + pol_v2 + red_v2 + ng8_v2 + hmpt + ens + egy_v2 + bpo.
  - The train splits of pol_v2, red_v2 and ng8_v2 are identical to pol, red and ng8 (expected_build_info_*_v2.json).
- **Decision part-vals for v3b_C (val only):**
  - bumps: pol_v2, red_v2, ng8_v2, RSID;
  - potholes: Bučko, plus egy_v2 (30 boxes; reported, too small to decide).
- **H-C3 replaced:** bump AP50 on pol_v2 val ≥ B* + 0.15 and on ng8_v2 val ≥ B* + 0.10; ng8_v2 ImgAcc ≥ B*. The bpo clause is dropped (bpo val is not trusted). The other hypotheses are as in Stage 24.
- **Pothole sources:** the ≥ 3 new independent source target is NOT met. Accepted: egy_v2 and bpo (2 sources).
  - Open leads: SaudiRD (144 pothole boxes, laptop vet), the KFUPM Saudi set (request to authors), HRP4K (nature.com blocked in the VM; laptop check), CMIRD (pothole vs crack ids UNRESOLVED).
- Downloads (VERIFIED): rf_bharat 4,082 images (bpo source); rf_dashcam7k downloaded for reference only (d7k = upstream of bpo, not used, Stage 25).
- Owner (2026-11-04 night): "get as close to 0.90 as possible". The cloud session-5 prompt was upgraded (`review/new_data_r3/PROMPT_cloud_session5_strong.md`). It covers MENA data (unmarked bumps, potholes, negatives), a range-aware metric with ignore-region semantics (STATUS L5; always shown next to full mAP50), WBF, sliced inference, TTA, recipe research, supervisor tables, the test ledger and the honest-0.90 draft.
- Laptop order after D2 (unchanged rules):
  1. v3b_C (960, D1 settings);
  2. a long run (L1: 150 epochs, patience 30) on the best data version, with 11n, and with 11s if time allows;
  3. a 2-seed WBF ensemble, TTA and sliced inference as separate rows;
  4. final candidates chosen on val only, then one test use each.

## Stage 26 — D2 result (VERIFIED, 2026-11-04 ~20:50), H-D2 judged against the Stage 21 text
- D2 `v3b_B_11n_960_s0` finished 70/70 epochs in the visible window; evals done; the batch stopped at the 1280 placeholder as planned. Val only, no test used.
- Files: `review/metrics_r3/val_r2_D2/report.md`, `partval_sr_D2`, `partval_rsid_D2`, `partval_bucko_D2`.

| eval set | class | D1 s0 AP50 | D2 AP50 | delta |
|---|---|---|---|---|
| r2 val | pothole | 0.596 | 0.615 | +0.019 |
| r2 val | speed_bump | 0.710 | 0.683 | −0.027 |
| r2 val | mean | 0.653 | 0.649 | −0.004 |
| sr part-val | pothole | 0.396 | 0.433 | +0.037 |
| RSID part-val | pothole (42 GT) | 0.259 | 0.307 | +0.048 |
| RSID part-val | speed_bump | 0.670 | 0.630 | −0.040 |
| Bučko part-val | pothole | 0.571 | 0.617 | +0.046 |

- **H-D2 (Stage 21): REJECTED as a whole.**
  - r2-val mAP50 0.649 ≥ D1 − 0.02 = 0.633: holds.
  - sr pothole AP50 ≥ D1 + 0.10: fails (+0.037 only).
  - r2 pothole precision at the F1-opt threshold did not drop (0.625 → 0.643): holds.
- **Inclusion guard for v3b_C (Stage 24/25 text: r2-val ≥ D1 − 0.02 AND pothole precision drop ≤ 0.03): HOLDS → `sr` minus `rad` goes into v3b_C**, as pre-registered.
- Observations (not hypotheses; D1 seed spread on r2 val was 0.014, Stage 22):
  - pothole AP50 rose on all 4 eval sets (+0.019 to +0.048);
  - speed_bump fell on r2 val (−0.027) and on RSID (−0.040);
  - r2 bump NearR fell 0.280 → 0.146 at the op threshold (thr 0.327 → 0.398); bump P@R50 rose 0.863 → 0.904.
  - Likely mechanism (UNVERIFIED): sr adds bump-free frames, which push bump scores down. v3b_C adds ~6 bump parts, which should counter this; H-C4 (r2 bump +0.00 to +0.04) tests it.
- Next steps wait for Ahmed (he asked not to start the next job yet): part builds (`run_r3_parts_C.bat`), then v3b_C.

## Stage 27 — v3b_C launched (2026-11-05 ~01:50), plan written BEFORE any build or result
- Ahmed asked to launch the new training, then hand over: from here on, Claude sends files and code, and Ahmed applies and runs them.
- **B\* = D1 s0.** r2-val mean mAP50: D1 s0 0.653 vs D2 0.649 (Stage 26). H-C1, H-C3 and H-C4 (Stages 24–25) are judged against D1 s0.
- One visible window, `run_r3_C_visible.bat` (`cmd /k`):
  1. part builds (`run_r3_parts_C.bat`);
  2. `tools/check_parts_expected.py`, the gate:
     - pol_v2 / red_v2 / ng8_v2 / egy_v2 val and test counts must match the cloud's expected files exactly;
     - every part's train counts must be within 2 %;
     - on failure it STOPS before composing;
  3. `build_v3b.py` → `road_hazards_v3b_C` (Stage 25 recipe, sr minus rad);
  4. D1 s0 and D2 baselines on the 4 new part-vals;
  5. train `v3b_C_11n_960_s0` (same settings as D1/D2: 11n, 960, 70 epochs, patience 20, seed 0);
  6. val-only evals and reports in `review/metrics_r3/*_C/`.
- No test use.
- `protected_hashes.npz` is not regenerated in this window. It is needed only for future cloud sessions, and the cloud credit is finished.

## Stage 28 — v3b_C result (VERIFIED, 2026-11-05 23:27) and diagnosis
- First try `runs/detect/v3b_C_11n_960_s0` died at epoch 1: `CUDA error: resource already mapped` in the DataLoader pin-memory thread. That folder is kept as evidence. The retry `v3b_C_11n_960_s0_r2` used the same data and args (`run_r3_C_retry_visible.bat`). It ran 70/70 epochs; best epoch 54 (results.csv mAP50 0.673), last epoch 0.646. Val only; no test used.
- r2 val (`review/metrics_r3/val_r2_C/report.md`):

| class | D1 s0 | D2 | C | C − D1 |
|---|---|---|---|---|
| pothole AP50 | 0.596 | 0.615 | 0.639 | +0.043 |
| speed_bump AP50 | 0.710 | 0.683 | 0.703 | −0.007 |
| mean | 0.653 | 0.649 | 0.671 | +0.018 |

- Other r2-val numbers for C:
  - pothole: F1 0.641, BoxAcc 0.471, ImgAcc 0.919, NearR 0.641;
  - bump: F1 0.704, BoxAcc 0.543, ImgAcc 0.866, NearR 0.306 (D2: 0.146).
  - C is the best r2-val model so far (v1 mean 0.669).
- Part-vals (`review/metrics_r3/partval_*_C/report.md`), AP50 for D1 → C:

| part-val | D1 | C |
|---|---|---|
| Bučko pothole | 0.571 | 0.636 |
| RSID bump | 0.670 | 0.680 |
| RSID pothole (42 GT) | 0.259 | 0.185 |
| sr pothole | 0.396 | 0.395 |
| egy_v2 pothole (30 GT) | 0.021 | 0.338 |
| pol_v2 bump | 0.255 | 0.950 |
| red_v2 bump | 0.176 | 0.993 |
| ng8_v2 bump | 0.669 | 0.924 |

- **Caveat (VERIFIED from the manifests):** these part-vals are recorded in the same place and on the same day as their own train splits, so a high score there shows the model learned that source, not that it generalizes.
  - red_v2: all 23 video groups were recorded on 2025-07-07;
  - ng8_v2: all groups on 2025-08-02;
  - pol_v2: frame-number blocks of the same recording.
  - So pol_v2 / red_v2 / ng8_v2 measure **in-source learning, not generalization**, and are never presented as "0.90 reached".
- **Hypotheses (Stages 24–25, B\* = D1 s0):**
  - **H-C1 HOLDS:** r2 0.671 ≥ 0.633; RSID bump 0.680 ≥ 0.640; Bučko 0.636 ≥ 0.541.
  - **H-C3 HOLDS as written:** pol_v2 +0.695 ≥ +0.15; ng8_v2 +0.255 ≥ +0.10; ng8_v2 ImgAcc 0.970 ≥ 0.925. Weak evidence, because of the caveat above.
  - **H-C4 NOT HELD:** pothole +0.043 is above the predicted +0.00–0.04 range; bump −0.007 is below it (within seed spread 0.014).
- **Confound found (VERIFIED, `train_args` in best.pt and `ultralytics/engine/trainer.py` lines 1180–1189):** `optimizer=auto` selects MuSGD with lr 0.01 when iterations > 10,000, and AdamW with lr 0.001667 and beta1 0.9 otherwise.
  - D1 and D2 got AdamW. C (10,562 images → 11.6k iterations) got **MuSGD**.
  - So C differs from D1 in both data and optimizer.
  - MuSGD moved the first layers further from the pretrained weights: layer-0 cosine 0.88 with norm ×4.5, vs AdamW 0.99 / ×1.1 (analysis script in the session scratchpad).
  - From now on every run sets the optimizer explicitly.
- **Layers check (VERIFIED):**
  - 448/499 pretrained tensors are transferred; the 51 that are not are the 2-class classification head (`model.23.cv3`), which is expected.
  - All conv layers changed in training, except the DFL conv, which is fixed by design. No layer bug.
- **Error analysis of C on r2 val** (op thresholds 0.251 / 0.192; read-only script in the session scratchpad):
  - **Near bumps** (157 GT): 30 % hit, 61 % no prediction at all. **Far bumps** (221): 89 % hit.
    - A sheet of 12 random near misses shows unmarked Egyptian asphalt humps close to the car.
    - r2 train has only **107 near rf8 bump boxes**; r2 val has 157. sb15 has 950 near bumps, but of another type.
    - So the model barely saw the deployment case.
  - **Potholes:** 62–64 % hit near and far; 25 % no prediction; 13 % found with IoU 0.1–0.5.
    - Recall is 0.59 for sqrt(area) < 0.03 (280 of 691 GT).
    - AP@IoU0.3 0.751 vs AP@0.5 0.639, so box extent (ambiguous pothole outlines) costs about 0.11.
  - Class-agnostic hazard AP50 0.658 ≈ the class mean, so pothole/bump confusion is negligible.
- **COCO evaluation added:** `tools/coco_eval.py` (pycocotools 2.0.8, pinned in `requirements-lock.txt`; tests in `tests/test_coco_eval.py`).
  - On r2 val (`review/metrics_r3/coco_val_r2_2026-11-06/report.md`), COCO AP50 equals our metrics_report AP50 for every model; C pothole 0.639 / bump 0.703.
  - COCO AP (0.50:0.95), all classes: v1 0.305, Run A 0.307, D1 0.291, D1_11s 0.302, D2 0.303, **C 0.317**.
- **PR #5 applied** (2026-11-06): 37 files via `git checkout github/claude/r3-cloud-data5 -- <files>`, all of them supersets of the local copies.
  - Local versions kept: STATUS (newer) and `rf_download.py` (key-file fallback).
  - Tests: **188 run, OK, 1 skipped**, plus 3 new COCO tests OK.

## Stage 29 — plan "E" (Ahmed asked Claude to execute it, 2026-11-06 ~04:30); hypotheses written BEFORE any run
Decision data: r2 val (frozen) for choosing; part-vals reported. The test split is never used to choose.
- **One visible window, `run_r3_E_visible.bat`, in this order:**
  1. **Levers on C, r2 val, no training** (pre-registered in CLOUD_REPORT §0-S5 B; same accept rule):
     - TTA (`augment=True`);
     - WBF of C + D1_11s (iou 0.55, skip 0.001);
     - sliced inference (tile 640, overlap 0.25, rows-from 0.4, NMS);
     - scored with metrics_report `--care near` and coco_eval.
     - **Accept rule:** Δ ≥ +0.02 r2-val mean AP50, or Δ ≥ +0.02 on one class with the other ≥ −0.02. Latency reported.
  2. **E1 `v3b_C_11n_960_adamw_s0`:** same data and args as C, but optimizer set to exactly what D1/D2 got (`optimizer=AdamW lr0=0.001667 momentum=0.9 warmup_bias_lr=0.0`).
     - **H-E1:** |E1 − C| r2-val mean AP50 < 0.02 (the optimizer is not the main factor).
     - **Choice rule for the default optimizer:** the higher r2-val mean AP50. If |Δ| < 0.02, the higher mean of (RSID bump AP50, Bučko pothole AP50), the two unseen-source part-vals.
  3. **E2 `v3b_C_11n-p2_960_adamw_s0`:** `models/yolo11n-p2.yaml`, pretrained yolo11n.pt, same data, AdamW as E1, **batch 8** (same as E1).
     - Changed from batch 6 before launch: a 1-epoch smoke test at 4 % of the data, in the session scratchpad and not kept, used 3.2 GB of GPU memory at batch 6, and "Transferred 297/593 items".
     - **H-E2 (CLOUD R-C):** vs E1, pothole AP50 +0.02 to +0.04 on r2 val; recall on pothole GT with sqrt(area) < 0.03 rises; bump within ±0.02; latency +30–60 %.
     - **Accept:** pothole Δ ≥ +0.02 and bump ≥ −0.02.
  4. After each training: evals on r2 val and all part-vals; metrics_report (C vs E1 vs E2) and coco_eval.
- **Data step (needs labels by a person; no pseudo-labels):** a train-only pool of Egyptian near unmarked-hump frames from new streets/videos, leak-checked. It is prepared for Ahmed to label; not part of this window.
- **Final:**
  - up to 2 candidates, chosen on r2 val only (best single model; plus WBF of the top two only if the WBF lever is accepted);
  - each gets ONE use on r2 test and BD87 (`tools/test_ledger.py check` first, then `add`), with COCO numbers;
  - supervisor package after that.

## Stage 30 — levers on C judged (VERIFIED, 2026-11-06 ~05:10; rule: Stage 29 / CLOUD_REPORT §0-S5 B)
Sources: `review/metrics_r3/val_r2_levers_C/report.md` and `coco_val_r2_levers_C/report.md`. r2 val only.

| row | pothole AP50 | bump AP50 | mean | Δ mean vs C | COCO AP | near AP50 pothole / bump | verdict |
|---|---|---|---|---|---|---|---|
| C | 0.639 | 0.703 | 0.671 | — | 0.317 | 0.683 / 0.339 | baseline |
| C + TTA | 0.610 | 0.711 | 0.661 | −0.010 | 0.321 | 0.666 / 0.341 | **REJECTED** (pothole −0.029; hypothesis +0.01–0.03 not held) |
| WBF(C, D1_11s) | 0.667 | 0.738 | 0.703 | **+0.032** | 0.319 | 0.658 / 0.404 | **ACCEPTED** (pothole +0.028, bump +0.035; hypothesis +0.01–0.03/class: pothole held, bump above) |
| C sliced (640 tiles) | 0.631 | 0.704 | 0.668 | −0.004 | 0.311 | 0.642 / 0.388 | **REJECTED** (pothole −0.008; hypothesis +0.02–0.05 not held) |

- **WBF cost:** two models per frame (11n + 11s), so about the sum of both latencies.
  - Its fused scores are lower (op thresholds 0.116 / 0.069), so the deploy conf 0.35 does NOT carry over: at 0.35, pothole R = 0.165.
  - A WBF candidate must use its own val-chosen thresholds. The FSM config is not changed; this is reported only.
- **Sliced cost:** median 195 ms per image on the laptop GPU (p95 314 ms; `runs/detect/SLICED_C_VALr2/predictions_latency.json`).
- Per Stage 29, WBF of the top two single models (chosen on r2 val after E1/E2) becomes the second final candidate.

## Stage 31 — E1 (AdamW) judged (VERIFIED, 2026-11-06 ~08:35; rule: Stage 29 step 2)
Sources: `review/metrics_r3/val_r2_E1/report.md`, `partval_<part>_E1/report.md`, `coco_val_r2_E1/report.md`. r2 val only; 70 epochs ran (no early stop).

| model | pothole AP50 | bump AP50 | mean | COCO AP (50-95) | near AP50 pothole / bump | bump NearR | RSID bump | Bučko pothole | egy_v2 pothole | sr pothole |
|---|---|---|---|---|---|---|---|---|---|---|
| C (MuSGD lr 0.01, auto) | 0.639 | 0.703 | **0.671** | **0.317** | 0.683 / 0.339 | 0.306 | 0.680 | **0.636** | **0.338** | 0.395 |
| E1 (AdamW lr 0.001667) | 0.603 | **0.733** | 0.668 | 0.308 | 0.634 / 0.399 | 0.261 | **0.689** | 0.590 | 0.299 | **0.433** |

- **H-E1 HELD:** |Δ mean| = 0.003 < 0.02, so the optimizer is not the main factor in the mean. It does shift the class balance: AdamW gives pothole −0.036 and bump +0.030.
- **Default optimizer (tie-break rule):** mean of (RSID bump, Bučko pothole) is C 0.658 vs E1 0.640, so **C's recipe (optimizer=auto → MuSGD) stays the default.**
- **What this means for D1/D2 (Stage 28 confound):** the C-vs-D gap was not mainly the optimizer, so the gain of C is mostly the data.
- **For E2:** the comparison stays E2 vs E1 (same optimizer), as pre-registered. If E2 is accepted, its result says P2 helps under AdamW; a MuSGD P2 run is not planned before 8 Nov.
- **Note for the final step (no choice made here):** E1 and C make different errors (class balance above), which is what WBF benefits from. The Stage 29/30 rule stands as written: WBF of the top two single models by r2-val mean AP50 after E2. With E1, that is currently C 0.671, v1 0.669, E1 0.668. The choice is made after E2, by the rule, and is not changed now.

## Stage 32 — E2 (P2) judged, final candidates fixed by the Stage 29/30 rule (2026-11-06 ~14:40), written BEFORE any test run
Sources: `review/metrics_r3/val_r2_E2/report.md`, `coco_val_r2_E2/report.md`, `partval_<part>_E2/report.md`; finalists: `val_r2_final/report.md`, `coco_val_r2_final/report.md`. r2 val only.

| model | pothole AP50 | bump AP50 | mean | COCO AP | COCO ARs pothole | near AP50 pothole / bump | bump NearR | RSID bump | Bučko pothole |
|---|---|---|---|---|---|---|---|---|---|
| E1 (AdamW) | 0.603 | 0.733 | 0.668 | 0.308 | 0.389 | 0.634 / 0.399 | 0.261 | 0.689 | 0.590 |
| E2 (P2, AdamW) | 0.618 | 0.675 | 0.647 | 0.296 | 0.418 | 0.630 / 0.220 | 0.057 | 0.635 | 0.514 |

- **H-E2 REJECTED:** pothole Δ = +0.015 (needed ≥ +0.02) and bump Δ = −0.058 (needed ≥ −0.02). One sub-claim held: small-object pothole recall rose (COCO ARs 0.389 → 0.418, a pixel-size proxy; the sqrt(area) < 0.03 recall was not computed). Near bumps collapsed (NearR 0.057), and part-vals are lower (RSID bump −0.054, Bučko pothole −0.076). Latency was not measured, because the model is rejected anyway. The P2 head is not used.
- **Final candidates (rule fixed in Stage 29/30, applied mechanically on r2 val, 4 decimals from coco_eval):**
  - single models ranked by r2-val mean AP50: C 0.6709 > v1 0.6690 > E1 0.6679 > Run A 0.6649 > D1_11s 0.6585 > D2 0.6489 > E2 0.6468;
  - **candidate 1 = C** `v3b_C_11n_960_s0_r2` (best single model);
  - **candidate 2 = WBF(C, v1)** (top two single models; v1 = `v3a_r1_11n_960_s0`, the deployed baseline). Same WBF settings as the accepted lever: iou 0.55, skip 0.001, equal weights.
- **Val numbers of candidate 2** (reported, not a choice): pothole 0.676, bump 0.752, mean **0.714**, COCO AP 0.332, near AP50 0.694 / 0.402, op thresholds 0.148 / 0.090. Its cost is two 11n models per frame.
- **Test protocol (one use each, nothing chosen on test):**
  - Benchmarks: r2 test (`road_hazards_v3a_r2`, split test) and external BD87 (`external_tests/bd_speedbreaker_v2_orig87_eval.yaml`).
  - Steps: `test_ledger.py check` for all 4 (model, benchmark) pairs BEFORE any `yolo val split=test`; then `yolo val save_json` (conf 0.001, same as val); WBF on the test predictions; `metrics_report --thresholds review/metrics_r3/val_r2_final/report.json --care near`; `coco_eval --allow-test`; `test_ledger.py add` for each.
  - BD87 is scored through a read-only view, `external_tests/bd87_eval_view/` (`tools/make_eval_view.py`: manifest with image sizes, plus byte copies of the 87 label files with their sha256; the source folder is not written).
  - **Note on v1:** v1's predictions on r2 test and BD87 are made only as WBF inputs. v1-alone numbers in those logs are not reported and not used. v1 on BD87 was already use #3. v1 on r2 test alone stays un-reported, as ledger row 4 asks.
  - Window: `run_r3_FINAL_tests_visible.bat`.

## Stage 33 — FINAL test uses (VERIFIED, 2026-11-06 14:35; ledger uses 6–9; protocol: Stage 32)
Window `run_r3_FINAL_tests_visible.bat` (PID 27664). A first launch, PID 33984, printed "not recognized" because the bat was given without a full path. It read no image and ran nothing; that window is left open.
Sources: `review/metrics_r3/test_r2_final/report.md`, `test_bd87_final/report.md`, `coco_test_r2_final/report.md`, `coco_test_bd87_final/report.md`.
Thresholds come from `val_r2_final/report.json` (C 0.251 / 0.192; WBF 0.148 / 0.090). Nothing was chosen on test.
Cross-check: the Ultralytics log for C on r2 test (`runs/v3b_C_11n_960_s0_r2_TEST_r2_json.txt`) gives pothole 0.713 and bump 0.316, against metrics_report 0.711 and 0.320 (within 0.004). For BD87, the log gives 0.732 against 0.731.

| benchmark | model | pothole AP50 | bump AP50 | mean | COCO AP (50-95) | pothole P / R / ImgAcc @op | bump P / R / ImgAcc @op | near AP50 pothole / bump |
|---|---|---|---|---|---|---|---|---|
| r2 test (323 img) | Run A (Stage 4, reference) | 0.631 | 0.294 | 0.462 | — | — | — | — |
| r2 test | **C** | **0.711** | 0.320 | 0.515 | 0.227 | 0.612 / 0.726 / 0.938 | 0.508 / 0.200 / 0.663 | 0.814 / 0.389 |
| r2 test | **WBF(C, v1)** | 0.698 | **0.463** | **0.580** | **0.240** | 0.671 / 0.688 / 0.938 | 0.565 / 0.381 / 0.780 | 0.801 / 0.482 |
| BD87 (87 img, bumps) | Run A / v1 (Stage 4, reference) | — | 0.367 / 0.328 | — | — | — | — | — |
| BD87 | **C** | — | **0.731** | — | **0.353** | — | 0.732 / 0.682 / 0.747 | — / 0.629 (n_near 2) |
| BD87 | WBF(C, v1) | — | **0.731** | — | 0.326 | — | 0.775 / 0.625 / 0.724 | — / 0.670 (n_near 2) |

- **Per-class mAP50 ≥ 0.90: NOT reached** on either test benchmark.
  - Best pothole: 0.711 (C, r2 test; Run A had 0.631).
  - Best bump: 0.463 on r2 test (WBF; Run A had 0.294) and 0.731 on BD87 (C and WBF; Run A had 0.367).
- **Pre-defined alternative metrics (Stage 7.2) that are ≥ 0.90 on test** (always shown next to the mAP50 above):
  - pothole ImgAcc 0.938 (both candidates, r2 test);
  - bump P@R50 0.936 (C, BD87);
  - pothole near AP50 0.814 / 0.801 is below 0.90.
- **Bump val→test gap stays the main finding:** C bump goes from 0.703 (val) to 0.320 (r2 test). The r2 test bumps are mostly the unmarked Egyptian humps (Stage 5), the same failure as the val near-bump analysis (Stage 28). BD87 (marked or visible bumps, independent annotation) doubled vs Run A.
- **WBF trade-off:**
  - +0.143 bump AP50 on r2 test, −0.013 pothole, and two 11n models per frame. Latency was not measured (PROVISIONAL about 2× one 11n).
  - Its fused scores are low, so at the deployed conf 0.35 its recall collapses (bump R 0.056). It needs its own thresholds (0.148 / 0.090). The FSM config was not changed.
- Supervisor tables (formatted from these report.json files only): `supervisor_2026-11-08/tables_val_final/`, `tables_test_r2/`, `tables_test_bd87/`.

## Stage 34 — plan "G": audit of the TRAIN labels of v3b_C, then retrain (Ahmed asked Claude to execute, 2026-11-06 ~23:20); written BEFORE any audit result
Context:
- Ahmed's own F1 run (mosaic 0.2, `review/f1_mosaic02/verdict.json`) was REJECTED by its pre-written rule: pothole −0.030, bump −0.035, near bump −0.081. C stays the base.
- Disk: the 153 GB Ultralytics `.npy` cache was removed by Ahmed. Images, labels and checksums were not touched.

Why:
- The cloud audits found label noise in sources that are in v3b_C train, e.g. bpo val/test had 12–19 % definite errors (`vet/VALTEST_AUDIT_S4.md`), and its train was never audited box by box.
- Train noise teaches wrong things in two ways:
  - a wrong box (manhole, crack, shadow) teaches false positives;
  - a visible but unlabelled hazard teaches "this is background".

Method (no pseudo-labels; no box is ever added or resized; r2 val/test and every part val/test unchanged):
1. **Model predictions on v3b_C train.** C predicts on every train image (`run_r3_G_audit_preds.bat`, wrapper `review/label_audit_r3/v3b_C_train_as_val.yaml`, conf 0.001).
2. **Candidates, by rule** (`tools/label_audit_candidates.py`):
   - (a) **unfit GT:** a GT box with no same-class prediction of score ≥ 0.05 at IoU ≥ 0.3 (a label the model refuses to learn);
   - (b) **possible missing label:** a prediction of score ≥ 0.5 with IoU < 0.1 to every GT of either class;
   - (c) **loose box:** a GT box whose best same-class prediction (score ≥ 0.3) has IoU 0.1–0.4.
3. **Visual review by Claude** of crop sheets (box drawn on its context), as in the cloud egy/hmp audits:
   - verdicts for (a)/(c): keep | remove_not_hazard | remove_manhole | remove_bad_box | uncertain (uncertain = kept);
   - verdicts for (b): drop_image (a clearly visible hazard is unlabelled, so the image is removed from train) | no_hazard (nothing changes).
   - Review order, until time runs out: the sources with known noise first (bpo, rdd_ji, sr, egy, sb15), then the rest. Unreviewed candidates stay as they are.
4. **New dataset `road_hazards_v3b_C2`:** v3b_C with only the reviewed train changes applied (`tools/apply_train_audit.py`). It writes change_log.csv, manifest, checksums and build_info. The val/test files must be byte-identical to v3b_C (checked by sha256).
5. **G1 = `v3b_C2_11n_960_s0`:** exactly C's args (yolo11n.pt, optimizer=auto, batch 8, 70 epochs, 960, cache=disk, seed 0). Then r2-val and part-val evals, metrics_report `--care near --by source`, and coco_eval vs C.

**H-G (written now):** cleaner train labels give G1 − C r2-val mean AP50 of 0.00 to +0.03; the largest gain is expected in pothole precision (fewer FPs on manholes and cracks).
- **Accept** (same rule as the levers): Δ mean ≥ +0.02, or one class ≥ +0.02 with the other ≥ −0.02. Guard: RSID bump and Bučko pothole each ≥ C − 0.03.
- **Note:** the seed spread is about 0.014 (Stage 3), so a Δ below 0.02 is not called an improvement.
- If accepted, G1 becomes a val-only candidate. No new test use is planned: the 4 final uses are done (Stage 33). A G1 test use would need Ahmed's explicit OK.

## Stage 35 — train-label audit done, `road_hazards_v3b_C2` built, G1 launched (2026-11-06 ~23:35; before any G1 result)
- **Predictions of C on v3b_C train** (`runs/AUDIT_C_on_v3bC_train.txt`): pothole AP50 0.670 and recall 0.55 on its OWN train data; bump 0.976. So pothole labels are much harder to fit, i.e. noisy or ambiguous.
- **Candidates** (`review/label_audit_r3/candidates.csv`, `tools/label_audit_candidates.py`): 1,106 in total.
  - unfit by source: bpo 292 of 1,413, rf8 159, rdd_ji 134, sr 115;
  - loose: 186;
  - missing: 112.
- **Reviewed by eye** (sheets in `review/label_audit_r3/sheets/`; verdicts in `review/label_audit_r3/verdicts.csv`, 327 rows):
  - **bpo unfit:** sheets 0–15, 18 and 22 (216 of 292). The lowest-score candidates are often boxes on smooth road, on the windshield or hood reflection, or on cracks only. Higher-score ones are mostly real broken patches.
  - **missing, all sources:** 111 of 111. Most are model FPs on manholes, drain grates and zebra crossings (not label errors). 24 are clear unlabelled hazards: 11 rf8 potholes, 2 red painted bumps, 3 egy, 2 ghpot, 2 rdd_ji, 2 sr, 1 bucko, 1 bpo.
  - **rf8 unfit:** sheets 0–2 viewed. All are real or ambiguous potholes, so there is no change. The rest of rf8/rdd_ji/sr unfit and all "loose" candidates were not reviewed and stay as they are.
  - **Totals:** remove_not_hazard 60 (all bpo); drop_image 24; uncertain 175 (kept); keep 27; no_hazard 41.
- **`road_hazards_v3b_C2`** (`tools/apply_train_audit.py`; `build_info.json`, `change_log.csv`):
  - train 10,538 images (−24); pothole boxes 6,842 (−126); bump boxes 3,981 (−1);
  - val/test: images and labels checked byte-identical to v3b_C (830 + 323, 0 mismatches);
  - images are hard links; no box was added or resized.
- **Expectation, per H-G (Stage 34):** the change is small (1.1 % of train boxes), so a Δ near 0 is likely. The accept rule stays as written.
- **G1 `v3b_C2_11n_960_s0`** launched in `run_r3_G_visible.bat` (PID 35460) with C's exact args.

## Stage 36 — G1 (label-audited train) judged: REJECTED by the Stage 34 rule (2026-11-07 ~03:40)
- G1 `v3b_C2_11n_960_s0` finished 70 epochs (`runs/detect/v3b_C2_11n_960_s0`). Val-only evals; **no test use**.
- **r2 val** (`review/metrics_r3/val_r2_G1/report.md`, thresholds = argmax F1 on val):

| model | pothole AP50 | bump AP50 | mean | pothole P / R @thr | bump P / R @thr | near bump R | COCO AP (all) |
|---|---|---|---|---|---|---|---|
| C | 0.639 | 0.703 | 0.671 | 0.654 / 0.628 | 0.770 / 0.648 | 0.306 | 0.317 |
| G1 | 0.648 | 0.686 | 0.667 | 0.760 / 0.573 | 0.835 / 0.601 | 0.197 | 0.313 |

- **Part vals, AP50 (C → G1):**
  - RSID: bump 0.680 → 0.697; pothole 0.185 → 0.277.
  - Bučko: pothole 0.636 → **0.531**.
  - sr: pothole 0.395 → 0.421.
  - pol_v2: bump 0.950 → 0.910.
  - red_v2: bump 0.993 → 0.996.
  - ng8_v2: bump 0.924 → 0.908.
  - egy_v2: pothole 0.338 → 0.369.
- **Rule (Stage 34):**
  - Δ mean = −0.004 (needs ≥ +0.02).
  - Pothole is +0.009 and bump is −0.017, so neither class reaches +0.02.
  - **Guard fails:** Bučko pothole is −0.105 (limit −0.03).
  - **→ REJECTED. C stays the default** and the finalists of Stage 32/33 do not change.
- **H-G (0.00 to +0.03) did not hold**, just below the range (−0.004). That is inside the seed spread (~0.014), so it means "no measurable gain".
- **What did change:** precision went up and recall went down at the operating point.
  - rf8 val pothole FP: 207 → 107; bump FP: 72 → 43.
  - Near-bump recall: 0.306 → 0.197.
  - AP is flat. Removing box-level noise trades FPs for misses; it does not add detection ability.
- **Bučko caution:** Bučko pothole AP50 moves 0.514–0.636 between runs of similar recipes (E2 0.514, D1 0.571, E1 0.590, C 0.636; 186 boxes). Part of the −0.105 may be run noise. The rule is applied as written anyway.
- **Lesson:**
  - With 60 removed boxes and 24 dropped images (1.1 % of train), label cleaning on train is too small to move val AP.
  - The pothole ceiling is not mainly train-label noise. More likely causes are the r2-val label style and the domain gap (Stage 28).
  - A larger audit (the ~800 unreviewed candidates) is not expected to change this by ≥ 0.02 and is not started.
- `road_hazards_v3b_C2` and the G1 weights are kept (nothing is deleted). Its ~60 GB `.npy` cache can be removed with `tools/clean_npy_cache.py` (Ahmed runs it).

## Stage 37 — egm labelling: owner decision, labeller = Claude (2026-11-07 ~04:50, before any frame was looked at)
- **Why:** the main remaining failure is near, unmarked Egyptian bumps (C: near-bump recall 0.250 on r2 test). A new
  public-data search (CANDIDATES.md §J) found no usable source. The Egyptian Mapillary pool `egm` (Cairo/Giza tiles
  390_375 + 391_375, `run_egm_step1.bat`, started 04:40) is the remaining route.
- **Owner decision (Ahmed, 7 Nov, in chat):** the egm frames are labelled **by Claude (AI), not by a human**, and this is
  acceptable for the project. This replaces the earlier plan "hand-labelled by Ahmed" for egm only.
- **Honesty rules that follow from it (fixed now):**
  - These labels are **AI labels**. They are never called "hand-labelled" or "human-labelled" anywhere (report,
    supervisor files, DATA.md). Every egm label row carries `labeller=claude`.
  - They are **not** detector pseudo-labels: no GP36 model (C, v1, WBF, …) is run on egm before or during labelling, and
    no model output is shown to the labeller. Labels come from looking at the pixels with the D1–D6 rules only.
  - Ahmed spot-checks a random sample of labelled frames (eval pool first); the sample size and the result are logged here.
  - The `eval` pool (split by creator, fixed by `make_egm_pool.py` before anyone looked) becomes benchmark `egm_eval`,
    reported as "AI-labelled Egyptian street frames". It is used once per model (TEST_LEDGER) and never trained on.
  - The `train` pool may become part `egm` only through `build_part.py` and a rule written here BEFORE its training result.
- **Box-quality caveat (expected, stated before labelling):** boxes drawn from downscaled views are looser than boxes
  drawn at full resolution; far, tiny objects that are not clearly visible are marked `unsure`, not boxed.

### Stage 37b — owner decision: model-ranked search for the TRAIN pool only (2026-11-07 ~05:35)
- Progress before the decision: eval pool frames #0–161 looked at (91 done/hazard-free, 41 unusable, 30 unsure
  (night/blur)); **0 bumps, 0 potholes**. Eval pool = 1,287 frames, train pool = 4,191.
- Ahmed chose: **eval pool keeps being looked at completely, by eye, in order** (unbiased benchmark). For the **train pool**,
  model C ranks frames (`tools/egm_mine_candidates.py`, `run_egm_mine.bat`, conf ≥ 0.05) so the frames most likely to hold
  a bump are looked at first. This changes the Stage 37 line "no GP36 model is run on egm" for train-creator frames only.
- Rules: C's boxes are never copied into labels and are not shown on the views used for drawing; every label is still drawn
  by looking. Eval-creator frames are never run through any model (asserted in the tool). Because the train frames are
  chosen with C's help, part `egm` will be biased toward what C already half-sees; this is acceptable for training, never
  for evaluation.
- Progress 2026-11-07 ~05:45: eval frames #0–629 looked at (of 1,287): 0 speed bumps, 0 potholes seen; night/blurred
  frames marked unsure, sky/side/hand-covered frames unusable. Log: review/new_data_r3/egm_labels/status_eval.csv
  (labeller=claude). C ranking of train-creator frames running (run_egm_mine.bat).

### Stage 37c (7 Nov) - egm train candidates checked by eye
- Top 54 train frames ranked by C bump score (max 3 per sequence, leak hit excluded): `GP36_Dataset/egm_work/cand_bump/`.
- Looked at all 54 (sheets + full-res zooms of c0, c3, c25, c36, c38, c47, c49). Real speed bumps found: 0.
- What C fires on: bridge expansion joints across the lane (c25, c47, c49), night glare / wet road, sky-tilted frames.
- Written: `status_train.csv` 54 rows (35 done with 0 boxes, 17 unusable, 2 unsure: c10 road patch, c28 rubble), labeller=claude. Empty label files in `labels_egm/train/`.
- `egm_ai_label.py write` now also takes `--id` (for frames outside egm_pool.csv).
- Eval pool still at index 630 of 1,287 (0 bumps so far).
