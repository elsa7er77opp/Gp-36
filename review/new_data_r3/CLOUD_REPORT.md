# GP36 — cloud session report (2026-11-04)

Session type: cloud VM, **no GPU, no project datasets, no trained weights**. Everything here is code, reports and
instructions for the training laptop. Labels: VERIFIED (read from a file or command output named here) ·
PROVISIONAL · UNRESOLVED · BLOCKED. No number in this file comes from a training run made here.

## 0-S5. Session 5 (2026-11-04 night): "full effort toward 0.90, honestly"
Branch `claude/r3-cloud-data5` (from `claude/r3-cloud-data4`). The v3b_C recipe is fixed on the laptop and is **not** changed
here. Nothing below is a result of a run made here; every row of the lever table is a PRE-REGISTERED hypothesis.

### Task status
| task | status | files |
|---|---|---|
| A data: search (Roboflow in 7 languages, Kaggle 39 terms, GitHub, HF, Zenodo, Figshare) | done; Mendeley / IEEE DataPort / PapersWithCode not re-searched (time) | `CANDIDATES.md` §I |
| A data: SaudiRD vetted → part `sau` (461 train, 459 hazard-free, all frames scanned) | done | `vet/sau/` |
| A data: IRDD (Iraq) → part `irq` (train-only, 2,118 pothole boxes) | done; val/test needs a full box audit | `vet/irq/` |
| A data: ≥ 800 unmarked bump boxes | **not met**: no public forward-view MENA source exists; requests drafted | `REQUESTS.md`, `vet/egm/` |
| A data: Egyptian Mapillary labelling pool | partial (tool + Cairo sample; labels needed) | `tools/make_egm_pool.py`, `vet/egm/README.md` |
| B1 `--care near` | done + tests | `tools/metrics_report.py` |
| B2 WBF | done + tests | `tools/wbf_ensemble.py` |
| B3 sliced inference | done (pure parts tested; GPU run on laptop) | `tools/sliced_predict.py` |
| B4 TTA | laptop command | §B below |
| B5 training recipes | 3 sets (R-A, R-B, R-C) + 3 rejected options with reasons | §B below |
| C1 supervisor tables | done + tests; val r2 tables generated | `tools/make_supervisor_tables.py`, `supervisor_2026-11-08/TABLES_val_r2_2026-11-04.md` |
| C2 test ledger | done + tests; back-filled (3 VERIFIED, 2 NOT_A_USE, 2 UNRESOLVED) | `tools/test_ledger.py`, `review/metrics_r3/TEST_LEDGER.csv` |
| C3 honest 0.90 statement | draft with `TODO(laptop)` | `supervisor_2026-11-08/README.md` §4a |
| D tests, re-read, risks | done: 188 run, OK, 3 skipped | §D below |

### A. Data (details: `CANDIDATES.md` §I)
New parts, both train only. The v3b_C recipe is unchanged; these are **candidates for an A/B after v3b_C**:
- `sau`: 461 images (459 hazard-free, 2 pothole boxes); SaudiRD windscreen frames, every frame checked by eye.
- `irq`: 7,802 images, 2,118 pothole boxes, 6,348 crack-only frames; IRDD, Iraqi smartphone dashcam.

Rejected: ztskn, sakib (re-uploads of `speedbreakerrefinedone`), tipdu (rf8 re-upload, 59 eval hits), road-hump (close-up
crops), the HF RDD-Egypt export (duplicate of `egy`), speedregulator (= `sr`). The main gap, **unmarked Egyptian bumps,
is not closed**. The two real routes are the author requests (`REQUESTS.md` R1, R2) and labelling the Egyptian
Mapillary pool (`vet/egm/README.md`).

**Laptop commands (A), after v3b_C is trained**, in order:
1. Build `sau` and `irq` with the commands in `vet/sau/VISUAL_SCAN.md` and `vet/irq/README.md`. Compare each build
   with its `expected_build_info.json`.
2. A/B, one seed each, same recipe as v3b_C plus one part:
   - `v3b_C+irq`: decide on Bučko val and egy_v2 val (potholes) and r2 val (both classes);
   - `v3b_C+sau`: decide on pol_v2, red_v2, ng8_v2 (bumps) and r2 val.

   Accept rules: `vet/irq/README.md`, and §D risk 6 for `sau`.
3. Before using irq's frames as bump negatives, scan a sample for unlabelled bumps (as was done for `sau`).

### B. Evaluation and inference levers (code tested here; GPU numbers come from the laptop)
Decision data for every lever: **r2 val** (frozen) + the part-vals pol_v2, red_v2, ng8_v2 (bumps), egy_v2, Bučko
(potholes). The test split is never used to choose a lever, a threshold or a merge setting. Baseline = the laptop's
v3b_C 11n 960 s0 model (or the best val model at that time), scored with the same tool. Seed noise for one seed:
mAP50 0.6747 ± 0.0106 (`runs/v3a_r2_seed_summary.txt`), so a lever needs Δ ≥ +0.02 (≈ 2 std) on r2 val all-class
mAP50 **or** on one class with the other class not dropping by more than 0.02.

| # | lever | tool / command | pre-registered hypothesis (written 2026-11-04, before any value) | accept rule | cost |
|---|---|---|---|---|---|
| B1 | near-range metric (`--care near`) | `tools/metrics_report.py --care near` | Not a model change, a second view. H (pothole): near AP50 ≥ full AP50, because far tiny potholes are a known miss (Stage 9 failure analysis) and ignoring far FPs removes false alarms too. H (bump): near AP50 **<** full AP50. At the operating threshold, NearR is below full recall for both classes for D1 (pothole 0.542 vs 0.579; bump 0.280 vs 0.619; `review/metrics_r3/val_r2_all_2026-11-04/report.md`), so near bumps are missed more often than far ones. Both outcomes are reported, whichever way they go. | none (a metric), always next to full AP50 | CPU, minutes |
| B2 | WBF of ≥ 2 models | `tools/wbf_ensemble.py --pred A --pred B --iou 0.55` | H: WBF(v3b_C 11n, D1_11s) gives +0.01–0.03 AP50 per class over the better single model on r2 val (the two models differ per class: 11s pothole 0.625 vs 11n 0.596, 11n bump 0.710 vs 11s 0.692, same report). Latency = sum of both models (not deployable on the Pi-side budget unless gain ≥ 0.03). | Δ ≥ +0.02 on a class, other class ≥ −0.02 | CPU merge + 2 val runs |
| B3 | sliced inference | `tools/sliced_predict.py --tile 640 --overlap 0.25 --rows-from 0.4 --merge nms` | H: pothole AP50 +0.02–0.05 (far potholes become larger in a tile); bump AP50 ±0.01; near-range AP50 unchanged (near boxes are already large); latency ×3–5 (full frame + ≈ 4–6 tiles). If the gain is real but the latency is not affordable, the result still tells us that resolution, not data, limits far potholes → B5 R-B / R-C. | Δ pothole ≥ +0.02, bump ≥ −0.02; latency reported | GPU, ≈ 10–20 min on r2 val |
| B4 | TTA (`augment=True`) | command below | H: +0.01–0.03 AP50 (Stage 20 L4), ≈ 2–3× slower | Δ ≥ +0.02 | GPU, minutes |
| B5 | training recipes R-A / R-B / R-C | below | see each row | Δ ≥ +0.02 all mAP50 on r2 val, no class −0.02; part-vals reported, not used to pick | ≤ 4 h each |

