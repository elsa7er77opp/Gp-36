# Metrics report — parts_r3\bucko / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | pothole | 186 | 0.399 | 0.133 | 0.202 | 0.497 | 0.403 | 0.445 | 0.286 | 0.696 (42) | 0.604 (48) | 0.363 | 0.560 / 0.274 / 0.672 |
| v1 | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 0.976 |
| runA_s0 | pothole | 186 | 0.422 | 0.140 | 0.305 | 0.569 | 0.398 | 0.468 | 0.306 | 0.720 (42) | 0.562 (48) | 0.412 | 0.606 / 0.339 / 0.680 |
| runA_s0 | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 0.992 |
| D1_11n | pothole | 186 | 0.571 | 0.237 | 0.201 | 0.591 | 0.575 | 0.583 | 0.412 | 0.848 (42) | 0.688 (48) | 0.597 | 0.701 / 0.366 / 0.752 |
| D1_11n | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| D1_11s | pothole | 186 | 0.606 | 0.224 | 0.256 | 0.640 | 0.565 | 0.600 | 0.429 | 0.824 (42) | 0.771 (48) | 0.684 | 0.730 / 0.452 / 0.776 |
| D1_11s | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| bumponly | pothole | 186 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.336 (42) | 0.000 (48) | 0.000 | 0.000 / 0.000 / 0.336 |
| bumponly | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |
| potonly | pothole | 186 | 0.527 | 0.192 | 0.209 | 0.567 | 0.548 | 0.557 | 0.386 | 0.824 (42) | 0.667 (48) | 0.600 | 0.746 / 0.285 / 0.704 |
| potonly | speed_bump | 0 | — | — | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 (125) | — (0) | 0.000 | 0.000 / 0.000 / 1.000 |

## v1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.445 | 0.505 | 0.471 | 55 | 0.824 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.503 | 0.475 | 0.543 | 21 | 0.727 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.226 | 0.000 | 0.000 | 0 | 0.512 |

## runA_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.493 | 0.556 | 0.462 | 44 | 0.804 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.518 | 0.621 | 0.514 | 11 | 0.788 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.117 | 0.500 | 0.031 | 1 | 0.561 |

## D1_11n: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.575 | 0.578 | 0.563 | 49 | 0.843 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.615 | 0.541 | 0.571 | 17 | 0.788 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.609 | 0.704 | 0.594 | 8 | 0.878 |

## D1_11s: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.622 | 0.667 | 0.538 | 32 | 0.824 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.618 | 0.512 | 0.629 | 21 | 0.788 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.604 | 0.750 | 0.562 | 6 | 0.854 |

## bumponly: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.000 | 0.000 | 0.000 | 0 | 0.176 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.000 | 0.000 | 0.000 | 0 | 0.364 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.000 | 0.000 | 0.000 | 0 | 0.512 |

## potonly: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=condition=Clear_weather;video=Vid_1_Pr | pothole | 51 | 119 | 0.528 | 0.532 | 0.555 | 58 | 0.863 |
| meta=condition=Evening;video=Vid_Pr_evening | pothole | 33 | 35 | 0.604 | 0.600 | 0.600 | 14 | 0.758 |
| meta=condition=Night;video=Vid_Pr_night | pothole | 41 | 32 | 0.503 | 0.700 | 0.438 | 6 | 0.829 |
