PR #3 was reviewed on the laptop and its files are applied there; the review is in STATUS Stage 24. Excellent audit work. The rules are the same as before.

Work on a NEW branch `claude/r3-cloud-data4`, created from `claude/r3-cloud-data3`, and open a new PR. Commit after each task.

**Laptop decision, for your information.** `rdd_ji:500` STAYS. It is in both D1 and D2, so dropping it would be an untested change to the baseline. The v3b_C recipe is now fixed on the laptop:
- r2 + rsid + bucko + rdd_ji:500 + (sr minus rad, if D2 passes its guard) + dmd + pol + red + ng8 + hmpt + ens + egy_v2 + bpo.
Do not change it.

## Task 1 (highest priority): audit the val/test splits of the new part-vals used for decisions
The parts are bpo, pol, ng8 and red. Their val/test sets will be used to judge v3b_C, so their labels must be trusted.
- For each part, check EVERY val/test box, plus 100 random train boxes (seed 0). Use the same CSV format as before: `vet/<part>/box_audit.csv`, with the same verdicts.
- Also flag val/test IMAGES that have a clearly visible but UNLABELLED pothole or speed bump. Write them to `vet/<part>/valtest_missing_labels.csv` with the columns `file`, `split`, `what`, `note`.
  - A missing label turns a correct detection into a false positive. Those images must be dropped from val/test, not relabelled.
- Extend `tools/apply_box_corrections.py`:
  - add an optional `--drop-images <csv>` that removes the listed images from val/test only (never from train);
  - log the removals in change_log.csv and in build_info;
  - add tests.
- Write the expected result for each part, `vet/<part>/expected_build_info_<part>_v2.json`, and report the error rates per split.
- If a part's val/test error rate is above 10 % after corrections, say so and recommend making it train-only.

## Task 2: help reach ≥ 3 pothole sources
- **CMIRD (Kerala):** find the class names. Check the paper, its GitHub, and any notebooks or code that use it. Name the evidence for each class; do not guess.
- **The 7k dashcam set `refyy-i/dashcam-mg6en-0fwjp`:** collect what you can WITHOUT the full export: project metadata, class names, the licence, the original Universe project and its author, and a sample of image file names (to check families against KNOWN_FAMILIES). The laptop will download and vet the images. Write `vet/d7k/PRECHECK.md`.
- Search further for forward-view pothole sets, with priority on Egypt and MENA. Use the same gate and record every candidate in CANDIDATES.md §H.

## Task 3: supervisor data documentation (no training numbers)
Update `supervisor_2026-11-08/DATA.md` with every new part: dmd, pol, red, ng8, hmpt, ens, egy_v2, bpo, and d7k if accepted. For each part give:
- source URL, author, licence and citation;
- region and viewpoint;
- counts per split, from the `expected_build_info` files;
- the gates it passed (leak rule v2, cross-source check, box audits with their error rates).
Also add the rejected-sources summary, and a short paragraph on the leak rule v2 bug and fix.

Every number cites its file. Keep `TODO(laptop)` wherever the laptop build must confirm a count.

## Output
- Update CLOUD_REPORT.md with a new §0-S4 that has the laptop commands.
- Run the full test suite.
- Push and open the PR, with a short status summary per task.