**Merge-setting rule (B2, B3):** defaults are fixed now (WBF iou 0.55, skip 0.001; sliced: tile 640, overlap 0.25, rows-from
0.4, NMS iou 0.5). At most ONE alternative per lever (WBF iou 0.6; sliced `--merge wbf`) may be tried, on r2 val only, and
both rows are reported. No grid search.

**Laptop commands (B), in order** — Windows, venv; `<M>` = the v3b_C model name, `<M2>` = `v3b_A_11s_960_s0`.
```
rem B1: near-range next to full, on existing val predictions (no GPU)
python -I tools/metrics_report.py --data road_hazards_v3a_r2 --split val --care near ^
    --pred <M>=runs\detect\<M>_VALr2_json\predictions.json --pred D1_11n=runs\detect\v3b_A_11n_960_s0_VALr2_json\predictions.json ^
    --pred D1_11s=runs\detect\v3b_A_11s_960_s0_VALr2_json\predictions.json --out review\metrics_r3\val_r2_near_<date>
rem B4: TTA on r2 val
venv\Scripts\yolo val model=runs\detect\<M>\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 ^
    save_json=True augment=True plots=False name=<M>_TTA_VALr2_json > runs\<M>_TTA_VALr2_json.txt 2>&1
rem B2: WBF of two val prediction files
python -I tools/wbf_ensemble.py --pred runs\detect\<M>_VALr2_json\predictions.json ^
    --pred runs\detect\v3b_A_11s_960_s0_VALr2_json\predictions.json --out runs\detect\WBF_<M>_11s_VALr2\predictions.json
rem B3: sliced inference on r2 val (also writes predictions_latency.json)
python -I tools/sliced_predict.py --weights runs\detect\<M>\weights\best.pt --data road_hazards_v3a_r2 --split val ^
    --imgsz 960 --tile 640 --overlap 0.25 --rows-from 0.4 --merge nms --out runs\detect\SLICED_<M>_VALr2\predictions.json
rem score B2-B4 with the same tool, near next to all
python -I tools/metrics_report.py --data road_hazards_v3a_r2 --split val --care near ^
    --pred base=runs\detect\<M>_VALr2_json\predictions.json --pred tta=runs\detect\<M>_TTA_VALr2_json\predictions.json ^
    --pred wbf=runs\detect\WBF_<M>_11s_VALr2\predictions.json --pred sliced=runs\detect\SLICED_<M>_VALr2\predictions.json ^
    --out review\metrics_r3\val_r2_levers_<date>
rem latency of TTA / 11s with the existing bench (same frames, same config); sliced latency is in its _latency.json
python -I tools/latency_bench.py --frames road_hazards_v3a_r2/images/val --n 300 --hazard runs\detect\<M>\weights\best.pt --out runs\latency_<date>_<M>.json
```
Note: Ultralytics `save_json` image_id may be an int for numeric stems; `metrics_report.py` compares `str(image_id)`, as
the sliced tool writes it.

**B5 — training recipes for the RTX 5050 (8 GB), ≤ 4 h each.** Throughput basis (VERIFIED, STATUS Stage 18 note):
YOLO11n, imgsz 960, batch 8 ≈ 26 train img/s ≈ 90k image-epochs per hour; D1 70 epochs took 1.948 h; 11s 70 epochs
2.803 h. So epochs E = min(150, floor(3.6 h × 90,000 / N_train)) for 11n at 960, where N_train = the v3b_C train count
from its `build_info.json` (not known here). At 1280 the cost per image is ≈ (1280/960)² = 1.78× → E_1280 ≈ E / 1.78.
Each run is one seed (s0); a winner gets a 2nd seed before it is called a gain.

| id | `yolo train` arguments (data=road_hazards_v3b_C\data.yaml, seed=0, deterministic=True, workers=2, cache=disk) | reason | hypothesis vs v3b_C 70-ep baseline |
|---|---|---|---|
| R-A long | `model=yolo11n.pt imgsz=960 batch=8 epochs=E patience=30 close_mosaic=15 mixup=0.1 scale=0.6` | D1 mAP50 still rising at ep 70 (0.654 → 0.658, Stage 20 L1); more close_mosaic epochs help the real-frame layout at the end; mild mixup + a wider scale range widen the size distribution of bumps | all mAP50 +0.01–0.03; both classes ≥ 0; latency unchanged |
| R-B 1280 | `model=yolo11n.pt imgsz=1280 batch=4 epochs=E_1280 patience=30 close_mosaic=10` (val/predict also at imgsz=1280) | far potholes are tiny at 960 (FAR_TINY rule removes only sqrt < 0.02; many remain at 0.02–0.05) | pothole +0.02–0.05, bump ±0.02; latency ≈ 1.8×. If STATUS already ran "1280", this row is that run and is NOT repeated |
| R-C P2 head | `model=models/yolo11n-p2.yaml pretrained=yolo11n.pt imgsz=960 batch=6 epochs=E patience=30 close_mosaic=15` (check first: `python -I tools/check_model_yaml.py models/yolo11n-p2.yaml`; `review/metrics_r3/model_check_yolo11n-p2.json`) | stride-4 head for small objects without the 1280 memory cost | pothole +0.02–0.04, near-range unchanged, latency +30–60 % |

Not proposed, and why:
- 11s vs 11n: done in Stage 16 (+0.005 all, REJECTED); Stage 20 L2 (11s with long training) is already on the laptop plan.
- `multi_scale=True`: at imgsz 960 it trains at up to 1.5× = 1440 px; with batch 8 on 8 GB this is an OOM risk, and
  batch 4 would halve throughput. Not worth a 4 h slot before R-A/R-B.
