# r2 validation (frozen benchmark)

Split: **val**. All numbers copied from the `report.json` named in each row (`tools/metrics_report.py`); this file computes nothing. IoU 0.5. Definitions: `supervisor_2026-11-08/METRICS.md` §1.

## pothole — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (r1 data) | 0.315 | 0.664 | 0.616 | 0.639 | 0.628 | 0.261 | 0.470 | 0.914 | 0.577 | 0.771 | — | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| Run A s0 | 0.272 | 0.617 | 0.603 | 0.610 | 0.605 | 0.255 | 0.439 | 0.900 | 0.563 | 0.730 | — | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11n (v3b_A) | 0.279 | 0.625 | 0.579 | 0.601 | 0.596 | 0.251 | 0.430 | 0.898 | 0.542 | 0.719 | — | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11s (v3b_A) | 0.289 | 0.643 | 0.624 | 0.633 | 0.625 | 0.266 | 0.463 | 0.912 | 0.577 | 0.758 | — | 691 | 830 (380) | 142 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |

## pothole — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| v1 (r1 data) | 0.693 | 0.588 | 0.636 | 0.466 | 0.902 | 0.556 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| Run A s0 | 0.703 | 0.527 | 0.602 | 0.431 | 0.866 | 0.472 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11n (v3b_A) | 0.693 | 0.517 | 0.592 | 0.420 | 0.857 | 0.500 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11s (v3b_A) | 0.688 | 0.563 | 0.619 | 0.449 | 0.894 | 0.528 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |

## speed_bump — at the operating threshold (argmax F1 on val; on test the val threshold is reused)

| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (r1 data) | 0.286 | 0.712 | 0.653 | 0.681 | 0.710 | 0.349 | 0.517 | 0.880 | 0.363 | 0.836 | — | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| Run A s0 | 0.328 | 0.864 | 0.571 | 0.688 | 0.725 | 0.359 | 0.524 | 0.823 | 0.191 | 0.950 | — | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11n (v3b_A) | 0.327 | 0.727 | 0.619 | 0.669 | 0.710 | 0.330 | 0.502 | 0.871 | 0.280 | 0.863 | — | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11s (v3b_A) | 0.244 | 0.753 | 0.622 | 0.681 | 0.692 | 0.339 | 0.516 | 0.854 | 0.261 | 0.892 | — | 378 | 830 (454) | 157 | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |

## speed_bump — at the deployed conf 0.35

| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |
|---|---|---|---|---|---|---|---|---|
| v1 (r1 data) | 0.754 | 0.601 | 0.669 | 0.502 | 0.855 | 0.261 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| Run A s0 | 0.897 | 0.556 | 0.686 | 0.522 | 0.811 | 0.166 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11n (v3b_A) | 0.735 | 0.595 | 0.658 | 0.490 | 0.861 | 0.242 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |
| D1 11s (v3b_A) | 0.814 | 0.566 | 0.668 | 0.501 | 0.835 | 0.172 | — | `review/metrics_r3/val_r2_all_2026-11-04/report.json` |

Thresholds per report: `review/metrics_r3/val_r2_all_2026-11-04/report.json`: argmax F1 on this split (val)
