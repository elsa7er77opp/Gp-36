@echo off
rem Visible training window (Ahmed, 2026-11-04: "the next training must be visible, with full per-class results").
rem Replaces queue 2 / queue 3 after D1 seed 1 (those background scripts were stopped; the running training was not).
rem Order: finish D1 seed 1 evals -> D2 (v3b_B) -> imgsz 1280 (v3b_A). Hypotheses: STATUS Stages 17-18.
rem One GPU job at a time; a run name that exists is never reused.
cd /d %~dp0
title GP36 training (do not close)
set FIND=%SystemRoot%\System32\find.exe
set PY=venv\Scripts\python -I

echo ================================================================
echo  Waiting for D1 seed 1 (v3b_A_11n_960_s1) to finish training ...
echo ================================================================
:wait
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %FIND% /i "yolo.exe" >nul && (ping -n 61 127.0.0.1 >nul & goto wait)

call :evals v3b_A_11n_960_s1 960 "rsid bucko"
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --pred D1_s0=runs\detect\v3b_A_11n_960_s0_VALr2_json\predictions.json --pred D1_s1=runs\detect\v3b_A_11n_960_s1_VALr2_json\predictions.json --out review\metrics_r3\val_r2_D1_seeds

rem D1 s0 / Run A on the new sr part-val (baselines for H-D2)
for %%M in ("v3b_A_11n_960_s0 D1s0" "v3a_r2_11n_960_s0 runA_s0") do for /f "tokens=1,2" %%a in (%%M) do (
  if not exist runs\detect\PARTVAL_sr_%%b venv\Scripts\yolo val model=runs\detect\%%a\weights\best.pt data=parts_r3\sr\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_sr_%%b > runs\PARTVAL_sr_%%b.txt 2>&1
)

call :train v3b_B_11n_960_s0 road_hazards_v3b_B 960 || goto fail
call :evals v3b_B_11n_960_s0 960 "rsid bucko sr"
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --pred D1_s0=runs\detect\v3b_A_11n_960_s0_VALr2_json\predictions.json --pred D2=runs\detect\v3b_B_11n_960_s0_VALr2_json\predictions.json --by source --out review\metrics_r3\val_r2_D2
%PY% tools\metrics_report.py --data parts_r3\sr --split val --pred runA_s0=runs\detect\PARTVAL_sr_runA_s0\predictions.json --pred D1_s0=runs\detect\PARTVAL_sr_D1s0\predictions.json --pred D2=runs\detect\PARTVAL_sr_v3b_B_11n_960_s0\predictions.json --by meta --out review\metrics_r3\partval_sr_D2
%PY% tools\metrics_report.py --data parts_r3\rsid --split val --pred D1_s0=runs\detect\PARTVAL_rsid_v3bA_s0\predictions.json --pred D2=runs\detect\PARTVAL_rsid_v3b_B_11n_960_s0\predictions.json --out review\metrics_r3\partval_rsid_D2
%PY% tools\metrics_report.py --data parts_r3\bucko --split val --pred D1_s0=runs\detect\PARTVAL_bucko_v3bA_s0\predictions.json --pred D2=runs\detect\PARTVAL_bucko_v3b_B_11n_960_s0\predictions.json --out review\metrics_r3\partval_bucko_D2

call :train v3b_A_11n_1280_s0 road_hazards_v3b_A 1280 || goto fail
call :evals v3b_A_11n_1280_s0 1280 "rsid bucko"
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --pred D1_s0=runs\detect\v3b_A_11n_960_s0_VALr2_json\predictions.json --pred D1_1280=runs\detect\v3b_A_11n_1280_s0_VALr2_json\predictions.json --out review\metrics_r3\val_r2_1280

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
echo  TRAINING %1   data=%2   imgsz=%3   start %date% %time%
echo ================================================================
venv\Scripts\yolo train model=yolo11n.pt data=%2\data.yaml epochs=70 imgsz=%3 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True name=%1
if errorlevel 1 (
  echo === %1 TRAIN FAILED
  exit /b 1
)
exit /b 0

:evals
echo.
echo ================================================================
echo  RESULTS %1  (val only; per class: P, R, mAP50, mAP50-95)
echo ================================================================
venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=%2 batch=8 save_json=True plots=True name=%1_VALr2_json > runs\%1_VALr2_json.txt 2>&1
echo --- r2 val (830 images) ---
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%1_VALr2_json.txt
for %%P in (%~3) do (
  venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=%2 batch=8 save_json=True plots=False name=PARTVAL_%%P_%1 > runs\PARTVAL_%%P_%1.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%1.txt
)
exit /b 0

:fail
echo === STOPPED: a step failed, nothing after it was run
:end
echo (window stays open; per-class tables with Accuracy are in review\metrics_r3\*\report.md)
