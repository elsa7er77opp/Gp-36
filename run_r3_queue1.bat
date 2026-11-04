@echo off
rem Stage 12 queue (review/clean_r2/STATUS_for_claude.md). One GPU job at a time; refuses to reuse a run name.
cd /d %~dp0
:waitd1
rem ping as a sleep: works the same whatever "timeout" is first on PATH (Git's coreutils shadowed it once)
if not exist runs\PARTVAL_bucko_v3bA_s0.txt (
  ping -n 61 127.0.0.1 >nul
  goto waitd1
)
tasklist /fi "imagename eq yolo.exe" | find /i "yolo.exe" >nul && (ping -n 61 127.0.0.1 >nul & goto waitd1)
call :run v3b_A_11n_960_bumponly_s0 yolo11n.pt "classes=[1]" || goto fail
call :run v3b_A_11n_960_potonly_s0 yolo11n.pt "classes=[0]" || goto fail
call :run v3b_A_11s_960_s0 yolo11s.pt "" || goto fail
echo === QUEUE DONE %date% %time%
exit /b 0

:run
if exist runs\detect\%1 (
  echo runs\detect\%1 exists - refusing
  exit /b 1
)
echo === %1 start %date% %time%
venv\Scripts\yolo train model=%2 data=road_hazards_v3b_A\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True name=%1 %~3 > runs\%1_train.log 2>&1
if errorlevel 1 (
  echo === %1 TRAIN FAILED
  exit /b 1
)
venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%1_VALr2_json > runs\%1_VALr2_json.txt 2>&1
for %%P in (rsid bucko) do venv\Scripts\yolo val model=runs\detect\%1\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%1 > runs\PARTVAL_%%P_%1.txt 2>&1
echo === %1 done %date% %time%
exit /b 0

:fail
echo === QUEUE STOPPED
exit /b 1