- `copy_paste`: in Ultralytics it pastes **segment** instances; our labels are boxes only, so it should do nothing
  (PROVISIONAL — check on the laptop: `findstr /n "segments" venv\Lib\site-packages\ultralytics\data\augment.py` near
  `class CopyPaste`). Not proposed.

### C. Supervisor deliverables
- `tools/make_supervisor_tables.py` + spec `supervisor_2026-11-08/tables_spec_val.json`: Markdown tables per class at
  the val-chosen threshold and at conf 0.35. Columns: P, R, F1, AP50, AP50-95, BoxAcc, ImgAcc, NearR, P@R50,
  near AP50, plus counts and the source file per row. With `figures: true` it also draws PNG figures. It only copies
  numbers and refuses a spec that calls a val report "test". Output from the existing report:
  `supervisor_2026-11-08/TABLES_val_r2_2026-11-04.md`. The values match `review/metrics_r3/val_r2_all_2026-11-04/report.md`
  (spot check: D1_11n pothole 0.596 / bump 0.710). The PNGs are generated on the laptop (images are not committed).
- `tools/test_ledger.py` + `review/metrics_r3/TEST_LEDGER.csv`, back-filled from the STATUS test-use log:
  - uses 1–3 are VERIFIED;
  - the two 21:48 BD87 attempts are NOT_A_USE;
  - v1 and v8n on the r1 test are UNRESOLVED (time not in any file seen here) and still block a repeat.
  - STATUS Stages 22–25, cited in the session-5 brief, are **not in the repo copy**, which ends at Stage 21. Any test
    use logged there must be added on the laptop: `TODO(laptop)`.
- `supervisor_2026-11-08/README.md` §4a: the "Honest 0.90 statement" (draft). It lists:
  - what can plausibly reach about 0.90: ImgAcc pothole, P@R50 bump, and near-range AP (not computed yet);
  - what cannot by 8 Nov: full per-class mAP50, with the evidence files;
  - what more time would bring;
  - `TODO(laptop)` placeholders.

  `METRICS.md` §1 has the near-range definition, written before any value.

### D. Quality and risks
Tests: `cd tests && python3 -m unittest discover -s .` → **188 run, OK, 3 skipped** (VERIFIED, 2026-11-04, cloud;
147 at the end of session 4). New test files: `test_wbf_ensemble`, `test_sliced_predict`,
`test_make_supervisor_tables`, `test_test_ledger`, `test_make_egm_pool`, plus `TestNearCare` in
`test_metrics_report` and a family case in `test_leak_check`.

Risks (found while re-reading the new code; none is known to be a bug):
1. **Near-range metric**
   - An unmatched prediction is ignored when the *prediction box itself* fails the care rule (y2 < 0.60 H or
     sqrt(area) < 0.05). The brief says "fully outside the care range"; we read "outside" with the same box rule
     as for GT, not as "no pixel below 0.6 H". A large far FP whose box reaches below 0.6 H still counts as an FP.
   - Matching takes care GT first. A duplicate prediction on a care GT that also overlaps an ignore GT is ignored,
     not counted as an FP (COCO crowd semantics).
   - A model that is blind far away looks good on this metric. That is why it is never shown alone.
2. **WBF:**
   - Scores are a weighted mean, rescaled by the share of models that agree. The paper's variant can exceed 1; ours
     cannot. Scores therefore differ from ZFTurbo's library, but the ranking within one setting is consistent.
   - `image_id` is matched as given. If one file has int ids and the other has str ids for the same image, the boxes
     are not fused. Both files come from the same Ultralytics version, so this is not expected; it is checked by the
     `boxes_in` / `boxes_out` counts in `_wbf_info.json`.
3. **Sliced inference:**
   - Boxes that touch an inner tile border are dropped; the full frame or a neighbouring tile must catch them. With
     640 px tiles and 25 % overlap, any object under 160 px fits whole in some tile.
   - `--rows-from 0.4` skips only tiles that end above 0.4 H. For 1080p frames that is none, so the default tiles
     everything.
   - The latency (×3–5, an estimate) has not been measured: PROVISIONAL until the laptop run.
   - It runs on the laptop only (needs ultralytics). Only the pure functions are tested here.
4. **Supervisor tables:**
   - They refuse a spec whose split differs from the report. They do **not** check that a test report used
     `--thresholds` from val; `metrics_report.py` itself refuses test without thresholds.
5. **Test ledger:**
   - It only works if it is run. `check` must come before every `yolo val split=test`.
   - Unclear past uses (UNRESOLVED) block a repeat on purpose.
   - Model names are matched exactly (after case and space normalisation), so `best.pt` paths must use the run name.
6. **Data `sau`:** these are hard negatives from Saudi highways and residential roads.
   - 12 ambiguous frames were removed by eye. A missed faint stud-hump in the remaining 459 frames would be a wrong
     negative (train only, so it cannot inflate any score).
   - The effect on bump recall must be checked on the part-vals (pol_v2, red_v2, ng8_v2). If bump AP drops by more
     than 0.02 there, drop `sau`.
7. **egm (Egyptian Mapillary):**
   - The licence is mixed (the mirror says Apache-2.0, Mapillary is CC BY-SA 4.0).
   - The frames are unlabelled and the tile→location map is fitted on only 3 tiles.
   - No boxes are counted until a person has labelled the frames.
8. **IRDD:**
   - Its own split is stratified by label, not by sequence. We re-split by our group rule, and its val/test are
     **not** used as given.
   - OBB → axis-aligned boxes inflate the box area for slanted potholes. That is acceptable for AP50 training labels
     but noted.
9. **KNOWN_FAMILIES += `SpeedBreaker-N-`:** no accepted part contains the pattern (checked against every
   `vet/*/keep_list.csv`). Case matters: `speedbreaker_N` (ng8) is not matched.

## 0-S4. Session 4 (2026-11-04 late): audits of the decision part-vals, d7k / CMIRD, DATA.md
Branch `claude/r3-cloud-data4` (from `claude/r3-cloud-data3`). The v3b_C recipe is fixed on the laptop and is **not** changed here.

