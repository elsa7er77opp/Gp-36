@echo off
rem Stage 39 step 5 (rule written in STATUS before this run): S1 = C's recipe on road_hazards_v4_clean.
rem VAL ONLY. The test split is never used here. One GPU job at a time. Nothing is overwritten.
cd /d %~dp0
title GP36 v4 step 5: baseline C on v4 val, then train S1 (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set C=v3b_C_11n_960_s0_r2
set S1=v4_clean_11n_960_s0
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class "
if not exist road_hazards_v4_clean\data.yaml (
  echo road_hazards_v4_clean not built yet - review not applied - run run_v4_4_apply_review.bat first
  goto end
)
if exist runs\detect\%S1% (
  echo runs\detect\%S1% exists - refusing to overwrite
  goto end
)
echo ===== 1. baseline: model C on the NEW val (all images, then standard-framing subset)   %date% %time%
if not exist runs\detect\%C%_VALv4 venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=road_hazards_v4_clean\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%C%_VALv4 > runs\%C%_VALv4.txt 2>&1
%FS% runs\%C%_VALv4.txt
if not exist runs\detect\%C%_VALv4frame venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=road_hazards_v4_clean\data_stdframe.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%C%_VALv4frame > runs\%C%_VALv4frame.txt 2>&1
%FS% runs\%C%_VALv4frame.txt
echo ================================================================
echo  2. TRAINING %S1%   start %date% %time%
echo ================================================================
rem same arguments as C; only the data changes. cache=False: the images are small now and no .npy files fill the disk.
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v4_clean\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=False patience=20 seed=0 deterministic=True optimizer=auto name=%S1%
if errorlevel 1 (
  echo === %S1% TRAIN FAILED
  goto end
)
echo ===== 3. S1 on the same val sets   %date% %time%
venv\Scripts\yolo val model=runs\detect\%S1%\weights\best.pt data=road_hazards_v4_clean\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%S1%_VALv4 > runs\%S1%_VALv4.txt 2>&1
venv\Scripts\yolo val model=runs\detect\%S1%\weights\best.pt data=road_hazards_v4_clean\data_stdframe.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%S1%_VALv4frame > runs\%S1%_VALv4frame.txt 2>&1
echo.
echo ---------------- RESULT (val only) ----------------
echo --- C  on v4 val (all) ---
%FS% runs\%C%_VALv4.txt
echo --- S1 on v4 val (all) ---
%FS% runs\%S1%_VALv4.txt
echo --- C  on v4 val (standard framing subset) ---
%FS% runs\%C%_VALv4frame.txt
echo --- S1 on v4 val (standard framing subset) ---
%FS% runs\%S1%_VALv4frame.txt
echo.
echo ================  ALL DONE %date% %time%  ================
:end
echo (window stays open; text results in runs\*_VALv4*.txt)
pause
