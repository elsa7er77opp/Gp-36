# Metrics report — parts_r3\sr / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| runA_s0 | pothole | 108 | 0.350 | 0.135 | 0.232 | 0.383 | 0.472 | 0.423 | 0.268 | 0.835 (128) | 0.370 (54) | 0.327 | 0.493 / 0.306 / 0.902 |
| runA_s0 | speed_bump | 35 | 0.000 | 0.000 | 0.486 | 0.000 | 0.000 | 0.000 | 0.000 | 0.799 (132) | 0.000 (34) | 0.000 | 0.000 / 0.000 / 0.793 |
| D1_s0 | pothole | 108 | 0.396 | 0.151 | 0.303 | 0.531 | 0.398 | 0.455 | 0.295 | 0.884 (128) | 0.463 (54) | 0.346 | 0.565 / 0.324 / 0.896 |
| D1_s0 | speed_bump | 35 | 0.000 | 0.000 | 0.001 | 0.002 | 0.029 | 0.004 | 0.002 | 0.463 (132) | 0.029 (34) | 0.000 | 0.000 / 0.000 / 0.805 |
| D2 | pothole | 108 | 0.433 | 0.179 | 0.290 | 0.538 | 0.389 | 0.452 | 0.292 | 0.890 (128) | 0.463 (54) | 0.377 | 0.621 / 0.333 / 0.909 |
| D2 | speed_bump | 35 | 0.000 | 0.000 | 0.624 | 0.000 | 0.000 | 0.000 | 0.000 | 0.811 (132) | 0.000 (34) | 0.000 | 0.000 / 0.000 / 0.811 |

## runA_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=family=dz | pothole | 93 | 3 | 0.001 | 0.000 | 0.000 | 14 | 0.849 |
| meta=family=kg | pothole | 39 | 105 | 0.417 | 0.477 | 0.486 | 56 | 0.846 |
| meta=family=rad | pothole | 32 | 0 | — | 0.000 | 0.000 | 12 | 0.781 |
| meta=family=rad | speed_bump | 32 | 35 | 0.000 | 0.000 | 0.000 | 0 | 0.000 |

## D1_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=family=dz | pothole | 93 | 3 | 0.008 | 0.000 | 0.000 | 5 | 0.914 |
| meta=family=dz | speed_bump | 93 | 0 | — | 0.000 | 0.000 | 304 | 0.258 |
| meta=family=kg | pothole | 39 | 105 | 0.435 | 0.592 | 0.400 | 29 | 0.795 |
| meta=family=kg | speed_bump | 39 | 0 | — | 0.000 | 0.000 | 32 | 0.795 |
| meta=family=rad | pothole | 32 | 0 | — | 0.000 | 0.000 | 4 | 0.906 |
| meta=family=rad | speed_bump | 32 | 35 | 0.000 | 0.000 | 0.000 | 111 | 0.625 |

## D2: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=family=dz | pothole | 93 | 3 | 0.006 | 0.000 | 0.000 | 4 | 0.925 |
| meta=family=kg | pothole | 39 | 105 | 0.476 | 0.600 | 0.400 | 28 | 0.795 |
| meta=family=rad | pothole | 32 | 0 | — | 0.000 | 0.000 | 4 | 0.906 |
| meta=family=rad | speed_bump | 32 | 35 | 0.000 | 0.000 | 0.000 | 1 | 0.031 |
