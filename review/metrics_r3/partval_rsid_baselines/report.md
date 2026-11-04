# Metrics report — parts_r3\rsid / val

Definitions: STATUS_for_claude.md Stage 7.2. Thresholds: argmax F1 on this split (val). IoU 0.5. Source: `report.json`.

| model | class | n_gt | AP50 | AP50-95 | thr | P | R | F1 | BoxAcc | ImgAcc (n_neg) | NearR (n) | P@R50 | P/R/ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | pothole | 42 | 0.023 | 0.010 | 0.193 | 0.081 | 0.143 | 0.103 | 0.055 | 0.813 (217) | 0.333 (6) | 0.011 | 0.026 / 0.024 / 0.821 |
| v1 | speed_bump | 140 | 0.028 | 0.007 | 0.118 | 0.086 | 0.164 | 0.112 | 0.060 | 0.492 (116) | 0.193 (57) | 0.000 | 0.098 / 0.079 / 0.484 |
| runA_s0 | pothole | 42 | 0.047 | 0.022 | 0.323 | 0.125 | 0.167 | 0.143 | 0.077 | 0.837 (217) | 0.500 (6) | 0.027 | 0.106 / 0.119 / 0.841 |
| runA_s0 | speed_bump | 140 | 0.036 | 0.009 | 0.070 | 0.081 | 0.164 | 0.108 | 0.057 | 0.500 (116) | 0.228 (57) | 0.000 | 0.171 / 0.043 / 0.520 |

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
