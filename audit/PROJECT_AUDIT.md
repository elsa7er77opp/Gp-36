# GP36 — PROJECT_AUDIT (Phase 0: read-only audit)

**Date:** 2026-10-30  **Scope:** `Desktop\GP36_AI`, `Desktop\GP36_Dataset`, `Desktop\graduation project` (backup copy), the training log `.docx`, and the installed environment.
**What was done:** filesystem inventory; environment checks; code review; a full integrity scan of every image and label (4,374 raw + 3,804 v2, with SHA-256, dHash, geometry and class checks); checkpoint loading; and **re-evaluation of the historical models on the historical test set** (inference only, outputs in the scratchpad, no project file changed).
**What was NOT done:** no training, no downloads, no installs, no modification or deletion of any original file. External datasets A, B, E–I were **not downloaded or inspected**, so every statement about them below is marked NOT_TESTED.

Companion reports: `ENVIRONMENT_REPORT.md`, `CODE_AUDIT.md`, `CRITICAL_ISSUES.md`. Evidence: `audit/evidence/`. Reproducible audit scripts: `audit/tools/` (they use hard-coded audit paths and are read-only with respect to the project).

---

## 1. Verified current state

| Item | Recorded | Found | Status |
|---|---|---|---|
| `prepare_dataset.py`, `train.py` | present | present | PASS |
| `detect_stream.py` | "may not exist" | **absent** | BLOCKED |
| `road_hazards_v2/data.yaml` | present | present: absolute path, `0 pothole, 1 speed_bump` | PASS |
| `road_hazards` (v1, 561 images) | not mentioned | present, 392/111/58 | PASS (kept as history) |
| `yolov8n.pt`, `yolov8s.pt`, `yolo11n.pt` | present | present; COCO 80 classes; all load | PASS |
| `weights/yolo26n.pt` | not mentioned | present; COCO 80 classes; loads in 8.4.192 | PASS |
| `runs/detect/` | 5 runs | 5 training + 5 test folders, all with `best.pt`/`last.pt` | PASS |
| Previous dataset: 3,804 images, test 266 | yes | 2,952 / 586 / 266 = 3,804 | PASS |
| `torch-…whl` (2.75 GB) | — | in the project root | note |
| Version control / lock file | — | none | FAIL (reproducibility) |

## 2. Confirmed problems
See `CRITICAL_ISSUES.md` for the full table. In brief:
1. **CI-1/CI-2 Leakage.** 42 test and 98 val images are byte-identical to train images. 100/266 test images have a near-duplicate in train/val.
2. **CI-3 Annotation noise.** 45% of duplicate Roboflow pairs disagree on the object count. A painted crosswalk is labelled "speed bump" in one copy.
3. **CI-4 Contaminated test set.** It was used for model selection.
4. **CI-5 Confounded conclusion.** Image size was not the only variable changed between runs 2 and 4.
5. **CI-6 The speed-bump video is split frame by frame.** It is one scene.
6. **CI-7 ROI-crop mismatch** between training and live inference.
7. **CI-8 No real-time, tracking, communication or fusion code.**
8. Latent code hazards: `rmtree` on the output folder, silent exception, 60-character truncation, class-ID override (`CODE_AUDIT.md`).

## 3. Problems requiring investigation (NEEDS_REVIEW)
* Visual confirmation of the 100 dHash-flagged test images and the 1,336 train↔val pairs.
* Ontology decision: is a painted or raised zebra crossing a `speed_bump`? This affects how CI-3 is resolved.
* `pothole_058` bottom-left box (most likely a real small pothole; see the overlay).
* 15 empty speed-bump frames.
* `pothole_208`: potholes on an unpaved/dirt road shoulder. Is that in scope for "pothole"?
* Licences of the GitHub sources (Androidest, biodatlab): not checked. `yolo-automotive-dataset` declares MIT, but contains BDD100K and Kaggle subsets with their own terms.

## 4. Condition of the existing datasets

