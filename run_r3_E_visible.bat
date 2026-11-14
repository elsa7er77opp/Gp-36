@echo off
rem Plan E (STATUS Stage 29, hypotheses written before this window): levers on C -> E1 (AdamW) -> E2 (P2 head, AdamW).
rem One GPU job at a time; every tool refuses to overwrite; the test split is never used here.
cd /d %~dp0
title GP36 plan E: levers, E1 AdamW, E2 P2 (do not close)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set E1=v3b_C_11n_960_adamw_s0
set E2=v3b_C_11n-p2_960_adamw_s0
set PARTS=rsid bucko sr pol_v2 red_v2 ng8_v2 egy_v2

echo ================================================================
echo  1/3 LEVERS ON C (r2 val): TTA, WBF C+D1_11s, sliced   start %date% %time%
echo ================================================================
if not exist runs\detect\%C%_TTA_VALr2_json venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True augment=True plots=False name=%C%_TTA_VALr2_json > runs\%C%_TTA_VALr2_json.txt 2>&1
%PY% tools\wbf_ensemble.py --pred runs\detect\%C%_VALr2_json\predictions.json --pred runs\detect\v3b_A_11s_960_s0_VALr2_json\predictions.json --out runs\detect\WBF_C_D1s_VALr2\predictions.json
%PY% tools\sliced_predict.py --weights runs\detect\%C%\weights\best.pt --data road_hazards_v3a_r2 --split val --imgsz 960 --tile 640 --overlap 0.25 --rows-from 0.4 --merge nms --out runs\detect\SLICED_C_VALr2\predictions.json
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred C_TTA=runs\detect\%C%_TTA_VALr2_json\predictions.json --pred WBF_C_D1s=runs\detect\WBF_C_D1s_VALr2\predictions.json --pred C_sliced=runs\detect\SLICED_C_VALr2\predictions.json --out review\metrics_r3\val_r2_levers_C
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred C_TTA=runs\detect\%C%_TTA_VALr2_json\predictions.json --pred WBF_C_D1s=runs\detect\WBF_C_D1s_VALr2\predictions.json --pred C_sliced=runs\detect\SLICED_C_VALr2\predictions.json --out review\metrics_r3\coco_val_r2_levers_C

echo ================================================================
echo  2/3 TRAIN E1 = C data, AdamW as D1/D2 got it
echo ================================================================
call :train %E1% "model=yolo11n.pt batch=8 optimizer=AdamW lr0=0.001667 momentum=0.9 warmup_bias_lr=0.0" || goto fail
call :evals %E1%
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --by source --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E1=runs\detect\%E1%_VALr2_json\predictions.json --out review\metrics_r3\val_r2_E1
for %%P in (%PARTS%) do %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred C=runs\detect\PARTVAL_%%P_%C%\predictions.json --pred E1=runs\detect\PARTVAL_%%P_%E1%\predictions.json --out review\metrics_r3\partval_%%P_E1
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E1=runs\detect\%E1%_VALr2_json\predictions.json --out review\metrics_r3\coco_val_r2_E1

echo ================================================================
echo  3/3 TRAIN E2 = P2 head, AdamW as E1, batch 8
echo ================================================================
call :train %E2% "model=models\yolo11n-p2.yaml pretrained=yolo11n.pt batch=8 optimizer=AdamW lr0=0.001667 momentum=0.9 warmup_bias_lr=0.0" || goto fail
call :evals %E2%
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --by source --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E1=runs\detect\%E1%_VALr2_json\predictions.json --pred E2=runs\detect\%E2%_VALr2_json\predictions.json --out review\metrics_r3\val_r2_E2
for %%P in (%PARTS%) do %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred C=runs\detect\PARTVAL_%%P_%C%\predictions.json --pred E1=runs\detect\PARTVAL_%%P_%E1%\predictions.json --pred E2=runs\detect\PARTVAL_%%P_%E2%\predictions.json --out review\metrics_r3\partval_%%P_E2
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E1=runs\detect\%E1%_VALr2_json\predictions.json --pred E2=runs\detect\%E2%_VALr2_json\predictions.json --out review\metrics_r3\coco_val_r2_E2

echo.
echo ================  ALL DONE %date% %time%  ================
goto end

:train
if exist runs\detect\%1 (
  echo runs\detect\%1 exists - refusing to overwrite
  exit /b 1
)
echo.
echo ================================================================
echo  TRAINING %1   start %date% %time%
echo ================================================================
venv\Scripts\yolo train %~2 data=road_hazards_v3b_C\data.yaml epochs=70 imgsz=960 workers=2 cache=disk patience=20 seed=0 deterministic=True name=%1
if errorlevel 1 (
  echo === %1 TRAIN FAILED
  exit /b 1
)
exit /b 0

:evals
echo.
echo ================================================================
echo  RESULTS %1  (val only)
echo ================================================================
venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%1_VALr2_json > runs\%1_VALr2_json.txt 2>&1
echo --- r2 val (830 images) ---
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%1_VALr2_json.txt
for %%P in (%PARTS%) do (
  venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%1 > runs\PARTVAL_%%P_%1.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%1.txt
)
exit /b 0

:fail
echo === STOPPED: a step failed, nothing after it was run
:end
echo (window stays open; reports in review\metrics_r3\*_levers_C, *_E1, *_E2)
