@echo off
rem H-seed (review/clean_r2/STATUS_for_claude.md): seeds 1 and 2 of the Run A config, one after the other.
rem Variance only: these runs do not replace the r2 candidate and are never evaluated on test.
cd /d %~dp0
for %%S in (1 2) do (
  if exist runs\detect\v3a_r2_11n_960_s%%S (
    echo runs\detect\v3a_r2_11n_960_s%%S exists - refusing to overwrite
    goto fail
  )
  echo === seed %%S start %date% %time%
  venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3a_r2\data.yaml epochs=150 imgsz=960 batch=8 workers=2 cache=disk patience=30 seed=%%S deterministic=True name=v3a_r2_11n_960_s%%S
  if errorlevel 1 goto fail
  venv\Scripts\yolo val model=runs\detect\v3a_r2_11n_960_s%%S\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 name=v3a_r2_11n_960_s%%S_VAL > runs\v3a_r2_11n_960_s%%S_VAL.txt 2>&1
  if errorlevel 1 goto fail
  echo === seed %%S done %date% %time%
)
echo === DONE
exit /b 0
:fail
echo === STOPPED: a step failed, nothing after it was run
exit /b 1
