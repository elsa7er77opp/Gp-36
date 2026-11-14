@echo off
rem Stage 45h: PLACE-level split of CARD + ORB leak check -> road_hazards_card_v3 (read-only on v1). No token needed.
cd /d %~dp0
title GP36 Stage 45h: place split + leak check (do not close)
venv\Scripts\python.exe review\card_v1\card_place_split.py
echo ================  DONE %date% %time%  ================
pause
