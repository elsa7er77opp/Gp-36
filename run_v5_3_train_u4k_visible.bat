@echo off
rem Stage 40d (rule written in STATUS before this run): F1u = C's exact arguments on road_hazards_v5_source_review_20261112_u4k
rem (all 10,562 train images, 960x720, labels fixed by AI eye review; val/test unchanged). VAL ONLY. The test split is never used here.
cd /d %~dp0
title GP36 v5 step 3: train F1u on v5 u4k (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set C=v3b_C_11n_960_s0_r2
set A1=v5_all_11n_960_s0
set F=v5_u4k_11n_960_s0
set D=road_hazards_v5_source_review_20261112_u4k
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  "
if not exist %D%\data.yaml (
  echo %D% not found
  goto end
)
if exist runs\detect\%F% (
  echo runs\detect\%F% exists - refusing to overwrite
  goto end
)
echo ================================================================
echo  TRAINING %F%   start %date% %time%
echo ================================================================
venv\Scripts\yolo train model=yolo11n.pt data=%D%\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=False patience=20 seed=0 deterministic=True optimizer=auto name=%F%
if errorlevel 1 (
  echo === %F% TRAIN FAILED
  goto end
)
venv\Scripts\yolo val model=runs\detect\%F%\weights\best.pt data=%D%\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%F%_VALv5 > runs\%F%_VALv5.txt 2>&1
echo ---------------- RESULT - val only ----------------
echo --- C  on v5 val ---
%FS% runs\%C%_VALv5.txt
echo --- A1 - all images, labels as they were ---
%FS% runs\%A1%_VALv5.txt
echo --- F1u - all images, labels fixed (u4k) ---
%FS% runs\%F%_VALv5.txt
echo ================  ALL DONE %date% %time%  ================
:end
echo The window stays open. Text results are in runs\*_VALv5.txt
pause
