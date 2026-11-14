@echo off
rem Stage 45 step A: list the CARD files and fetch the (tiny) label files only. NO images here (they need Ahmed's OK on size).
rem You will be asked for your Hugging Face READ token (hidden input, not saved). Get it at huggingface.co/settings/tokens
cd /d %~dp0
title GP36 Stage 45 A: CARD list + labels (do not close)
if not exist review\card_v1\card_index.csv (
  venv\Scripts\python.exe review\card_v1\card_fetch.py list || (echo LIST FAILED & goto end)
) else (echo card_index.csv already exists - list skipped)
venv\Scripts\python.exe review\card_v1\card_fetch.py labels || (echo LABEL DOWNLOAD FAILED & goto end)
venv\Scripts\python.exe review\card_v1\card_classcheck.py > review\card_v1\class_check.txt 2>&1
type review\card_v1\class_check.txt
echo ================  DONE %date% %time%  ================
:end
echo The window stays open. Send Claude a message when it says DONE.
pause
