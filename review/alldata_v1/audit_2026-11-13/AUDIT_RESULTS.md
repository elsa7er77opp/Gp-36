# Stage 41 audit of ALLVAL (model C) — 2026-11-13. VAL ONLY, read-only, no training, no test predictions.

Inputs (all measured from files in this repo):
- `review/alldata_v1/export_2026-11-13/predictions_C_ALLVAL.zip` sha256 `aa0170bf…d6294` (contains `predictions_C_ALLVAL.csv` sha256 `57ce8082…9acb8` + `classes.txt`)
- full-precision predictions `review/alldata_v1/onnx_eval/pred_C_val/*.npy` (and `pred_A1_val`), manifest `review/alldata_v1/allval.txt`,
  labels `review/alldata_v1/ds/labels/val` (byte-identical to the originals), `parts_r3/*/manifest.csv`, `road_hazards_v3b_C/build_info.json`.
- Evaluator: same logic as `onnx_eval/onnx_val.py` (Ultralytics 8.4.192 val: imgsz 960, rect batch 8, conf 0.001, NMS IoU 0.7, max_det 300, 101-point AP).

Re-run (from the repo root):
```
venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a1_reconcile.py
venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a2_score.py pred_C_val
venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a2_score.py pred_A1_val
venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a4_extra.py
```
Logs: `a1_reconcile.log`, `a2_score_C.log`, `a2_score_A1.log`, `a4_extra.log`.
Tables: `metrics_AP50_C.csv`, `metrics_operating_points_C.csv` (0.05/0.10/0.25/0.50), `error_log_per_gt_C.csv` (1,798 GT rows),
`reconcile_images.csv` (1,754 rows), `zero_boxes.csv`, same `_A1` files. Sheets: `sheet_sr_bump_0..2.jpg`, `overlays_sr_speed_bump/`.

## Findings
1. **Manifest: no image was skipped.** 1,754 manifest = 1,754 prediction files; 47,985 rows; 1,722 images in the CSV. The 32 others
   (ng8_v2 16, egy_v2 13, sr 2, pol_v2 1) were evaluated and have zero predictions at conf ≥ 0.001. One of them has a GT box (1 bump).
2. **Class order is consistent**: 0 pothole, 1 speed_bump in `classes.txt`, `data_allval.yaml`, labels and the scorer.
3. **11 zero-size boxes** are zero at full precision too: boxes that lie in the letterbox padding and are clipped to the image border
   (x or y = 0 or = image size). Max conf 0.0038. Not a rounding problem. Effect on AP50: none measurable (they can never match).
4. **CONFIRMED DEFECT (evaluation set, not the model): all 35 sr val "speed_bump" boxes are family `rad`** (32 images, 6 videos).
   STATUS Stage 18 judged the rad bump labels unusable and `road_hazards_v3b_C/build_info.json` drops `family=rad` from training,
   but `allval.txt` took the whole sr val split. dz val has 0 bump boxes, kg val has 0. C: 0/35 found at conf 0.25; 25 of 35 have no
   box near at all. The overlays show the boxes on dirt/sand road patches (AI visual check only, NOT a human review).
   Sensitivity (official number stays the one WITH rad until a human decides):
   | set | images | pothole AP50 | bump AP50 (GT) | mean |
   |---|---|---|---|---|
   | ALLVAL official | 1,754 | 0.5872 | 0.7243 (741) | 0.6557 |
   | ALLVAL minus 32 rad images | 1,722 | 0.5883 | 0.7595 (706) | 0.6739 |
   ALLTEST has the same issue by manifest count (24 rad images, 27 bump boxes); no test prediction was made.
5. **bucko val and test are one location group** (`bucko_Pr`: val 125, test 120). Train is separate (Ca, Pd). bucko test is not
   independent of bucko val. Other parts: 0 groups shared between splits (rsid, sr, pol_v2, red_v2, ng8_v2, egy_v2).
6. Scorer vs the report: identical to `RESULTS_ALLVAL_onnx.md` (0.587 / 0.724 / 0.656).

## Not done (needs Ahmed or a run in a visible window)
- WBF(C+v1) on ALLVAL: no v1 predictions on ALLVAL exist. PROPOSED, not run.
- Latency on the demo device: NOT MEASURED.
- Human decision on the 32 rad val images: NEEDED before any change to the official ALLVAL list.
