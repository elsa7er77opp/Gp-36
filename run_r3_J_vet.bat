@echo off
rem Round r3 section J (7 Nov 2026): vet two Roboflow speed-bump candidates. Download + mechanical vet only.
rem Nothing is trained, nothing is added to any dataset, val/test untouched. Needs the PRIVATE Roboflow key
rem (ROBOFLOW_API_KEY or %USERPROFILE%\.roboflow\api_key). Contact sheets go OUTSIDE git (..\GP36_Dataset\vet_sheets).
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo venv not found in %cd% & pause & exit /b 1)
if not exist ..\GP36_Dataset\vet_sheets mkdir ..\GP36_Dataset\vet_sheets

echo === J1 bump-catcf (frame_inv_*, 640x240) ===
if not exist ..\GP36_Dataset\raw_v3\rf_bumpcatcf venv\Scripts\python -I tools\rf_download.py refyy-i/bump-catcf-fawye 1 ..\GP36_Dataset\raw_v3\rf_bumpcatcf
venv\Scripts\python -I tools\vet_source.py --name bcf --root ..\GP36_Dataset\raw_v3\rf_bumpcatcf\x --out review\new_data_r3\vet\bcf --sheet ..\GP36_Dataset\vet_sheets\sheet_bcf.jpg

echo === J2 hump-16nup (Hump class only is relevant) ===
if not exist ..\GP36_Dataset\raw_v3\rf_hump16 venv\Scripts\python -I tools\rf_download.py refyy-i/hump-16nup-4bmvs 1 ..\GP36_Dataset\raw_v3\rf_hump16
venv\Scripts\python -I tools\vet_source.py --name h16 --root ..\GP36_Dataset\raw_v3\rf_hump16\x --out review\new_data_r3\vet\h16 --sheet ..\GP36_Dataset\vet_sheets\sheet_h16.jpg

echo.
echo Done. Results: review\new_data_r3\vet\bcf\vet.md and vet\h16\vet.md ; sheets in ..\GP36_Dataset\vet_sheets
pause
