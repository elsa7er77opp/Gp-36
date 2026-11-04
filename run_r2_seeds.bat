@echo off
rem H-seed (review/clean_r2/STATUS_for_claude.md): seeds 1 and 2 of the Run A config, one after the other.
rem Variance only: these runs do not replace the r2 candidate and are never evaluated on test.
rem 31 Oct 23:05: seed 1 was interrupted at epoch 30 (window closed). Now: a seed with a VAL result is skipped,
rem an interrupted seed is RESUMED from its own last.pt (nothing overwritten), a missing seed is started.
cd /d %~dp0
for %%S in (1 2) do call :seed %%S || goto fail
echo === DONE
pause
exit /b 0

:seed
set S=%1
set R=runs\detect\v3a_r2_11n_960_s%S%
if exist runs\v3a_r2_11n_960_s%S%_VAL.txt (
  echo === seed %S% already finished - skipped
  exit /b 0
)
if exist %R%\weights\last.pt (
  echo === seed %S% resume from last.pt %date% %time%
  venv\Scripts\yolo train resume model=%R%\weights\last.pt
) else (
  if exist %R% (
    echo %R% exists without last.pt - refusing to overwrite
    exit /b 1
  )
  echo === seed %S% start %date% %time%
  venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3a_r2\data.yaml epochs=150 imgsz=960 batch=8 workers=2 cache=disk patience=30 seed=%S% deterministic=True name=v3a_r2_11n_960_s%S%
)
if errorlevel 1 exit /b 1
venv\Scripts\yolo val model=%R%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 name=v3a_r2_11n_960_s%S%_VAL > runs\v3a_r2_11n_960_s%S%_VAL.txt 2>&1
if errorlevel 1 exit /b 1
echo === seed %S% done %date% %time%
exit /b 0

:fail
echo === STOPPED: a step failed, nothing after it was run
pause
exit /b 1
