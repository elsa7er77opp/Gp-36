@echo off
rem v3b_C retry: first try (runs\detect\v3b_C_11n_960_s0) died at epoch 1,
rem "CUDA error: resource already mapped" in the pin-memory thread. Same data and args, new name.
cd /d %~dp0
title GP36 training v3b_C retry (do not close)
set PY=venv\Scripts\python -I
set N=v3b_C_11n_960_s0_r2
if exist runs\detect\%N% (echo runs\detect\%N% exists - refusing to overwrite & goto end)

venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3b_C\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True name=%N%
if errorlevel 1 (echo === %N% TRAIN FAILED & goto end)

venv\Scripts\yolo val model=runs\detect\%N%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%N%_VALr2_json > runs\%N%_VALr2_json.txt 2>&1
echo --- r2 val (830 images) ---
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%N%_VALr2_json.txt
for %%P in (rsid bucko sr pol_v2 red_v2 ng8_v2 egy_v2) do (
  venv\Scripts\yolo val model=runs\detect\%N%\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%N% > runs\PARTVAL_%%P_%N%.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%N%.txt
)

%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --pred D1_s0=runs\detect\v3b_A_11n_960_s0_VALr2_json\predictions.json --pred D2=runs\detect\v3b_B_11n_960_s0_VALr2_json\predictions.json --pred C=runs\detect\%N%_VALr2_json\predictions.json --by source --out review\metrics_r3\val_r2_C
%PY% tools\metrics_report.py --data parts_r3\rsid --split val --pred D1_s0=runs\detect\PARTVAL_rsid_v3bA_s0\predictions.json --pred D2=runs\detect\PARTVAL_rsid_v3b_B_11n_960_s0\predictions.json --pred C=runs\detect\PARTVAL_rsid_%N%\predictions.json --out review\metrics_r3\partval_rsid_C
%PY% tools\metrics_report.py --data parts_r3\bucko --split val --pred D1_s0=runs\detect\PARTVAL_bucko_v3bA_s0\predictions.json --pred D2=runs\detect\PARTVAL_bucko_v3b_B_11n_960_s0\predictions.json --pred C=runs\detect\PARTVAL_bucko_%N%\predictions.json --out review\metrics_r3\partval_bucko_C
%PY% tools\metrics_report.py --data parts_r3\sr --split val --pred D1_s0=runs\detect\PARTVAL_sr_D1s0\predictions.json --pred D2=runs\detect\PARTVAL_sr_v3b_B_11n_960_s0\predictions.json --pred C=runs\detect\PARTVAL_sr_%N%\predictions.json --by meta --out review\metrics_r3\partval_sr_C
for %%P in (pol_v2 red_v2 ng8_v2 egy_v2) do (
  %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred D1_s0=runs\detect\PARTVAL_%%P_D1s0\predictions.json --pred D2=runs\detect\PARTVAL_%%P_D2\predictions.json --pred C=runs\detect\PARTVAL_%%P_%N%\predictions.json --out review\metrics_r3\partval_%%P_C
)
echo ================  ALL DONE %date% %time%  ================
:end
echo (window stays open)
