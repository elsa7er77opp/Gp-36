# GP36 Perception Pod — hazard detector status for the supervisor (DRAFT, 8 Nov 2026)

Project #36 · student Ahmed Elreefy · supervisor Dr. Peter Makeen.
Every number has its source file next to it. Status words: VERIFIED (read from that file), PROVISIONAL,
UNRESOLVED, BLOCKED. `TODO(test)` = filled in only after the single final test run.
Metric definitions: `METRICS.md`. Data: `DATA.md`.

## 1. What the system does
One camera, two detectors in `perception/`: a YOLO11n hazard model (classes `pothole`, `speed_bump`) and the
COCO YOLO11n for road users. Both feed a warning state machine. Its thresholds were not tuned on test data.

## 2. Where the hazard model stands (validation data only; the test set is used once at the end)
| model | data | r2-val pothole AP50 | r2-val bump AP50 | source |
|---|---|---|---|---|
| Run A (YOLO11n, 3 seeds, mean) | r2 (cleaned, 3,035 train images) | 0.623 | 0.726 | `runs/v3a_r2_seed_summary.txt` |
| **D1, current candidate** (YOLO11n) | v3b_A = r2 + RSID + Bučko + RDD2022 (500) | **0.597** | **0.712** | `runs/v3b_A_11n_960_s0_VALr2_json.txt` |

The r2 validation set did not change much when data was added. On **new countries** the model changed a lot (VERIFIED):
| held-out new-country set (own sequences, never trained on) | before new data (Run A) | D1 | source |
|---|---|---|---|
| RSID (Lithuania) speed bump AP50 | 0.035 | **0.663** | `runs/PARTVAL_rsid_v3bA_s0.txt` |
| Bučko (Slovakia, incl. night/evening) pothole AP50 | 0.421 | **0.572** | `runs/PARTVAL_bucko_v3bA_s0.txt` |

What we tried that did **not** pass its criterion, which was written down before the run (STATUS Stages 14–16):
single-class models (bump 0.650 vs 0.712; pothole 0.554 vs 0.597), and YOLO11s (all mAP50 +0.005, criterion
was +0.02). **More curated data from new places is the only change that has helped.**

## 3. Test results (frozen internal r2 test + external BD87)
- Previous candidate, Run A, tested once (VERIFIED, `runs/v3a_r2_11n_960_s0_TEST.txt`): all mAP50 0.462;
  pothole 0.631; **speed bump 0.294** (recall 0.225). BD87 external bump set: 0.367 (`runs/EXT_bd87_v3a_r2_11n_960_s0_b.txt`).
- Final candidate: `TODO(test)`: r2 test per class, BD87, and the frozen operating thresholds from val.

## 4. Is ≥ 0.90 reached? Honest answer: **No**, not on any of the agreed metrics so far.
- The 0.90 counts only for per-class mAP50, or for the alternative metrics A1–A3. These were defined **before** they
  were measured (STATUS Stage 7.2; see METRICS.md), on a leak-free evaluation set split by sequence.
- Best values so far (validation):
  - per-class mAP50: best is bump 0.736 (Run A seed 1); D1 is 0.712 (`review/metrics_r3/val_r2_baselines/report.md`, `val_r2_all_2026-11-04/report.md`);
  - A1 near-range recall: bump 0.280 and pothole 0.542 for D1 (`review/metrics_r3/val_r2_all_2026-11-04/report.md`);
  - A3 precision at recall 0.50 is the only metric near 0.9: bump 0.863 for D1 and 0.950 for Run A s0 (same file).
    It is **not** claimed as "the 0.90", because it is not yet measured on test with frozen thresholds: `TODO(test)`;
  - A2 image-level accuracy: pothole 0.848 on Bučko val (42 hazard-free images); bump 0.758 on RSID val
    (`review/metrics_r3/partval_{bucko,rsid}_all_2026-11-04/report.md`).
- Why not: the main failure is **unmarked, low-contrast speed bumps** in Egyptian / developing-country dashcam
  footage (141 of 168 missed val bumps come from two Egyptian dashcam groups, STATUS Stage 5), plus tiny far potholes.
  The val→test drop for bumps (0.723 → 0.294 for Run A) shows the limit is the variety of scenes, not training time.
- What would move it: labelled forward-view data of unmarked bumps from Egypt / the Middle East / South Asia.
  Two leads were found that match this (DriveIndia's *unmarked speed bump* class; an Egyptian student project with
  its own street videos), but both need a request (`review/new_data_r3/CANDIDATES.md` §E).

## 5. Data work since 1 Nov (details in DATA.md, CANDIDATES.md)
- Candidates checked: 159 Kaggle listings (`CANDIDATES.md` intro), Roboflow Universe, Zenodo, Figshare, Mendeley,
  Hugging Face, about 60 GitHub repositories (`CANDIDATES.md` §E) and paper supplements. Each was rejected, blocked or accepted, with the reason recorded.
- Every accepted source passes a gate: explicit class map, FAR_TINY rule, leak guard against all evaluation
  images, and a split by sequence.
- Parts built 2–4 Nov: rsid, bucko, rdd_ji, rdd_cz, sr (`parts_r3/*/build_info.json`); 1 more accepted
  in the cloud session (dm-druid, 277 images / 319 bump boxes, train only; `review/new_data_r3/CLOUD_REPORT.md`).
- A gap in the duplicate guard was found and fixed. Mirrored or flipped copies of evaluation images were not
  caught by the old rule. In one rejected re-upload, the new rule catches 328 such copies of evaluation images,
  where the old rule caught 229 (`CLOUD_REPORT.md` §1.2). Existing parts are being re-checked: `TODO(laptop step 0)`.

## 6. Next (in order) — `review/new_data_r3/CLOUD_REPORT.md` §3
1. Re-check the parts with the fixed guard.
2. Add the vetted bump sources and build v3b_C (pothole:bump near 1:1).
3. Train v3b_C, and a P2-head variant for tiny potholes (`models/yolo11n-p2.yaml`).
4. Choose per-class thresholds on val (`tools/calibrate_thresholds.py`).
5. Run the test once and fill in `TODO(test)`.
