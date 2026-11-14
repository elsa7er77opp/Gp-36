# GP36 Perception Pod — hazard detector status for the supervisor (DRAFT, 8 Nov 2026)

Project #36 · student Ahmed Elreefy · supervisor Dr. Peter Makeen.
Every number has its source file next to it. Status words: VERIFIED (read from that file), PROVISIONAL,
UNRESOLVED, BLOCKED. `TODO(test)` = filled in only after the single final test run.
Metric definitions: `METRICS.md`. Data: `DATA.md`.

## 0. FINAL results (VERIFIED, 6 Nov 2026). This section replaces the older drafts in §2–§4a.
Two final candidates were chosen on r2 **val** by a rule written down before any result (STATUS Stages 29–32).
Each was then run **once** on the frozen r2 test and once on the external BD87 set (`review/metrics_r3/TEST_LEDGER.csv`,
uses 6–9). The operating thresholds come from val. Full tables: `tables_test_r2/`, `tables_test_bd87/`, `tables_val_final/`.

| benchmark | model | pothole AP50 | bump AP50 | mAP50 (mean) | COCO AP 50-95 | source |
|---|---|---|---|---|---|---|
| r2 test | previous candidate Run A (31 Oct) | 0.631 | 0.294 | 0.462 | — | `runs/v3a_r2_11n_960_s0_TEST.txt` |
| r2 test | **C** (YOLO11n, data v3b_C) | **0.711** | 0.320 | 0.515 | 0.227 | `review/metrics_r3/test_r2_final/report.md`, `coco_test_r2_final/` |
| r2 test | **WBF(C, v1)** (two YOLO11n fused) | 0.698 | **0.463** | **0.580** | **0.240** | same |
| BD87 (external, bumps) | Run A / v1 (31 Oct) | — | 0.367 / 0.328 | — | — | `runs/EXT_bd87_*_b.txt` |
| BD87 | **C** | — | **0.731** | — | **0.353** | `review/metrics_r3/test_bd87_final/report.md`, `coco_test_bd87_final/` |
| BD87 | **WBF(C, v1)** | — | **0.731** | — | 0.326 | same |

Precision, recall, F1, BoxAcc, ImgAcc, NearR, P@R50 and near-range AP50 for each class are in the `tables_test_*` files. COCO numbers come from pycocotools with default parameters.

**Honest 0.90 statement.**
- **Per-class mAP50 ≥ 0.90 is NOT reached.** The best values are pothole 0.711 (r2 test) and speed bump 0.731 (BD87); speed bump is 0.463 on r2 test.
- Two of the alternative metrics defined in advance (METRICS.md §1) are ≥ 0.90 on test:
  - pothole image-level accuracy 0.938 (r2 test);
  - speed-bump precision at recall 0.50: 0.936 (BD87).
- They are reported **next to** the mAP50 above and do not replace it.
- **Why the bump number is low on r2 test:** most r2-test bumps are unmarked, low-contrast Egyptian street humps seen from a dashcam. On val, 61 % of the near ones get no prediction at all (STATUS Stage 28). More public data from other countries (v3b_C) doubled the external BD87 score but moved r2-test bumps only from 0.294 to 0.320, or 0.463 with WBF.
- **What would close the gap:** human-labelled Egyptian near-hump frames from new streets, split by drive. No public set of this kind exists (CANDIDATES.md §A–§I).

What was tried in the last round and rejected by its pre-written rule (STATUS Stages 30–32 and 36):
- test-time augmentation (−0.010 val mean);
- sliced inference (−0.004, 195 ms per image);
- AdamW instead of the default optimizer (−0.003);
- a P2 small-object head (−0.021; bump −0.058).
- a reviewed clean-up of train labels (60 non-hazard boxes removed, 24 images with unlabelled hazards dropped; −0.004, Bučko pothole −0.105; STATUS Stages 34–36).

Accepted: WBF of two models (+0.032 to +0.043 val mean). Its cost is two models per frame, with their own thresholds (0.148 / 0.090).

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
- Final candidates: done 6 Nov, see §0 (C and WBF(C, v1); ledger uses 6–9).

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

### 4a. Honest 0.90 statement (DRAFT, cloud session 5; to be finished on the laptop)
Every 0.90 claim below is either backed by a named file or marked `TODO(laptop)`. Full per-class mAP50 is always
shown next to any other metric, never replaced by it.

