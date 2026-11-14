# GP36_AI — folder map (8 Nov 2026)

Start with `review/clean_r2/STATUS_for_claude.md` (full history, Stages 1–38c).

| what | where |
|---|---|
| Meeting 8 Nov (what to show, outline PDF, results) | `meeting_2026-11-08/` (copies only) |
| Project Outline (submit this) | `outline_2026-11-08/final_2026-11-07b/` |
| Supervisor results pack | `supervisor_2026-11-08/` (older: `supervisor_2026-11-01/`) |
| Final model C | `runs/detect/v3b_C_11n_960_s0_r2/weights/best.pt` |
| Test-use ledger (9 uses) | `review/metrics_r3/TEST_LEDGER.csv` |
| All reports (val, part-val, test) | `review/metrics_r3/` |
| Datasets: frozen benchmark r2 / C train set | `road_hazards_v3a_r2/`, `road_hazards_v3b_C/` |
| Other dataset versions (kept, not deleted) | `road_hazards*`, `parts_r3/` |
| Vehicle software (do not edit without review) | `perception/` |
| Tools / tests | `tools/`, `gp36data/`, `tests/` |
| Run scripts (must stay in this folder: they use paths relative to it) | `run_*.bat`, `START_F1.bat`, `RETRY_F1.bat` |
| Old zips, review packages, applied packages, torch installer | `_archive_2026-11-08/` (log of every move: `MOVED.csv`) |

Nothing was deleted when tidying; only untracked, unused files were moved, and each move is in `_archive_2026-11-08/MOVED.csv`.
