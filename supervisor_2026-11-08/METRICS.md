# GP36 — metric definitions and current values (DRAFT, 8 Nov 2026)

These definitions were fixed on 2026-11-02, before the new metrics were measured
(`review/clean_r2/STATUS_for_claude.md` Stage 7.2). The same tool scores every model:
`tools/metrics_report.py`. Its tests are in `tests/test_metrics_report.py`. Its AP50 matches Ultralytics to
within 0.002 (STATUS Stage 8.1).

## 1. Definitions (per class: pothole, speed_bump; never only the average)
| metric | definition |
|---|---|
| AP50, AP50-95 | COCO-style 101-point interpolated average precision, IoU 0.5 (and 0.5:0.95) |
| operating threshold | per model and class, the confidence that maximises F1 on **val**. The same value is then used on test (`--thresholds`). The deployed value conf 0.35 (`perception/config.yaml` `fsm.hazard_min_conf`) is reported as a second row |
| P, R, F1 | at the operating threshold, IoU ≥ 0.5, greedy matching by score |
| BoxAcc | TP / (TP + FP + FN) |
| ImgAcc (A2) | share of images where "class present" equals "class predicted"; meaningful only on sets with hazard-free frames |
| NearR (A1) | recall over GT boxes with bottom edge y2 ≥ 0.60·H and sqrt(area fraction) ≥ 0.05 (the near road that the FSM acts on) |
| P@R50 (A3) | interpolated precision at recall 0.50 |

**The 0.90 counts** only for per-class mAP50 or A1–A3, on a leak-free, sequence-aware evaluation set. It does not
count if it came from tuning on test, from dropping hard images, or from a random frame split.

Threshold selection for deployment (new, `tools/calibrate_thresholds.py`): from val predictions only. Per class it
chooses one of three: max F1; the highest confidence that still reaches a target recall; or the lowest confidence
that keeps a target precision. It can also report bootstrap 5/50/95 % ranges. The output is a proposal. The live
config is changed only by the owner.

## 2. Current values — validation only (VERIFIED, files named)
r2 val: 830 images, 691 pothole / 378 bump boxes. Only 10 images are hazard-free, so ImgAcc on r2 is mostly
"the other class" (caveat in STATUS 8.1).

| model | class | AP50 | P | R | BoxAcc | NearR (n) | P@R50 | file |
|---|---|---|---|---|---|---|---|---|
| Run A s0 | pothole | 0.605 | 0.617 | 0.603 | 0.439 | 0.563 (142) | 0.730 | `review/metrics_r3/val_r2_all_2026-11-04/report.md` |
| Run A s0 | speed_bump | 0.725 | 0.864 | 0.571 | 0.524 | 0.191 (157) | 0.950 | same |
| **D1** | pothole | 0.596 | 0.625 | 0.579 | 0.430 | 0.542 (142) | 0.719 | same |
| **D1** | speed_bump | 0.710 | 0.727 | 0.619 | 0.502 | 0.280 (157) | 0.863 | same |
| D1-size (11s) | pothole | 0.625 | 0.643 | 0.624 | 0.463 | 0.577 (142) | 0.758 | same |
| D1-size (11s) | speed_bump | 0.692 | 0.753 | 0.622 | 0.516 | 0.261 (157) | 0.892 | same |

(Ultralytics' own printout for D1: pothole 0.597, bump 0.712, all 0.655, `runs/v3b_A_11n_960_s0_VALr2_json.txt`.)

New-country part vals (held-out sequences/locations, with hazard-free frames):
| set | model | class | AP50 | ImgAcc (n_neg) | NearR (n) | file |
|---|---|---|---|---|---|---|
| RSID val (Lithuania) | D1 | speed_bump | 0.670 | 0.758 (116) | 0.544 (57) | `review/metrics_r3/partval_rsid_all_2026-11-04/report.md` |
| Bučko val (Slovakia) | D1 | pothole | 0.571 | 0.848 (42) | 0.688 (48) | `review/metrics_r3/partval_bucko_all_2026-11-04/report.md` |

Seed noise (Run A config, 3 seeds): all mAP50 0.6747 ± 0.0106; pothole 0.6227 ± 0.0147; bump 0.7263 ± 0.0114
(`runs/v3a_r2_seed_summary.txt`). A single-seed difference smaller than about 0.02 is within noise.

## 3. Test values (used once per final candidate)
| model | set | class | AP50 | P | R | file |
|---|---|---|---|---|---|---|
| Run A s0 | r2 test (323 img) | pothole | 0.631 | 0.549 | 0.681 | `runs/v3a_r2_11n_960_s0_TEST.txt` |
| Run A s0 | r2 test | speed_bump | 0.294 | 0.461 | 0.225 | same |
| Run A s0 | BD87 external (88 bump boxes) | speed_bump | 0.367 | 0.531 | 0.318 | `runs/EXT_bd87_v3a_r2_11n_960_s0_b.txt` |
| final candidate | r2 test | pothole / speed_bump | `TODO(test)` | `TODO(test)` | `TODO(test)` | `TODO(test)` |
| final candidate | BD87 | speed_bump | `TODO(test)` | | | |
| final candidate | r2 test, A1 / A2 / A3 at val thresholds | both | `TODO(test)` | | | `metrics_report.py --thresholds` |

## 4. Status of the ≥ 0.90 target (honest)
| pre-registered metric | best value so far | reached? |
|---|---|---|
| per-class mAP50 (r2 val) | bump 0.736 (Run A s1, `review/metrics_r3/val_r2_baselines/report.md`) | **no** |
| per-class mAP50 (r2 test) | pothole 0.631, bump 0.294 (Run A) | **no** |
| A1 near-range recall | pothole 0.613 (Run A s1, val baselines); bump 0.544 (D1, RSID val) | **no** |
| A2 image-level accuracy | only measurable on sets with hazard-free frames: pothole 0.848 (Bučko val), bump 0.758 (RSID val) | **no** |
| A3 precision at recall 0.50 | bump 0.950 (Run A s0, val); 0.863 (D1, val) | **near / above on val for one model; UNRESOLVED until test with frozen thresholds** |

Reading: A3 says that, when the detector keeps half of the bumps, those warnings are mostly right. It does not say
that most bumps are found. The target cannot honestly be called reached on mAP50 or recall. The gap comes from
unseen scenes (val→test bump 0.723 → 0.294, STATUS Stage 4), and the remedy is new labelled data from those scenes.
