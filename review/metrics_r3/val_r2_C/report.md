# Metrics report — road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1_s0 | pothole | 691 | 0.596 | 0.251 | 0.279 | 0.625 | 0.579 | 0.601 | 0.430 | 0.898 (380) | 0.542 (142) | 0.719 | 0.693 / 0.517 / 0.857 |
| D1_s0 | speed_bump | 378 | 0.710 | 0.330 | 0.327 | 0.727 | 0.619 | 0.669 | 0.502 | 0.871 (454) | 0.280 (157) | 0.863 | 0.735 / 0.595 / 0.861 |
| D2 | pothole | 691 | 0.615 | 0.261 | 0.296 | 0.643 | 0.601 | 0.621 | 0.451 | 0.916 (380) | 0.535 (142) | 0.736 | 0.702 / 0.550 / 0.878 |
| D2 | speed_bump | 378 | 0.683 | 0.346 | 0.398 | 0.818 | 0.571 | 0.673 | 0.507 | 0.835 (454) | 0.146 (157) | 0.904 | 0.782 / 0.579 / 0.840 |
| C | pothole | 691 | 0.639 | 0.275 | 0.251 | 0.654 | 0.628 | 0.641 | 0.471 | 0.919 (380) | 0.641 (142) | 0.792 | 0.749 / 0.541 / 0.871 |
| C | speed_bump | 378 | 0.703 | 0.359 | 0.192 | 0.770 | 0.648 | 0.704 | 0.543 | 0.866 (454) | 0.306 (157) | 0.900 | 0.869 / 0.542 / 0.819 |

## D1_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.629 | 0.477 | 0.724 | 46 | 0.918 |
| source=rf8 | pothole | 781 | 633 | 0.604 | 0.649 | 0.566 | 194 | 0.896 |
| source=rf8 | speed_bump | 781 | 378 | 0.710 | 0.727 | 0.619 | 88 | 0.863 |

## D2: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.615 | 0.513 | 0.672 | 37 | 0.898 |
| source=rf8 | pothole | 781 | 633 | 0.623 | 0.660 | 0.592 | 193 | 0.915 |
| source=rf8 | speed_bump | 781 | 378 | 0.683 | 0.818 | 0.571 | 48 | 0.825 |

## C: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| source=ghpot | pothole | 49 | 58 | 0.764 | 0.657 | 0.759 | 23 | 0.898 |
| source=ghpot | speed_bump | 49 | 0 | — | 0.000 | 0.000 | 1 | 0.980 |
| source=rf8 | pothole | 781 | 633 | 0.625 | 0.653 | 0.616 | 207 | 0.921 |
| source=rf8 | speed_bump | 781 | 378 | 0.704 | 0.773 | 0.648 | 72 | 0.859 |
