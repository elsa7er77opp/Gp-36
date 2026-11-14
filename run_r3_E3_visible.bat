@echo off
rem Stage 38 (STATUS, written before any build or result): E3 = C's exact recipe + part egm
rem (eye-checked hazard-free egm TRAIN-creator frames as background). Val only - the test split is never used here.
rem One GPU job at a time; every tool refuses to overwrite; nothing is deleted.
cd /d %~dp0
title GP36 Stage 38: E3 = C + egm background (do not close)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & goto end)
if not exist review\new_data_r3\egm_labels\check_r38_done.txt (
  echo the Stage 38 eye check is not finished yet - not starting
  goto end
)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set G1=v3b_C2_11n_960_s0
set E3=v3b_C3_11n_960_s0
set PARTS=rsid bucko sr pol_v2 red_v2 ng8_v2 egy_v2
set IT=review\new_data_r3\items
set G=external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test parts_r3/bucko:val,test parts_r3/sr:val,test parts_r3/rdd_cz:test parts_r3/pol:val,test parts_r3/red:val,test parts_r3/ng8:val,test parts_r3/egy_v2:val,test
if exist runs\detect\%E3% (
  echo runs\detect\%E3% exists - refusing to overwrite
  goto end
)
echo ===== 1. items + part egm   %date% %time%
if not exist %IT%\items_egm.csv %PY% tools\egm_bg_items.py --out %IT%\items_egm.csv || goto fail
if not exist parts_r3\egm %PY% tools\build_part.py --items %IT%\items_egm.csv --part egm --out parts_r3/egm --guard %G% || goto fail
echo ===== 2. dataset road_hazards_v3b_C3 (C recipe + egm)
if not exist road_hazards_v3b_C3 %PY% tools\build_v3b.py --out road_hazards_v3b_C3 --parts parts_r3/rsid parts_r3/bucko parts_r3/rdd_ji:500 parts_r3/sr parts_r3/dmd parts_r3/pol_v2 parts_r3/red_v2 parts_r3/ng8_v2 parts_r3/hmpt parts_r3/ens parts_r3/egy_v2 parts_r3/bpo parts_r3/egm --drop-meta sr=family=rad || goto fail
echo ================================================================
echo  3. TRAINING %E3%   start %date% %time%
echo ================================================================
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3b_C3\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True optimizer=auto name=%E3%
if errorlevel 1 goto fail
echo ===== 4. val only   %date% %time%
venv\Scripts\yolo val model=runs\detect\%E3%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=True name=%E3%_VALr2_json > runs\%E3%_VALr2_json.txt 2>&1
%SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " /c:"Class " runs\%E3%_VALr2_json.txt
for %%P in (%PARTS%) do (
  venv\Scripts\yolo val model=runs\detect\%E3%\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%E3% > runs\PARTVAL_%%P_%E3%.txt 2>&1
  echo --- part-val %%P ---
  %SystemRoot%\System32\findstr.exe /r /c:"^ *all  " /c:"^ *pothole  " /c:"^ *speed_bump  " runs\PARTVAL_%%P_%E3%.txt
)
rem egm part val = hazard-free egm TRAIN-creator sequences held out of the part train (never eval creators)
for %%M in (%C% %G1% %E3%) do venv\Scripts\yolo val model=runs\detect\%%M\weights\best.pt data=parts_r3\egm\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_egm_%%M > runs\PARTVAL_egm_%%M.txt 2>&1
echo ===== 5. reports
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split val --care near --by source --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E3=runs\detect\%E3%_VALr2_json\predictions.json --out review\metrics_r3\val_r2_E3
for %%P in (%PARTS%) do %PY% tools\metrics_report.py --data parts_r3\%%P --split val --pred C=runs\detect\PARTVAL_%%P_%C%\predictions.json --pred E3=runs\detect\PARTVAL_%%P_%E3%\predictions.json --out review\metrics_r3\partval_%%P_E3
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split val --pred C=runs\detect\%C%_VALr2_json\predictions.json --pred E3=runs\detect\%E3%_VALr2_json\predictions.json --out review\metrics_r3\coco_val_r2_E3
for %%M in (C:%C% G1:%G1% E3:%E3%) do for /f "tokens=1,2 delims=:" %%a in ("%%M") do if not exist review\metrics_r3\thr_%%a_f1_E3stage.json %PY% tools\calibrate_thresholds.py --data road_hazards_v3a_r2 --split val --pred runs\detect\%%b_VALr2_json\predictions.json --model %%a --mode f1 --out review\metrics_r3\thr_%%a_f1_E3stage.json
%PY% tools\neg_fp_count.py --data parts_r3/egm --split val --model C runs\detect\PARTVAL_egm_%C%\predictions.json review\metrics_r3\thr_C_f1_E3stage.json --model G1 runs\detect\PARTVAL_egm_%G1%\predictions.json review\metrics_r3\thr_G1_f1_E3stage.json --model E3 runs\detect\PARTVAL_egm_%E3%\predictions.json review\metrics_r3\thr_E3_f1_E3stage.json --out review\metrics_r3\negfp_egm_E3
echo.
echo ================  ALL DONE %date% %time%  ================
goto end
:fail
echo === FAILED at %date% %time% (see the lines above)
:end
echo (window stays open; reports in review\metrics_r3\*_E3)
pause
