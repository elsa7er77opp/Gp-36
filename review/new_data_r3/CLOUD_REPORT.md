# GP36 — cloud session report (2026-11-04)

Session type: cloud VM, **no GPU, no project datasets, no trained weights**. Everything here is code, reports and
instructions for the training laptop. Labels: VERIFIED (read from a file or command output named here) ·
PROVISIONAL · UNRESOLVED · BLOCKED. No number in this file comes from a training run made here.

## 1. What was done

### 1.1 Data search (Task 1) — target NOT met in the cloud (BLOCKED by network policy)
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

## 3. What the laptop must run next, in order
One GPU job at a time; no heavy CPU job while training (Stage 11 rule). Paths as on the laptop (`GP36_AI` folder,
`venv\Scripts\python`). Every command refuses to overwrite.

**Step 0 — re-check the existing parts with leak rule v2 (CPU, before any new training).**
```
venv\Scripts\python -I -m unittest discover -s tests
venv\Scripts\python -I tools/leak_check.py parts_r3/rsid/images/train review/new_data_r3/leakv2_rsid_train.csv
venv\Scripts\python -I tools/leak_check.py parts_r3/bucko/images/train review/new_data_r3/leakv2_bucko_train.csv
venv\Scripts\python -I tools/leak_check.py parts_r3/sr/images/train review/new_data_r3/leakv2_sr_train.csv
venv\Scripts\python -I tools/leak_check.py parts_r3/rdd_ji/images/train review/new_data_r3/leakv2_rdd_ji_train.csv
```
Note: these parts' own val/test images are themselves in `protected_hashes.npz`, so hits whose `closest_id` is the
same part's val/test are expected only if the within-part guard missed a flipped copy. Any eval hit → write it in
STATUS, drop that image with a new part version (never edit the old one), and re-score D1 only if the hit was in its
training data. Also re-run for `road_hazards_v3a_r2/images/train` against val/test ids (r2 train hits on r2 val/test
would mean the r2 split itself has flipped duplicates across splits).

**Step 1 — part `dmd`.**
```
git clone --depth 1 https://github.com/dm-druid/SpeedBumps-Detection ..\GP36_Dataset\raw_v3\github_dmdruid_speedbumps
venv\Scripts\python -I tools/make_items_dmdruid.py --out review/new_data_r3/items/items_dmd.csv
venv\Scripts\python -I tools/build_part.py --items review/new_data_r3/items/items_dmd.csv --part dmd --out parts_r3/dmd --guard external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test parts_r3/bucko:val,test parts_r3/sr:val,test parts_r3/rdd_cz:test
```
Expected: train 277 / 319 bump boxes (§2). A big deviation means the clone differs; stop and look.

