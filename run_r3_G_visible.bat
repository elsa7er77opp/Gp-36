@echo off
rem Plan G (STATUS Stage 34, hypothesis written before this window): G1 = C's exact recipe on road_hazards_v3b_C2
rem (train labels audited: 60 wrong boxes removed, 24 images with visible unlabelled hazards left out; val/test identical).
rem One GPU job at a time; every tool refuses to overwrite; the test split is never used here.
cd /d %~dp0
title GP36 plan G: G1 on cleaned train labels (do not close)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set G1=v3b_C2_11n_960_s0
set PARTS=rsid bucko sr pol_v2 red_v2 ng8_v2 egy_v2
if exist runs\detect\%G1% (
  echo runs\detect\%G1% exists - refusing to overwrite
  goto end
)
echo ================================================================
echo  TRAINING %G1%   start %date% %time%
echo ================================================================
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3b_C2\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True optimizer=auto name=%G1%
if errorlevel 1 (
  echo === %G1% TRAIN FAILED
  goto end
)
echo ================================================================
echo  RESULTS %G1%  (val only)   %date% %time%
echo ================================================================
venv\Scripts\yolo val model=runs\detect\%G1%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%G1%_VALr2_json > runs\%G1%_VALr2_json.txt 2>&1
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%G1%_VALr2_json.txt
for %%P in (%PARTS%) do (
  venv\Scripts\yolo val model=runs\detect\%G1%\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%G1% > runs\PARTVAL_%%P_%G1%.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%G1%.txt
)
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --by source --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred G1=runs\detect\%G1%_VALr2_json\predictions.json --out review\metrics_r3\val_r2_G1
for %%P in (%PARTS%) do %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred C=runs\detect\PARTVAL_%%P_%C%\predictions.json --pred G1=runs\detect\PARTVAL_%%P_%G1%\predictions.json --out review\metrics_r3\partval_%%P_G1
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred G1=runs\detect\%G1%_VALr2_json\predictions.json --out review\metrics_r3\coco_val_r2_G1
echo.
echo ================  ALL DONE %date% %time%  ================
:end
echo (window stays open; reports in review\metrics_r3\*_G1)
