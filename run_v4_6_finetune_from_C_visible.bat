@echo off
rem Stage 39 OPTIONAL step 6: S2 = start from model C's weights (already trained on road hazards) and fine-tune
rem on road_hazards_v4_clean. Run ONLY if the supervisor meant "start from an already-trained model". VAL ONLY.
cd /d %~dp0
title GP36 v4 step 6: S2 fine-tune from C (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set C=v3b_C_11n_960_s0_r2
set S2=v4_clean_11n_960_ftC_s0
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class "
if not exist road_hazards_v4_clean\data.yaml (
  echo road_hazards_v4_clean not built yet - review not applied
  goto end
)
if exist runs\detect\%S2% (
  echo runs\detect\%S2% exists - refusing to overwrite
  goto end
)
venv\Scripts\yolo train model=runs\detect\%C%\weights\best.pt data=road_hazards_v4_clean\data.yaml epochs=40 imgsz=960 batch=8 workers=2 cache=False patience=15 seed=0 deterministic=True optimizer=auto name=%S2%
if errorlevel 1 (
  echo === %S2% TRAIN FAILED
  goto end
)
venv\Scripts\yolo val model=runs\detect\%S2%\weights\best.pt data=road_hazards_v4_clean\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%S2%_VALv4 > runs\%S2%_VALv4.txt 2>&1
venv\Scripts\yolo val model=runs\detect\%S2%\weights\best.pt data=road_hazards_v4_clean\data_stdframe.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%S2%_VALv4frame > runs\%S2%_VALv4frame.txt 2>&1
echo --- S2 on v4 val (all) ---
%FS% runs\%S2%_VALv4.txt
echo --- S2 on v4 val (standard framing subset) ---
%FS% runs\%S2%_VALv4frame.txt
echo ================  ALL DONE %date% %time%  ================
:end
pause
