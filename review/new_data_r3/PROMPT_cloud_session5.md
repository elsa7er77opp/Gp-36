PR #4 was reviewed on the laptop, and its files are applied there (STATUS Stage 25). The polygon self-correction was exactly right: thank you for reporting it openly.

Laptop decisions so you know:
- bpo is train-only.
- The decision part-vals for v3b_C are:
  - bumps: pol_v2, red_v2, ng8_v2 and RSID;
  - potholes: Bučko and egy_v2 (egy_v2 is reported only, because it is small).
- The recipe stays fixed.

Same rules as before. Work on a new branch `claude/r3-cloud-data5` from `claude/r3-cloud-data4`, open a new PR, and commit after each task.

## Task 1: supervisor tables and figures tool (high priority; the laptop fills in the numbers)
Write `tools/make_supervisor_tables.py`.
- **Input:**
  - one or more `review/metrics_r3/<name>/report.json` files, as written by `tools/metrics_report.py` (read that code for the exact schema);
  - a small YAML/JSON "table spec" that says which model/eval-set rows to show.
- **Output:**
  - Markdown tables for `supervisor_2026-11-08/METRICS.md`, per class (pothole, speed_bump), with P, R, F1, mAP50, mAP50-95, BoxAcc = TP/(TP+FP+FN), ImgAcc, NearR and P@R50. Show them both at the val-chosen operating threshold and at deploy conf 0.35. Each table names its source report file and the number of images and boxes.
  - PNG figures (matplotlib, Agg): per-class grouped bars of mAP50 per model and eval set, and a recall/precision plot per class at the operating point.
- **Refusals:**
  - it refuses to label anything as "test" unless the report's split is test;
  - it never computes metrics itself, it only formats them.
- **Tests:** use synthetic report.json files.

## Task 2: test-use ledger (honesty guard)
Write `tools/test_ledger.py` and the file `review/metrics_r3/TEST_LEDGER.csv`.
- The ledger has these columns: model weights SHA-256, model name, benchmark (r2_test, bd87, rsid_test, bucko_test, sr_test, rdd_cz_test, pol_v2_test, red_v2_test, ng8_v2_test, egy_v2_test), date and command.
- `check <weights> <benchmark>` exits non-zero if that pair is already in the ledger.
- `add ...` appends a row.
- Also fill the ledger with the PAST test uses recorded in `review/clean_r2/STATUS_for_claude.md`, citing the stage. Example: Run A s0 on r2 test, `runs/v3a_r2_11n_960_s0_TEST.txt`. If a past use is unclear, mark it UNRESOLVED.
- Add tests.

## Task 3: pothole sources, time-boxed to about 1/3 of the session
- Vet SaudiRD (`refyy-i/saudird-luumi`) if its export is ready.
- Continue the MENA / forward-view pothole search: Jordan, Morocco, Iraq, Gulf, Turkey, Pakistan, plus other Egyptian graduation projects on GitHub or Kaggle. Use the same gate, record the results in CANDIDATES.md §I, and list any new forks.

## Output
- Update CLOUD_REPORT.md with a new §0-S5.
- Run the full test suite.
- Push and open the PR, with a short status summary per task.