**Metrics that can plausibly reach about 0.90** (all on r2 **val**; on test only after the single final run):
| metric (definition in METRICS.md §1) | best value so far | source | status |
|---|---|---|---|
| ImgAcc (A2), pothole, at the val operating threshold | 0.914 (v1), 0.912 (D1 11s), 0.898 (D1 11n) | `review/metrics_r3/val_r2_all_2026-11-04/report.md` | VERIFIED (val) |
| ImgAcc (A2), speed bump | 0.880 (v1), 0.871 (D1 11n) | same | VERIFIED (val); below 0.90 |
| P@R50 (A3), speed bump | 0.950 (Run A s0), 0.892 (D1 11s), 0.863 (D1 11n) | same | VERIFIED (val) |
| P@R50 (A3), pothole | 0.771 (v1), 0.758 (D1 11s) | same | VERIFIED (val); below 0.90 |
| near-range AP50 (`--care near`, defined 2026-11-04 before any value) | `TODO(laptop)`: CLOUD_REPORT §0-S5 B1 | `review/metrics_r3/val_r2_near_<date>/report.md` | not computed yet |

Caution, written before the near-range values exist: near-range *recall* (NearR) for bumps is low, 0.280 for D1
(same report). So near-range bump AP50 may come out **below** 0.90, or even below the full AP50. It is reported
either way.

**What cannot reach 0.90 by 8 Nov: full per-class mAP50.** Best val values are bump 0.736 (Run A seed 1) and pothole
0.628 (v1) (`review/metrics_r3/val_r2_baselines/report.md`, `val_r2_all_2026-11-04/report.md`). The only test so
far is Run A: pothole 0.631, bump 0.294 (`runs/v3a_r2_11n_960_s0_TEST.txt`). Reasons, each with evidence:
1. **Scarce data of Egyptian unmarked bumps.** 141 of the 168 missed val bumps come from two Egyptian dashcam groups
   (STATUS Stage 5). Four sessions of searching (`review/new_data_r3/CANDIDATES.md` §A–§I) found no public, labelled,
   forward-view set of unmarked Egyptian or MENA bumps. The closest leads all need a request (`REQUESTS.md`).
2. **Tiny far potholes, and not only those.** The FAR_TINY rule only removes boxes with sqrt(area) < 0.02, and
   many potholes at 0.02–0.05 remain.
   - The near-range recall is **not** higher than the full recall. For D1, pothole NearR is 0.542 against a full
     recall of 0.579, and bump NearR is 0.280 against 0.619, both at the operating threshold (same report).
   - So far, tiny objects are one limit, but near misses matter too. `TODO(laptop)`: add the near vs full AP50 from
     the B1 report.
3. **Label noise found by the audits.**
   - In the Egyptian pothole source, 400 of 954 boxes (42 %) are not potholes by our rules, and 270 (28 %) are
     manhole covers (`review/new_data_r3/vet/egy/BOX_AUDIT.md`).
   - In bpo val/test, 12.0 % / 19.4 % of the boxes are definite errors (`review/new_data_r3/vet/VALTEST_AUDIT_S4.md`).
   - Missing pothole labels in r2 val/test show up as "background FPs" (STATUS Stage 20, L3).

   Noise like this caps the measurable AP for every model alike. It is corrected through new benchmark versions
   (r3), never by editing r2.

**What would get there with more time** (none of it is available by 8 Nov):
- DriveIndia's *unmarked speed bump* class: request needed (`review/new_data_r3/REQUESTS.md`).
- The Egyptian student project's own street videos: request to the author (`REQUESTS.md`).
- Our own labelled pod footage from Egyptian streets, split by drive and never mixed into training. This is the
  only evaluation that matches the deployment.
- Training levers B5 (longer schedule, 1280, P2 head), and inference levers B2–B4 (WBF, sliced inference, TTA).
  All are pre-registered in CLOUD_REPORT §0-S5. Expected gains are +0.01 to +0.05 each (PROVISIONAL), which is not
  enough to close a gap of 0.17 (bump) to 0.27 (pothole) on val mAP50.

`TODO(laptop)`: fill in the v3b_C val row, the B1–B4 rows (through `tools/make_supervisor_tables.py`), and, after
`tools/test_ledger.py check`, the single final test row.

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
