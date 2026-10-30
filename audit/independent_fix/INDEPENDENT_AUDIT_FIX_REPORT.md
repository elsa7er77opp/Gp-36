# Independent Audit: Findings and Targeted Fixes (GP36 AI)

**Date:** 30 Oct 2026
**Branch:** `audit-fixes-2026-10-30`
**Baseline:** commit `baef271` on master, tag `baseline-2026-10-30`
**Fixes:** not committed. View them with `git diff baseline-2026-10-30`; the same diff is in `audit/independent_fix/fixes.patch`.
**Status:** STOPPED, waiting for owner approval. Nothing was retrained or rebuilt, and the running training was not touched.

## 0. How this was run (read first)

**Where it ran:**
- All work was done on the laptop's own files, through the remote bridge.
- Code ran in a **Linux VM with `python3`**, not in the Windows venv.

**Run afterwards on Windows by the owner** (see §9):
- **Update 22:13:** the owner ran both on the Windows venv (`tests_counted_windows.txt`):
  - tests: 79 ran, 78 passed, 0 failed, 0 errors, 1 skipped (the symlink test, as expected on Windows);
  - `tools/verify_dataset.py road_hazards_v3a`, strict mode with the near-duplicate check on: **PASS**, 0 errors, 1 warning (3,918 Ultralytics cache files).

**Evidence:**
- Every number below comes from a script and an output file in `audit/independent_fix/`.

| Issue | Priority | Reproduced? | Status |
|---|---|---|---|
| 1. Verifier accepts missing splits | HIGH | **CONFIRMED.** The old code PASSes a dataset with no `test` split when `checksums.sha256` is absent. | Fixed; regression tests pass (Linux) |
| 2. Checksums not strict | MED–HIGH | **CONFIRMED**, all 5 sub-cases | Fixed (strict + labelled legacy mode); tests pass (Linux) |
| 3. Near-duplicate AND rule | MEDIUM | **Partly confirmed.** AND is fine for edited copies, but **no hash rule** reliably catches adjacent video frames. | Measured only; **no rule changed** |
| 4. Unsafe temp-folder cleanup | MEDIUM | **CONFIRMED.** A foreign file was deleted. | Fixed; tests pass (Linux) |
| 5. "56/56 passed" wording | LOW | **CONFIRMED** wording error | Re-run and reported per category; docs corrected |
| 6. 3,032 unreviewed rows | HIGH (final eval) | Confirmed. In v3a, **4,064 of 4,352 images (93.4%)** have never been inspected by eye. | Review plan written; no data changed |
| 7. Leakage | HIGH | **NEW CONFIRMED DEFECT:** temporal leakage of rf8 video frames across v3a splits | Measured; **not fixed** (needs a new split, so owner approval) |

---

## 1. Issue 1: missing splits

**Root cause** (`gp36data/verify.py`, before the fix):
- `if not img_dir.exists(): continue` silently skipped a whole split.
- A missing `labels/<split>` folder only showed up as per-image errors.
- The `train`/`val`/`test` entries in `data.yaml` were never checked.
- The only thing that made missing splits fail was a side effect of the (optional) checksum check.

**Evidence:**
- `repro_BEFORE.txt`, last line, run against the backed-up old `verify.py` (sha `c6a6f57b…`): missing `test` split **and** no checksum file gives **PASS**.

**Fix:**
- In **both** modes, every split must have `images/<split>` and `labels/<split>` folders, and at least one image. Otherwise the result is an error.
- In strict mode, `data.yaml` must point `train`/`val`/`test` to `images/<split>`.
- Empty-label files (verified negatives) are still accepted, and are now counted as `empty_label_images`.
- The command line (`tools/verify_dataset.py`) already returned 1 on failure. This is now covered by a test.

**After:**
- `repro_AFTER.txt`: every missing-split case gives FAIL, in strict and in legacy mode.

## 2. Issue 2: strict checksums

**Root cause:**
- `checksums.sha256` was optional (`if ck.exists()`).
- `line.split("  ", 1)` crashed on a malformed line.
- No check for duplicate records, for paths outside the dataset root, or for files on disk that are not listed.

**Evidence (`repro_BEFORE.txt`):**

| Case | Old result |
|---|---|
| Checksum file deleted | PASS |
| Malformed line | CRASH (`ValueError`) |
| `../outside.txt` entry | Reported as "modified file", i.e. it was hashed outside the root |
| Unlisted extra image + label | PASS |
| Duplicate record | PASS |

