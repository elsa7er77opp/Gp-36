# Metrics report — road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 691 | 0.639 | 0.275 | 0.251 | 0.654 | 0.628 | 0.641 | 0.471 | 0.919 (380) | 0.641 (142) | 0.792 | 0.749 / 0.541 / 0.871 |
| C | speed_bump | 378 | 0.703 | 0.359 | 0.192 | 0.770 | 0.648 | 0.704 | 0.543 | 0.866 (454) | 0.306 (157) | 0.900 | 0.869 / 0.542 / 0.819 |
| G1 | pothole | 691 | 0.648 | 0.278 | 0.312 | 0.760 | 0.573 | 0.653 | 0.485 | 0.883 (380) | 0.535 (142) | 0.797 | 0.791 / 0.521 / 0.858 |
| G1 | speed_bump | 378 | 0.686 | 0.347 | 0.284 | 0.835 | 0.601 | 0.698 | 0.537 | 0.835 (454) | 0.197 (157) | 0.923 | 0.877 / 0.563 / 0.817 |

## Near range (care = near, ignore-region semantics) NEXT TO all

Care range: y2 >= 0.60 H and sqrt(area) >= 0.05. GT outside = ignore; predictions on ignore GT or outside the care range are neither TP nor FP. Same thresholds as the full table.

| model | class | AP50 all | AP50 near | n_gt all | n_gt near (ignored) | P/R all @thr | P/R near @thr | BoxAcc all / near | ImgAcc all / near | P/R near @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0.639 | 0.683 | 691 | 142 (549) | 0.654 / 0.628 | 0.728 / 0.641 | 0.471 / 0.517 | 0.919 / 0.949 | 0.814 / 0.556 |
| C | speed_bump | 0.703 | 0.339 | 378 | 157 (221) | 0.770 / 0.648 | 0.571 / 0.306 | 0.543 / 0.249 | 0.866 / 0.872 | 0.528 / 0.121 |
| G1 | pothole | 0.648 | 0.668 | 691 | 142 (549) | 0.760 / 0.573 | 0.800 / 0.535 | 0.485 / 0.472 | 0.883 / 0.940 | 0.830 / 0.514 |
| G1 | speed_bump | 0.686 | 0.314 | 378 | 157 (221) | 0.835 / 0.601 | 0.600 / 0.191 | 0.537 / 0.169 | 0.835 / 0.848 | 0.595 / 0.159 |

## C: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.764 | 0.657 | 0.759 | 23 | 0.898 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 1 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.625 | 0.653 | 0.616 | 207 | 0.921 |
| source=rf8 | speed_bump | 781 | 378 | 0.704 | 0.773 | 0.648 | 72 | 0.859 |

## G1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.692 | 0.679 | 0.655 | 18 | 0.837 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 2 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.647 | 0.769 | 0.564 | 107 | 0.886 |
| source=rf8 | speed_bump | 781 | 378 | 0.689 | 0.840 | 0.598 | 43 | 0.825 |
