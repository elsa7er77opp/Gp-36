# v3a_r1: test-set visual review and rotation check (30 Oct 2026)

**Status:** first pass by Claude. **Nothing is applied until the owner approves.**

## 1. Split v3a_r1 (`manifests/v3a_r1_split_manifest.csv`, `tools/make_split_v3a_r1.py`)
- **Same 4,352 images and labels as v3a.** Only the grouping changed. Groups are built from:
  - the v3a groups;
  - rf8 GoPro frame numbers within 10 of each other;
  - rf8 numeric-name families within 10 of each other;
  - sb15 frames ≤ 5 s apart that also look alike.
- **Split result (seed 0):**

  | Split | Images |
  |---|---|
  | train | 3,045 (all 1,692 sb15 images end up here) |
  | val | 872 |
  | test | 435 |

- **Leakage check** (`audit/independent_fix/leakage_r1_report.txt`), all across splits:
  - exact copies: 0;
  - near-duplicates: 0;
  - rf8 frames within 10 numbers of each other: 0.
- A first attempt with a numeric gap of 3 left 54 cross-split pairs. It was kept as `v3a_r1_split_manifest_attempt1_numgap3.csv`.

## 2. Test set: 100% visual review (`TEST_REVIEW.csv`, sheets T01–T05 and R01–R48)
- Every test image was checked: the full frame plus a zoom on the labelled region.
- **Result:** 316 OK, 20 FIX, 99 UNSURE.
- **Main reasons:**

  | Reason | Images |
  |---|---|
  | Far speed bump not visible even when zoomed | 42 |
  | Far tiny pothole box | 13 |
  | Ambiguous (erosion channel, ravelling, stain) | 21 |
  | Missing boxes (clear potholes not labelled) | 6 |
  | Patch, crack, manhole or shadow boxed as pothole (owner rule D5) | about 20 |
  | **Rotation mismatch** (see §3) | 8 |

## 3. New source defect: sideways phone photos (`ROTATION_REVIEW.csv`, sheets rot_*)
- Some rf8 `IMG_xxxx` phone photos are stored rotated 90°, while their labels match the upright image. The boxes therefore fall on the wrong place.
- **Check:** all 302 `IMG_*` images were shown twice with the same boxes, once as stored and once rotated 90° clockwise.

| Split | Need a 90° clockwise rotation | Unsure |
|---|---|---|
| train | 19 | 2 |
| val | 16 | 2 |
| test | 8 | 0 |

- All the affected images fall in the range IMG_4421–IMG_4582.
- Fixing them means rotating the pixels only. The labels stay as they are.

## 4. Proposal for the owner
- **Test v3a_r1:**
  - keep the 316 OK images, plus the 8 rotation-fixed images;
  - exclude the 111 FIX/UNSURE images. They are **not** moved to train or val, because their groups sit in test.
  - The final test set would hold 324 images: 286 pothole boxes and 160 speed-bump boxes.
- **Train/val:**
  - rotate the 35 confirmed images;
  - drop the 4 unsure ones.
  - Everything else in train/val stays interim (it has not been reviewed by eye).
- **Other notes from the rotation sheets** (train only, not changed):
  - 4 crosswalks are labelled as speed bumps. Under D1/D2 it is unclear whether they are flat or raised.
  - 3 manhole covers are boxed as potholes (D5).
