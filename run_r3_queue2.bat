@echo off
rem Stage 17 queue (review/clean_r2/STATUS_for_claude.md). One GPU job at a time; refuses to reuse a run name.
cd /d %~dp0
tasklist /fi "imagename eq yolo.exe" | find /i "yolo.exe" >nul && (echo a yolo process is running - refusing & exit /b 1)
call :run v3b_A_11n_960_s1 960 "seed=1" || goto fail
call :run v3b_A_11n_1280_s0 1280 "seed=0" || goto fail
echo === QUEUE DONE %date% %time%
exit /b 0

:run
if exist runs\detect\%1 (
  echo runs\detect\%1 exists - refusing
  exit /b 1
)
echo === %1 start %date% %time%
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3b_A\data.yaml epochs=70 imgsz=%2 batch=8 workers=2 cache=disk patience=20 deterministic=True name=%1 %~3 > runs\%1_train.log 2>&1
if errorlevel 1 (
  echo === %1 TRAIN FAILED
  exit /b 1
)
venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=%2 batch=8 save_json=True plots=False name=%1_VALr2_json > runs\%1_VALr2_json.txt 2>&1
for %%P in (rsid bucko) do venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=%2 batch=8 save_json=True plots=False name=PARTVAL_%%P_%1 > runs\PARTVAL_%%P_%1.txt 2>&1
echo === %1 done %date% %time%
exit /b 0

:fail
echo === QUEUE STOPPED
exit /b 1
