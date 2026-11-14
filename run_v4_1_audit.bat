@echo off
rem Stage 39 step 1: AUDIT only. Reads road_hazards_v3b_C and writes a report. Nothing is built or trained.
cd /d %~dp0
title GP36 v4 step 1: pattern audit (read-only)
set PY=venv\Scripts\python -I
if exist review\std_v4\audit (
  echo review\std_v4\audit exists - refusing to overwrite. Rename the old folder first.
  goto end
)
%PY% tools\std_dataset.py audit --src road_hazards_v3b_C --out review\std_v4\audit --unstretch sb15=1.7778
echo.
echo Report: review\std_v4\audit\audit.md  (per image: audit.csv)
:end
pause
