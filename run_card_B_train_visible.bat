@echo off
rem Stage 45 training chain on CARD (VAL ONLY - CARD test is NOT read here; data.yaml has no test key).
rem Run 1: C's best.pt -> CARD, C's recipe (imgsz 960, batch 8, seed 0, deterministic), epochs 35 (owner decision 14 Nov 12:57, time), patience 20.
rem Run 2: yolo11s.pt (COCO) -> CARD, same settings. Each run is skipped if its folder exists; a crashed run is resumed.
rem After each run: CARD val with save_json. Run 2 starts only after Run 1 (one GPU job at a time).
cd /d %~dp0
title GP36 Stage 45: CARD training chain (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training or eval is running - not starting & goto end)
if not exist road_hazards_card_v4\data.yaml (echo road_hazards_card_v4 not built yet & goto end)
set D=road_hazards_card_v4\data.yaml
set A=data=%D% epochs=35 patience=20 imgsz=960 batch=8 workers=2 cache=disk seed=0 deterministic=True plots=False
call :one card_C_11n_960_s0 runs\detect\v3b_C_11n_960_s0_r2\weights\best.pt
call :one card_11s_960_s0 yolo11s.pt
echo ---------------- RESULT - CARD VAL ----------------
for %%M in (card_C_11n_960_s0 card_11s_960_s0) do (
  if exist runs\%%M_CARDVAL.txt (echo --- %%M --- & %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\%%M_CARDVAL.txt)
)
echo ================  DONE %date% %time%  ================
goto end
:one
if exist runs\detect\%1\weights\best.pt if exist runs\%1_train.done goto val
if exist runs\detect\%1\weights\last.pt (
  echo ===== resume %1 & venv\Scripts\yolo detect train resume model=runs\detect\%1\weights\last.pt >> runs\%1_train.log 2>&1
) else (
  echo ===== train %1 & venv\Scripts\yolo detect train model=%2 name=%1 %A% > runs\%1_train.log 2>&1
)
%SystemRoot%\System32\findstr.exe /c:"epochs completed in" runs\%1_train.log >nul && echo done> runs\%1_train.done
if not exist runs\%1_train.done (echo %1 did not finish - run this bat again to resume & exit /b)
:val
if exist runs\detect\%1\weights\best.pt if not exist runs\%1_CARDVAL.txt (
  venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=%D% split=val imgsz=960 batch=8 save_json=True plots=False name=%1_CARDVAL > runs\%1_CARDVAL.txt 2>&1
)
exit /b
:end
echo The window stays open.
pause
