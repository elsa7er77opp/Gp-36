@echo off
title GP36 egm: rank train-creator frames with C (no labels written)
rem STATUS Stage 37b. GPU job (inference only, no training). Eval-creator frames are never run through the model.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo venv not found & pause & exit /b 1)
venv\Scripts\python -I tools\egm_mine_candidates.py --tiles ..\GP36_Dataset\raw_v3\egm --pool review\new_data_r3\items\egm_pool.csv --weights runs\detect\v3b_C_11n_960_s0_r2\weights\best.pt --out review\new_data_r3\vet\egm\mine_C_train.csv
echo.
echo === DONE %date% %time%
pause
