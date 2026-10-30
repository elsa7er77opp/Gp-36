# GP36 AI subsystem: review package (status on 30 Oct 2026, 19:45 Cairo; corrected after the independent audit, see `INDEPENDENT_AUDIT_FIX_REPORT.md`)

Project #36, *AI-Powered Multi-Modal Perception System for Autonomous Micro-Mobility Environmental Awareness*. Student: Ahmed Mohamed Elsayed Elreefy (23022692). Supervisor: Dr. Peter Makeen.

This package is for an independent reviewer. It sets out:
1. what was **required** (`01_REQUIREMENTS_master_prompt.md`);
2. what has been **done**, with the evidence files;
3. what is **still open**.

Every number below comes from a file in this package. Nothing here has been verified by a second person yet.

---

## 1. What was required (summary of `01_REQUIREMENTS_master_prompt.md`)

**Workflow:** AUDIT → DIAGNOSE → CLEAN → VERIFY → APPROVE → TRAIN → EVALUATE → INTEGRATE → VALIDATE, with quality gates A–H.

**Rules:**
- Read-only audit first.
- Nothing original is deleted or overwritten.
- External datasets are untrusted until checked.
- No training before the data audits and owner approval.
- Test data is never used for development decisions.
- Every step must be reproducible.
- No fabricated results.

**Target models:**
- Hazard detector (0 = pothole, 1 = speed_bump), trained as YOLOv8n and as YOLO11n on the same frozen data.
- An independent COCO YOLO11n (all 80 classes), never retrained.
- Both run on the same frame and feed a unified perception layer with namespaced IDs, then tracking, then sensor fusion. YOLO26n and a unified detector come later.

**Datasets:**

| Dataset | Planned role |
|---|---|
| RDD2022 | Potholes (D40 only) |
| Roboflow speed-bump v15 | Speed bumps |
| Roboflow v8 | Kept after cleaning |
| GitHub sources | Kept after review |
| Nature 2026 | Deferred to the end |
| EGY_PDD | Future (Egyptian roads) |
| Mendeley | Probably not usable for detection |
| Cityscapes / GOOSE | Future segmentation work only |

---

## 2. What has been done

| Phase | Status | Evidence |
|---|---|---|
| **Phase 0 audit** (environment, code, data, historical runs) | Done | `GP36_AI/audit/PROJECT_AUDIT.md`, `ENVIRONMENT_REPORT.md`, `CODE_AUDIT.md`, `CRITICAL_ISSUES.md`, `audit/evidence/` |
| **1a** Freeze history | Done | SHA-256 manifests (on the laptop, `manifests/2026-10-30_phase1a/`; not included, large); read-only Roboflow backup; `git init` (nothing committed); `requirements-lock.txt` |
| **1b** New tooling + tests | Done | `gp36data/`, `tools/`, `tests/`. **Corrected:** the original 56 tests ran OK on the Windows venv (0 skipped); on Linux *without* `GP36_Dataset`, 53 passed and **3 were skipped** (real-data regressions), so "56/56 on Linux" was wrong. After the audit fixes: 79 tests, Linux VM with real data: 79 passed, 0 failed, 0 errors, 0 skipped. Windows not yet re-run. |
| **1c** Forensic review package | Done | `review/phase1c_2026-10-30/summary.json`, `ANNOTATION_AUDIT.csv` (3,804 rows) |
| **1d** Human/visual review | **Partly done** | `review/phase1d_claude/PHASE1D_PROGRESS.md`, proposals CSVs, index CSVs |
| New data: Roboflow speed-bump v15 | Downloaded and checked | `review/v15_forensics/V15_NOTES.md` |
| New data: RDD2022 | Downloaded, D40 extracted, converted, sample-checked | `review/rdd_forensics/RDD2022_NOTES.md` |
| **1e** Build dataset **v3a (interim)** | Built, **BUILD PASS** | `road_hazards_v3a/build_info.json`, `manifest.csv`, `manifests/v3a_split_manifest.csv` |
| **Independent audit** (7 issues) | Diagnosed; issues 1, 2, 4 fixed on branch `audit-fixes-2026-10-30` (not merged); **new defect: temporal leakage of rf8 video frames across v3a splits** (not fixed) | `audit/independent_fix/INDEPENDENT_AUDIT_FIX_REPORT.md` |
| **Phase 2** training on v3a | **Running** (YOLOv8n, then YOLO11n). **Val numbers are optimistic** because of the temporal leakage | `runs/detect/v3a_v8n_960_s0/args.yaml`, `results.csv` (partial) |
| Phases 3–5 (dual-model pipeline, tracking, fusion, ESP32, YOLO26n) | Not started | — |

