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
