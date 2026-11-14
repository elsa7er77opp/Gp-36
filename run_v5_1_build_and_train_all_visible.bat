@echo off
rem Stage 40 step 1 (rule written in STATUS before this run): NOTHING is removed.
rem road_hazards_v5_all = all 10,562 train images of road_hazards_v3b_C at exactly 960x720 (labels as they are),
rem then A1 = C's exact arguments on it. VAL ONLY. The test split is never used here.
cd /d %~dp0
title GP36 v5 step 1: build v5_all (all images, 960x720) then train A1 (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set A1=v5_all_11n_960_s0
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class "
if exist runs\detect\%A1% (
  echo runs\detect\%A1% exists - refusing to overwrite
  goto end
)
echo ===== 1. build road_hazards_v5_all   %date% %time%
if not exist road_hazards_v5_all %PY% tools\std_dataset_v2.py build --src road_hazards_v3b_C --out road_hazards_v5_all --unstretch sb15=1.7778 --frame-rules none --no-dedup
if not exist road_hazards_v5_all\data.yaml (
  echo === BUILD FAILED
  goto end
)
echo ===== 2. baseline: model C on the v5 val   %date% %time%
if not exist runs\detect\%C%_VALv5 venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=road_hazards_v5_all\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%C%_VALv5 > runs\%C%_VALv5.txt 2>&1
%FS% runs\%C%_VALv5.txt
echo ================================================================
echo  3. TRAINING %A1%   start %date% %time%
echo ================================================================
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v5_all\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=False patience=20 seed=0 deterministic=True optimizer=auto name=%A1%
if errorlevel 1 (
  echo === %A1% TRAIN FAILED
  goto end
)
venv\Scripts\yolo val model=runs\detect\%A1%\weights\best.pt data=road_hazards_v5_all\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%A1%_VALv5 > runs\%A1%_VALv5.txt 2>&1
echo ---------------- RESULT - val only ----------------
echo --- C  on v5 val ---
%FS% runs\%C%_VALv5.txt
echo --- A1 on v5 val ---
%FS% runs\%A1%_VALv5.txt
echo ================  ALL DONE %date% %time%  ================
:end
echo The window stays open. Text results are in runs\*_VALv5.txt
pause
