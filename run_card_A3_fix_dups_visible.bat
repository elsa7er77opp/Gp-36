@echo off
rem Stage 45g: remove near-duplicate leakage between splits (same road on two sequences). Read-only on road_hazards_card_v1,
rem builds road_hazards_card_v2 with a new route split where linked sequences stay together. No token needed.
cd /d %~dp0
title GP36 Stage 45g: fix near-duplicates (do not close)
venv\Scripts\python.exe review\card_v1\card_fix_dups.py
echo ================  DONE %date% %time%  ================
pause