| Source | Images | Labels | Integrity | Duplicates | Semantics | Verdict |
|---|---|---|---|---|---|---|
| **Roboflow "Humps/Bumps & Potholes" v8** (CC BY 4.0 per README) | 3,243 (2,560/475/208) | 7,022 objects: 6,025 pothole, 997 bump (1 stored as a polygon) | all readable, all JPEG, 0 orphan files, 0 geometry errors | **395 identical pairs**; 281 stems duplicated within a split; 153 stems in more than one split | 45% of duplicate pairs disagree; crosswalk labelled as bump | **NEEDS_REVIEW**: keep it as the main source after deduplication and review of the pairs. Its speed bumps are the most varied in the project (test AP50 about 0.88). |
| **Speed bumps** (Androidest GitHub) | 370 frames 1920×1080, all one video | 355 boxes, 15 empty | all readable, geometry OK | 12,708 near-duplicate pairs (one video) | thin boxes (median height 1.7%) | **NEEDS_REVIEW**: keep it as one group. Best use: an "unseen road" held-out test. |
| **Potholes** (biodatlab GitHub) | 191 (named `.jpg`, but really 155 JPEG, 27 WEBP, 8 PNG, 1 GIF) | 516 boxes, class 0 only | all readable, geometry OK | 3 internal near-duplicates; 6 cross-source matches with Roboflow | crowd-sourced; mixed box styles (one big box vs several) | **NEEDS_REVIEW**: full visual review (191 images is feasible). |
| **yolo-automotive-dataset** | 6,216 (4,314 JPG + 1,902 PNG) | ≥20 class IDs, no names file found | NOT_TESTED | NOT_TESTED | not a hazard dataset | Not needed for the Hazard Detector (COCO model covers it). Future unified-detector research only. |

Global label facts (v2): 5,190 pothole and 1,017 speed-bump train boxes, about a 5:1 imbalance. 0 boxes out of range, 0 zero-area boxes, 0 duplicate lines, 0 invalid class IDs. All EXIF orientation = 1.

## 5. Condition of the historical model weights, and re-verified metrics
All 10 trained checkpoints load. Each has `nc=2`, `names=[pothole, speed_bump]` and Ultralytics 8.4.192, and points at the expected data.yaml. Epoch counts match the log (50/50/100/106/125, best at 48/49/70/76/95).

**Historical test metrics were re-run and reproduce exactly.** n = number of test images.

| Run | Full test (n=266) mAP50 / pothole / bump | No exact duplicates (n=224) | **No near-duplicates (n=166)** | mAP50-95 (full → no near-dup) | Recall (full → no near-dup) |
|---|---|---|---|---|---|
| 2 v8n 640 | 0.652 / 0.573 / 0.730 | 0.642 | **0.579** | 0.267 → 0.229 | 0.579 → 0.508 |
| 3 v8s 960 | 0.618 / 0.629 / 0.607 | 0.597 | **0.538** | 0.276 → 0.234 | 0.557 → 0.490 |
| 4 v8n 960 | 0.689 / 0.631 / 0.747 | 0.674 | **0.626** | 0.301 → 0.259 | 0.589 → 0.507 |
| 5 11n 960 | 0.680 / 0.633 / 0.727 | 0.661 | **0.610** | 0.310 → 0.276 | 0.633 → 0.570 |

Interpretation:
* Leakage inflated the historical mAP50 by about **0.06–0.08**. The pothole AP is stable (≈0.60). The speed-bump AP falls (≈0.75 → ≈0.65), so speed bumps benefited most from leakage.
* Run 4 vs run 5 differ by 0.016 mAP50 on 166 images with a single seed. **No winner can be established statistically**: run 5 has higher recall and mAP50-95, run 4 has higher mAP50.
* The historical weights are valid **baselines**, but their published numbers must be annotated "with a leaked test set". **Gate F for them: FAIL as final models; PASS as preserved history.**
* The latency printed by `val` (2–9 ms) was measured during validation and is **not a benchmark**. Phase 2 must measure p50/p95/p99 properly.

## 6. Suitability of the proposed new datasets (all NOT_TESTED: nothing downloaded)

| ID | Dataset | Likely value | Main risks to check | Access | Status |
|---|---|---|---|---|---|
| A | RDD2022 (sekilab) | Large, multi-country source of D40 potholes | Crack labels must not become potholes. Images with cracks are not clean negatives. Dashcam viewpoint. Separate image/annotation licence (to verify). Download is tens of GB (to verify). | Public download | NOT_TESTED |
| B | Roboflow speed-bump v15 | More varied speed bumps (fixes CI-6) | "Stretch" 640×640 resize distorts aspect and cannot be undone. Video-frame duplicates. Possible overlap with Roboflow v8. | **Needs your Roboflow account/API key.** I must not enter credentials, so you would download it. | NOT_TESTED |
| C | Roboflow v8 (existing) | Main source | CI-1/2/3 | already local | audited above |
| D | Androidest / biodatlab (existing) | Keep after review | CI-6, CI-10 | already local | audited above |
| E | Nature Sci. Rep. 2026 (s41598-026-46679-4) | Deferred advanced experiment | Polygon→bbox conversion; manholes and cracks are not potholes. Publication and dataset details unverified. | to verify | DEFERRED / NOT_TESTED |
| F | EGY_PDD (Port Said Univ.) | Egyptian domain: most strategically important for evaluation | "Bumps & Sags" ≠ engineered speed bumps; academic licence | **Request through your supervisor**: not requested yet (log §8) | BLOCKED |
| G | Mendeley bvpt9xdjz8 | Appearance analysis only, if the images are crops | Cropped images have no detection boxes; boxes must not be invented | Public | NOT_TESTED |
| H/I | Cityscapes, The Great Outdoors | Future segmentation/terrain work | Different task (segmentation). Cityscapes needs registration and is research-only. | Registration | Out of current scope |

