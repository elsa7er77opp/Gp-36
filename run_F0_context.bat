@echo off
setlocal
cd /d "%~dp0"
title GP36 F0 context collection
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -I "tools\collect_f0_context.py" --root "%CD%"
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -I "tools\collect_f0_context.py" --root "%CD%"
) else (
  echo Project Python not found. Run this with your training Python:
  echo python tools\collect_f0_context.py
  goto end
)
if errorlevel 1 (
  echo FAILED. Send the error text.
) else (
  echo Send the newest ZIP from review\f0_context
)
:end
pause
endlocal
