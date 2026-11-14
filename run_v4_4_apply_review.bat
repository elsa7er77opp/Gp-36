@echo off
rem Stage 39 step 4: road_hazards_v4_clean = road_hazards_v4_std without the train images marked bad in bad.txt.
cd /d %~dp0
title GP36 v4 step 4: apply the review
set PY=venv\Scripts\python -I
if exist road_hazards_v4_clean (
  echo road_hazards_v4_clean exists - refusing to overwrite
  goto end
)
set /p WHO=Who looked at the sheets? (type ahmed or claude): 
if "%WHO%"=="" goto end
%PY% tools\v4_review.py apply --data road_hazards_v4_std --review review\std_v4\review_sheets --out road_hazards_v4_clean --reviewed-by %WHO%
:end
pause
