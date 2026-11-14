# r2 validation (frozen benchmark) - final round, 2026-11-06

Split: **val**. All numbers copied from the `report.json` named in each row (`tools/metrics_report.py`); this file computes nothing. IoU 0.5. Definitions: `supervisor_2026-11-08/METRICS.md` §1.

## pothole — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (deployed baseline, r1 data) | 0.315 | 0.664 | 0.616 | 0.639 | 0.628 | 0.261 | 0.470 | 0.914 | 0.577 | 0.771 | 0.653 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_final/report.json` |
| C (v3b_C, YOLO11n) - final candidate 1 | 0.251 | 0.654 | 0.628 | 0.641 | 0.639 | 0.275 | 0.471 | 0.919 | 0.641 | 0.792 | 0.683 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_final/report.json` |
| E1 (C data, AdamW) | 0.300 | 0.669 | 0.577 | 0.620 | 0.603 | 0.260 | 0.449 | 0.900 | 0.570 | 0.749 | 0.634 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_E2/report.json` |
| E2 (C data, P2 head) | 0.268 | 0.681 | 0.566 | 0.618 | 0.618 | 0.267 | 0.447 | 0.893 | 0.585 | 0.749 | 0.630 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_E2/report.json` |
| WBF(C, D1 11s) - lever test | 0.116 | 0.659 | 0.679 | 0.669 | 0.667 | 0.272 | 0.502 | 0.922 | 0.592 | 0.802 | 0.658 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_final/report.json` |
| WBF(C, v1) - final candidate 2 | 0.148 | 0.728 | 0.634 | 0.677 | 0.676 | 0.278 | 0.512 | 0.906 | 0.577 | 0.808 | 0.694 | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_final/report.json` |

## pothole — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| v1 (deployed baseline, r1 data) | 0.693 | 0.588 | 0.636 | 0.466 | 0.902 | 0.556 | 0.718 / 0.556 | `review/metrics_r3/val_r2_final/report.json` |
| C (v3b_C, YOLO11n) - final candidate 1 | 0.749 | 0.541 | 0.629 | 0.458 | 0.871 | 0.556 | 0.814 / 0.556 | `review/metrics_r3/val_r2_final/report.json` |
| E1 (C data, AdamW) | 0.716 | 0.525 | 0.606 | 0.435 | 0.865 | 0.528 | 0.694 / 0.528 | `review/metrics_r3/val_r2_E2/report.json` |
| E2 (C data, P2 head) | 0.781 | 0.453 | 0.573 | 0.402 | 0.816 | 0.486 | 0.734 / 0.486 | `review/metrics_r3/val_r2_E2/report.json` |
| WBF(C, D1 11s) - lever test | 0.891 | 0.165 | 0.278 | 0.162 | 0.598 | 0.183 | 0.929 / 0.183 | `review/metrics_r3/val_r2_final/report.json` |
| WBF(C, v1) - final candidate 2 | 0.884 | 0.198 | 0.324 | 0.193 | 0.624 | 0.289 | 0.911 / 0.289 | `review/metrics_r3/val_r2_final/report.json` |

## speed_bump — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (deployed baseline, r1 data) | 0.286 | 0.712 | 0.653 | 0.681 | 0.710 | 0.349 | 0.517 | 0.880 | 0.363 | 0.836 | 0.310 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_final/report.json` |
| C (v3b_C, YOLO11n) - final candidate 1 | 0.192 | 0.770 | 0.648 | 0.704 | 0.703 | 0.359 | 0.543 | 0.866 | 0.306 | 0.900 | 0.339 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_final/report.json` |
| E1 (C data, AdamW) | 0.253 | 0.821 | 0.630 | 0.713 | 0.733 | 0.357 | 0.553 | 0.854 | 0.261 | 0.950 | 0.399 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_E2/report.json` |
| E2 (C data, P2 head) | 0.427 | 0.944 | 0.532 | 0.680 | 0.675 | 0.325 | 0.515 | 0.800 | 0.057 | 0.960 | 0.220 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_E2/report.json` |
| WBF(C, D1 11s) - lever test | 0.069 | 0.742 | 0.698 | 0.719 | 0.738 | 0.367 | 0.562 | 0.895 | 0.420 | 0.915 | 0.404 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_final/report.json` |
| WBF(C, v1) - final candidate 2 | 0.090 | 0.753 | 0.709 | 0.730 | 0.752 | 0.385 | 0.575 | 0.907 | 0.433 | 0.896 | 0.402 | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_final/report.json` |

## speed_bump — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| v1 (deployed baseline, r1 data) | 0.754 | 0.601 | 0.669 | 0.502 | 0.855 | 0.261 | 0.446 / 0.261 | `review/metrics_r3/val_r2_final/report.json` |
| C (v3b_C, YOLO11n) - final candidate 1 | 0.869 | 0.542 | 0.668 | 0.501 | 0.819 | 0.121 | 0.528 / 0.121 | `review/metrics_r3/val_r2_final/report.json` |
| E1 (C data, AdamW) | 0.872 | 0.577 | 0.694 | 0.532 | 0.823 | 0.166 | 0.619 / 0.166 | `review/metrics_r3/val_r2_E2/report.json` |
| E2 (C data, P2 head) | 0.877 | 0.545 | 0.672 | 0.506 | 0.814 | 0.076 | 0.414 / 0.076 | `review/metrics_r3/val_r2_E2/report.json` |
| WBF(C, D1 11s) - lever test | 0.972 | 0.362 | 0.528 | 0.359 | 0.717 | 0.038 | 0.667 / 0.038 | `review/metrics_r3/val_r2_final/report.json` |
| WBF(C, v1) - final candidate 2 | 0.940 | 0.370 | 0.531 | 0.362 | 0.727 | 0.038 | 0.545 / 0.038 | `review/metrics_r3/val_r2_final/report.json` |

Thresholds per report: `review/metrics_r3/val_r2_E2/report.json`: argmax F1 on this split (val); `review/metrics_r3/val_r2_final/report.json`: argmax F1 on this split (val)
