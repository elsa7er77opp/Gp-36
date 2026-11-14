## Stage 41b — WBF(C, v1) on ALLVAL, val only (written BEFORE the run and any result; 2026-11-13)
- **Why:** WBF(C, v1) gained on r2 (Stage 29/32) but was never measured on the other 7 sources. Stage 41 left it out ("needs its own script").
- **What runs:** `run_alldata_2_wbf_val_visible.bat` (visible window): `yolo val save_json` for C and for v1 (`v3a_r1_11n_960_s0`) on
  `review/alldata_v1/data_allval.yaml` (imgsz 960, batch 8, conf 0.001), then `review/alldata_v1/audit_2026-11-13/a5_wbf_allval.py`.
  **No test image is read**, so no ledger row.
- **Frozen settings (nothing is tuned on ALLVAL):** WBF iou 0.55, skip 0.001, equal weights (Stage 29/32, `tools/wbf_ensemble.py`).
  Operating thresholds for the P/R table: the r2-val ones in `review/metrics_r3/val_r2_final/report.json`
  (C 0.251 / 0.192; WBF 0.148 / 0.090; v1 0.315 / 0.286) and a fixed 0.25 row.
- **Hypothesis H-41b (PROVISIONAL):** WBF raises speed_bump AP50 on ALLVAL and does not raise pothole AP50 (same direction as r2 test:
  bump +0.143, pothole −0.013). The size on non-r2 sources is unknown.
- **Decision rule (the Stage 41 rule, unchanged):** WBF replaces C as the ALLVAL choice only if its ALLVAL mean AP50 >= C + 0.02.
  The official number is the one WITH the 32 sr `rad` val images; the "minus rad" row is a sensitivity row only, until a human decides
  on those labels (audit finding 4, `review/alldata_v1/audit_2026-11-13/AUDIT_RESULTS.md`).
- **Reported whatever the outcome:** C, v1 and WBF, per class and per source, also if WBF is worse. v1 alone is a WBF input; it is shown for
  context and is not a candidate.
- **Not covered:** latency. WBF runs two models per frame; speed on the demo device is NOT MEASURED.
- **Script check done before the run (no new model result):** C's stored ALLVAL predictions converted to the save_json format give
  0.5872 / 0.7243 / 0.6557 through `a5_wbf_allval.py`, equal to Stage 41a. If the GPU `yolo val` numbers for C differ from these by more
  than 0.003, stop and look before reading the WBF row.
