@echo off
cd /d %~dp0
echo === 1/4 build road_hazards_v3a_r2 (approved 2026-10-31, incl. test IMG_4581 drop)
if exist road_hazards_v3a_r2\build_info.json (
  echo road_hazards_v3a_r2 already built and verified by the builder - build skipped
) else (
  venv\Scripts\python tools\build_v3a_r2.py --drop-test-image
  if errorlevel 1 goto fail
)
echo === 2/4 strict verify
venv\Scripts\python tools\verify_dataset.py road_hazards_v3a_r2 --no-near-dups
if errorlevel 1 goto fail
echo === 3/4 v1 model evaluated on the corrected val (eval only, no training)
venv\Scripts\yolo val model=runs\detect\v3a_r1_11n_960_s0\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 name=v3a_r1_11n_VAL_on_r2
if errorlevel 1 goto fail
echo === 4/4 Run A: same settings as v1, corrected labels (about 2.5-3 h)
venv\Scripts\yolo train model=yolo11n.pt data=road_hazards_v3a_r2\data.yaml epochs=150 imgsz=960 batch=8 workers=2 cache=disk patience=30 seed=0 deterministic=True name=v3a_r2_11n_960_s0
if errorlevel 1 goto fail
echo === DONE
goto end
:fail
echo === STOPPED: a step failed, nothing after it was run
:end
pause
