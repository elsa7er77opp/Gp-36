@echo off
rem Free disk space: removes the Ultralytics cache=disk .npy files from road_hazards_*\images (rebuildable cache only).
rem Images, labels, manifests, checksums, runs and weights are never touched. Log: review\disk_cleanup_<date>.csv
rem Do NOT run while a training is running (it reads that cache).
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo venv not found in %cd% & pause & exit /b 1)
if not exist tools\clean_npy_cache.py (echo tools\clean_npy_cache.py not found & pause & exit /b 1)

echo === Dry run (nothing is deleted) ===
venv\Scripts\python -I tools\clean_npy_cache.py
if errorlevel 1 (echo dry run failed & pause & exit /b 1)

echo.
choice /c YN /m "Delete the cache files listed above"
if errorlevel 2 (echo Cancelled - nothing deleted. & pause & exit /b 0)

venv\Scripts\python -I tools\clean_npy_cache.py --delete
echo.
pause
