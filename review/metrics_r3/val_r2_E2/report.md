# Metrics report — road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 691 | 0.639 | 0.275 | 0.251 | 0.654 | 0.628 | 0.641 | 0.471 | 0.919 (380) | 0.641 (142) | 0.792 | 0.749 / 0.541 / 0.871 |
| C | speed_bump | 378 | 0.703 | 0.359 | 0.192 | 0.770 | 0.648 | 0.704 | 0.543 | 0.866 (454) | 0.306 (157) | 0.900 | 0.869 / 0.542 / 0.819 |
| E1 | pothole | 691 | 0.603 | 0.260 | 0.300 | 0.669 | 0.577 | 0.620 | 0.449 | 0.900 (380) | 0.570 (142) | 0.749 | 0.716 / 0.525 / 0.865 |
| E1 | speed_bump | 378 | 0.733 | 0.357 | 0.253 | 0.821 | 0.630 | 0.713 | 0.553 | 0.854 (454) | 0.261 (157) | 0.950 | 0.872 / 0.577 / 0.823 |
| E2 | pothole | 691 | 0.618 | 0.267 | 0.268 | 0.681 | 0.566 | 0.618 | 0.447 | 0.893 (380) | 0.585 (142) | 0.749 | 0.781 / 0.453 / 0.816 |
| E2 | speed_bump | 378 | 0.675 | 0.325 | 0.427 | 0.944 | 0.532 | 0.680 | 0.515 | 0.800 (454) | 0.057 (157) | 0.960 | 0.877 / 0.545 / 0.814 |

## Near range (care = near, ignore-region semantics) NEXT TO all

Care range: y2 >= 0.60 H and sqrt(area) >= 0.05. GT outside = ignore; predictions on ignore GT or outside the care range are neither TP nor FP. Same thresholds as the full table.

| model | class | AP50 all | AP50 near | n_gt all | n_gt near (ignored) | P/R all @thr | P/R near @thr | BoxAcc all / near | ImgAcc all / near | P/R near @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0.639 | 0.683 | 691 | 142 (549) | 0.654 / 0.628 | 0.728 / 0.641 | 0.471 / 0.517 | 0.919 / 0.949 | 0.814 / 0.556 |
| C | speed_bump | 0.703 | 0.339 | 378 | 157 (221) | 0.770 / 0.648 | 0.571 / 0.306 | 0.543 / 0.249 | 0.866 / 0.872 | 0.528 / 0.121 |
| E1 | pothole | 0.603 | 0.634 | 691 | 142 (549) | 0.669 / 0.577 | 0.669 / 0.570 | 0.449 / 0.445 | 0.900 / 0.933 | 0.694 / 0.528 |
| E1 | speed_bump | 0.733 | 0.399 | 378 | 157 (221) | 0.821 / 0.630 | 0.612 / 0.261 | 0.553 / 0.224 | 0.854 / 0.865 | 0.619 / 0.166 |
| E2 | pothole | 0.618 | 0.630 | 691 | 142 (549) | 0.681 / 0.566 | 0.643 / 0.585 | 0.447 / 0.441 | 0.893 / 0.940 | 0.734 / 0.486 |
| E2 | speed_bump | 0.675 | 0.220 | 378 | 157 (221) | 0.944 / 0.532 | 0.529 / 0.057 | 0.515 / 0.055 | 0.800 / 0.829 | 0.414 / 0.076 |

## C: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.764 | 0.657 | 0.759 | 23 | 0.898 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 1 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.625 | 0.653 | 0.616 | 207 | 0.921 |
| source=rf8 | speed_bump | 781 | 378 | 0.704 | 0.773 | 0.648 | 72 | 0.859 |

## E1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.723 | 0.594 | 0.707 | 28 | 0.878 |
| source=rf8 | pothole | 781 | 633 | 0.596 | 0.679 | 0.566 | 169 | 0.901 |
| source=rf8 | speed_bump | 781 | 378 | 0.733 | 0.821 | 0.630 | 52 | 0.845 |

## E2: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.674 | 0.519 | 0.690 | 37 | 0.857 |
| source=rf8 | pothole | 781 | 633 | 0.625 | 0.705 | 0.555 | 147 | 0.895 |
| source=rf8 | speed_bump | 781 | 378 | 0.676 | 0.943 | 0.529 | 12 | 0.786 |
