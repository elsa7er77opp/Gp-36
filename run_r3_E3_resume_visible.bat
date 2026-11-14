@echo off
rem Stage 38 E3 resume (Ahmed, 7 Nov: "Resume from last.pt"). The first E3 window stopped after epoch 6 (disk full, see STATUS 38b).
rem Same run, same args (Ultralytics resume reads runs\detect\v3b_C3_11n_960_s0\args.yaml); then steps 4-5 of run_r3_E3_visible.bat unchanged.
rem Val only - the test split is never used here. One GPU job at a time; nothing is deleted.
cd /d %~dp0
title GP36 Stage 38: E3 resume from last.pt (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set G1=v3b_C2_11n_960_s0
set E3=v3b_C3_11n_960_s0
set PARTS=rsid bucko sr pol_v2 red_v2 ng8_v2 egy_v2
if not exist runs\detect\%E3%\weights\last.pt (
  echo runs\detect\%E3%\weights\last.pt missing - nothing to resume
  goto end
)
if exist runs\%E3%_VALr2_json.txt (
  echo runs\%E3%_VALr2_json.txt exists - E3 was already evaluated, not starting
  goto end
)
echo ================================================================
echo  3. TRAINING %E3% RESUME   start %date% %time%
echo ================================================================
venv\Scripts\yolo train resume=True model=runs\detect\%E3%\weights\last.pt
if errorlevel 1 goto fail
echo ===== 4. val only   %date% %time%
venv\Scripts\yolo val model=runs\detect\%E3%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%E3%_VALr2_json > runs\%E3%_VALr2_json.txt 2>&1
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%E3%_VALr2_json.txt
for %%P in (%PARTS%) do (
  venv\Scripts\yolo val model=runs\detect\%E3%\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%E3% > runs\PARTVAL_%%P_%E3%.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%E3%.txt
)
rem egm part val = hazard-free egm TRAIN-creator sequences held out of the part train (never eval creators)
for %%M in (%C% %G1% %E3%) do venv\Scripts\yolo val model=runs\detect\%%M\weights\best.pt data=parts_r3\egm\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_egm_%%M > runs\PARTVAL_egm_%%M.txt 2>&1
echo ===== 5. reports
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --by source --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E3=runs\detect\%E3%_VALr2_json\predictions.json --out review\metrics_r3\val_r2_E3
for %%P in (%PARTS%) do %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred C=runs\detect\PARTVAL_%%P_%C%\predictions.json --pred E3=runs\detect\PARTVAL_%%P_%E3%\predictions.json --out review\metrics_r3\partval_%%P_E3
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E3=runs\detect\%E3%_VALr2_json\predictions.json --out review\metrics_r3\coco_val_r2_E3
for %%M in (C:%C% G1:%G1% E3:%E3%) do for /f "tokens=1,2 delims=:" %%a in ("%%M") do if not exist review\metrics_r3\thr_%%a_f1_E3stage.json %PY% tools\calibrate_thresholds.py --data road_hazards_v3a_r2 --split val --pred runs\detect\%%b_VALr2_json\predictions.json --model %%a --mode f1 --out review\metrics_r3\thr_%%a_f1_E3stage.json
%PY% tools\neg_fp_count.py --data parts_r3/egm --split val --model C runs\detect\PARTVAL_egm_%C%\predictions.json review\metrics_r3\thr_C_f1_E3stage.json --model G1 runs\detect\PARTVAL_egm_%G1%\predictions.json review\metrics_r3\thr_G1_f1_E3stage.json --model E3 runs\detect\PARTVAL_egm_%E3%\predictions.json review\metrics_r3\thr_E3_f1_E3stage.json --out review\metrics_r3\negfp_egm_E3
echo.
echo ================  ALL DONE %date% %time%  ================
goto end
:fail
echo === FAILED at %date% %time% (see the lines above)
:end
echo (window stays open; reports in review\metrics_r3\*_E3)
pause
