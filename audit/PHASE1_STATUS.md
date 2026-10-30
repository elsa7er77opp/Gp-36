# GP36 — Phase 1a–1c status report

**Date:** 2026-10-30. **Approved scope:** Phase 1a (non-destructive setup), 1b (tooling + tests), 1c (forensic review package).
**Not done (out of scope):** no training, downloads, installs, deletions or edits of original files. No git commit (awaiting approval). No dataset was built.

## Phase 1a — history frozen: PASS
| Action | Evidence | Result |
|---|---|---|
| SHA-256 manifests | `manifests/2026-10-30_phase1a/` | raw `GP36_Dataset` 20,050 files (3.80 GB); `road_hazards_v2` 7,609 files excluding `.npy`/`.cache`; v1 1,126; `runs` 171; `weights/` 1; root `.pt`/scripts/log in `root_files.sha256` |
| Roboflow raw backup | `Desktop/graduation project/GP36_Dataset/roboflow` | 6,489 files copied; `--verify` against `raw_roboflow_v8.csv`: **0 missing / 0 extra / 0 changed**; all files set read-only |
| Version control | `.gitignore`, `git init` | Repository initialised, **nothing committed** |
| Environment lock | `requirements-lock.txt` | `pip freeze`. Note: torch is pinned to the local `.whl` path, so keep the wheel or reinstall torch 2.11.0+cu128 from the PyTorch cu128 index |

Check against the historical record at any time:
```
venv\Scripts\python tools\make_manifest.py --root ..\GP36_Dataset --verify manifests\2026-10-30_phase1a\raw_GP36_Dataset.csv
```

## Phase 1b — tooling and tests: PASS (45/45 tests)
The new package `gp36data/` leaves `prepare_dataset.py` untouched. It contains:
* `io_utils`: deterministic pairing. A stem is the name minus its *final* suffix. Ambiguous stems fail. Real image format is detected. Output names are `<source>__<sha16>`: no dots, no truncation, collision-free.
* `labels`: strict parser (13 error codes, 2 warning codes), polygon→bbox conversion, class mapping **by name** with explicit `ignore`, and an annotation comparison (same / minor / conflict).
* `hashing`, `dedup`: SHA-256, dHash, pHash, and union-find leakage groups (exact / near / metadata).
* `split`: deterministic group-aware split with chi-square balancing of images and of each class. Forced groups (e.g. a held-out video) are supported.
* `build`: atomic builder. It validates everything first, writes into a marked temp folder, verifies, then renames. It refuses existing targets, never deletes a foreign folder, recovers from interruption, rejects EXIF-rotated images until they are handled explicitly, and writes `manifest.csv` + `checksums.sha256` + `build_info.json` + a portable `data.yaml` (no absolute path).
* `verify`: pairing, labels, class range, cross-split identical images and near-duplicates, checksums.
* CLIs: `tools/make_manifest.py`, `tools/run_forensics.py`, `tools/build_dataset.py`, `tools/verify_dataset.py`.

Run the tests with:
```
venv\Scripts\python -m unittest discover -s tests -t tests
```
Coverage of the required regression tests:

| Requirement | Test(s) |
|---|---|
| Multiple periods / unusual names | `test_multi_dot_and_unusual_names_pair_one_to_one`, `test_historical_with_suffix_bug_is_real`, `test_long_names_sharing_a_60_char_prefix_do_not_collide` |
| Image without label / label without image | `test_missing_label_and_orphan_label_are_reported`, verify `orphan` check |
| Corrupted / truncated images | `test_truncated_image_is_not_ok`, `test_garbage_bytes_not_ok`, build `corrupt image` |
| Invalid class IDs / mappings | `test_unmapped_source_class_raises`, `test_unknown_target_name_raises`, verify `class 5 >= nc 2` |
| Invalid boxes / out-of-range / polygons | `test_errors` (13 cases), `test_small_overhang_is_clipped_with_warning`, `test_polygon_converted_to_bbox` |
| Duplicates across splits | `test_duplicate_content_across_splits_rejected`, verify `identical image` + `near-duplicate` |
| Interrupted build | `test_interrupted_build_leaves_no_version_and_recovers`, `test_foreign_temp_folder_is_not_deleted` |
| Repeated execution | `test_rebuild_is_identical` (identical checksums and fingerprint) |
| Inputs never modified | `test_build_passes_and_is_traceable` (input manifest identical before and after) |
| Real-data regressions | `pothole_058`, `G0040808` conflict pair, Roboflow multi-dot pairing |

