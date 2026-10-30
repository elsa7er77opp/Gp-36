# Roboflow speed-bump-detection v15 — forensic notes (30 Oct 2026, read-only)

Source zip: `Downloads\Speed Bump Detection.v15-proporsi-60-20-20.yolov8.zip` (110.8 MB), SHA-256 c7365c649a58b044c139c634c287cbd81e2e1df3c936792a773676b116496cc8.
Copy: `GP36_Dataset\_downloads\roboflow_speedbump_v15\`; extracted to `GP36_Dataset\raw_v3\roboflow_speedbump_v15\` (3,387 files, verified complete against the zip).
Export date 14 Feb 2025; licence CC BY 4.0; preprocessing: auto-orient + **resize 640×640 Stretch**; no augmentation.

## Verified facts
| Item | Value |
|---|---|
| Images | 1,692 (train 1,014 / valid 339 / test 339) = 60/20/20 |
| Classes | 0 = `Rumble Strip`, 1 = `Speed-Bump` |
| Boxes | 1,767 — Rumble Strip 691 (train 536 / valid 103 / test 52), Speed-Bump 1,076 (train 522 / valid 238 / test 316) |
| Images with each class | Rumble Strip 687, Speed-Bump 1,005 |
| Label integrity | 0 missing labels, 0 empty labels, 0 polygon/malformed lines, 0 boxes < 6 px side at 640 |
| Exact duplicate images | 0 |
| Median box size (w×h, normalised) | Rumble 0.31×0.067 · Speed-Bump 0.23×0.045 |

## Problems found
1. **Video frames split at image level (leakage).** Every file is a video frame named `frame0-HH-MM-SS…` (7 name patterns). 250 pairs of frames ≤2 s apart in the same sequence sit in different splits. 210 source stems have >1 Roboflow copy, 61 of them across splits. dHash ≤4 flags only 6 valid / 10 test images, so near-duplicate hashing **under-detects** this leakage — the split must be time/sequence-aware, not hash-only.
2. **Stretch preprocessing**: original wide frames were squeezed to 640×640 (visible horizontal compression). Aspect ratio cannot be recovered. Live ESP32-CAM frames will be 4:3 or 16:9 un-stretched → train/inference mismatch (same family as CI-7). Mitigation options: letterbox-style training on these as-is and test the effect on un-stretched data; or keep v15 out of the final test set.
3. **Class ontology**: `Rumble Strip` in v15 = painted transverse white line sets on highways (thermoplastic strips). This is decision **D6 (OPEN)**. They must NOT be merged into `speed_bump` silently.
4. **Domain**: Indonesian residential streets (Speed-Bump class: mostly unpainted asphalt humps, many far/small) and highways (Rumble Strip). Different from Roboflow v8 (South Africa) and from Egypt.
5. Visual sample (16 + 16 random, seed 0): Speed-Bump boxes mostly on visible humps; a few far boxes are hard to verify at 640 (FAR_TINY rule applies). Some Rumble Strip boxes sit on faint/near-invisible lines.

## Proposed use (needs owner approval)
- Speed-Bump class → `speed_bump` after visual review; Rumble Strip → `ignore` (or a separate class) until D6 is decided.
- Re-split by time segments (e.g. 30 s blocks per sequence) with group-aware split; never use the Roboflow split.
- Report results on v15 separately (stretched domain).

Evidence: `GP36_AI\review\v15_forensics\` (stats_part1.txt, dhash.json, multi_copy_stems.json, sample_speed_bump.jpg, sample_rumble_strip.jpg).
