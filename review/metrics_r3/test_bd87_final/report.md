# Metrics report — external_tests\bd87_eval_view / test

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: review\metrics_r3\val_r2_final\report.json. IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0 | — | — | 0.251 | 0.000 | 0.000 | 0.000 | 0.000 | 0.920 (87) | — (0) | 0.000 | 0.000 / 0.000 / 0.966 |
| C | speed_bump | 88 | 0.731 | 0.353 | 0.192 | 0.732 | 0.682 | 0.706 | 0.545 | 0.747 (0) | 0.500 (2) | 0.936 | 0.857 / 0.614 / 0.667 |
| WBF_C_v1 | pothole | 0 | — | — | 0.148 | 0.000 | 0.000 | 0.000 | 0.000 | 0.977 (87) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| WBF_C_v1 | speed_bump | 88 | 0.731 | 0.326 | 0.090 | 0.775 | 0.625 | 0.692 | 0.529 | 0.724 (0) | 0.500 (2) | 0.898 | 1.000 / 0.205 / 0.207 |

## Near range (care = near, ignore-region semantics) NEXT TO all

Care range: y2 >= 0.60 H and sqrt(area) >= 0.05. GT outside = ignore; predictions on ignore GT or outside the care range are neither TP nor FP. Same thresholds as the full table.

| model | class | AP50 all | AP50 near | n_gt all | n_gt near (ignored) | P/R all @thr | P/R near @thr | BoxAcc all / near | ImgAcc all / near | P/R near @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | — | — | 0 | 0 (0) | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.920 / 0.954 | 0.000 / 0.000 |
| C | speed_bump | 0.731 | 0.629 | 88 | 2 (86) | 0.732 / 0.682 | 0.500 / 0.500 | 0.545 / 0.333 | 0.747 / 0.977 | 0.500 / 0.500 |
| WBF_C_v1 | pothole | — | — | 0 | 0 (0) | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.977 / 1.000 | 0.000 / 0.000 |
| WBF_C_v1 | speed_bump | 0.731 | 0.670 | 88 | 2 (86) | 0.775 / 0.625 | 0.500 / 0.500 | 0.529 / 0.333 | 0.724 / 0.977 | 0.000 / 0.000 |
