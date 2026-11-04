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