**Step 2 — more bump sources (needs Ahmed's Roboflow key and Kaggle token; this is where the 1,500 boxes must come from).**
For each candidate in `CANDIDATES.md` §E2 (order: E2.2 Qassim unmarked, E2.3 qu-j2rlc, E2.4 alia-khalifa ×3,
E2.7 ensam total-jcwvt, E2.5 emirhan-ilhan, E2.6; Kaggle A5/A7 sets still marked VALIDATE in §D):
```
rem download the YOLOv8 export of ONE version into a NEW folder, e.g. ..\GP36_Dataset\raw_v3\rf_<short>
venv\Scripts\python -I tools/vet_source.py --name <short> --root ..\GP36_Dataset\raw_v3\rf_<short> --out review/new_data_r3/vet/<short> --sheet ..\GP36_Dataset\_sheets\sheet_<short>.jpg
```
- Reject if `leak_hits_eval` > 0 and the hits are not confined to a file-name family that can be dropped.
- Look at the sheet yourself (D1 flat zebra = background, D2 raised crossing / hump = speed_bump, D5 manhole/crack/
  patch = background, D6 rumble strip = not a bump) and write ~5 lines in CANDIDATES.md.
- Then, with the class map decided from the sheet (example for a 2-class marked/unmarked set):
```
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_<short> --part <short> --cmap "{\"0\": \"speed_bump\", \"1\": \"speed_bump\"}" --out review/new_data_r3/items/items_<short>.csv --max-per-group 4
venv\Scripts\python -I tools/build_part.py --items review/new_data_r3/items/items_<short>.csv --part <short> --out parts_r3/<short> --guard external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test parts_r3/bucko:val,test parts_r3/sr:val,test parts_r3/rdd_cz:test
```
  Use `--all-train` for sets from a single place. Sets with unmarked bumps from new countries get their own part
  val/test (default 6-way group split), so a new part-val can measure the unmarked case.
- Also: request DriveIndia (E2.1) and the Egyptian videos (E1.3). These are the two sources that match the failure.

**Step 3 — compose `road_hazards_v3b_C` (train only; val/test stay r2).** Suggested composition with caps that
keep pothole:bump near 1:1 (PROVISIONAL: the real counts come from each `parts_r3/<p>/build_info.json`):
```
venv\Scripts\python -I tools/build_v3b.py --out road_hazards_v3b_C --parts parts_r3/rsid parts_r3/bucko parts_r3/sr parts_r3/dmd parts_r3/<new bump parts...> parts_r3/rdd_ji:<N_rdd> --drop-meta sr=family=rad
```
- v3b_B train is 5,055 pothole / 1,925 bump boxes (2.6 : 1, `supervisor_2026-11-08/DATA.md` §5 / STATUS Stage 18).
  The v3b_B command above is reconstructed from STATUS Stage 18 (v3b_A + sr kg+dz); compare with
  `road_hazards_v3b_B/build_info.json` before running.
- Caps, in this order, until pothole:bump ≤ 1.3 : 1:
  1. all bump parts uncapped (bumps are the scarce class);
  2. `rdd_ji`: N_rdd from 500 down to 0 (it adds ≈ 1.86 pothole boxes per image: 5,428 / 2,920, `parts_r3/rdd_ji/build_info.json`);
  3. if still > 1.3 : 1, cap `sr` with `sr:<N>` (its train has 1,125 pothole vs 247 bump boxes, Stage 18).
- Arithmetic example (PROVISIONAL): v3b_B + dmd (+319 bumps) with rdd_ji 500 → 0 (≈ −930 pothole) gives about
  4,125 / 2,244 = 1.84 : 1. Reaching ≈ 1.3 : 1 needs about **+930 more bump boxes** from step 2, or ≈ 1:1 about +1,880.
- Strict verify must PASS (build_v3b does it).

**Step 4 — runs (hypotheses below, write them into STATUS before starting).**
1. `v3b_C_11n_960_s0`: D1 settings (yolo11n.pt, imgsz 960, batch 8, workers 2, cache disk, seed 0, deterministic,
   epochs 70, patience 20), data v3b_C. Val evals: r2 val (`save_json=True`), every part val incl. the new ones.
2. `v3b_C_11n-p2_960_s0`: same, `model=models/yolo11n-p2.yaml pretrained=yolo11n.pt` (only if run 1 is not worse
   than D1 on r2 val by more than 0.02). Then `tools/latency_bench.py` on an idle machine.
3. Thresholds for the selected candidate (val only):
```
venv\Scripts\python -I tools/calibrate_thresholds.py --data road_hazards_v3a_r2 --split val --pred runs/detect/<run>_VALr2_json/predictions.json --model <run> --mode f1 --bootstrap 200 --out review/metrics_r3/thresholds_<run>_f1.json
venv\Scripts\python -I tools/calibrate_thresholds.py --data road_hazards_v3a_r2 --split val --pred runs/detect/<run>_VALr2_json/predictions.json --model <run> --mode recall:0.80 --out review/metrics_r3/thresholds_<run>_r80.json
```
   The JSON is a proposal for the owner. `perception/config.yaml` has one `fsm.hazard_min_conf`; per-class values
   need an owner-reviewed change in `perception/`, which this session did not make.
4. Final: frozen r2 test and BD87 once for the final candidate, with `tools/metrics_report.py --thresholds <val report.json>`.
   Fill the `TODO(test)` markers in `supervisor_2026-11-08/README.md` / `METRICS.md`.

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
| H-P2 | P2 head vs 11n, same data | r2-val pothole AP50 ≥ +0.03 AND all mAP50 ≥ −0.01 | tiny far potholes are a known failure (Stage 5); +60 % GFLOPs at 960 (23.69 vs 14.80) (VERIFIED above), so latency must be re-checked |
| H-T | calibrated per-class thresholds | no AP change by definition; at `recall:0.80` the bump precision on val is reported, to show the FSM trade-off | operating point only |
| H-90 | any of the above | per-class mAP50 ≥ 0.90 on r2 val or test: **very unlikely** by 8 Nov | best r2-val class so far is bump 0.736 (Run A s1, `review/metrics_r3/val_r2_baselines/report.md`); test bump 0.294 (`runs/v3a_r2_11n_960_s0_TEST.txt`) |

## 6. What was not done, and why
- No dataset other than GitHub-hosted ones could be downloaded or leak-checked (network policy, §1.1).
- No training, evaluation or latency numbers (no GPU, no weights, no data).
- Hard negatives: none acquired here. Candidates: hazard-free frames inside accepted parts (already used for rsid/sr),
  Giordani 2026 cracks/manholes, and Egyptian video frames (request 2).
- `perception/` was not changed.
