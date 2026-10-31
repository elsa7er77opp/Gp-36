# AI Training Results — v3a_r1 (31 Oct 2026)

Continues `claude/15-ai-training-log.md`. Where the two disagree, this file supersedes it.

**Detail:**
- `audit/INDEPENDENT_AUDIT_FIX_REPORT.md`
- On the laptop:
  - `review/v3a_r1_test_review/REVIEW_SUMMARY.md`
  - `runs/v3a_r1_RESULTS.csv`
  - `runs/v3a_r1_*_{VAL,TEST}.txt`

## Dataset `road_hazards_v3a_r1`
**Build:** strict-verified PASS. Fingerprint `19747b58…878d`. Manifest: `manifests/v3a_r1_final_split_manifest.csv`.

| Split | Images | Pothole boxes | Bump boxes | Negatives | Notes |
|---|---|---|---|---|---|
| train | 3,043 | 2,695 | 1,413 | 687 | interim: not reviewed by eye |
| val | 870 | 768 | 403 | 0 | interim |
| test | 324 | 286 | 160 | 0 | **100% reviewed by eye**, frozen |

**What is different from v3a:**
- **Grouping.** Groups also join video frames that are close in time:
  - rf8 frame numbers within 10 of each other;
  - sb15 frames ≤ 5 s apart that also look alike.
  - Result across splits: 0 exact duplicates, 0 near-duplicates, 0 temporal neighbours.
- **Test review.** 111 of the 435 test images were excluded: unclear far bumps, tiny far boxes, missing labels, and patch/crack/manhole boxes.
- **Rotation fix.** 43 rf8 phone photos (IMG_4421–4582) were stored sideways while their labels match the upright view. Their pixels are rotated 90° clockwise at build time (`rotate_cw`). 4 photos whose orientation was unclear were dropped.

## Results
All runs use: imgsz 960, batch 8, patience 30, seed 0, single run.

| Model | Val mAP50 | Val pothole | Val bump | Test mAP50 | Test pothole | Test bump | Test mAP50-95 | Inference |
|---|---|---|---|---|---|---|---|---|
| YOLOv8n (3.1M params) | 0.617 | 0.574 | 0.659 | 0.446 | 0.623 | 0.269 | 0.186 | 4.6 ms |
| **YOLO11n** (2.6M params) | **0.636** | 0.583 | 0.689 | **0.507** | **0.660** | **0.354** | 0.204 | 5.2 ms |

- **Selection:** YOLO11n, chosen on val. The test was run **once** per model and agrees with val.
- **Frozen baseline v1 = `runs/detect/v3a_r1_11n_960_s0/weights/best.pt`.**
- **Caveats:**
  - A single seed, so there are no confidence intervals.
  - "NMS time limit exceeded" appeared on the first batch (CUDA warm-up) of the v8n test run and the 11n val run. Those numbers may be slightly pessimistic.

## How to read them
- **Pothole, test mAP50 0.66:** an honest number. The test set is reviewed by eye and does not leak.
- **Speed bump, test mAP50 0.35:** the 152 test bump images come from **only 2 rf8 dash-cam sequences**, 132 of them from one drive (frames 1623–1807: parking gates, a sun-glare highway). So this number means "generalising to one unseen video", with very high variance.
  - The val bumps come from 4 sequences. The train bumps are dominated by one sb15 video cluster (1,110 of 1,334 bump images).
  - **The bottleneck is speed-bump data diversity, not the training recipe.**
- **Old vs new numbers:** the earlier "0.69–0.71" numbers were inflated by leakage (duplicate images and adjacent video frames across the splits).
- **Error pattern (val confusion matrix):**
  - the two classes are almost never confused with each other;
  - most false positives are "pothole" on background, consistent with patch/crack/manhole labels in the unreviewed train set.

## What would improve it (in order of expected value)
1. **More independent speed-bump videos.** Many short clips from different streets beat many frames from one clip. Sources: EGY_PDD (ask the supervisor); other public bump sets; the pod's own camera once the lab car is available. The brief requires a local micro-mobility dataset anyway (Task 3).
2. **Review the train labels.** Start with patch, manhole and crack boxes labelled as pothole, and with crosswalks labelled as speed bump.
3. **v3b (already prepared).** It adds RDD2022 D40 potholes to train only, so val and test are unchanged and the comparison is clean. It helps potholes only.
4. **Training-recipe changes are low priority:**
   - multi-seed runs (for confidence intervals);
   - imgsz 1280 for far objects;
   - augmentation.
   - Expect small gains until the data changes.
5. **Domain gap.** The pod camera (low mounting, ESP32-CAM or webcam) differs from dash-cam data. Final validation must use pod footage.
