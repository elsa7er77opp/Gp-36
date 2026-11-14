@echo off
rem Stage 41c: re-run A1 (v5_all_11n_960_s0) on ALLVAL. The first try (18:35) aborted on a window-CLOSE event and left
rem an EMPTY folder runs\detect\v5_all_11n_960_s0_ALLVAL, so run_alldata_1 now skips A1. Nothing is deleted: new name _r2.
rem VAL ONLY - no test here.
cd /d %~dp0
title GP36 Stage 41c: A1 on ALLVAL (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training or eval is running - not starting & goto end)
if exist runs\detect\v5_all_11n_960_s0_ALLVAL_r2 (echo already done & goto show)
echo ===== A1 on ALLVAL   %date% %time%
venv\Scripts\yolo val model=runs\detect\v5_all_11n_960_s0\weights\best.pt data=review\alldata_v1\data_allval.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=v5_all_11n_960_s0_ALLVAL_r2 > runs\v5_all_11n_960_s0_ALLVAL_r2.txt 2>&1
:show
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\v5_all_11n_960_s0_ALLVAL_r2.txt
echo ================  DONE %date% %time%  ================
:end
echo The window stays open.
pause