### Task status
| task | status | files |
|---|---|---|
| 1 val/test audit bpo, pol, ng8, red (+100 train each) + `--drop-images` | **done**. pol and red: 0 errors. ng8: 0 box errors, 1 test image dropped for an unlabelled pothole. **bpo val 12.0 % / test 19.4 % definite errors → recommend train-only.** A tooling bug was found (polygons misread in the crop sheets); 25 bpo rows were re-judged and the **session-3 hmp audit was corrected** (test 35.3 % → 0 % / 5.9 % with uncertain) | `vet/VALTEST_AUDIT_S4.md`, `vet/<part>/box_audit.csv`, `valtest_missing_labels.csv`, `expected_build_info_<part>_v2.json`, `vet/hmp/BOX_AUDIT.md`, `tools/apply_box_corrections.py`, `tools/audit_crop_sheets.py`, `tests/test_apply_box_corrections.py` |
| 2 pothole sources | **partly done**. d7k pre-checked: it is the upstream of bpo (same drives), so it is not a third source. CMIRD class IDs found, but pothole vs crack (IDs 7/4) is unclear → UNRESOLVED. New MENA leads: SaudiRD (forked, export pending), KFUPM Saudi set (request), HRP4K (laptop). The ≥ 3-source pothole target is **still not met**: accepted pothole sources are egy_v2 and bpo (same family as d7k) | `vet/d7k/PRECHECK.md`, `CANDIDATES.md` §H |
| 3 DATA.md | **done** (§6: every new part with source, licence, region, counts from the expected files, gates, rejected summary, leak rule v2) | `supervisor_2026-11-08/DATA.md` |

### Laptop commands (after the parts of §0-S3 / §3 are built)
```
rem corrected decision part-vals (new folders; the old parts stay)
for %P in (pol ng8 red bpo) do venv\Scripts\python -I tools/apply_box_corrections.py --part parts_r3/%P --audit review/new_data_r3/vet/%P/box_audit.csv --drop-images review/new_data_r3/vet/%P/valtest_missing_labels.csv --out parts_r3/%P_v2
rem compare each parts_r3/<p>_v2/build_info.json "splits" with review/new_data_r3/vet/<p>/expected_build_info_<p>_v2.json
```
- Part-vals for judging v3b_C: **pol_v2, red_v2, ng8_v2** (bumps), **egy_v2** and Bučko (potholes).
- Do **not** use bpo val/test for decisions. In the fixed recipe, bpo stays as it is in train (bpo_v2 train is identical: 1,413 boxes).
- d7k: see `vet/d7k/PRECHECK.md`. Use it only instead of bpo, never together with it.
- (`%P` → `%%P` in a .bat.)

### Roboflow forks (session 4)
`refyy-i/saudird-luumi` (SaudiRD, export pending; LAPTOP-VET: 1,171 images, only 144 pothole boxes per the project metadata). Nothing to delete from this session.

## 0-S3. Session 3 (2026-11-04 evening): audits, cross-source check, potholes
Branch `claude/r3-cloud-data3` (from `claude/r3-cloud-data2`). The v3b_C recipe is NOT changed here; the numbers below are inputs for the laptop's decision after D2.

### Task status
| task | status | files |
|---|---|---|
| 1 egy box audit (all 954 Pothole boxes) | **done**. 400 boxes are not potholes, incl. 270 manhole covers or drain grates. `egy_v2`: train 500 / val 30 / test 23 pothole boxes (VERIFIED, cloud build) | `vet/egy/box_audit.csv`, `vet/egy/BOX_AUDIT.md`, `vet/egy/expected_build_info_egy_v2.json`, `tools/apply_box_corrections.py`, `tests/test_apply_box_corrections.py` |
| 2 hmp audit (all val/test boxes + 100 train, seed 0) | **done**. Box error rate: val 0 %, **test 35.3 %**, train 4 %. Val is 51 % product, stock or rotated photos, and same-scene copies span the splits → **recommend hmp train-only** | `vet/hmp/box_audit.csv`, `vet/hmp/BOX_AUDIT.md` |
| 3 cross-source duplicates | **done**. 2 rule-v2 pairs (dmd/train = hmp/train), 0 hits on protected sets, **empty val/test drop list**; 44 loose pairs touching val/test checked by eye: none is a duplicate | `vet/cross_source_pairs.csv`, `vet/cross_source_drop_valtest.csv`, `vet/CROSS_SOURCE.md`, `tools/cross_source_dups.py` |
| 4 potholes (target ≥ 1,500 boxes from ≥ 3 sources) | **partly met**. 1 new source accepted (`bpo`, India dashcam): **1,829 pothole boxes** (1,413 train / 214 val / 202 test). Plus `egy_v2` (Egypt, from session 2): 553. The ≥ 3-source target is **not met**; one 7k-image dashcam set is waiting for the laptop (over the size limit) | `vet/bpo/*`, `CANDIDATES.md` §G |

### Laptop commands (same style as §3; run after §3 steps 1–3 have built `egy`)
```
rem egy_v2 = egy with the audited boxes removed (new folder; parts_r3/egy is not changed)
venv\Scripts\python -I tools/apply_box_corrections.py --part parts_r3/egy --audit review/new_data_r3/vet/egy/box_audit.csv --out parts_r3/egy_v2
rem compare parts_r3/egy_v2/build_info.json "splits" with review/new_data_r3/vet/egy/expected_build_info_egy_v2.json

rem hmp train-only: rebuild the items with every image in train (new part name, old one kept)
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_humps\x --part hmpt --cmap "{\"0\": \"ignore\", \"1\": \"speed_bump\", \"2\": \"ignore\", \"3\": \"pothole\", \"4\": \"ignore\"}" --include "humps-v\d+-_\d+" --all-train --out review/new_data_r3/items/items_hmpt.csv
venv\Scripts\python -I tools/build_part.py --items review/new_data_r3/items/items_hmpt.csv --part hmpt --out parts_r3/hmpt --guard %G%

rem bpo = BharatPotHole (India dashcam potholes)
venv\Scripts\python -I tools/rf_download.py refyy-i/bharatpothole-udcit 1 ..\GP36_Dataset\raw_v3\rf_bharat
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_bharat\x --part bpo --cmap "{\"0\": \"pothole\"}" --include ".*_frame_\d*[02468]" "--group-regex=^(\d{14}_\d{4}|signal-[\d-]+-\d{6}(?:_\d{3})?)" --out review/new_data_r3/items/items_bpo.csv
venv\Scripts\python -I tools/build_part.py --items review/new_data_r3/items/items_bpo.csv --part bpo --out parts_r3/bpo --guard %G%
rem compare with review/new_data_r3/vet/bpo/expected_build_info.json and keep_list.csv

rem optional, pothole source over the size limit here
venv\Scripts\python -I tools/rf_download.py refyy-i/dashcam-mg6en-0fwjp 1 ..\GP36_Dataset\raw_v3\rf_dashcam7k
venv\Scripts\python -I tools/vet_source.py --name d7k --root ..\GP36_Dataset\raw_v3\rf_dashcam7k\x --out review/new_data_r3/vet/d7k --sheet ..\GP36_Dataset\_sheets\sheet_d7k.jpg
```
- Expected `bpo` (VERIFIED, cloud build with the protected hashes): train 442 images / 1,413 pothole boxes, val 102 / 214, test 93 / 202. Drops: 36 `only_far_tiny`; 158 FAR_TINY boxes were removed. 0 leak drops.
- `bpo` val/test (13 + 13 videos) can serve as a new-country pothole part-val. It is labelled by the uploader and has not been audited box by box; a sample audit like hmp's is advised before it is used for a decision.
- Arithmetic for the laptop's `rdd_ji` question (PROVISIONAL, no recipe change):
  - `bpo` train (1,413) + `egy_v2` train (500) = 1,913 new forward-view pothole boxes. That is close to the ≈ 930 boxes from `rdd_ji:500` that §3 removes (1.86 per image, `parts_r3/rdd_ji/build_info.json`), plus about 980 more.
  - The egy correction itself removes 335 train boxes compared with the §3 arithmetic (835 → 500).

