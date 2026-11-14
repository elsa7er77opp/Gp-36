# External BD87 TEST (87 images, speed bumps only; used once per model) - val-chosen thresholds

Split: **test**. All numbers copied from the `report.json` named in each row (`tools/metrics_report.py`); this file computes nothing. IoU 0.5. Definitions: `supervisor_2026-11-08/METRICS.md` §1.

## pothole — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.251 | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.920 | — | 0.000 | — | 0 | 87 (87) | 0 | `review/metrics_r3/test_bd87_final/report.json` |
| WBF(C, v1) | 0.148 | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.977 | — | 0.000 | — | 0 | 87 (87) | 0 | `review/metrics_r3/test_bd87_final/report.json` |

## pothole — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.000 | 0.000 | 0.000 | 0.000 | 0.966 | — | 0.000 / 0.000 | `review/metrics_r3/test_bd87_final/report.json` |
| WBF(C, v1) | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | — | 0.000 / 0.000 | `review/metrics_r3/test_bd87_final/report.json` |

## speed_bump — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.192 | 0.732 | 0.682 | 0.706 | 0.731 | 0.353 | 0.545 | 0.747 | 0.500 | 0.936 | 0.629 | 88 | 87 (0) | 2 | `review/metrics_r3/test_bd87_final/report.json` |
| WBF(C, v1) | 0.090 | 0.775 | 0.625 | 0.692 | 0.731 | 0.326 | 0.529 | 0.724 | 0.500 | 0.898 | 0.670 | 88 | 87 (0) | 2 | `review/metrics_r3/test_bd87_final/report.json` |

## speed_bump — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| C (v3b_C, YOLO11n) | 0.857 | 0.614 | 0.715 | 0.557 | 0.667 | 0.500 | 0.500 / 0.500 | `review/metrics_r3/test_bd87_final/report.json` |
| WBF(C, v1) | 1.000 | 0.205 | 0.340 | 0.205 | 0.207 | 0.000 | 0.000 / 0.000 | `review/metrics_r3/test_bd87_final/report.json` |

Thresholds per report: `review/metrics_r3/test_bd87_final/report.json`: review\metrics_r3\val_r2_final\report.json
