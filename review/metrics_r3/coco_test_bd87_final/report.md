# COCO evaluation (pycocotools) — bd87_eval_view / test

Official COCOeval bbox, default parameters (IoU .50:.05:.95, maxDets 100). AP = mAP50-95, AP50 = mAP@0.5.
Area ranges (small < 32², medium 32²–96², large > 96² px) are in original pixels; our sources range from 640 px to 4K wide, so the size columns are not comparable across sources. Source: `report.json`.

| model | class | n_gt | AP | AP50 | AP75 | APs | APm | APl | AR100 | ARs | ARm | ARl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | all | 88 | 0.353 | 0.731 | 0.332 | — | 0.206 | 0.418 | 0.465 | — | 0.300 | 0.530 |
| C | pothole | 0 | — | — | — | — | — | — | — | — | — | — |
| C | speed_bump | 88 | 0.353 | 0.731 | 0.332 | — | 0.206 | 0.418 | 0.465 | — | 0.300 | 0.530 |
| WBF_C_v1 | all | 88 | 0.326 | 0.731 | 0.200 | — | 0.162 | 0.388 | 0.452 | — | 0.320 | 0.505 |
| WBF_C_v1 | pothole | 0 | — | — | — | — | — | — | — | — | — | — |
| WBF_C_v1 | speed_bump | 88 | 0.326 | 0.731 | 0.200 | — | 0.162 | 0.388 | 0.452 | — | 0.320 | 0.505 |
