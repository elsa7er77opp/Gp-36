# Metrics report — road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | pothole | 691 | 0.628 | 0.261 | 0.315 | 0.664 | 0.616 | 0.639 | 0.470 | 0.914 (380) | 0.577 (142) | 0.771 | 0.693 / 0.588 / 0.902 |
| v1 | speed_bump | 378 | 0.710 | 0.349 | 0.286 | 0.712 | 0.653 | 0.681 | 0.517 | 0.880 (454) | 0.363 (157) | 0.836 | 0.754 / 0.601 / 0.855 |
| runA_s0 | pothole | 691 | 0.605 | 0.255 | 0.272 | 0.617 | 0.603 | 0.610 | 0.439 | 0.900 (380) | 0.563 (142) | 0.730 | 0.703 / 0.527 / 0.866 |
| runA_s0 | speed_bump | 378 | 0.725 | 0.359 | 0.328 | 0.864 | 0.571 | 0.688 | 0.524 | 0.823 (454) | 0.191 (157) | 0.950 | 0.897 / 0.556 / 0.811 |
| runA_s1 | pothole | 691 | 0.632 | 0.268 | 0.327 | 0.657 | 0.595 | 0.624 | 0.454 | 0.899 (380) | 0.613 (142) | 0.763 | 0.671 / 0.576 / 0.893 |
| runA_s1 | speed_bump | 378 | 0.736 | 0.350 | 0.344 | 0.791 | 0.683 | 0.733 | 0.578 | 0.894 (454) | 0.401 (157) | 0.908 | 0.796 / 0.669 / 0.888 |
| runA_s2 | pothole | 691 | 0.628 | 0.259 | 0.335 | 0.682 | 0.602 | 0.640 | 0.470 | 0.898 (380) | 0.577 (142) | 0.760 | 0.689 / 0.593 / 0.893 |
| runA_s2 | speed_bump | 378 | 0.715 | 0.346 | 0.418 | 0.749 | 0.656 | 0.700 | 0.538 | 0.886 (454) | 0.376 (157) | 0.883 | 0.659 / 0.669 / 0.901 |

## v1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.640 | 0.557 | 0.672 | 31 | 0.878 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 2 | 0.959 |
| source=rf8 | pothole | 781 | 633 | 0.634 | 0.676 | 0.610 | 185 | 0.917 |
| source=rf8 | speed_bump | 781 | 378 | 0.712 | 0.715 | 0.651 | 98 | 0.873 |

## runA_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.583 | 0.543 | 0.655 | 32 | 0.796 |
| source=rf8 | pothole | 781 | 633 | 0.610 | 0.625 | 0.599 | 227 | 0.907 |
| source=rf8 | speed_bump | 781 | 378 | 0.725 | 0.864 | 0.571 | 34 | 0.812 |

## runA_s1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.596 | 0.532 | 0.707 | 36 | 0.878 |
| source=rf8 | pothole | 781 | 633 | 0.640 | 0.674 | 0.585 | 179 | 0.900 |
| source=rf8 | speed_bump | 781 | 378 | 0.737 | 0.791 | 0.683 | 68 | 0.887 |

## runA_s2: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.624 | 0.521 | 0.638 | 34 | 0.837 |
| source=rf8 | pothole | 781 | 633 | 0.644 | 0.703 | 0.597 | 160 | 0.900 |
| source=rf8 | speed_bump | 781 | 378 | 0.715 | 0.749 | 0.656 | 83 | 0.878 |
