# COCO evaluation (pycocotools) — road_hazards_v3a_r2 / val

Official COCOeval bbox, default parameters (IoU .50:.05:.95, maxDets 100). AP = mAP50-95, AP50 = mAP@0.5.
Area ranges (small < 32², medium 32²–96², large > 96² px) are in original pixels; our sources range from 640 px to 4K wide, so the size columns are not comparable across sources. Source: `report.json`.

| model | class | n_gt | AP | AP50 | AP75 | APs | APm | APl | AR100 | ARs | ARm | ARl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | all | 1069 | 0.317 | 0.671 | 0.248 | 0.176 | 0.306 | 0.324 | 0.500 | 0.345 | 0.485 | 0.532 |
| C | pothole | 691 | 0.275 | 0.639 | 0.190 | 0.176 | 0.311 | 0.282 | 0.496 | 0.345 | 0.508 | 0.554 |
| C | speed_bump | 378 | 0.359 | 0.703 | 0.307 | — | 0.301 | 0.365 | 0.504 | — | 0.461 | 0.509 |
| E3 | all | 1069 | 0.305 | 0.647 | 0.231 | 0.178 | 0.282 | 0.308 | 0.493 | 0.359 | 0.466 | 0.525 |
| E3 | pothole | 691 | 0.268 | 0.637 | 0.165 | 0.178 | 0.306 | 0.265 | 0.499 | 0.359 | 0.509 | 0.556 |
| E3 | speed_bump | 378 | 0.342 | 0.657 | 0.297 | — | 0.257 | 0.351 | 0.487 | — | 0.422 | 0.494 |