One defect was found and fixed while testing: the first splitter version left train at 77% of the images instead of 70%, because the image and class objectives cancelled each other. It was replaced by chi-square balancing plus local search. The result is now 69.8/20.0/10.2% for images and 70.2/19.8/10.0% for pothole objects.

## Phase 1c — forensic review package: PASS (generated); review not started
Folder: `review/phase1c_2026-10-30/`. Read the guide first: `review/REVIEW_GUIDE.md`. Contents:

| Output | Content |
|---|---|
| `ANNOTATION_AUDIT.csv` | 3,804 rows with automatic flags, group id and sheet references. Every row is `review_status = UNREVIEWED`. |
| `inventory.csv`, `links.csv`, `groups.csv`, `problems.csv`, `summary.json` | Machine evidence |
| `sheets/` (291 contact sheets, 100 MB) | exact_duplicates 99 · near_dup_cross_split 136 · ghpot_all 16 · ghsb_all 24 · rf8 random 4+4 · regression_cases 1 · label_problems 7 |

Key numbers (thresholds: dHash ≤4 **and** pHash ≤10):
* 0 pairing problems, 0 unreadable images, 0 label errors. 77 boxes overhang the image edge by ≤1% (CLIPPED warning). 1 polygon label.
* **395 exact-duplicate pairs: 225 conflict, 161 minor difference, 9 identical labels.** The comparison is per-class box matching with IoU ≥0.5. 225 is higher than Phase 0's 179, because Phase 0 counted only differences in the number of boxes, while this also counts boxes that are present in both copies but not overlapping.
* 2,355 leakage groups: 1,838 singletons; the largest is the 370-frame speed-bump video, then Roboflow GoPro sequences of 47, 31, 23 and 22 frames.
* **New finding CI-14:** Roboflow v8 contains consecutive video frames spread across its splits. 85 of 208 Roboflow test images (41%) share a group with train/valid images.
* 12 images form cross-source groups (6 crowd-sourced potholes duplicated inside Roboflow).
* 383 images have a box shorter than 6 px when letterboxed to 960 px (`TINY_BOX`).
* 36 crowd-sourced files have an extension that does not match their real format. The builder converts these.
* Auto-status: NEEDS_REVIEW 1,962 · AUTO_CHECKS_PASSED 1,842. AUTO_CHECKS_PASSED is **not** PASS.

**Threshold check (visual):** I inspected `near_dup_cross_split_001.jpg`, which holds the pairs *at* the threshold limit (d=4, p=10). Every pair is consecutive frames of the same scene. So the threshold is **not too loose**, and may be conservative: more distant frames of the same sequence may still be ungrouped. This is a NEEDS_REVIEW item for the later sheets.

## Ontology decisions recorded: `audit/CLASS_MAPPING.md`
D1 painted crosswalk = background · D2 raised crossing and unpainted hump = speed_bump · D3 unpaved-road potholes = pothole · D4 one box per defect · D5 patch/manhole/crack/shadow = background (project rule) · **D6 rumble strips = OPEN**.

## Gates
| Gate | Status | Reason |
|---|---|---|
| A Environment | PASS | unchanged |
| B Raw integrity | **PASS** for the local sources (inventoried, hashed, backed up, 0 integrity errors). Licences of the GitHub sources are still NEEDS_REVIEW. | |
| C Annotation quality | **FAIL** (expected) | 225 conflicting duplicate pairs and 1,962 NEEDS_REVIEW rows remain unreviewed |
| D Splitting | **NEEDS_REVIEW** | Tooling is ready and tested. Groups are computed; the threshold needs to be confirmed on more sheets. |
| E Training readiness | BLOCKED | Depends on C and D |

## What is next (each step needs your go-ahead)
1. **Phase 1d: human review.**
   - Start with `exact_duplicates`: it is 225 conflicts, and resolving them fixes most of CI-3.
   - Then `ghpot_all` and `ghsb_all`.
   - Then scan `near_dup_cross_split` to confirm the threshold.
   - Fill in `ANNOTATION_AUDIT.csv` as described in the guide.
   - Option: I pre-mark the rows that the decisions make purely mechanical (e.g. for the 9 identical duplicate pairs, keep one copy and reject the other). That would be a proposal for you to confirm, never an automatic PASS.
2. **Phase 1e: build `road_hazards_v3_clean`** from the reviewed CSV:
   - group-aware 70/20/10 split;
   - the speed-bump video as one forced group (as an "unseen road" test, or all in train: your choice);
   - a frozen new holdout;
   - `verify_dataset` must PASS.
