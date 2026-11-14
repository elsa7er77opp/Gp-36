# Session report — 4–5 Nov 2026 (cloud sessions 1–5, D2 result, v3b_C build, crash and retry)

Scope: the five cloud sessions, and everything done on the laptop from the end of D2 to the v3b_C retry. Val only; **no test split was used**. Every number cites a file.

## 1. Cloud sessions (5 sessions, 4 Nov 2026; now finished)
The cloud sessions ran in a VM with **no GPU, no project datasets and no trained weights**. They produced code, data vetting, audits and instructions; every training and evaluation number comes from the laptop.
- Full cloud report: `review/new_data_r3/CLOUD_REPORT.md`. Every source checked, accepted or rejected: `review/new_data_r3/CANDIDATES.md`.
- The cloud credit is used up; no more cloud prompts will be sent.

| session | branch / PR | main output | laptop status |
|---|---|---|---|
| 1 | `claude/tender-faraday-43rjjv` (PR #1) | leak-rule bug fixed (v2); part `dmd`; P2 model yaml; calibration and vetting tools; 32 new tests | applied (STATUS Stage 21) |
| 2 | `claude/r3-cloud-data2` (PR #2) | 6 new Roboflow parts vetted: pol, red, ng8, hmp, ens, egy | applied (Stage 23) |
| 3 | `claude/r3-cloud-data3` (PR #3) | egy and hmp box audits; cross-source duplicate check; new pothole part `bpo` | applied (Stage 24) |
| 4 | `claude/r3-cloud-data4` (PR #4) | val/test audits of the decision part-vals → `_v2` parts; hmp audit corrected; `DATA.md` | applied (Stage 25) |
| 5 | `claude/r3-cloud-data5` (PR #5) | parts `irq` and `sau`; WBF, sliced inference and near-range metric; supervisor tables; test ledger; draft of the honest 0.90 statement | fetched and reviewed, **not applied** |

### Session 1: leak bug, first part, tools (STATUS Stage 21)
- **Network:** the VM could reach only GitHub and PyPI. The data search therefore used web and GitHub search.
- **Real bug found: leak rule v1 compared pHash unrotated only.**
  - So a flipped, re-encoded copy of a val/test image could pass the leak check.
  - On a rejected Roboflow re-export: rule v1 found 229 eval hits; the fixed rule v2 found 328.
  - Rule v2 compares both hashes under the same one of 8 flips/rotations (`tools/leak_check.py`, `tools/build_part.py`).
- **Two more fixes, made on the laptop during the review:**
  - `leak_check` now prefers the eval hit when an image matches both train and eval;
  - the guard-path parser no longer splits Windows paths at the drive colon.
- **Re-check of all data used so far with rule v2: 0 eval hits** (Stage 22: `recheck_rule_v2_all.csv`, `recheck_rule_v2_heldout_vs_train.csv`). The bug leaked nothing; the D1 results stand.
- **New part `dmd`** (dm-druid, China campus, marked bumps): 277 images, 319 bump boxes, train only.
- **New model file:** `models/yolo11n-p2.yaml`, YOLO11n with an extra stride-4 head for small objects. 2.67 M params vs 2.59 M; 23.7 vs 14.8 GFLOPs at 960 (`review/metrics_r3/model_check_yolo11n-p2.json`).
- **New tools:**
  - `calibrate_thresholds.py`: per-class thresholds from val only; refuses test;
  - `vet_source.py`, `make_items_yolo_export.py`, `sample_sheet.py`: the data gate.
- **Tests:** 32 new; the suite passed 139 OK after the fixes.
- **First supervisor drafts:** `supervisor_2026-11-08/README.md` and `METRICS.md`.

### Session 2: six new Roboflow parts (Stage 23)
- **Network:** open this time; Roboflow was used through the connector (public projects forked into `refyy-i`).
- **Parts vetted:**
  - bumps: `pol` (Indonesia, unmarked), `red` (Latin America), `ng8` (India dash video), `hmp` (India, night), `ens` (South Asia campus);
  - potholes: `egy` (Egypt dashcam).
- **Totals:** 1,973 new train bump boxes (1,551 without ens) and 835 Egyptian pothole boxes (`CLOUD_REPORT.md` §0.3).
- **Laptop checks before use:**
  - all six downloads matched the cloud's expected image counts;
  - ens was checked by eye against rf8 and accepted as train-only.

### Session 3: audits and a new pothole source (Stage 24)
- **egy audit, all 954 boxes:** 400 are not potholes (270 are manholes or grates) → corrected part `egy_v2`: 500 train / 30 val / 23 test pothole boxes.
- **hmp:** made train-only (`hmpt`), because its val is half stock or rotated photos.
- **Cross-source duplicates:** 2 train/train pairs; nothing to drop from val/test (`vet/CROSS_SOURCE.md`).
- **New part `bpo`** (BharatPotHole, India dashcam): 1,413 train pothole boxes.

### Session 4: decision part-val audits (Stage 25)
- **Audits** (`vet/VALTEST_AUDIT_S4.md`):
  - pol and red: 0 % errors;
  - ng8: 1 test image dropped;
  - **bpo:** val 12 % / test 19 % definite errors → train-only.
- **Corrected part versions:** `pol_v2`, `red_v2`, `ng8_v2`.
- **Self-correction:** the session-3 hmp audit had misread polygon labels. The real test error rate is 0 %, not 35 %; hmp stays train-only for its other reasons.
- **d7k** (a 7k-image dashcam set) is the upstream of bpo, so it is not a new source.
- **`supervisor_2026-11-08/DATA.md`:** every part with its source, licence, region, counts and gates.

### Session 5: "full effort toward 0.90" (PR #5, not applied yet)
- **Data:**
  - `irq` (IRDD, Iraq dashcam): 7,802 images, 2,118 pothole boxes, train-only;
  - `sau` (SaudiRD): 461 frames, 459 of them hazard-free negatives.
  - Both are candidates for an A/B after v3b_C. Rejected sources: `CANDIDATES.md` §I.
- **Main gap still open:** ≥ 800 unmarked Egyptian bump boxes. No public forward-view MENA source exists. Remaining routes:
  - author request emails in `REQUESTS.md`;
  - an Egyptian Mapillary labelling pool (`tools/make_egm_pool.py`, `vet/egm/`).
- **Evaluation and inference tools**, each a separate row with a pre-registered hypothesis (`CLOUD_REPORT.md` §0-S5 B):
  - `metrics_report.py --care near`: near-range AP with ignore-region semantics, always shown next to full mAP50;
  - `wbf_ensemble.py`: weighted boxes fusion of 2+ models;
  - `sliced_predict.py`: full frame plus tiles, for far small potholes;
  - TTA command.
- **Training recipes for the RTX 5050**, ≤ 4 h each:
  - R-A: long run plus close_mosaic 15;
  - R-B: imgsz 1280;
  - R-C: P2 head.
- **Supervisor tools:**
  - `make_supervisor_tables.py`: formats reports only; refuses to call val "test";
  - `test_ledger.py` + `TEST_LEDGER.csv`: one test use per model per benchmark; past uses back-filled.
- **Draft:** the honest 0.90 statement (README §4a).
- **Tests:** 188 run, OK.
- `leak_check.py`: new KNOWN_FAMILY `SpeedBreaker-N-`.
- The review on the laptop found the code sound.

## 2. D2 result (STATUS Stage 26)
Source: `review/metrics_r3/val_r2_D2`, `partval_sr_D2`, `partval_rsid_D2`, `partval_bucko_D2`.

| eval set | class | D1 s0 AP50 | D2 AP50 |
|---|---|---|---|
| r2 val | pothole | 0.596 | 0.615 |
| r2 val | speed_bump | 0.710 | 0.683 |
| r2 val | mean | 0.653 | 0.649 |
| sr part-val | pothole | 0.396 | 0.433 |
| RSID part-val | pothole | 0.259 | 0.307 |
| RSID part-val | speed_bump | 0.670 | 0.630 |
| Bučko part-val | pothole | 0.571 | 0.617 |

- **H-D2 REJECTED.** The sr pothole gain was +0.037; the hypothesis required ≥ +0.10.
- **The inclusion guard HELD**, so `sr` minus `rad` goes into v3b_C, as pre-registered.
- Bump NearR fell from 0.280 to 0.146; bump P@R50 rose from 0.863 to 0.904.
- The main gain is on unseen sources, compared with v1:
  - RSID bump: 0.028 → 0.630;
  - Bučko pothole: 0.399 → 0.617.
- On r2 val, no model has beaten v1 yet (pothole 0.628, bump 0.710).

## 3. v3b_C: plan, build and check (STATUS Stage 27, written before any result)
- **Recipe:** r2 + rsid + bucko + rdd_ji:500 + sr (minus rad) + dmd + pol_v2 + red_v2 + ng8_v2 + hmpt + ens + egy_v2 + bpo.
- **Baseline:** B\* = D1 s0 (r2-val mean 0.653 vs D2 0.649).
- **Hypotheses** (Stages 24–25):
  - **H-C1:** r2 val ≥ B\* − 0.02, RSID bump ≥ B\* − 0.03 and Bučko pothole ≥ B\* − 0.03.
  - **H-C3:** pol_v2 bump ≥ B\* + 0.15, ng8_v2 bump ≥ B\* + 0.10, and ng8_v2 ImgAcc ≥ B\*.
  - **H-C4:** r2 bump and pothole each +0.00 to +0.04.
- **New tool:** `tools/check_parts_expected.py` compares the laptop part builds with the cloud's `expected_build_info*.json`.
  - Gate: for the decision part-vals (`_v2`), val/test counts must match exactly; train counts must be within 2 %.
  - Result: **PASS** (`review/new_data_r3/vet/laptop_build_check_20261105_020633.md`).
- **Composed dataset** `road_hazards_v3b_C`, train split:

  | | D2 | v3b_C |
  |---|---|---|
  | images | 6,893 | 10,562 |
  | pothole boxes | 5,055 | 6,968 |
  | speed_bump boxes | 1,925 | 3,982 |
  | negatives | — | 3,446 |

- **Baseline vals:** D1 s0 and D2 were run on pol_v2, red_v2, ng8_v2 and egy_v2 (`runs/detect/PARTVAL_<p>_D1s0`, `PARTVAL_<p>_D2`).

## 4. Problems and fixes
1. **First launch stopped immediately.**
   - Error: `'run_r3_parts_C.bat' is not recognized`. On this machine, cmd does not find a .bat in the current folder by bare name.
   - Fix: `call "%~dp0run_r3_parts_C.bat"`. Relaunched in window PID 35636; the first window, PID 21336, is left open.
2. **v3b_C training crashed at epoch 1** (5 Nov, 02:22).
   - Run folder: `runs/detect/v3b_C_11n_960_s0`. It has no `results.csv` and no weights; it is kept as evidence.
   - Error (window text): `torch.AcceleratorError: CUDA error: resource already mapped`, raised in the DataLoader **pin-memory thread**.
   - Cause: pinned host memory failed. This is a transient driver/RAM issue, not a data or model problem. RAM is 16 GB, and 4.1 GB was free when checked after the crash.
   - D1 and D2 ran 70/70 epochs with the same arguments.
   - Nothing after training ran. The window stopped as designed ("a step failed, nothing after it was run").
3. **Retry** (5 Nov afternoon):
   - `run_r3_C_retry_visible.bat`: same data and same arguments, new name `v3b_C_11n_960_s0_r2`.
   - It trains, runs the val evals, then writes the `review/metrics_r3/*_C` reports.
   - Before launch: the D1/D2 baseline predictions were checked to exist, and no GPU job was running.
   - **Fallback if the crash repeats:** `workers=0`. This disables pinned memory and is slower.

## 5. Question answered: "is there a problem in the layers?"
No. The evidence is `runs/detect/v3b_A_11n_960_s0/results.csv` and `v3b_B_11n_960_s0/results.csv`:
- All layers are trained (`freeze: null`), starting from pretrained `yolo11n.pt`.
- Train loss falls until the last epoch. For D1, box loss goes from 2.41 to 1.52 and cls loss from 6.24 to 1.05, so the model learns.
- Val mAP50 rises until about epoch 50, then flattens:
  - D1: 0.637 at epoch 50, 0.658 at epoch 70 (best 0.667 at epoch 64);
  - D2: 0.627 at epoch 50, 0.643 at epoch 70.
- Val box loss is flat at about 2.0 from epoch 30 on.

So the model fits the training data but does not generalize further. The limit is the data and the domain gap, plus the smallest model size, not slow learning. More epochs alone are unlikely to help much.

Architecture levers worth testing **after** v3b_C, each as a separate pre-registered row:
- **P2 head** (cloud recipe R-C): an extra stride-4 detection layer for small, far objects (`models/yolo11n-p2.yaml`).
- **imgsz 1280** (R-B): far potholes become larger, at about 1.8× the compute.
- **YOLO11s:** at 70 epochs it gave only +0.005 overall (STATUS Stage 16, rejected). It is kept only as a long-training row (L2).

## 6. Idea discussed: sensor + camera fusion
- **Idea:** when the range sensor or IMU and the camera both detect something raised, count it as a bump.
- **Verdict:** a valid **system-level** feature. `perception/fsm.py` already notes that the range sensor and IMU are not yet connected.
- **Limits:**
  - It does **not** change model mAP. Counting sensor hits as correct camera detections would not be an honest model metric.
  - "Raised" also matches curbs, cars and people.
  - Potholes are depressions, so this does not help them.
- **If built**, report it separately as a system metric, e.g. bump confirmation rate with fusion vs. camera only, defined before it is measured.
- `perception/` safety logic is not changed for metrics.

## 7. Working mode from 5 Nov
Ahmed applies and runs the code. Claude sends files, code and commands, and only acts when explicitly asked. Visible `cmd /k` windows are never closed.

## 8. Pending
- [ ] v3b_C retry finishes → read `review/metrics_r3/*_C/report.md` → judge H-C1, H-C3 and H-C4 against D1 s0 → STATUS Stage 28.
- [ ] Apply PR #5 tools (near-range, WBF, sliced, TTA rows, supervisor tables, test ledger).
- [ ] Long run L1 (150 epochs) on the best data version; 11s / P2 if time allows.
- [ ] Final candidates chosen on val only, then one test use each, logged in `TEST_LEDGER.csv`.
- [ ] Supervisor package `supervisor_2026-11-08/` with the honest 0.90 statement.
