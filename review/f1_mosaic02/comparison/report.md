# Metrics report — C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 691 | 0.639 | 0.275 | 0.251 | 0.654 | 0.628 | 0.641 | 0.471 | 0.919 (380) | 0.641 (142) | 0.792 | 0.749 / 0.541 / 0.871 |
| C | speed_bump | 378 | 0.703 | 0.359 | 0.192 | 0.770 | 0.648 | 0.704 | 0.543 | 0.866 (454) | 0.306 (157) | 0.900 | 0.869 / 0.542 / 0.819 |
| F1 | pothole | 691 | 0.610 | 0.258 | 0.279 | 0.682 | 0.559 | 0.614 | 0.443 | 0.887 (380) | 0.549 (142) | 0.747 | 0.786 / 0.462 / 0.818 |
| F1 | speed_bump | 378 | 0.667 | 0.331 | 0.232 | 0.771 | 0.606 | 0.679 | 0.513 | 0.851 (454) | 0.236 (157) | 0.900 | 0.831 / 0.548 / 0.819 |

## Near range (care = near, ignore-region semantics) NEXT TO all

Care range: y2 >= 0.60 H and sqrt(area) >= 0.05. GT outside = ignore; predictions on ignore GT or outside the care range are neither TP nor FP. Same thresholds as the full table.

| model | class | AP50 all | AP50 near | n_gt all | n_gt near (ignored) | P/R all @thr | P/R near @thr | BoxAcc all / near | ImgAcc all / near | P/R near @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| C | pothole | 0.639 | 0.683 | 691 | 142 (549) | 0.654 / 0.628 | 0.728 / 0.641 | 0.471 / 0.517 | 0.919 / 0.949 | 0.814 / 0.556 |
| C | speed_bump | 0.703 | 0.339 | 378 | 157 (221) | 0.770 / 0.648 | 0.571 / 0.306 | 0.543 / 0.249 | 0.866 / 0.872 | 0.528 / 0.121 |
| F1 | pothole | 0.610 | 0.626 | 691 | 142 (549) | 0.682 / 0.559 | 0.684 / 0.549 | 0.443 / 0.438 | 0.887 / 0.943 | 0.793 / 0.486 |
| F1 | speed_bump | 0.667 | 0.258 | 378 | 157 (221) | 0.771 / 0.606 | 0.446 / 0.236 | 0.513 / 0.182 | 0.851 / 0.851 | 0.393 / 0.140 |

## C: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.764 | 0.657 | 0.759 | 23 | 0.898 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 1 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.625 | 0.653 | 0.616 | 207 | 0.921 |
| source=rf8 | speed_bump | 781 | 378 | 0.704 | 0.773 | 0.648 | 72 | 0.859 |

## F1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.730 | 0.661 | 0.707 | 21 | 0.857 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 1 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.600 | 0.685 | 0.545 | 159 | 0.889 |
| source=rf8 | speed_bump | 781 | 378 | 0.669 | 0.774 | 0.606 | 67 | 0.843 |
