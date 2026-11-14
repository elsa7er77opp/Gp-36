@echo off
rem Stage 40 step 2: F1 = C's exact arguments on road_hazards_v5_fixed (same 10,562 images, labels fixed by eye).
rem VAL ONLY. The test split is never used here.
cd /d %~dp0
title GP36 v5 step 2: train F1 on v5_fixed (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set C=v3b_C_11n_960_s0_r2
set A1=v5_all_11n_960_s0
set F1=v5_fixed_11n_960_s0
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class "
if not exist road_hazards_v5_fixed\data.yaml (
  echo road_hazards_v5_fixed not built yet - the label fixes are not applied
  goto end
)
if exist runs\detect\%F1% (
  echo runs\detect\%F1% exists - refusing to overwrite
  goto end
)
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v5_fixed\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=False patience=20 seed=0 deterministic=True optimizer=auto name=%F1%
if errorlevel 1 (
  echo === %F1% TRAIN FAILED
  goto end
)
venv\Scripts\yolo val model=runs\detect\%F1%\weights\best.pt data=road_hazards_v5_fixed\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%F1%_VALv5 > runs\%F1%_VALv5.txt 2>&1
echo ---------------- RESULT - val only ----------------
echo --- C  on v5 val ---
if exist runs\%C%_VALv5.txt %FS% runs\%C%_VALv5.txt
echo --- A1 - all images, labels as they were ---
if exist runs\%A1%_VALv5.txt %FS% runs\%A1%_VALv5.txt
echo --- F1 - all images, labels fixed ---
%FS% runs\%F1%_VALv5.txt
echo ================  ALL DONE %date% %time%  ================
:end
echo The window stays open. Text results are in runs\*_VALv5.txt
pause
