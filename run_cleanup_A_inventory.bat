@echo off
rem Cleanup step A: READ-ONLY size inventory of GP36_AI (nothing is deleted here). Result: review\cleanup_2026-11-13\inventory.csv
cd /d %~dp0
title GP36 cleanup A: inventory (read-only)
venv\Scripts\python.exe review\cleanup_2026-11-13\inventory.py
echo ================  DONE %date% %time%  ================
pause