### Key findings of the audit (details in `CRITICAL_ISSUES.md`)
1. **The old test set leaked.** 42 of 266 test images were byte-identical to train images, and 100 had a near-duplicate. Without the near-duplicates, the old "best" mAP50 of 0.689 becomes **0.626** (run 4), and run 5 gives 0.610. Neither run is a statistical winner.
2. **Roboflow v8 annotation noise.** 395 byte-identical pairs, of which 225 have conflicting labels: manholes, patches, shadows and litter boxed as potholes, a flat crosswalk boxed as a speed bump, and far tiny boxes.
3. **Roboflow v8 contains video sequences spread across its own splits.** 41 % of its test images share a group with train/valid images.
4. **The earlier conclusion "image size is what helped" was confounded.** Nine settings changed between the two runs.
5. **The "box on the CAUTION sign" error was not reproduced.** It was a drawing artefact: the label text was drawn over the sign.

### Owner decisions recorded (`audit/CLASS_MAPPING.md`)
- **D1** A painted flat crosswalk is background.
- **D2** A raised crossing or an unpainted hump is a `speed_bump`.
- **D3** A pothole on an unpaved road is a `pothole`.
- **D4** One box per defect.
- **D5** Patch, manhole, crack and shadow are background.
- **D6** A rumble strip is **not** a speed bump (ignored).
- **FAR_TINY:** a far box that is not visibly a pothole is dropped.
- Class ratio: natural for v3a.

### Phase 1d review done so far
- **All 225 conflicting duplicate pairs** were reviewed visually, on zoomed side-by-side overlays. Result: 130 keep one copy, 91 quarantine, 3 fix, 1 reject. The owner approved, and the result was written to `ANNOTATION_AUDIT.csv` (backup kept).
- **All 161 minor-difference duplicate pairs** were reviewed: 158 keep, 2 quarantine, 1 fix (a raised hump missing from both copies). Approved and written.
- `ANNOTATION_AUDIT.csv` now holds: PASS 288, REJECTED 294, QUARANTINED 186, NEEDS_REVIEW 4, **UNREVIEWED 3,032**.

### Dataset v3a (interim): what is in it
| Split | Images | Pothole boxes | Speed-bump boxes | rf8 | ghpot | sb15 |
|---|---|---|---|---|---|---|
| train | 3,046 | 2,700 | 1,412 | 1,440 | 104 | 1,502 |
| val | 870 | 771 | 404 | 655 | 59 | 156 |
| test | 436 | 385 | 202 | 379 | 23 | 34 |

**Selection rules:**
- Included: PASS rows, and UNREVIEWED rows whose only automatic flags are leakage or format flags. These are marked **"interim"**: about 4,000 of the 4,352 images have **not** been inspected by eye.
- Excluded: REJECTED, QUARANTINED, NEEDS_REVIEW, TINY_BOX images, regression cases, and duplicate copies.
- The old one-video speed-bump set (370 frames) is held out as an "unseen road" test list.

**Split:**
- Group-aware 70/20/10 with seed 0, over exact-duplicate, near-duplicate (with a safety margin) and video-time-block groups.
- The first build attempt was **refused by the verifier** because of one cross-split near-duplicate pair (G0066108 vs G0066364). The grouping margin was fixed, the split was rebuilt, and the build then passed the verifier: no shared SHA-256 and no near-duplicate across splits.

**Build:** `max_side` 1920 and a fingerprint, both in `build_info.json`.
- Note: `configs/sources.yaml` was extended with `rdd22` **after** the v3a build. The v3a build hash refers to the earlier version, which did not have that block.

