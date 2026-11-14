@echo off
rem egm step 2: hand labelling on this laptop (no upload, no model). Eval pool first (must be labelled completely).
rem Keys: 1 pothole, 2 speed_bump, drag = box, SPACE next, U unsure, X unusable, Z undo, B back, +/- zoom, Q quit.
rem Rules: audit\CLASS_MAPPING.md (D1-D6). Unmarked asphalt humps ARE speed_bump. Resume any time.
cd /d "%~dp0"
if not exist review\new_data_r3\items\egm_pool.csv (echo run run_egm_step1.bat first & pause & exit /b 1)
choice /c ET /m "Label which pool: E = eval (do this first), T = train"
if errorlevel 2 (venv\Scripts\python -I tools\egm_label.py --pool train) else (venv\Scripts\python -I tools\egm_label.py --pool eval)
pause
