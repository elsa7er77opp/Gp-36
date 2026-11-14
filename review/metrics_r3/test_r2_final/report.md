# Metrics report — road_hazards_v3a_r2 / test

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: review\metrics_r3\val_r2_final\report.json. IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 285 | 0.711 | 0.337 | 0.251 | 0.612 | 0.726 | 0.665 | 0.498 | 0.938 (152) | 0.807 (119) | 0.838 | 0.727 / 0.674 / 0.904 |
| C | speed_bump | 160 | 0.320 | 0.118 | 0.192 | 0.508 | 0.200 | 0.287 | 0.168 | 0.663 (171) | 0.250 (104) | 0.269 | 0.767 / 0.144 / 0.607 |
| WBF_C_v1 | pothole | 285 | 0.698 | 0.324 | 0.148 | 0.671 | 0.688 | 0.679 | 0.514 | 0.938 (152) | 0.773 (119) | 0.837 | 0.860 / 0.344 / 0.706 |
| WBF_C_v1 | speed_bump | 160 | 0.463 | 0.157 | 0.090 | 0.565 | 0.381 | 0.455 | 0.295 | 0.780 (171) | 0.394 (104) | 0.480 | 1.000 / 0.056 / 0.557 |

## Near range (care = near, ignore-region semantics) NEXT TO all

Care range: y2 >= 0.60 H and sqrt(area) >= 0.05. GT outside = ignore; predictions on ignore GT or outside the care range are neither TP nor FP. Same thresholds as the full table.

| model | class | AP50 all | AP50 near | n_gt all | n_gt near (ignored) | P/R all @thr | P/R near @thr | BoxAcc all / near | ImgAcc all / near | P/R near @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0.711 | 0.814 | 285 | 119 (166) | 0.612 / 0.726 | 0.667 / 0.807 | 0.498 / 0.575 | 0.938 / 0.963 | 0.760 / 0.773 |
| C | speed_bump | 0.320 | 0.389 | 160 | 104 (56) | 0.508 / 0.200 | 0.542 / 0.250 | 0.168 / 0.206 | 0.663 / 0.796 | 0.769 / 0.192 |
| WBF_C_v1 | pothole | 0.698 | 0.801 | 285 | 119 (166) | 0.671 / 0.688 | 0.773 / 0.773 | 0.514 / 0.630 | 0.938 / 0.963 | 0.889 / 0.471 |
| WBF_C_v1 | speed_bump | 0.463 | 0.482 | 160 | 104 (56) | 0.565 / 0.381 | 0.562 / 0.394 | 0.295 / 0.301 | 0.780 / 0.851 | 1.000 / 0.087 |

## C: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 46 | 50 | 0.850 | 0.717 | 0.860 | 17 | 0.935 |
| source=rf8 | pothole | 277 | 235 | 0.679 | 0.590 | 0.698 | 114 | 0.939 |
| source=rf8 | speed_bump | 277 | 160 | 0.323 | 0.508 | 0.200 | 31 | 0.606 |

## WBF_C_v1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 46 | 50 | 0.829 | 0.741 | 0.860 | 15 | 0.957 |
| source=ghpot | speed_bump | 46 | 0 | — | 0.000 | 0.000 | 1 | 0.978 |
| source=rf8 | pothole | 277 | 235 | 0.664 | 0.654 | 0.651 | 81 | 0.935 |
| source=rf8 | speed_bump | 277 | 160 | 0.466 | 0.570 | 0.381 | 46 | 0.747 |
