@echo off
rem Stage 39 step 3: sheets of EVERY train image of road_hazards_v4_std with the boxes drawn, for the eye review.
cd /d %~dp0
title GP36 v4 step 3: review sheets
set PY=venv\Scripts\python -I
if not exist road_hazards_v4_std\manifest.csv (
  echo road_hazards_v4_std not built yet - run run_v4_2_build.bat first
  goto end
)
%PY% tools\v4_review.py sheets --data road_hazards_v4_std --out review\std_v4\review_sheets
echo.
echo Open review\std_v4\review_sheets\sheet_0001.jpg ... and write the BAD cells in bad.txt, for example:
echo     0012: 3 7
echo     SOURCE ens
echo When every sheet is done, write DONE on the last line of bad.txt.
:end
pause