**Fix:** `verify_dataset(..., mode="strict")` is now the default. The command line takes `--legacy`.

| Check | Strict | Legacy (historical datasets only) |
|---|---|---|
| `checksums.sha256` and `manifest.csv` must exist | error | warning, plus a `LEGACY MODE` banner; the command line prints `LEGACY PASS (not a strict integrity result)` |
| Malformed, duplicate or outside-root record (absolute path, drive, `\`, `..`, or resolving outside the root) | error, and the file is **not** read | error |
| Missing file / hash mismatch | error | error |
| File on disk not listed in checksums | error | warning |
| `manifest.csv` vs disk (every image listed once, right split, `out_sha256` matches) | error | error if the manifest exists |

- There is no silent downgrade: an unknown mode raises `ValueError`.

**New finding during the fix:**
- Ultralytics `cache=disk` has written **3,916 `*.npy` files and `labels/train.cache` / `labels/val.cache` into `road_hazards_v3a`** during training.
- Without an exception for these, strict mode would FAIL the approved v3a.
- They are now tolerated **only** in these exact forms, and are reported as a warning with a count:
  - `images/<split>/<stem>.npy` next to an image that *is* listed;
  - `labels/<split>.cache`.
- Any other unlisted file is still an error, including an `.npy` with no matching image (this is tested).

**v3a check under the new rules** (`v3a_structure_check.txt`; read-only; **file contents NOT re-hashed**):
- 8,706 checksum records, 0 malformed / outside-root / duplicate.
- 0 records point to a missing file.
- 12,626 files on disk:

  | Files | Count |
  |---|---|
  | Listed in checksums | 8,706 |
  | Derived caches (3,916 `.npy` + 2 `.cache`) | 3,918 |
  | `build_info.json` + `checksums.sha256` | 2 |
  | Unlisted, anything else | 0 |

- `manifest.csv` matches the images on disk, and every split matches its folder.
- The build fingerprint recomputed from `checksums.sha256` is `f8771747…c128`, which equals `build_info.json`.

## 3. Issue 3: near-duplicate rule (evaluated; **nothing changed**)

**Current rules:**
- Verifier: `dHash ≤ 4 AND pHash ≤ 10`.
- v3a split grouping:
  - exact SHA-256;
  - **AND** `dHash ≤ 7 AND pHash ≤ 14` (safety margin);
  - sb15 `video_timeblock:10`.

**Controlled evaluation** (`eval_neardup_rules.py` → `neardup_eval_results.txt`, all pairs in `neardup_eval_pairs.csv`):
- Positive pairs:
  - 120 random v3a images, each as an exact copy, resized ×0.5, JPEG q30, brightness ×0.75 and brightness ×1.25;
  - 519 rf8 GoPro pairs with consecutive frame numbers.
- Negative pairs:
  - 3,000 random pairs from different sources;
  - 2,000 rf8 GoPro pairs ≥ 300 frames apart (hard negatives: same camera and town).

| Rule | Edited copies caught (5 kinds × 120) | Adjacent GoPro frames caught (519) | False positives, different sources (3,000) | False positives, hard negatives (2,000) |
|---|---|---|---|---|
| AND d≤4 & p≤10 (verifier) | 590/600 (brightness 115–116/120) | 157 (30%) | 0 | 0 |
| AND d≤7 & p≤14 (grouping) | **600/600** | 267 (51%) | 0 | 2 |
| OR d≤4 \| p≤10 | 600/600 | 300 (58%) | 1 | 6 |
| OR d≤7 \| p≤14 | 600/600 | 403 (78%) | 4 | 32 |
| p≤16 alone | 600/600 | 427 (82%) | 1 | 59 |
| d+p ≤ 28 | 600/600 | 418 (81%) | 0 | 26 |

**Visual check** (`visual/neardup_borderline.jpg`):
- Both hard negatives flagged by AND 7/14, and 3 sampled OR-only flags, are **different scenes**. So these are real false positives.
- Adjacent GoPro pairs with large distances (d 16–18) **are the same scene**.

**Invalid positive set:**
- The planned "sb15 adjacent frames (Δt ≤ 0.5 s)" positive set turned out to be **invalid**. Pairs with large distances were visibly **different videos**.
- sb15 file names do not identify the video: 210 timestamps occur in more than one frame.
- That set is excluded from every conclusion.

**Conclusion and recommendation (needs approval before any change):**
- For *edited copies*, the AND rule works. The 7/14 margin catches 100% with 2/5,000 false positives.
- For *temporal neighbours*, **no hash threshold is adequate**: the best rules miss about 20% and their false positives grow quickly.
- Recommendation: **keep the hash rules as they are**, and handle video sequences with **metadata (frame-number / sequence) grouping** (Issue 7).
- Optional: switch the verifier to the 7/14 margin to match the grouping rule. It would still report 0 cross-split pairs on v3a.
- The v3a and v3b manifests were not modified.

## 4. Issue 4: temp-folder safety

**Every delete / overwrite operation in `gp36data/build.py`:**

| # | Operation | Before the fix | After the fix |
|---|---|---|---|
| 1 | `shutil.rmtree(tmp)` on `<parent>/.<target>.building` | Ran when the marker file merely existed | Guarded (see below) |
| 2 | `(tmp/MARKER).unlink()` | Deletes the builder's own marker | Unchanged |
| 3 | `os.rename(tmp, out_dir)` | Target existence was checked only at the start | Target is checked again right before the rename |
| 4 | Image and label writes | Only inside the fresh `tmp` | Unchanged |

**Inputs:** never written. Confirmed by the existing test `test_build_passes_and_is_traceable`.

**Root cause:** the presence of the marker file was treated as proof of ownership, and then the whole tree was deleted.

**Evidence:** `repro_BEFORE.txt`: a marked temp folder containing `USER_NOTES.docx` → the build ran → the file was gone.

**Fix:**
- `stale_temp_problems()` allows deletion **only** when all of these hold:
  - the folder is a plain directory (not a symlink);
  - the marker is a JSON ownership record `{"owner": "gp36data.build", "target": <this target>}`;
  - the contents are only the builder's own layout (`images|labels/<train|val|test>/*.img|*.txt` and the builder's top-level files);
  - there are no symlinks anywhere inside.
- Otherwise the build raises `BuildError` and lists the reasons. **Nothing is deleted.**

**After:** `repro_AFTER.txt`: a BuildError is raised, and the foreign file still exists.

## 5. Issue 5: test reporting

**Cause of the 3 skips:**
- They are the 3 tests in `tests/test_real_data_regressions.py`. That class is `@skipUnless(GP36_Dataset exists)`.
- What they cover, on real raw data:
  - multi-dot file-name pairing;
  - `pothole_058` (the CAUTION-sign case);
  - the conflicting `G0040808` pair.
- They are skipped wherever `GP36_Dataset` is absent, e.g. the container used to make the package.
- In the owner's earlier Windows run they were **not** skipped ("Ran 56 tests … OK").
- The status line "56/56 pass on Windows **and Linux**" was wrong for the Linux run: 53 passed and 3 were skipped. It has been corrected.

**Is any skipped test critical?**
- Pairing of real file names matters, but these tests are not the verification gate itself.
- New: `GP36_REQUIRE_REAL_DATA=1` turns the skip into an error, so a run without data cannot look clean.

**Now (Linux VM, laptop files, real data available)** — `run_tests_counted.py` → `tests_counted_vm.txt`:

| Ran | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|
| 79 | 79 | 0 | 0 | 0 |

- 79 = 56 old tests + 23 new tests in `tests/test_audit_fixes.py`.
- With `GP36_REQUIRE_REAL_DATA=1`, the 3 real-data tests ran and passed.

**Windows venv (owner's run, 22:13):** 79 ran, 78 passed, 0 failed, 0 errors, **1 skipped**: `test_symlink_inside_temp_refused_and_target_untouched` (creating symlinks needs admin rights on Windows). That behaviour is covered by the Linux run.

## 6. Issue 6: annotation quality and review plan

**Current v3a reality** (`road_hazards_v3a/manifest.csv` × `ANNOTATION_AUDIT.csv`):

| Split | Reviewed PASS | rf8 unreviewed | ghpot unreviewed | sb15 (never in the audit) | Total |
|---|---|---|---|---|---|
| train | 164 | 1,276 | 104 | 1,502 (687 of them rumble-strip-only negatives) | 3,046 |
| val | 106 | 549 | 59 | 156 | 870 |
| test | **18** | 361 | 23 | 34 | 436 |

**Additional finding:** val and test contain **0 negative images**. All 687 background images are in train.
- So val/test metrics do not measure false positives on hazard-free frames.

**Plan (nothing is applied without approval; all decisions are recorded in a new versioned CSV):**

1. **Test set first, 100% review (436 images).**
   - Do not sample here: the test set is small and final.
   - Checklist per image:
     - wrong class;
     - missed object;
     - ambiguous pothole (D3/D5);
     - false speed bump (D1/D2/D6);
     - tiny or far box (FAR_TINY);
     - box geometry;
     - repeated scene (Issue 7 list).
   - A second pass by a second reviewer on a random 20% (about 87 images) to measure agreement (Cohen's κ).
   - Record in `review/v3a_test_review/TEST_REVIEW.csv` with these columns: `sample_id, decision {OK, FIX, DROP, UNSURE}, codes, corrected_label, reviewer, date`.
   - Any correction makes a **new** folder `road_hazards_v3a_test_r1`. The current test set is never edited.
   - Report metrics on both the old and the corrected test set (impact report).
2. **Val: stratified sample** by source × class: rf8-pothole, rf8-bump, rf8-both, ghpot, sb15-bump.
   - 60 images per stratum, about 300 in total.
   - If a stratum has 0 errors in 60, its error rate is below 6% at 95% confidence (Wilson upper bound about 6.0%).
   - If any stratum's upper bound is above 10%, review that stratum in full.
3. **Train: risk-first.**
   - 100% of the images in `v3a_temporal_neighbour_images.csv` that are kept.
   - A 100-image sample of the 687 rumble-strip-only negatives (risk: a missed speed bump trains the model to ignore it).
   - A stratified 300-image sample of the rest.
4. Report every number as an **error rate with a Wilson 95% interval per stratum**.
   - Until (1) is done, v3a results are **interim** and must not be presented as final.

## 7. Issue 7: leakage verification (built v3a; read-only)

**Scripts:** `leakage_check_v3a.py`, `temporal_detail.py`.
**Outputs:** `leakage_v3a_report.txt`, `temporal_detail.txt`, `temporal_crosssplit_examples.csv`, `v3a_temporal_neighbour_images.csv`.

| Check | Result |
|---|---|
| Exact SHA-256 (original and output files) across splits | **0** |
| Near-duplicates across splits, AND 4/10 and AND 7/14 (hashes of the original images, all 4,352) | **0** |
| OR / single-hash rules | 1,306–4,002 pairs, mostly false positives per §3; not leakage evidence on their own |
| **rf8 GoPro frames (`G00xxxxx`), consecutive number, different split** | **129 pairs. 42 test images (9.6% of test) have the very next or previous frame in train/val.** At gap ≤ 3: 68 test / 132 val / 194 train images. **Visual check: 10/10 sampled pairs are the same scene a few metres apart** (`visual/rf8_adjacent_frames_crosssplit.jpg`). |
| rf8 numeric names (`123_jpg`, `Image00370`, `image28`) | 202 consecutive-number cross-split pairs. Visual sample: **4/8 same scene, 4/8 unrelated** (`visual/rf8_numeric_adjacent_crosssplit.jpg`). Partly sequential. |
| sb15 (same "video" key, Δt ≤ 3 s, different split) | 41 pairs, all hash-distant (d ≥ 15, p ≥ 26). The file names cannot identify the video, so this is **not confirmed and not excluded**. |
| v3a vs v3b_full and v3b_capped val/test | **Identical** (1,306 = 1,306 rows) |
| Built v3a vs `v3a_split_manifest.csv` | Identical |
| Is evaluation data used in training? | `args.yaml`: `data=road_hazards_v3a/data.yaml`, `split: val`. Training uses `images/train`; val is used for per-epoch metrics, early stopping and `best.pt` selection; **test is never used**. |

**Root cause:**
- The Phase 1c audit (CRITICAL_ISSUES CI-14) had already recommended *"an extra frame-number proximity rule for sequential names"*.
- I did **not** implement it in `make_split_v3a.py`. Hashes alone were used.

**Consequences:**
- The v3a val numbers (e.g. mAP50 0.70 at epoch 88) and the `best.pt` selection are **optimistic** by an unknown amount.
- Any v3a test result will be too:
  - up to 163 of 436 test images have a cross-split neighbour at gap ≤ 3 (68 GoPro, high confidence; 95 numeric, about 50% confidence).
- The size of the bias has **not** been measured.

**Options (owner decides; none done):**
- **(a) No retraining.** When the test set is evaluated (once, as planned), also report the metric on the "temporally clean" subset: test minus the images in `v3a_temporal_neighbour_images.csv`. Present both.
- **(b) Correct fix.** `v3a_r1` split:
  - group rf8 sequences by frame-number proximity (GoPro gap ≤ 10; numeric families gap ≤ 3, or only after a visual check);
  - rebuild into a **new** folder;
  - retrain.
  - This changes val/test, so v3b must be re-derived from v3a_r1 to keep the controlled comparison.
- **(c)** Both: (a) now, for Sunday; (b) afterwards.

## 8. Files changed

| File | Change |
|---|---|
| `gp36data/verify.py` | Issues 1 and 2: required splits, `data.yaml` checks, strict/legacy modes, strict checksum parsing, completeness and outside-root checks, `manifest.csv` cross-check, Ultralytics cache exception, file handle closed (needed before the rename on Windows) |
| `gp36data/build.py` | Issue 4: ownership marker in JSON, `stale_temp_problems()`, target re-check before the rename; verifies its temp folder in strict mode |
| `tools/verify_dataset.py` | `--legacy`; prints the mode, warnings and "near-dup SKIPPED"; exit 0/1 unchanged |
| `tests/test_audit_fixes.py` (new) | 23 regression tests for issues 1, 2 and 4 |
| `tests/test_real_data_regressions.py` | `GP36_REQUIRE_REAL_DATA=1` option |

- Backups: `audit/independent_fix/backup_before_fix/` (with `SHA256SUMS`), plus git tag `baseline-2026-10-30`.
- New audit scripts and outputs: `audit/independent_fix/*`.

## 9. Windows run (done by the owner, 22:13)

```
cd C:\Users\ahmed\Desktop\GP36_AI
set GP36_REQUIRE_REAL_DATA=1
venv\Scripts\python audit\independent_fix\run_tests_counted.py
venv\Scripts\python tools\verify_dataset.py road_hazards_v3a
```

Expected:
- **Tests:** 79 ran, 1 skipped (the symlink test on Windows), 0 failed.
- **Verifier:** PASS, with a warning about 3,918 derived training-cache files.
- **Actual:** exactly as expected. Tests 78 passed, 1 skipped; verifier strict PASS with near-duplicates on, 0 errors, 1 warning (3,918 cache files). Also: 687 empty-label images in train and 0 in val/test, which confirms the §6 finding.

## 10. Remaining limitations

- `.npy` cache contents are not verified. If an image changed after caching, Ultralytics would train on stale pixels.
  - Recommendation: delete the caches (`*.npy`, `labels/*.cache`) before any final run, or use `cache=ram`. This needs approval, because it deletes files.
- Between the safety check and the `rmtree` there is still a theoretical race window: something could appear in the temp folder in between. This is acceptable for a single-user laptop.
- The issue 3 evaluation is small (120 images × 5 edits; 519 adjacent pairs) and covers a single camera family for the temporal positives.
- Issue 7 for sb15 cannot be resolved from file names.

## 11. Risks introduced by the changes

- **Strict is now the default.** Older datasets (`road_hazards_v1`/`v2`, which have no checksums or manifest) will FAIL unless they are checked with `--legacy`. This is intended.
- **An empty split is now an error**, so a build with no images in a split fails.
- **Leftover temp folders in the old marker format** (a plain date) are now refused and must be removed by hand. No such folder exists now.
- **The Ultralytics cache exception** is a deliberate, narrow hole in strict completeness. It is documented in the code and reported in the warnings.

## 12. Confirmed untouched

- **`road_hazards_v3a`:** fingerprint recomputed `f8771747…c128`, equal to `build_info.json`. File times are 16:44 (build). The only writer since then is the Ultralytics cache.
- **`manifests/` and `configs/`:** `git diff` against the baseline is empty.
- **Raw datasets and weights:** not opened for writing. `best.pt` and `last.pt` are written only by the running training.
- **`runs/detect/v3a_v8n_960_s0/results.csv`:** shows a git diff, caused **only by the running training**.
- **The training process:** not interrupted. It was at epoch 88 at the last check.

## 13. Needs owner approval

1. Accept or reject the fixes for issues 1, 2 and 4, then commit them on the branch and merge.
2. Issue 7: option (a), (b) or (c).
3. Issue 3: keep the rules (recommended), or switch the verifier to 7/14.
4. Issue 6: start the 100% test-set review, and choose who is the second reviewer.
5. Delete the Ultralytics `.npy` caches before final runs (deletion).
6. All earlier pending items still stand: v3b capped vs full, the test evaluation, the 4 NEEDS_REVIEW fixes, the EGY_PDD email.

D1–D6 and FAR_TINY were not changed.
