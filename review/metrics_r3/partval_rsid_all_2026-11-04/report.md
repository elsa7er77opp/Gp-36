# Metrics report — parts_r3\rsid / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | pothole | 42 | 0.023 | 0.010 | 0.193 | 0.081 | 0.143 | 0.103 | 0.055 | 0.813 (217) | 0.333 (6) | 0.011 | 0.026 / 0.024 / 0.821 |
| v1 | speed_bump | 140 | 0.028 | 0.007 | 0.118 | 0.086 | 0.164 | 0.112 | 0.060 | 0.492 (116) | 0.193 (57) | 0.000 | 0.098 / 0.079 / 0.484 |
| runA_s0 | pothole | 42 | 0.047 | 0.022 | 0.323 | 0.125 | 0.167 | 0.143 | 0.077 | 0.837 (217) | 0.500 (6) | 0.027 | 0.106 / 0.119 / 0.841 |
| runA_s0 | speed_bump | 140 | 0.036 | 0.009 | 0.070 | 0.081 | 0.164 | 0.108 | 0.057 | 0.500 (116) | 0.228 (57) | 0.000 | 0.171 / 0.043 / 0.520 |
| D1_11n | pothole | 42 | 0.259 | 0.124 | 0.182 | 0.462 | 0.286 | 0.353 | 0.214 | 0.917 (217) | 0.333 (6) | 0.126 | 0.583 / 0.167 / 0.893 |
| D1_11n | speed_bump | 140 | 0.670 | 0.344 | 0.463 | 0.779 | 0.529 | 0.630 | 0.460 | 0.758 (116) | 0.544 (57) | 0.779 | 0.614 / 0.614 / 0.821 |
| D1_11s | pothole | 42 | 0.226 | 0.105 | 0.097 | 0.308 | 0.381 | 0.340 | 0.205 | 0.905 (217) | 0.667 (6) | 0.216 | 0.308 / 0.095 / 0.865 |
| D1_11s | speed_bump | 140 | 0.639 | 0.332 | 0.270 | 0.633 | 0.629 | 0.631 | 0.461 | 0.825 (116) | 0.684 (57) | 0.745 | 0.684 / 0.557 / 0.790 |
| bumponly | pothole | 42 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.861 (217) | 0.000 (6) | 0.000 | 0.000 / 0.000 / 0.861 |
| bumponly | speed_bump | 140 | 0.600 | 0.319 | 0.275 | 0.648 | 0.593 | 0.619 | 0.449 | 0.790 (116) | 0.649 (57) | 0.763 | 0.753 / 0.521 / 0.754 |
| potonly | pothole | 42 | 0.163 | 0.071 | 0.101 | 0.186 | 0.452 | 0.264 | 0.152 | 0.833 (217) | 0.333 (6) | 0.168 | 0.375 / 0.071 / 0.861 |
| potonly | speed_bump | 140 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.460 (116) | 0.000 (57) | 0.000 | 0.000 / 0.000 / 0.460 |

## v1: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.000 | 0.000 | 0.000 | 28 | 0.712 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.041 | 0.130 | 0.107 | 40 | 0.610 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.022 | 0.059 | 0.111 | 16 | 0.750 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.091 | 0.157 | 0.276 | 43 | 0.722 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.120 | 0.250 | 0.200 | 15 | 0.692 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.019 | 0.041 | 0.105 | 47 | 0.615 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 0.000 | 0.000 | 0.000 | 0 | 0.973 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.102 | 0.333 | 0.194 | 14 | 0.324 |
| meta=kind=neg_empty;family=DASHKR | pothole | 1 | 0 | — | 0.000 | 0.000 | 1 | 0.000 |
| meta=kind=neg_empty;family=DASHKR | speed_bump | 1 | 0 | — | 0.000 | 0.000 | 1 | 0.000 |
| meta=kind=neg_empty;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_empty;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 11 | 0.467 |
| meta=kind=neg_manhole;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 4 | 0.733 |
| meta=kind=neg_manhole;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 10 | 0.533 |
| meta=kind=neg_manhole;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_manhole;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 23 | 0.267 |
| meta=kind=neg_manhole;family=ZED | pothole | 10 | 0 | — | 0.000 | 0.000 | 2 | 0.900 |
| meta=kind=neg_manhole;family=ZED | speed_bump | 10 | 0 | — | 0.000 | 0.000 | 8 | 0.200 |
| meta=kind=neg_empty;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 34 | 0.267 |
| meta=kind=neg_empty;family=ZED | speed_bump | 8 | 0 | — | 0.000 | 0.000 | 12 | 0.000 |
| meta=kind=neg_manhole;family=DASHKR | speed_bump | 2 | 0 | — | 0.000 | 0.000 | 3 | 0.500 |

