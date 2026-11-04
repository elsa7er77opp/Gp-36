@echo off
rem Stage 18: D2 on v3b_B after queue 2 has finished. One GPU job at a time.
cd /d %~dp0
:wait
%SystemRoot%\System32\findstr.exe /c:"QUEUE DONE" /c:"QUEUE STOPPED" runs\r3_queue2.log >nul || (ping -n 61 127.0.0.1 >nul & goto wait)
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (ping -n 61 127.0.0.1 >nul & goto wait)
set N=v3b_B_11n_960_s0
if exist runs\detect\%N% (echo %N% exists - refusing & exit /b 1)
echo === %N% start %date% %time%
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3b_B\data.yaml epochs=70 imgsz=960 batch=8 workers=2 cache=disk patience=20 seed=0 deterministic=True name=%N% > runs\%N%_train.log 2>&1
if errorlevel 1 (echo === %N% TRAIN FAILED & exit /b 1)
venv\Scripts\yolo val model=runs\detect\%N%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=%N%_VALr2_json > runs\%N%_VALr2_json.txt 2>&1
for %%P in (rsid bucko sr) do venv\Scripts\yolo val model=runs\detect\%N%\weights\best.pt data=parts_r3\%%P\data.yaml split=val imgsz=960 batch=8 save_json=True plots=False name=PARTVAL_%%P_%N% > runs\PARTVAL_%%P_%N%.txt 2>&1
echo === %N% done %date% %time%
echo === QUEUE DONE
