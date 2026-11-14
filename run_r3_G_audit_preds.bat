@echo off
rem Label audit step 1 (STATUS Stage 34): predictions of C on the v3b_C TRAIN split, for finding label errors. No training.
cd /d %~dp0
title GP36 label audit: C predictions on v3b_C train (do not close)
if exist runs\detect\AUDIT_C_on_v3bC_train echo runs\detect\AUDIT_C_on_v3bC_train exists - refusing & goto end
venv\Scripts\yolo val model=runs\detect\v3b_C_11n_960_s0_r2\weights\best.pt data=review\label_audit_r3\v3b_C_train_as_val.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=AUDIT_C_on_v3bC_train > runs\AUDIT_C_on_v3bC_train.txt 2>&1
echo === DONE %date% %time%
:end
