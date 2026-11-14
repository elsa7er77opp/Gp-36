# ALLVAL results (Stage 41a) — CPU ONNX re-implementation of `yolo val`, 13 Nov 2026

Method: `onnx_eval/onnx_val.py` (Ultralytics 8.4.192 val logic: imgsz 960, batch 8 rect, pad 0.5, conf 0.001, iou 0.7,
multi-label NMS, greedy matching, 101-point AP). Models exported to ONNX (opset 17, dynamic); ONNX vs PyTorch max output
difference 0.0006 px on a synthetic input. Predictions: `onnx_eval/pred_C_val`, `onnx_eval/pred_A1_val`.

Check against the official Ultralytics files in `runs/` (C, AP50, pothole / bump):
r2 0.642/0.705 vs 0.640/0.705 (VALr2_json); rsid 0.187/0.683 vs 0.185/0.681; bucko 0.636 vs 0.637; sr 0.392/0.000 vs 0.393/0.000;
pol_v2 0.945 vs 0.945; red_v2 0.989 vs 0.989; ng8_v2 0.924 vs 0.924; egy_v2 0.335 vs 0.332. All within 0.003.

## ALLVAL (1,754 images: 1,057 pothole / 741 speed_bump boxes)
| Model | pothole AP50 | bump AP50 | mean AP50 | mean AP50-95 |
|---|---|---|---|---|
| C  (v3b_C_11n_960_s0_r2) | 0.587 | 0.724 | 0.656 | 0.337 |
| A1 (v5_all_11n_960_s0)   | 0.577 | 0.679 | 0.628 | 0.316 |
| A1 - C | -0.010 | -0.045 | -0.028 | -0.022 |

## Per source, AP50 (pothole / bump / mean)
| source | images | C | A1 |
|---|---|---|---|
| r2 (rf8+ghpot) | 830 | 0.642 / 0.705 / 0.674 | 0.639 / 0.651 / 0.645 |
| rsid (Lithuania) | 252 | 0.187 / 0.683 / 0.435 | 0.261 / 0.635 / 0.448 |
| bucko (Slovakia) | 125 | 0.636 / - | 0.572 / - |
| sr | 164 | 0.392 / 0.000 / 0.196 | 0.402 / 0.000 / 0.201 |
| pol_v2 | 100 | - / 0.945 | - / 0.895 |
| red_v2 | 69 | - / 0.989 | - / 0.985 |
| ng8_v2 | 67 | - / 0.924 | - / 0.872 |
| egy_v2 | 147 | 0.335 / - | 0.378 / - |

Note: sr speed_bump (35 val boxes) is 0.000 for both models and also in the official file: to be looked at by eye
(possible label/definition mismatch). Val labels are not changed.
