@echo off
rem Stage 41 step 1 (rule written in STATUS before this run): evaluate C, A1 and F1u on ALLVAL
rem (r2 val + val splits of rsid, bucko, sr, pol_v2, red_v2, ng8_v2, egy_v2 = 1,754 images). VAL ONLY - no test here.
rem Safe to run again: a model whose ALLVAL result exists is skipped. F1u is skipped until its training has finished.
cd /d %~dp0
title GP36 Stage 41: all-sources VAL (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training or eval is running - not starting & goto end)
set D=review\alldata_v1\data_allval.yaml
set FS=%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  "
for %%M in (v3b_C_11n_960_s0_r2 v5_all_11n_960_s0 v5_u4k_11n_960_s0) do (
  if exist runs\detect\%%M\weights\best.pt (
    if not exist runs\detect\%%M_ALLVAL (
      echo ===== %%M on ALLVAL   %date% %time%
      venv\Scripts\yolo val model=runs\detect\%%M\weights\best.pt data=%D% split=val imgsz=960 batch=8 save_json=True plots=False name=%%M_ALLVAL > runs\%%M_ALLVAL.txt 2>&1
    ) else (echo %%M already done)
  ) else (echo %%M has no best.pt yet - skipped)
)
echo ---------------- RESULT - ALLVAL (val only) ----------------
for %%M in (v3b_C_11n_960_s0_r2 v5_all_11n_960_s0 v5_u4k_11n_960_s0) do (
  if exist runs\%%M_ALLVAL.txt (
    echo --- %%M ---
    %FS% runs\%%M_ALLVAL.txt
  )
)
echo ================  DONE %date% %time%  ================
:end
echo The window stays open. Text results are in runs\*_ALLVAL.txt
pause
