@echo off
rem egm step 1 (7 Nov 2026): download the Cairo/Giza Mapillary tiles (~6.1 GB), build the labelling pool, leak check.
rem No training. No labels are made here. Nothing is deleted. Needs internet (huggingface.co), about 6.1 GB free.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo venv not found in %cd% & pause & exit /b 1)

echo === 1/3 download + extract (resumes if stopped; run again if it fails) ===
venv\Scripts\python -I tools\egm_download.py --tiles 390_375 391_375 --out ..\GP36_Dataset\raw_v3\egm
if errorlevel 1 (echo download failed - run this file again to resume & pause & exit /b 1)

echo === 2/3 labelling pool (split by creator, fixed before anyone looks) ===
if not exist review\new_data_r3\items\egm_pool.csv venv\Scripts\python -I tools\make_egm_pool.py --tiles ..\GP36_Dataset\raw_v3\egm --out review\new_data_r3\items\egm_pool.csv
if not exist review\new_data_r3\items\egm_pool.csv (echo pool not written & pause & exit /b 1)

echo === 3/3 leak check against all protected val/test/external images ===
venv\Scripts\python -I tools\leak_check.py ..\GP36_Dataset\raw_v3\egm review\new_data_r3\vet\egm\leak_egm.csv

echo.
echo Done. Pool: review\new_data_r3\items\egm_pool.csv   Leak: review\new_data_r3\vet\egm\leak_egm.csv
pause
