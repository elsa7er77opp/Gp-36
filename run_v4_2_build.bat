@echo off
rem Stage 39 step 2: BUILD road_hazards_v4_std (every image 960x720, one framing, no duplicates in train).
rem CPU job, about 20-40 minutes. The source dataset is not changed. No training here.
cd /d %~dp0
title GP36 v4 step 2: build road_hazards_v4_std (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
set PY=venv\Scripts\python -I
if exist road_hazards_v4_std (
  echo road_hazards_v4_std exists - refusing to overwrite
  goto end
)
%PY% tools\std_dataset.py build --src road_hazards_v3b_C --out road_hazards_v4_std --unstretch sb15=1.7778
echo.
echo Now open road_hazards_v4_std\sheets\*.jpg and road_hazards_v4_std\build_info.json BEFORE training.
:end
pause
