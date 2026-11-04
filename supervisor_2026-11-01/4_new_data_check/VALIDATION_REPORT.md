# New speed-bump data — validation for v3a_r2b (2026-10-31)

Tools:
- `tools/intake_zip.py` (safe extraction);
- `tools/new_data_forensics.py` (integrity, labels, SHA-256, dHash over 8 flip/rotation variants, pHash, vs all 4,188 r2 images and the 10,017 owned hashes);
- `tools/new_vs_r2_pairs.py` (pair sheets).

Every number below is from `summary.json`, `new_images.csv` or `pairs_sub5_val_test.csv` in this folder, unless another file is named.

## Per set
| Set (folder in `GP36_Dataset/raw_v3`) | Images | Boxes by source class | Integrity | Overlap with r2 (strict: dHash≤4 and pHash≤10) | Verdict |
|---|---|---|---|---|---|
| **sub5** `roboflow_speed_unmarked_bumb_v5` | 2,249 (640×640 stretch) | Speed Bump 1,358 · Unmarked Bump 1,177 · Manhole 14 · Pothole 14 · Open Manhole 1 | 0 label errors, 0 empty | 0 exact. Near: train 89 images, **val 140, test 8**. `pairs_sub5_val_test.csv`: 148 images / 199 pairs, all against rf8 (168 val, 31 test) | **FAIL as bulk data** |
| **qub1** `roboflow_qassim_unmarked_bumps_v1` | 1,183 | Unmarked 1,552 · Pothole 153 · Manhole 14 | 1 empty | near val 1, test 1 | **REJECT**: README says 2 augmented versions per source image (flips, 90° rotations) of qub2 |
| **qub2** `roboflow_qassim_unmarked_bumps2_v1` | 820 | Unmarked 1,133 · Pothole 117 · Manhole 12 | 0 errors | near val 1, test 1. All 241 of its within-new groups are shared with other new sets | **REJECT**: same families as sub5 (MVI_15xx, imgge, newonetrwww, speedbreakerrefinedone, VIDEO0012), mostly rotated / upside-down / colour-inverted, oversized boxes (sheet `qub2_random.jpg`) |
| **qubo** `roboflow_qu_bumps_v1_obb` | 300 (OBB labels) | Unmarked 159 · Speed Bump 133 · Manhole 18 · Pothole 7 | **77 images POLY_OUT_OF_RANGE** (rotated boxes beyond the edge), **66 empty labels** | 0 near r2 | **NEEDS_REVIEW**: most varied source (Saudi streets, real humps), but has missing labels, asphalt patches labelled as bumps (D5), and zebra/chevron paint (D1). Usable only after a per-image relabel |

## Why sub5 fails
1. **Same sources as our val/test.** The near-duplicate pairs at the threshold limit (sheet `pairs_sub5_val_test_01.jpg`) are the same places: the Indian campus series `Image00xxx` and the Egyptian videos `MVI_15xx` / `VID_20190924` / `VIDEO0012`. These appear in rf8 under other names. Filename families vs r2 (computed from `new_images.csv` and `road_hazards_v3a_r2/manifest.csv`):
   - `Image` 916 images; r2 has 164 val + 35 train of this family;
   - `MVI_` 615 (9 near val/test);
   - `VIDEO` 73 (8);
   - `VID_20190924_` 63 (14);
   - numeric `NUM` 103 (rf8 numeric names in all r2 splits).

   Any frame of these videos can sit next to a val/test frame, so **whole families are excluded** (rule 4: no new data may leak into the internal val/test).
2. **Remaining families after exclusion:** `speedbreakerrefinedone` (one motorcycle ride, 90 frame numbers, 2.24 copies each), `imgge` (77 originals, 3.09 copies each, with rotated / upside-down / grayscale copies), `newonetrwww` (18 originals) and about 10 misc images. That is **≈185 originals**, not the ≈856 in the preliminary note.
3. **Labels:**
   - `speedbreakerrefinedone` mixes clear raised humps (yellow/black) with flat white chevron/zebra paint (D1 conflict);
   - many `Unmarked Bump` boxes in the excluded MVI families cover half the frame with no visible bump.

The README's "No image augmentation" is contradicted by the grayscale and rotated copies.

## Decision (autonomous, 2026-10-31)
- **No v3a_r2b / Run B from this data now.** Hypothesis check: ≈150–185 originals from 2–3 scenes, added to 3,035 train images, cannot produce a val difference measurably larger than seed noise. Run A vs v1 is single-seed, and seed variance is not yet known. A GPU run is not justified.
- Kept for later, after manual relabel: qubo (300; most varied) and the ≈185 sub5 originals. One upright colour copy per original, D1/D5 checks.
- BD speedbreaker v2 valid+test originals become the external unseen-bump test (next step).
- Within-new grouping note: dihedral dHash≤4 chained 1,956 of the sub5 images into one group (low-texture road images). This grouping is not used for decisions; family exclusion is used instead.