## 0. Session 2 (2026-11-04 afternoon, network open) — PARTIAL, updated as parts are accepted
### 0.1 Access check in this VM (VERIFIED by request results, 2026-11-04 ~14:00 UTC)
| host | result | note |
|---|---|---|
| www.kaggle.com/api/v1 | 200 | `KAGGLE_API_TOKEN` set; downloads work (`tools/kaggle_dl.py`); file listings hit HTTP 429 quickly |
| zenodo.org, api.figshare.com, huggingface.co, data.mendeley.com, ieee-dataport.org, arxiv.org | 200 | |
| api.roboflow.com | 200, but the key in the env (`roboflow_api_token`) is a **publishable `rf_` key** → 401 "API key does not exist" on dataset calls | `ROBOFLOW_API_KEY` is not set |
| Roboflow connector (MCP, workspace `refyy-i`) | works | public Universe projects were **forked** into `refyy-i`, a version with **no augmentation / no resize** generated, exported as yolov8 |
| universe.roboflow.com (web) | 403 | not needed with the connector |
| www.mdpi.com | 403 | |
| tihan.iith.ac.in/tiand-datasets/ | 404 | DriveIndia still not published there |

Roboflow forks created in `refyy-i` (all private copies of public CC BY / MIT projects): unmarked-bumps-dkmuf,
speed-unmarked-bumb-p4jcc, speed-bump-yiaek-ktwnm, speed-bump-tonyt-jdbdu, total-jcwvt-f9ffa, rdd-6706t-8szyz,
speed-bump-detection-pwqpb-kdlvd, speed-bump-detection-xd07j-fhzl2, pothole-speed-bump-bmcyv, speed-bump-vl46b-ukywr,
speed-bump-jvyxp-acqpe, road-hazard-detection-6-g5pbz, deteksi-polisi-tidur-tblnr, reductor-w4anu-q04yg,
speed-breaker-detection-ng8ne-pmyzk, hump-16nup-4bmvs, hump-detection-uac1m-o5jmj. Used by accepted parts: deteksi-polisi-tidur-tblnr,
reductor-w4anu-q04yg, speed-breaker-detection-ng8ne-pmyzk, road-hazard-detection-6-g5pbz, rdd-6706t-8szyz, total-jcwvt-f9ffa.
The others were rejected and can be deleted by the owner.

### 0.2 Leak counts re-run with the merged `leak_check.py` (eval-hit preference, rule v2)
- dm-druid 277 originals: 0 eval / 0 r2-train; all 5,983 images: 0 / 0 (VERIFIED, this VM).
- akash-kumbar re-upload (rejected): not re-run (the copy had been deleted); its rejection does not depend on the count.

### 0.3 Parts accepted (details `CANDIDATES.md` §F, files `review/new_data_r3/vet/<part>/`)
Counts are VERIFIED: `tools/build_part.py` was run in this VM on exactly these items, with the leak cache =
`protected_hashes.npz` (r2 all splits + BD87 + every existing part val/test). Results: `vet/<part>/expected_build_info.json`;
kept files: `vet/<part>/keep_list.csv` (file name, SHA-256, split, group); family evidence: `vet/<part>/family_breakdown.md`.

| part | region / what | train img / pothole / bump / neg | val img / pothole / bump | test img / pothole / bump | status |
|---|---|---|---|---|---|
| dmd | China campus, marked rubber bumps | 277 / 0 / 319 / 0 | — | — | ACCEPT |
| pol | **Indonesia**, alleys, **unmarked** concrete + painted humps | 375 / 0 / 375 / 0 | 100 / 0 / 100 | 25 / 0 / 25 | ACCEPT |
| red | Latin America, painted reducers, low 4K camera | 334 / 0 / 338 / 2 | 69 / 0 / 68 | 35 / 0 / 40 | ACCEPT |
| ng8 | **India**, phone dash video, painted breakers + hazard-free frames | 278 / 0 / 145 / 133 | 67 / 0 / 20 (47 neg) | 39 / 0 / 12 (27 neg) | ACCEPT (D1/D2 PROVISIONAL for zebra-like tables) |
| hmp | **India**, mostly **night** dashcam humps | 357 / 0 / 374 / 0 | 62 / 0 / 67 | 12 / 0 / 17 | ACCEPT (label quality PROVISIONAL) |
| ens | South Asia campus, painted raised humps | 414 / 0 / 422 / 0 | — | — | PROVISIONAL: check `vet/ens/sequence_check_pairs.csv` against rf8 val/test first |
| egy | **Egypt** dashcam potholes (city not verified) | 1,118 / 835 / 0 / 427 | 147 / 66 / 0 | 105 / 52 / 0 | PROVISIONAL: remove manhole boxes from val/test first |

**New speed-bump boxes: 2,322 in all splits from 6 independent sources; 1,973 in train** (1,551 without `ens`).
Target (≥ 1,500 from ≥ 3 sources) is met without `ens`: 319 + 375 + 338 + 145 + 374 = 1,551 train boxes from 5 sources.
New pothole boxes on Egyptian roads: 835 train + 118 in own val/test.

## 1. What was done