### Training now running (Phase 2, first pass)
- **Command:** `yolo train model=yolov8n.pt data=road_hazards_v3a/data.yaml epochs=150 imgsz=960 batch=8 workers=2 cache=disk patience=30 seed=0 name=v3a_v8n_960_s0`, followed by the same command with `yolo11n.pt` (`v3a_11n_960_s0`).
- **Last value seen** (epoch 25, validation set): P 0.66, R 0.58, mAP50 0.61, mAP50-95 0.25. Training is in progress, so **this is not a result**.
- **Evaluation plan:** compare the two models on **val**, then run **test once** per model. A single seed per model is a time constraint; the plan is multi-seed.

### Prepared but not yet run
- **v3b**: v3a plus RDD2022 D40 images (Japan and India) in **train only**. Val and test are identical to v3a, so v3b vs v3a is a single-variable experiment.
  - `v3b_full`: +2,920 images. Pothole:bump ratio is about 5.8 : 1.
  - `v3b_capped`: +791 images (seed 0). Ratio is about 3 : 1. **The owner has to choose.**
- Czech (154 RDD images) is set aside as an unseen-country test. China_MotorBike and United_States were excluded after a visual check: top-down view, Google Street View, and tiny far boxes.

---

## 3. Still open / known limitations
1. **3,032 images remain unreviewed by eye.** The v3a numbers will come from partially reviewed data and must be presented that way.
2. The 4 NEEDS_REVIEW "fix" items still need their corrected label files.
3. Not yet reviewed:
   - the 191 crowd-sourced potholes (`ghpot`);
   - the 370 one-video speed-bump frames;
   - the near-duplicate threshold sheets.
4. v15 labels: about half of the sampled speed bumps cannot be visually confirmed at 640 px. The images are stretched to 640×640, and the set covers only about 15 minutes of video.
5. RDD labels were sample-checked only (25 images).
6. Single seed, so no confidence intervals yet. The latency benchmark (p50/p95/p99) has not been done.
7. EGY_PDD has not been requested (needs the supervisor). The Nature 2026 dataset is deferred.
8. No dual-model pipeline, tracking, ESP32 streaming or fusion code exists yet. Gates G and H are BLOCKED.
9. Git: baseline commit `baef271` (tag `baseline-2026-10-30`); audit fixes on branch `audit-fixes-2026-10-30`, uncommitted, waiting for approval.
10. **Temporal leakage in v3a** (rf8 sequential frames across splits). See the audit report, section 7.

## 4. Gates
| Gate | Status |
|---|---|
| A Environment | PASS |
| B Raw integrity | PASS for local sources and the new downloads (inventoried and checked); GitHub licences are NEEDS_REVIEW |
| C Annotation quality | **PARTIAL**: the reviewed subset passes; v3a is explicitly interim |
| D Splitting | **FAIL (corrected)** for v3a: 0 exact or hash near-duplicates across splits, but rf8 consecutive video frames do cross splits (42 test images have the adjacent frame in train/val; visually confirmed) |
| E Training readiness | Owner approved training on v3a interim |
| F Model validation | NOT_TESTED (training running) |
| G / H | BLOCKED (not implemented) |

## 5. How a reviewer can check
- Tests: `set GP36_REQUIRE_REAL_DATA=1` then `venv\Scripts\python audit\independent_fix\run_tests_counted.py`; it prints passed / failed / errors / skipped separately.
- Rebuild check: `tools/build_dataset.py` refuses to overwrite. Building the same manifest into a new folder must give the same `fingerprint_sha256`.
- Sample review: the ID in each row of `review/phase1d_claude/phase1d_proposals_*.csv` maps through the index CSVs to the original image paths.

## 6. Questions for the reviewer
- Is the interim selection rule for unreviewed images acceptable for a first result?
- v3b_capped or v3b_full?
- Should RDD (cracks still visible but ignored) be used as training data at all, given that it is a different viewpoint and resolution from an ESP32-CAM?
- What should the minimum review sample size be before the final test set is frozen?
