# r2 TEST (frozen, used once per model) - val-chosen thresholds

Split: **test**. All numbers copied from the `report.json` named in each row (`tools/metrics_report.py`); this file computes nothing. IoU 0.5. Definitions: `supervisor_2026-11-08/METRICS.md` §1.

## pothole — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.251 | 0.612 | 0.726 | 0.665 | 0.711 | 0.337 | 0.498 | 0.938 | 0.807 | 0.838 | 0.814 | 285 | 323 (152) | 119 | `review/metrics_r3/test_r2_final/report.json` |
| WBF(C, v1) | 0.148 | 0.671 | 0.688 | 0.679 | 0.698 | 0.324 | 0.514 | 0.938 | 0.773 | 0.837 | 0.801 | 285 | 323 (152) | 119 | `review/metrics_r3/test_r2_final/report.json` |

## pothole — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.727 | 0.674 | 0.699 | 0.538 | 0.904 | 0.773 | 0.760 / 0.773 | `review/metrics_r3/test_r2_final/report.json` |
| WBF(C, v1) | 0.860 | 0.344 | 0.491 | 0.326 | 0.706 | 0.471 | 0.889 / 0.471 | `review/metrics_r3/test_r2_final/report.json` |

## speed_bump — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.192 | 0.508 | 0.200 | 0.287 | 0.320 | 0.118 | 0.168 | 0.663 | 0.250 | 0.269 | 0.389 | 160 | 323 (171) | 104 | `review/metrics_r3/test_r2_final/report.json` |
| WBF(C, v1) | 0.090 | 0.565 | 0.381 | 0.455 | 0.463 | 0.157 | 0.295 | 0.780 | 0.394 | 0.480 | 0.482 | 160 | 323 (171) | 104 | `review/metrics_r3/test_r2_final/report.json` |

## speed_bump — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.767 | 0.144 | 0.242 | 0.138 | 0.607 | 0.192 | 0.769 / 0.192 | `review/metrics_r3/test_r2_final/report.json` |
| WBF(C, v1) | 1.000 | 0.056 | 0.107 | 0.056 | 0.557 | 0.087 | 1.000 / 0.087 | `review/metrics_r3/test_r2_final/report.json` |

Thresholds per report: `review/metrics_r3/test_r2_final/report.json`: review\metrics_r3\val_r2_final\report.json