## 7. Exact corrections required (Phase 1, in order)
1. **Freeze history.** Write a SHA-256 manifest of `GP36_Dataset`, `road_hazards_v2` (excluding `.npy`), `runs/` and all `.pt` files. Back up `roboflow/`.
2. **New tooling** in `GP36_AI/tools/` with tests in `GP36_AI/tests/`. `prepare_dataset.py` is left untouched as history. The tools are:
   * inventory and integrity;
   * a label validator;
   * duplicate discovery (SHA-256, pHash/dHash, Roboflow source stem, `lin*` video group);
   * an overlay and contact-sheet generator;
   * a review CSV (`ANNOTATION_AUDIT.csv`, with PASS / NEEDS_REVIEW / FIXED_AND_VERIFIED / QUARANTINED / REJECTED);
   * a group-aware splitter;
   * an atomic builder (build in a temp folder, then rename, never `rmtree` an existing version);
   * manifest and checksums;
   * a final verifier.
3. **Deduplicate and resolve.** One copy per identical group, with labels reconciled through human review. Cross-source duplicates are kept once, with their provenance recorded.
4. **Ontology document** (`CLASS_MAPPING.md`). Positive, negative and ambiguous examples, including the crosswalk, raised table, rumble strip, manhole, patch and dirt-road pothole cases.
5. **Preprocessing policy.** Settle CI-7 (ROI crop). Store v3 images resized to at most 1920 px on the long side, aspect preserved. That cuts decode cost and cache size without losing detail at `imgsz` ≤ 960.
6. **Splits.**
   * Group-aware 70/20/10 for Roboflow.
   * The `lin*` video kept as one separate "unseen road" test group.
   * A **new frozen holdout** of independent groups, ideally EGY_PDD or self-recorded ESP32-CAM footage of Egyptian roads, which would be the most honest test of the deployment domain.
   * The historical 266-image test kept only for backward comparison.
7. **Build `road_hazards_v3_clean`** together with its manifest, `DATA_QUALITY_REPORT.md`, `LEAKAGE_REPORT.md`, `CLASS_MAPPING.md`, `DATASET_LICENSES.md` and `DATASET_SOURCE_REGISTER.csv`.
8. **Then** (Phase 2, separate approval) a new `train.py`. It records the experiment registry and dataset checksum, sets `workers=2`, makes cache opt-in, never evaluates on test automatically, and supports multiple seeds.

## 8. Tests needed to prove each correction

| Correction | Test |
|---|---|
| Filename handling | pytest: 0/1/3/6-dot names, Unicode and spaces, stems over 60 characters sharing a prefix, `.JPG`/`.jpg`, a WEBP disguised as `.jpg`; output pairs are 1:1 and stems are preserved |
| Unreadable image | Builder raises an error and writes no label |
| Labels | Fixtures for an invalid class ID, coordinates out of range, zero area, a 2-point polygon, non-numeric tokens; each is rejected with a reason |
| Class mapping | Per-source mapping table; a source class without a mapping causes a hard failure; COCO and hazard namespaces never collide |
| Leakage | Built splits share no SHA-256 and no dHash group; the `lin*` group sits in exactly one partition |
| Idempotence / atomicity | Building twice gives identical checksums; an interrupted build leaves no partial version folder |
| Non-destructive | The builder refuses to write into an existing version folder |
| Regression cases | `pothole_058`, `G0040808` pair, `pothole_015`↔`157_jpg`, `pothole_076`↔`pothole_151` |

## 9. Risks of each proposed modification

