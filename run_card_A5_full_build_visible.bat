@echo off
rem Stage 45j: FULL CARD build (all 15,368 labelled frames, no frame skipping), PLACE split of Stage 45h, images resized to 960,
rem then the ORB leak check. Output road_hazards_card_v4. No token needed. Resumable: run again if it stops.
cd /d %~dp0
title GP36 Stage 45j: full CARD build + leak check (do not close)
venv\Scripts\python.exe review\card_v1\card_prefill_v4.py || goto end
venv\Scripts\python.exe review\card_v1\card_build.py build --map 0:0,1:1 --resize 960 --split split_place.csv --out road_hazards_card_v4 --report build_report_v4.json --no-dhash || goto end
venv\Scripts\python.exe review\card_v1\card_leakcheck.py road_hazards_card_v4
echo ================  DONE %date% %time%  ================
:end
pause