## runA_s0: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.014 | 0.000 | 0.000 | 15 | 0.831 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.054 | 0.200 | 0.125 | 28 | 0.492 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.064 | 0.133 | 0.222 | 13 | 0.750 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.083 | 0.159 | 0.241 | 37 | 0.750 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.143 | 0.250 | 0.200 | 15 | 0.615 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.054 | 0.051 | 0.211 | 75 | 0.487 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 0.026 | 0.000 | 0.000 | 0 | 0.973 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.124 | 0.172 | 0.139 | 24 | 0.378 |
| meta=kind=neg_empty;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_empty;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 23 | 0.333 |
| meta=kind=neg_manhole;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 4 | 0.733 |
| meta=kind=neg_manhole;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 16 | 0.667 |
| meta=kind=neg_manhole;family=ZED | pothole | 10 | 0 | — | 0.000 | 0.000 | 1 | 0.900 |
| meta=kind=neg_manhole;family=ZED | speed_bump | 10 | 0 | — | 0.000 | 0.000 | 8 | 0.400 |
| meta=kind=neg_empty;family=DASHKR | speed_bump | 1 | 0 | — | 0.000 | 0.000 | 1 | 0.000 |
| meta=kind=neg_empty;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 6 | 0.733 |
| meta=kind=neg_empty;family=ZED | speed_bump | 8 | 0 | — | 0.000 | 0.000 | 10 | 0.375 |
| meta=kind=neg_manhole;family=DASHKR | speed_bump | 2 | 0 | — | 0.000 | 0.000 | 2 | 0.500 |
| meta=kind=neg_manhole;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 32 | 0.200 |

## D1_11n: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.379 | 0.500 | 0.143 | 1 | 0.915 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.775 | 0.809 | 0.679 | 9 | 0.780 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.378 | 0.600 | 0.333 | 2 | 0.861 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.638 | 0.786 | 0.379 | 3 | 0.556 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.297 | 0.471 | 0.320 | 9 | 0.795 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.324 | 0.400 | 0.105 | 3 | 0.615 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 0.029 | 0.000 | 0.000 | 0 | 0.973 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.800 | 0.920 | 0.639 | 2 | 0.649 |
| meta=kind=neg_empty;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_manhole;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_manhole;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_empty;family=ZED | speed_bump | 8 | 0 | — | 0.000 | 0.000 | 2 | 0.750 |
| meta=kind=neg_manhole;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |

## D1_11s: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.195 | 0.125 | 0.143 | 7 | 0.864 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.746 | 0.704 | 0.679 | 16 | 0.780 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.351 | 0.375 | 0.333 | 5 | 0.861 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.658 | 0.594 | 0.655 | 13 | 0.778 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.316 | 0.414 | 0.480 | 17 | 0.897 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.215 | 0.385 | 0.263 | 8 | 0.667 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 0.333 | 0.000 | 0.000 | 2 | 0.946 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.771 | 0.714 | 0.694 | 10 | 0.784 |
| meta=kind=neg_empty;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |
| meta=kind=neg_empty;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.933 |
| meta=kind=neg_manhole;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_manhole;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |
| meta=kind=neg_manhole;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |

## bumponly: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.000 | 0.000 | 0.000 | 0 | 0.898 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.688 | 0.717 | 0.679 | 15 | 0.763 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.000 | 0.000 | 0.000 | 0 | 0.778 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.684 | 0.621 | 0.621 | 11 | 0.778 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.000 | 0.000 | 0.000 | 0 | 0.487 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.178 | 0.333 | 0.158 | 6 | 0.667 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 0.000 | 0.000 | 0.000 | 0 | 0.973 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.736 | 0.852 | 0.639 | 4 | 0.703 |
| meta=kind=neg_empty;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |
| meta=kind=neg_empty;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_empty;family=ZED | speed_bump | 8 | 0 | — | 0.000 | 0.000 | 1 | 0.875 |
| meta=kind=neg_manhole;family=DASHKR | speed_bump | 2 | 0 | — | 0.000 | 0.000 | 1 | 0.500 |
| meta=kind=neg_manhole;family=VLNdash | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 1 | 0.933 |
| meta=kind=neg_manhole;family=VLNphone | speed_bump | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.933 |
| meta=kind=neg_manhole;family=ZED | speed_bump | 10 | 0 | — | 0.000 | 0.000 | 1 | 0.900 |

## potonly: subsets (at the operating threshold)

| subset | class | n_img | n_gt | AP50 | P | R | FP | ImgAcc |
|---|---|---|---|---|---|---|---|---|
| meta=kind=hazard;family=DASHKR | pothole | 59 | 7 | 0.257 | 0.200 | 0.429 | 12 | 0.831 |
| meta=kind=hazard;family=DASHKR | speed_bump | 59 | 56 | 0.000 | 0.000 | 0.000 | 0 | 0.102 |
| meta=kind=hazard;family=VLNdash | pothole | 36 | 9 | 0.107 | 0.138 | 0.444 | 25 | 0.750 |
| meta=kind=hazard;family=VLNdash | speed_bump | 36 | 29 | 0.000 | 0.000 | 0.000 | 0 | 0.222 |
| meta=kind=hazard;family=VLNphone | pothole | 39 | 25 | 0.281 | 0.270 | 0.400 | 27 | 0.795 |
| meta=kind=hazard;family=VLNphone | speed_bump | 39 | 19 | 0.000 | 0.000 | 0.000 | 0 | 0.513 |
| meta=kind=hazard;family=ZED | pothole | 37 | 1 | 1.000 | 1.000 | 1.000 | 0 | 1.000 |
| meta=kind=hazard;family=ZED | speed_bump | 37 | 36 | 0.000 | 0.000 | 0.000 | 0 | 0.027 |
| meta=kind=neg_empty;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |
| meta=kind=neg_empty;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 2 | 0.867 |
| meta=kind=neg_manhole;family=VLNdash | pothole | 15 | 0 | — | 0.000 | 0.000 | 8 | 0.600 |
| meta=kind=neg_manhole;family=VLNphone | pothole | 15 | 0 | — | 0.000 | 0.000 | 4 | 0.800 |
| meta=kind=neg_manhole;family=ZED | pothole | 10 | 0 | — | 0.000 | 0.000 | 3 | 0.800 |
