# COCO evaluation (pycocotools) — road_hazards_v3a_r2 / test

Official COCOeval bbox, default parameters (IoU .50:.05:.95, maxDets 100). AP = mAP50-95, AP50 = mAP@0.5.
Area ranges (small < 32², medium 32²–96², large > 96² px) are in original pixels; our sources range from 640 px to 4K wide, so the size columns are not comparable across sources. Source: `report.json`.

| model | class | n_gt | AP | AP50 | AP75 | APs | APm | APl | AR100 | ARs | ARm | ARl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | all | 445 | 0.227 | 0.515 | 0.151 | 0.185 | 0.205 | 0.260 | 0.452 | 0.332 | 0.468 | 0.466 |
| C | pothole | 285 | 0.337 | 0.710 | 0.273 | 0.185 | 0.262 | 0.403 | 0.536 | 0.332 | 0.548 | 0.565 |
| C | speed_bump | 160 | 0.118 | 0.320 | 0.028 | — | 0.148 | 0.118 | 0.367 | — | 0.388 | 0.366 |
| WBF_C_v1 | all | 445 | 0.240 | 0.580 | 0.151 | 0.124 | 0.251 | 0.267 | 0.437 | 0.321 | 0.505 | 0.444 |
| WBF_C_v1 | pothole | 285 | 0.323 | 0.697 | 0.243 | 0.124 | 0.292 | 0.375 | 0.503 | 0.321 | 0.523 | 0.523 |
| WBF_C_v1 | speed_bump | 160 | 0.157 | 0.463 | 0.059 | — | 0.209 | 0.158 | 0.371 | — | 0.487 | 0.365 |
