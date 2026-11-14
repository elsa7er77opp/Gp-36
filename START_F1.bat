@echo off
setlocal
cd /d "%~dp0"
title GP36 F1 mosaic experiment
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -I "tools\run_f1_mosaic.py" --execute
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -I "tools\run_f1_mosaic.py" --execute
) else (
  echo Training Python not found in venv or .venv.
  goto end
)
if errorlevel 1 (
  echo STOPPED. Send the error or review\f1_mosaic02\GP36_F1_results.zip if created.
) else (
  echo DONE. Send review\f1_mosaic02\GP36_F1_results.zip
)
:end
pause
endlocal
