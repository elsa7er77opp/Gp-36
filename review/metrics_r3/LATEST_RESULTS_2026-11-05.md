# GP36 — latest results (as of 5 Nov 2026, 16:00)

**Status:** v3b_C (`v3b_C_11n_960_s0_r2`) is training, 4/70 epochs done; its results are not in this file. The best finished models are **D1** (`v3b_A_11n_960_s0`) and **D2** (`v3b_B_11n_960_s0`). Every number below is copied from the file named with it; nothing is computed here.

Models:
- **v1:** the deployed baseline (`v3a_r1_11n_960_s0`).
- **Run A:** first r2 model (`v3a_r2_11n_960_s0`).
- **D1:** r2 + RSID + Bučko + rdd_ji:500; YOLO11n, 960 px, 70 epochs. D1_11s is the same data with YOLO11s.
- **D2:** D1 + sr (Malaysia/Indonesia, minus rad).

Metric definitions (STATUS Stage 7.2):
- Threshold = argmax F1 on val; IoU 0.5.
- **BoxAcc** = TP / (TP + FP + FN).
- **ImgAcc** = share of images where the class is correctly present or absent.
- **NearR** = recall on near boxes (y2 ≥ 0.6·H and sqrt(area) ≥ 0.05).
- **P@R50** = precision at 50 % recall.
- The "@0.35" column uses deploy confidence 0.35.

---

## 1. Main benchmark: r2 val (830 images; 691 pothole, 378 bump boxes)
Source: `review/metrics_r3/val_r2_all_2026-11-04/report.md` and `val_r2_D2/report.md`.

### Pothole
| model | AP50 | AP50-95 | P | R | F1 | BoxAcc | ImgAcc | NearR | P@R50 | P / R / ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 | **0.628** | 0.261 | 0.664 | 0.616 | 0.639 | 0.470 | 0.914 | 0.577 | 0.771 | 0.693 / 0.588 / 0.902 |
| Run A | 0.605 | 0.255 | 0.617 | 0.603 | 0.610 | 0.439 | 0.900 | 0.563 | 0.730 | 0.703 / 0.527 / 0.866 |
| D1 (11n) | 0.596 | 0.251 | 0.625 | 0.579 | 0.601 | 0.430 | 0.898 | 0.542 | 0.719 | 0.693 / 0.517 / 0.857 |
| D1 (11s) | 0.625 | 0.266 | 0.643 | 0.624 | 0.633 | 0.463 | 0.912 | 0.577 | 0.758 | 0.688 / 0.563 / 0.894 |
| **D2** | 0.615 | 0.261 | 0.643 | 0.601 | 0.621 | 0.451 | **0.916** | 0.535 | 0.736 | 0.702 / 0.550 / 0.878 |

### Speed bump
| model | AP50 | AP50-95 | P | R | F1 | BoxAcc | ImgAcc | NearR | P@R50 | P / R / ImgAcc @0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 0.710 | 0.349 | 0.712 | 0.653 | 0.681 | 0.517 | **0.880** | 0.363 | 0.836 | 0.754 / 0.601 / 0.855 |
| Run A | **0.725** | 0.359 | 0.864 | 0.571 | 0.688 | 0.524 | 0.823 | 0.191 | **0.950** | 0.897 / 0.556 / 0.811 |
| D1 (11n) | 0.710 | 0.330 | 0.727 | 0.619 | 0.669 | 0.502 | 0.871 | 0.280 | 0.863 | 0.735 / 0.595 / 0.861 |
| D1 (11s) | 0.692 | 0.339 | 0.753 | 0.622 | 0.681 | 0.516 | 0.854 | 0.261 | 0.892 | 0.814 / 0.566 / 0.835 |
| **D2** | 0.683 | 0.346 | 0.818 | 0.571 | 0.673 | 0.507 | 0.835 | 0.146 | 0.904 | 0.782 / 0.579 / 0.840 |

**Reading:**
- On r2 val, every model sits at about 0.60–0.63 pothole and 0.68–0.73 bump. No newer model clearly beats v1 here.
- D1 seed spread is about ±0.01–0.02 (Stage 22), so differences under 0.02 are noise.

---

## 2. New, unseen sources (part-vals; val only)
These measure generalization to roads the old model never saw. This is where the gains are.

