# Metrics report — parts_r3\ng8_v2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (67) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| C | speed_bump | 20 | 0.924 | 0.558 | 0.434 | 1.000 | 0.900 | 0.947 | 0.900 | 0.970 (47) | — (0) | 1.000 | 1.000 / 0.900 / 0.970 |
| G1 | pothole | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (67) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| G1 | speed_bump | 20 | 0.908 | 0.555 | 0.535 | 1.000 | 0.850 | 0.919 | 0.850 | 0.955 (47) | — (0) | 1.000 | 1.000 / 0.850 / 0.955 |
