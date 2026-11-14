# Metrics report — road_hazards_v3a_r2 / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1_s0 | pothole | 691 | 0.596 | 0.251 | 0.279 | 0.625 | 0.579 | 0.601 | 0.430 | 0.898 (380) | 0.542 (142) | 0.719 | 0.693 / 0.517 / 0.857 |
| D1_s0 | speed_bump | 378 | 0.710 | 0.330 | 0.327 | 0.727 | 0.619 | 0.669 | 0.502 | 0.871 (454) | 0.280 (157) | 0.863 | 0.735 / 0.595 / 0.861 |
| D2 | pothole | 691 | 0.615 | 0.261 | 0.296 | 0.643 | 0.601 | 0.621 | 0.451 | 0.916 (380) | 0.535 (142) | 0.736 | 0.702 / 0.550 / 0.878 |
| D2 | speed_bump | 378 | 0.683 | 0.346 | 0.398 | 0.818 | 0.571 | 0.673 | 0.507 | 0.835 (454) | 0.146 (157) | 0.904 | 0.782 / 0.579 / 0.840 |

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