### Pothole
| eval set (n boxes) | v1 | Run A | D1 11n | D1 11s | D2 | file |
|---|---|---|---|---|---|---|
| Bučko, Slovakia (186) AP50 | 0.399 | 0.422 | 0.571 | 0.606 | **0.617** | `partval_bucko_all_2026-11-04`, `partval_bucko_D2` |
| Bučko ImgAcc | 0.696 | 0.720 | 0.848 | 0.824 | 0.848 | same |
| RSID (42) AP50 | 0.023 | 0.047 | 0.259 | 0.226 | **0.307** | `partval_rsid_all_2026-11-04`, `partval_rsid_D2` |
| sr, Malaysia/Indonesia (108) AP50 | — | 0.350 | 0.396 | — | **0.433** | `partval_sr_D2` |
| egy_v2, Egypt (30) mAP50\* | — | — | 0.021 | — | 0.029 | `runs/PARTVAL_egy_v2_{D1s0,D2}.txt` |

### Speed bump
| eval set (n boxes) | v1 | Run A | D1 11n | D1 11s | D2 | file |
|---|---|---|---|---|---|---|
| RSID (140) AP50 | 0.028 | 0.036 | **0.670** | 0.639 | 0.630 | `partval_rsid_*` |
| RSID ImgAcc | 0.492 | 0.500 | 0.758 | 0.825 | **0.845** | same |
| pol_v2, Indonesia unmarked (100) mAP50\* | — | — | 0.250 | — | **0.540** | `runs/PARTVAL_pol_v2_{D1s0,D2}.txt` |
| red_v2, Latin America (68) mAP50\* | — | — | **0.172** | — | 0.154 | `runs/PARTVAL_red_v2_*.txt` |
| ng8_v2, India (20) mAP50\* | — | — | **0.662** | — | 0.614 | `runs/PARTVAL_ng8_v2_*.txt` |

\* Plain Ultralytics `yolo val` output. These are the baselines for v3b_C. The full metrics_report tables (BoxAcc, ImgAcc, …) for these four sets are written when v3b_C finishes.

**Reading:**
- From v1 to D1/D2, RSID bump went from 0.028 to 0.63–0.67, and Bučko pothole from 0.399 to 0.617. The new training data clearly made the model work on new countries.
- Egyptian potholes (egy_v2) and Latin-American bumps (red_v2) are still very weak. These are exactly the sources that v3b_C adds to training.

---

## 3. Test results (each used once; ledger `review/metrics_r3/TEST_LEDGER.csv`)
Only Run A has been tested so far. No D1, D2 or v3b_C model has touched the test split.

| test set | model | class | P | R | mAP50 | mAP50-95 | file |
|---|---|---|---|---|---|---|---|
| r2 test (323 img, 445 boxes) | Run A | all | 0.505 | 0.453 | 0.462 | 0.189 | `runs/v3a_r2_11n_960_s0_TEST.txt` |
| | | pothole | 0.549 | 0.681 | **0.631** | 0.269 | |
| | | speed_bump | 0.461 | 0.225 | **0.294** | 0.108 | |
| BD87 external (88 bumps) | Run A | speed_bump | 0.531 | 0.318 | 0.367 | 0.127 | `runs/EXT_bd87_v3a_r2_11n_960_s0_b.txt` |
| BD87 external | v1 | speed_bump | 0.406 | 0.397 | 0.328 | 0.117 | `runs/EXT_bd87_v3a_r1_11n_960_s0_b.txt` |

**Reading:** the bump val→test gap was large (0.72 → 0.29). Unseen scenes, especially unmarked Egyptian humps, are the main failure. D1/D2 were built to fix this, and the unseen-source part-vals above suggest they do. That will be confirmed by one test use per final model.

---

## 4. Where we stand vs the 0.90 target
- **About 0.90 already reached:** pothole ImgAcc 0.916 (D2, r2 val); bump P@R50 0.904 (D2) and 0.950 (Run A).
- **Not reached:** per-class mAP50 is about 0.60–0.63 (pothole) and 0.68–0.73 (bump) on r2 val. It is lower on unseen sources and on test.
- **Why:** the model learns the training set well, but val plateaus around epoch 50. The limit is data diversity (unmarked Egyptian bumps, far tiny potholes) and label noise, not training length or a layer problem (`review/clean_r2/SESSION_REPORT_2026-11-05.md` §5).

## 5. Next
1. **v3b_C:** about 10,562 train images; bump boxes doubled to 3,982. Training; results expected tonight. It is judged against D1 on H-C1, H-C3 and H-C4 (STATUS Stages 24–27).
2. **Levers on the best model**, each as its own row: near-range metric, TTA, WBF, sliced inference, P2 head, 1280 px, and a long run (`CLOUD_REPORT.md` §0-S5).
3. **Final candidates:** picked on val only, then one test use each (r2 test and BD87), logged in the ledger.
