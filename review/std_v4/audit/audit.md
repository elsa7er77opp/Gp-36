# Pattern audit of road_hazards_v3b_C (target 960x720; nothing was written to the dataset)

Rules that would remove a TRAIN image: ['portrait', 'extreme_aspect', 'closeup', 'high_box', 'lowres']. Thresholds: min-keep 0.5, max-box-area 0.35, min-cy 0.3.

| source | split | images | most common size | letterboxed | portrait | extreme_aspect | closeup | high_box | lowres | flagged (any rule) |
|---|---|---|---|---|---|---|---|---|---|---|
| bpo | train | 442 | 640x640 (442) | 3 | 0 | 0 | 1 | 59 | 0 | 59 |
| bucko | train | 282 | 1920x1080 (282) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dmd | train | 277 | 640x426 (100) | 28 | 98 | 14 | 22 | 7 | 82 | 100 |
| egy | train | 1118 | 1920x1440 (388) | 62 | 267 | 53 | 8 | 68 | 0 | 299 |
| ens | train | 414 | 640x640 (414) | 14 | 0 | 0 | 85 | 354 | 0 | 411 |
| ghpot | test | 46 | 1920x1440 (6) | 4 | 2 | 0 | 14 | 1 | 4 | 17 |
| ghpot | train | 85 | 1920x1440 (6) | 24 | 7 | 1 | 7 | 29 | 6 | 43 |
| ghpot | val | 49 | 1920x1440 (6) | 15 | 5 | 2 | 17 | 4 | 6 | 27 |
| hmpt | train | 431 | 640x640 (386) | 25 | 13 | 0 | 55 | 15 | 0 | 74 |
| ng8 | train | 278 | 1080x1920 (179) | 278 | 278 | 278 | 0 | 72 | 0 | 278 |
| pol | train | 375 | 1920x1080 (375) | 57 | 0 | 0 | 0 | 62 | 0 | 62 |
| rdd_ji | train | 500 | 720x720 (246) | 1 | 0 | 0 | 1 | 26 | 0 | 27 |
| red | train | 334 | 3840x2160 (334) | 280 | 0 | 0 | 126 | 129 | 0 | 252 |
| rf8 | test | 277 | 1920x1440 (1273) | 59 | 9 | 0 | 3 | 17 | 4 | 28 |
| rf8 | train | 1258 | 1920x1440 (1273) | 158 | 107 | 87 | 22 | 111 | 7 | 230 |
| rf8 | val | 781 | 1920x1440 (1273) | 182 | 158 | 87 | 12 | 66 | 0 | 201 |
| rsid | train | 773 | 1920x1080 (390) | 125 | 0 | 0 | 3 | 94 | 0 | 97 |
| sb15 | train | 1692 | 640x640 (1692) | 11 | 0 | 0 | 0 | 0 | 0 | 0 |
| sr | train | 2303 | 640x360 (1824) | 482 | 479 | 478 | 0 | 7 | 0 | 483 |

| split | images | flagged | unflagged |
|---|---|---|---|
| train | 10562 | 2415 | 8147 |
| val | 830 | 228 | 602 |
| test | 323 | 45 | 278 |

Different image sizes in the source: 321.
Flagged train images would be left out by `build`; flagged val/test images stay and are only left out of the *_stdframe lists.