### 1.1 Data search (Task 1), session 1 — blocked by network policy then (session 2 result: §0.3)
- **Access (VERIFIED, request results 2026-11-04):** the environment's network policy refuses (HTTP 403 at the
  proxy) kaggle.com, zenodo.org, figshare.com, huggingface.co, roboflow.com, data.mendeley.com,
  ieee-dataport.org, arxiv.org, mdpi.com. `KAGGLE_API_TOKEN` and `ROBOFLOW_API_KEY` are not set. GitHub and PyPI work.
  To change this, the environment's *Network access* setting must allow those hosts
  (https://code.claude.com/docs/en/cloud-environments#network-access); the laptop is not affected.
- So the search was: web search (all platforms) + GitHub repository search (about 60 repositories listed, about 30 file
  trees read, 4 cloned in full, 2 leak-checked). Every candidate is in `CANDIDATES.md` §E.
- **Accepted: 1 new source, 277 images, 319 speed-bump boxes** (`dm-druid/SpeedBumps-Detection`, China campus,
  marked rubber bumps; train only). VERIFIED: counts from `tools/make_items_dmdruid.py` output; leak check
  0 hits on protected eval sets (rule v2).
- **Target (≥ 1,500 new bump boxes from ≥ 3 sources): NOT reached here.** 319 boxes from 1 source. The rest must
  come from the laptop (Roboflow / Kaggle / DriveIndia request), §3 step 2.
- **Rejected after download:** the Roboflow `akash-kumbar/speed_breakers-pothole` v8 re-export on GitHub
  (328 hits on r2 val/test + ghpot with rule v2; augmented; 3,540 `Image-N-` and 988 `potholesN` file names). This confirms the A13 note that many Roboflow bump sets are
  rf8-family re-uploads.
- **Most valuable lead for the main failure (unmarked Egyptian bumps):** `Mohamed20384/Speed-Bump-Detection-marked-unmarked`
  (Egyptian graduation project, own dashcam videos, day + night, no labels, no licence) → ask the author (§4).

### 1.2 Leak-guard bug found and fixed (Task 2c side effect) — VERIFIED by `tests/test_leak_check.py`
- Old rule: "dHash over 8 flips/rotations ≤ 4 AND pHash ≤ 10", but the pHash was compared **unrotated only**.
  A horizontally flipped, re-encoded copy of a protected image measured dHash 2 / pHash 32 → **not a hit**.
- **Measured on real data (VERIFIED, cloud leak runs on the rejected akash-kumbar re-export, 6,045 images):**
  rule v1 → 229 hits on protected eval sets; rule v2 → **328**. So 99 flipped copies of protected val/test images
  passed the old rule in that one set. Whether any flipped copy is inside an *accepted* part (rsid, bucko, sr,
  rdd_ji) is **UNRESOLVED until §3 step 0**; RSID/Bučko/RDD are not Roboflow exports, so the risk is lowest there.
- Fix (rule v2): both hashes are compared under the **same** one of the 8 transforms, in
  `tools/leak_check.py` (`check_image`) and `tools/build_part.py` (`near8`, also used for the within-part guard).
  `build_info.json` of new parts records "rule v2". Old parts keep their files; nothing was rebuilt.
- Second fix: `build_part.py` crashed (`rows[0]` IndexError) when every item of a part was dropped; it now writes an
  empty manifest.

### 1.3 Code for per-class accuracy (Task 2)
| file | what | check |
|---|---|---|
| `models/yolo11n-p2.yaml` | YOLO11n + P2 (stride-4) head, Detect on P2–P5 (SBP-YOLO / yolov8-p2 idea) | built on CPU, Ultralytics 8.4.202: **2,666,952 params; 10.45 / 23.69 / 42.55 GFLOPs at 640 / 960 / 1280**, vs YOLO11n (2 classes) 2,590,230 params; 6.50 / 14.80 / 26.74 GFLOPs. Strides 4, 8, 16, 32. `yolo11n.pt` transfers 297 / 593 tensors (backbone + first neck block; the P2 branch and the re-indexed head start random). VERIFIED: `review/metrics_r3/model_check_yolo11n-p2.json` |
| `tools/check_model_yaml.py` | builds any model YAML on CPU, prints params / GFLOPs / strides / weight transfer | produced the file above |
| `tools/calibrate_thresholds.py` | per-class confidence from **val** `predictions.json`: `f1`, `recall:R` (highest conf reaching R) or `precision:P` (lowest conf keeping P); optional bootstrap CI; refuses `--split test`; writes a JSON **proposal** — `perception/` is not touched | `tests/test_calibrate_thresholds.py` |
| `tools/vet_source.py` | automated part of the data gate for one source: class ids, data.yaml names, licence lines, Roboflow copies per base, within-source near-dup clusters, known re-upload families, leak check, contact sheet (kept outside git) | run on dm-druid (§2) |
| `tools/make_items_yolo_export.py` | items CSV for any Roboflow/Kaggle YOLO export: explicit class map, one copy per Roboflow base, known families dropped, group = near-dup cluster ∪ name block, 6-way group split (val/test/train) or `--all-train`, `--max-per-group` | smoke-run on the rejected akash-kumbar set (not kept) |
| `tools/make_items_dmdruid.py` | items CSV for the accepted dm-druid source | 277 items, 319 raw bump boxes |
| `tools/sample_sheet.py` | 20-image contact sheet with raw ids for the visual D1–D6 check | used for §2 |
| `tools/leak_check.py` | + `KNOWN_FAMILIES` file-name flags (Image000xx/Image-N-, MVI_15xx, VID_20190924, G00xxxxx, newonetrwww, speedbreakerrefinedone, rdd_, kg_/dz_, potholesN), importable functions, rule v2 | tests |
| tests | `test_metrics_report.py` (AP on toy cases, matching, ImgAcc, NearR, deploy conf), `test_build_part.py` (class map + ignore, unmapped id = hard error, FAR_TINY remove/drop, exact + flipped/re-encoded leak, `--guard`, within-part guard, no overwrite), `test_leak_check.py`, `test_calibrate_thresholds.py` | **32 new tests pass; full suite 139 tests OK, 3 skipped** (`python -m unittest discover -s tests`, VERIFIED in this VM, Python 3.13) |

### 1.4 Supervisor drafts (Task 3)
`supervisor_2026-11-08/README.md` and `METRICS.md`: only numbers already in `STATUS_for_claude.md` or
`review/metrics_r3/`, each with its file; `TODO(test)` markers where the final test numbers go.

## 2. Accepted source: dm-druid (part `dmd`)
- Licence MIT (2018, `LICENSE` in the repository). Region: China (campus roads), one day. Viewpoint: phone at
  windscreen height, mostly forward; 3/20 sampled images point down at the bump.
- Classes: 0 speed bump → `speed_bump`; 1 person → `ignore` (images with only id 1 are VOC web photos and are skipped).
- **Augmentation:** each original appears 10× (photometric copies; file index period 279), and the copies are spread
  over the source's own train and val (all 260 near-dup clusters span both). Only `xqq062000001–00279` are used.
- Group key: block of 10 consecutive photo numbers (traceability only). **Split: all train** (one place, one day: no
  independent evaluation value).
- Expected counts (VERIFIED from `make_items_dmdruid.py` in this VM; `build_part.py` may still drop exact duplicates
  inside the part): **train 277 images / 319 speed_bump boxes / 0 pothole / 0 negatives; val 0; test 0.**
  FAR_TINY removes 0 boxes (all sqrt(w·h) ≥ 0.02, computed here).
- Download on the laptop (≈ 0.9 GB with git history depth 1):
  ```
  git clone --depth 1 https://github.com/dm-druid/SpeedBumps-Detection C:\Users\ahmed\Desktop\GP36_Dataset\raw_v3\github_dmdruid_speedbumps
  ```

## 3. What the laptop must run next, in order (rewritten in session 2)
One GPU job at a time; no heavy CPU job while training. Windows `cmd` in `GP36_AI`; data under `..\GP36_Dataset\raw_v3`.
Every tool refuses to overwrite. The Roboflow downloads need the **private** key: `set ROBOFLOW_API_KEY=...`.

**Step 0 — already running on the laptop (STATUS Stage 21):** re-check of all parts and r2 train with leak rule v2.

**Step 1 — downloads (about 4 GB in total).**
```
git clone --depth 1 https://github.com/dm-druid/SpeedBumps-Detection ..\GP36_Dataset\raw_v3\github_dmdruid_speedbumps
venv\Scripts\python -I tools/rf_download.py refyy-i/deteksi-polisi-tidur-tblnr 1 ..\GP36_Dataset\raw_v3\rf_polisi
venv\Scripts\python -I tools/rf_download.py refyy-i/reductor-w4anu-q04yg 1 ..\GP36_Dataset\raw_v3\rf_reductor
venv\Scripts\python -I tools/rf_download.py refyy-i/speed-breaker-detection-ng8ne-pmyzk 1 ..\GP36_Dataset\raw_v3\rf_ng8ne
venv\Scripts\python -I tools/rf_download.py refyy-i/road-hazard-detection-6-g5pbz 1 ..\GP36_Dataset\raw_v3\rf_humps
venv\Scripts\python -I tools/rf_download.py refyy-i/rdd-6706t-8szyz 1 ..\GP36_Dataset\raw_v3\rf_egyrdd
venv\Scripts\python -I tools/rf_download.py refyy-i/total-jcwvt-f9ffa 1 ..\GP36_Dataset\raw_v3\rf_ensam
```
Expected image counts: polisi 1,000; reductor 438; ng8ne 710; humps 5,000 (2.2 GB); egyrdd 1,372; ensam 884
(VERIFIED here from the same exports). The Roboflow sources are the `refyy-i` forks, version 1 = no augmentation, no
resize, auto-orient only, so the files are byte-for-byte the ones checked here.

**Step 2 — items (the exact commands used in the cloud; output = the item CSVs).**
```
venv\Scripts\python -I tools/make_items_dmdruid.py --src ..\GP36_Dataset\raw_v3\github_dmdruid_speedbumps --out review/new_data_r3/items/items_dmd.csv
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_polisi\x --part pol --cmap "{\"0\": \"speed_bump\", \"1\": \"speed_bump\"}" --block 50 --include "frame_\d*[02468]" --out review/new_data_r3/items/items_pol.csv
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_reductor\x --part red --cmap "{\"0\": \"ignore\", \"1\": \"ignore\", \"2\": \"ignore\", \"3\": \"speed_bump\"}" "--group-regex=-frame_(VID_\d{8}_\d{6}|\d{3})" --out review/new_data_r3/items/items_red.csv
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_ng8ne\x --part ng8 --cmap "{\"0\": \"speed_bump\"}" --include "(VID_\d+_\d+_frame_\d+|IMG_\d+_\d+(_\d+)?)" --group-regex "(VID_\d{8}_\d{6}|IMG_\d{8})" --out review/new_data_r3/items/items_ng8.csv
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_humps\x --part hmp --cmap "{\"0\": \"ignore\", \"1\": \"speed_bump\", \"2\": \"ignore\", \"3\": \"pothole\", \"4\": \"ignore\"}" --include "humps-v\d+-_\d+" --out review/new_data_r3/items/items_hmp.csv
venv\Scripts\python -I tools/make_items_egyrdd.py --src ..\GP36_Dataset\raw_v3\rf_egyrdd\x --out review/new_data_r3/items/items_egy.csv
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_ensam\x --part ens --cmap "{\"0\": \"speed_bump\", \"1\": \"speed_bump\"}" --include "[0-9]{3,}" --all-train --out review/new_data_r3/items/items_ens.csv
```
`make_items_yolo_export.py` uses `max-per-group` 0 (no cap) for all of these: the frame subsampling is done by
`--include` (polisi) or is already sparse in the source.

**Step 3 — parts (guard every existing eval set; the new parts' own val/test are guarded by the within-part rule).**
```
set G=external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test parts_r3/bucko:val,test parts_r3/sr:val,test parts_r3/rdd_cz:test
for %P in (dmd pol red ng8 hmp egy ens) do venv\Scripts\python -I tools/build_part.py --items review/new_data_r3/items/items_%P.csv --part %P --out parts_r3/%P --guard %G%
```
(`%P` → `%%P` inside a .bat.) Then compare each `parts_r3/<p>/build_info.json` "splits" with
`review/new_data_r3/vet/<p>/expected_build_info.json`, and the manifest file names with `vet/<p>/keep_list.csv`.
They must match. The cloud build used a hash cache covering the same protected sets, so 0 leak drops are expected.
Afterwards, regenerate `protected_hashes.npz` with the new parts' val/test, so that later sources are guarded against them too.

**Step 4 — the two PROVISIONAL checks before use.**
1. `ens`: open the 40 pairs in `vet/ens/sequence_check_pairs.csv` (ens file vs closest protected rf8 val/test image).
   If any pair shows the same street/scene → drop `ens` (or the affected numeric range) and record it in STATUS.
2. `egy`: in `parts_r3/egy/labels/{val,test}` remove the pothole boxes that lie on manhole covers (D5), as a
   corrections file + new part version `egy_v2` (never edit the built part). The train split can stay as is for a first run.

**Step 5 — compose `road_hazards_v3b_C` (train only; val/test = r2, frozen).**
```
venv\Scripts\python -I tools/build_v3b.py --out road_hazards_v3b_C --parts parts_r3/rsid parts_r3/bucko parts_r3/sr parts_r3/dmd parts_r3/pol parts_r3/red parts_r3/ng8 parts_r3/hmp parts_r3/egy parts_r3/ens --drop-meta sr=family=rad
```
- Change vs v3b_B: **`rdd_ji` removed** (it was the pothole-heavy cap of 500); 6 bump parts + `egy` added.
- Expected train boxes (PROVISIONAL arithmetic; the exact numbers come from `road_hazards_v3b_C/build_info.json`):
  - v3b_B: 5,055 pothole / 1,925 bump (STATUS Stage 18, `road_hazards_v3b_B/build_info.json`).
  - Minus `rdd_ji:500`: ≈ 930 pothole, using 1.86 boxes per image (5,428 / 2,920, `parts_r3/rdd_ji/build_info.json`).
  - Plus `egy` 835 pothole.
  - Plus bumps 319 + 375 + 338 + 145 + 374 + 422 = 1,973.
  - Result ≈ **4,960 pothole / 3,898 bump = 1.27 : 1** (with `ens`), or ≈ 4,960 / 3,476 = 1.43 : 1 without `ens`.
- If closer to 1:1 is wanted: keep `dz` (Algerian bumps) and drop the Italian `kg` potholes of `sr` with
  `--drop-meta sr=family=rad sr=family=kg`. The exact effect is in `parts_r3/sr/manifest.csv` (meta `family=kg`).
- `hmp` brings mostly **night** frames; `ng8` brings 133 hazard-free train frames (hard negatives).

**Step 6 — runs and evaluation (val only; write hypotheses §5 into STATUS first).**
1. `v3b_C_11n_960_s0`: the D1 settings (or the L1 150-epoch protocol, if Stage 20 adopts it for all candidates).
2. Val-only evals with `save_json=True`:
   - r2 val;
   - part-vals: rsid, bucko, sr;
   - **new part-vals: pol (Indonesia, unmarked), ng8 (India, with negatives), hmp (India night), red (LatAm), egy (Egypt potholes, after the manhole fix)**.
   Use `tools/metrics_report.py` for each.
3. Optionally, `models/yolo11n-p2.yaml` on v3b_C (H-P2), then `tools/calibrate_thresholds.py` on r2 val, then the single test use.

## 4. Requests for Ahmed (cannot be done by code)
1. DriveIndia access (TiHAN IIT-H): academic use, cite the paper. Biggest known source with an *unmarked speed bump* class.
2. Email the author of `Mohamed20384/Speed-Bump-Detection-marked-unmarked` (Egyptian streets, unmarked bumps):
   permission + labelled frames. If only videos: hand-label ~300 frames as an **Egyptian part-val** (sequence-aware,
   by video), and use frames far from bumps as Egyptian hard negatives for train from *other* videos only.
3. Roboflow API key on the laptop (for §E2), and the Giordani 2026 Italian set (potholes + crack/manhole negatives).

## 5. Expected gains — hypotheses, not results
Write these into STATUS (Stage 19) before the runs. All are val-only; seed std of r2-val mAP50 is 0.0106
(`runs/v3a_r2_seed_summary.txt`).
| ID | Change | Hypothesis | Reasoning |
|---|---|---|---|
| H-C1 | v3b_C vs D1 | r2-val mAP50 ≥ 0.655 − 0.02 AND RSID part-val bump AP50 ≥ 0.663 − 0.03 AND every new bump part-val bump AP50 ≥ D1 + 0.10 | the only lever that has worked so far is new curated data (D1: RSID bump 0.035 → 0.663, Stage 13) |
| H-C2 | v3b_C vs D1, r2 val bump | +0.00 to +0.04 bump AP50 | the r2-val bump misses are two Egyptian dashcam groups (Stage 5); dmd and most Roboflow sets are marked bumps, so a large r2 gain is not expected unless an unmarked Middle-East/South-Asia source passes the gate |
| H-C3 | v3b_C vs D1 on the NEW part-vals (pol, ng8, hmp, red, egy) | speed_bump AP50 on pol val ≥ D1 + 0.15, and on ng8 val ≥ D1 + 0.10; egy-val pothole AP50 ≥ D1 + 0.05 (after the manhole fix); ImgAcc on ng8 val (47 hazard-free frames) does not drop below D1's | same mechanism as RSID in Stage 13 (0.035 → 0.663 after training on its own train split); D1 baselines on these part-vals must be measured first (val only) |
| H-C4 | v3b_C vs D1 on r2 val, bumps | +0.00 to +0.04 (the target groups are Egyptian unmarked bumps; pol is the closest new match: unmarked concrete humps in narrow streets) | r2 val is the old benchmark; the honest expectation is small |
| H-P2 | P2 head vs 11n, same data | r2-val pothole AP50 ≥ +0.03 AND all mAP50 ≥ −0.01 | tiny far potholes are a known failure (Stage 5); +60 % GFLOPs at 960 (23.69 vs 14.80) (VERIFIED above), so latency must be re-checked |
| H-T | calibrated per-class thresholds | no AP change by definition; at `recall:0.80` the bump precision on val is reported, to show the FSM trade-off | operating point only |
| H-90 | any of the above | per-class mAP50 ≥ 0.90 on r2 val or test: **very unlikely** by 8 Nov | best r2-val class so far is bump 0.736 (Run A s1, `review/metrics_r3/val_r2_baselines/report.md`); test bump 0.294 (`runs/v3a_r2_11n_960_s0_TEST.txt`) |

## 6. What was not done, and why
- Session 2: hard negatives come only from accepted parts (`ng8` 207 hazard-free frames, `egy` 567 crack-only /
  empty frames); no clean large hazard-free set was found (the Sri Lankan background frames are pseudo-labelled).
- Session 2: DriveIndia still not published (TiHAN page 404); the Egyptian video author (E1.3) not contacted.
- Session 2: `amier-haziq` hump fork, `mohamedaminebelasri7/roadscan`, `mukul2427` (US potholes) and `shuaifanpi`
  (China) were not vetted (low priority after the bump target was met).
- No dataset other than GitHub-hosted ones could be downloaded or leak-checked (network policy, §1.1).
- No training, evaluation or latency numbers (no GPU, no weights, no data).
- Hard negatives: none acquired here. Candidates: hazard-free frames inside accepted parts (already used for rsid/sr),
  Giordani 2026 cracks/manholes, and Egyptian video frames (request 2).
- `perception/` was not changed.