| Modification | Risk | Mitigation |
|---|---|---|
| Deduplication | Removes legitimate hard examples; changes the class balance | Keep one copy per group; log every removal; recheck the class histogram |
| Human label reconciliation | Reviewer bias; time cost (395 pairs + 191 potholes + about 100 test flags) | Written ontology; second reviewer (supervisor) for ambiguous cases |
| New holdout | Small n leads to wide confidence intervals | Report bootstrap CIs; grouped statistics |
| Image down-sizing to ≤1920 px | Loses detail on tiny potholes if `imgsz` is raised later | Keep the originals; resizing is a reproducible build parameter |
| Dropping the ROI crop | Speed-bump recall on the `lin*` road may fall | Measure it on the separate unseen-road test |
| Deleting the 65 GB cache | None for results (it is regenerable) | Only after your approval |
| Adding external datasets | Domain shift, ontology mismatch, licence | One source at a time, with an ablation against the clean baseline |

## 10. Resource estimates (from measured files and hardware)
* **Disk:** about 147 GB free now. A v3 build with ≤1920 px JPEGs would be about 1–1.5 GB. Ultralytics `cache=disk` saves each *decoded source image* as an `.npy` file, which is why 3,538 images reached 65 GB. With ≤1920 px storage that cache would be about 29 GB, and about 13 GB at ≤1280 px. Recommendation: no disk cache. The Roboflow backup needs 2.2 GB. RDD2022 needs tens of GB (to verify before download).
* **Training time:** measured 80 s/epoch (11n@960) and 80 s/epoch (v8n@960, 106 epochs in 2.35 h) on 2,952 images with a disk cache. A controlled Phase 2 grid would be:
  * {v8n, 11n} × {640, 960} × 3 seeds = 12 runs, about 25–35 GPU-hours;
  * a reduced first pass (2 models × 960 × 1 seed) takes about 5–6 h.
* **RAM:** use `workers=2` and close other apps. Only about 4 GB was free during the audit.
* **Human review:** roughly 6–10 hours to review the overlays (your time, or shared with your supervisor).

## 11. Ordered implementation plan
1. **Phase 1a (non-destructive setup):** history manifest, Roboflow backup, `git init` and lock file.
2. **Phase 1b (tooling + tests):** the dataset tools and pytest suite (§7.2, §8).
3. **Phase 1c (forensics outputs):** overlays and contact sheets, duplicate groups, `ANNOTATION_AUDIT.csv` pre-filled with automatic flags.
4. **Phase 1d (human review):** you review the flagged samples, and the ontology decisions are recorded.
5. **Phase 1e (build):** `road_hazards_v3_clean`, plus the holdout freeze, plus all dataset reports. Gates C, D and E are checked here.
6. **Phase 2:** controlled retraining of YOLOv8n and YOLO11n (separate approval), evaluation with CIs, error analysis, latency benchmark.
7. **Phase 3:** `detect_stream.py`, a dual-model shared-frame pipeline with namespaced IDs, tested first on video, then webcam, then ESP32-CAM.
8. **Phase 4:** tracking, then fusion and the UDP schema, run in monitoring mode only.
9. **Phase 5:** deferred datasets (Nature, EGY_PDD), YOLO26n.

## 12. Quality gates

| Gate | Status | Reason |
|---|---|---|
| A Environment | **PASS** | Stack verified on GPU. Resource risks noted. |
| B Raw dataset integrity | **NEEDS_REVIEW** | Local sources fully inventoried and integrity-checked. Licences of the GitHub sources unverified. External datasets not acquired. |
| C Annotation quality | **FAIL** | CI-3 (inconsistent duplicate annotations), unresolved ontology questions |
| D Dataset splitting | **FAIL** | CI-1, CI-2, CI-6 |
| E Training readiness | **BLOCKED** | Depends on C and D |
| F Model validation | **FAIL** for historical models as final models (leaked test). New models NOT_TESTED. | |
| G Dual-model integration | **BLOCKED** | No pipeline code |
| H Sensor fusion | **BLOCKED** | No code or hardware tests |

## 13. Actions requiring your approval
1. Copy `GP36_Dataset/roboflow` to a read-only backup (2.2 GB), and write SHA-256 manifests of all raw data, v2, runs and weights.
2. `git init` in `GP36_AI` with a `.gitignore` for data, weights and the venv, plus `pip freeze > requirements-lock.txt`.
3. Start Phase 1b–1c: create `tools/`, `tests/` and the forensic outputs (new files only).
4. *(Optional)* Delete the regenerable `.npy` cache in `road_hazards_v2` (frees about 65 GB) and the installed torch wheel (2.75 GB).
5. Ontology decisions (needed before Phase 1e): crosswalk / raised table / rumble strip, and unpaved-road potholes.
6. External data:
   * you download Roboflow speed-bump v15 (it needs your account);
   * approve the RDD2022 download, after I verify its size and licence;
   * request EGY_PDD through Dr. Peter Makeen.
