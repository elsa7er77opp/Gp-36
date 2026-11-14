# COCO evaluation (pycocotools) — road_hazards_v3a_r2 / val

Official COCOeval bbox, default parameters (IoU .50:.05:.95, maxDets 100). AP = mAP50-95, AP50 = mAP@0.5.
Area ranges (small < 32², medium 32²–96², large > 96² px) are in original pixels; our sources range from 640 px to 4K wide, so the size columns are not comparable across sources. Source: `report.json`.

| model | class | n_gt | AP | AP50 | AP75 | APs | APm | APl | AR100 | ARs | ARm | ARl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | all | 1069 | 0.317 | 0.671 | 0.248 | 0.176 | 0.306 | 0.324 | 0.500 | 0.345 | 0.485 | 0.532 |
| C | pothole | 691 | 0.275 | 0.639 | 0.190 | 0.176 | 0.311 | 0.282 | 0.496 | 0.345 | 0.508 | 0.554 |
| C | speed_bump | 378 | 0.359 | 0.703 | 0.307 | — | 0.301 | 0.365 | 0.504 | — | 0.461 | 0.509 |
| E1 | all | 1069 | 0.308 | 0.668 | 0.237 | 0.168 | 0.269 | 0.320 | 0.514 | 0.389 | 0.494 | 0.545 |
| E1 | pothole | 691 | 0.260 | 0.603 | 0.180 | 0.168 | 0.289 | 0.268 | 0.508 | 0.389 | 0.512 | 0.564 |
| E1 | speed_bump | 378 | 0.357 | 0.733 | 0.294 | — | 0.248 | 0.372 | 0.521 | — | 0.475 | 0.526 |
| E2 | all | 1069 | 0.296 | 0.647 | 0.227 | 0.195 | 0.269 | 0.300 | 0.513 | 0.418 | 0.475 | 0.533 |
| E2 | pothole | 691 | 0.267 | 0.619 | 0.177 | 0.195 | 0.301 | 0.264 | 0.528 | 0.418 | 0.545 | 0.558 |
| E2 | speed_bump | 378 | 0.325 | 0.675 | 0.276 | — | 0.237 | 0.336 | 0.498 | — | 0.406 | 0.507 |
