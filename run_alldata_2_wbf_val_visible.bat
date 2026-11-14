@echo off
rem Stage 41b (paste review\alldata_v1\audit_2026-11-13\STAGE41b_paste_into_STATUS.md into STATUS BEFORE this run):
rem WBF(C, v1) on ALLVAL (1,754 val images). VAL ONLY - no test image is read, so no ledger use.
rem WBF settings are the ones frozen in Stage 29/32: iou 0.55, skip 0.001, equal weights. Nothing is tuned here.
rem Safe to run again: an existing prediction run is reused; the WBF result folder is never overwritten.
cd /d %~dp0
title GP36 Stage 41b: WBF(C,v1) on ALLVAL - val only (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training or eval is running - not starting & goto end)
set D=review\alldata_v1\data_allval.yaml
set C=v3b_C_11n_960_s0_r2
set V1=v3a_r1_11n_960_s0
set OUT=review\alldata_v1\wbf_allval_C_v1
if exist %OUT% (echo %OUT% exists - refusing to overwrite & goto end)

echo ===== 1/3  C on ALLVAL (same command as run_alldata_1_val_visible.bat)   %date% %time%
if not exist runs\detect\%C%_ALLVAL\predictions.json (
  venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=%D% split=val imgsz=960 batch=8 save_json=True plots=False name=%C%_ALLVAL > runs\%C%_ALLVAL.txt 2>&1 || goto fail
) else (echo already done - reused)
echo ===== 2/3  v1 on ALLVAL (WBF input)   %date% %time%
if not exist runs\detect\%V1%_ALLVAL_WBFinput\predictions.json (
  venv\Scripts\yolo val model=runs\detect\%V1%\weights\best.pt data=%D% split=val imgsz=960 batch=8 save_json=True plots=False name=%V1%_ALLVAL_WBFinput > runs\%V1%_ALLVAL_WBFinput.txt 2>&1 || goto fail
) else (echo already done - reused)
echo ===== 3/3  WBF + scoring (C, v1, WBF; per source; with and without the 32 sr rad images)   %date% %time%
venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a5_wbf_allval.py --c runs\detect\%C%_ALLVAL\predictions.json --v1 runs\detect\%V1%_ALLVAL_WBFinput\predictions.json --out %OUT% > runs\WBF_C_v1_ALLVAL.txt 2>&1 || goto fail
type runs\WBF_C_v1_ALLVAL.txt
echo ---------------- Ultralytics lines (C, then v1) ----------------
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  "
%FS% runs\%C%_ALLVAL.txt
%FS% runs\%V1%_ALLVAL_WBFinput.txt
echo ================  DONE %date% %time%  ================
echo Results: %OUT%\metrics_WBF_ALLVAL.csv and summary.json ; text: runs\WBF_C_v1_ALLVAL.txt
goto end
:fail
echo ******** FAILED - see the last runs\*.txt log above. Nothing was overwritten. ********
:end
echo The window stays open.
pause
