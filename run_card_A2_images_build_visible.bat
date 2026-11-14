@echo off
rem Stage 45 step A2 (after run_card_A): download the cam_1 images of the 15,368 LABELLED frames only (7.41 GB, measured
rem from the HF listing), then class check sheets, route split, build road_hazards_card_v1 (images resized to 960, every 2nd
rem labelled frame). NO empty frames as negatives (CARD labels only 40%% of the frames that contain an irregularity, so an empty
rem label file does not mean an empty road). Asks for your READ token once (hidden, not saved). Resumable: just run it again.
cd /d %~dp0
title GP36 Stage 45 A2: CARD images + build (do not close)
if not exist review\card_v1\card_index.csv (echo run run_card_A_list_labels_visible.bat first & goto end)
venv\Scripts\python.exe review\card_v1\card_fetch.py images 0 || (echo IMAGE DOWNLOAD STOPPED - run this bat again to resume & goto end)
if not exist review\card_v1\class_check_done.txt (
  venv\Scripts\python.exe review\card_v1\card_classcheck.py > review\card_v1\class_check_after_images.txt 2>&1
  type review\card_v1\class_check_after_images.txt
  echo done> review\card_v1\class_check_done.txt
)
if not exist review\card_v1\split_groups.csv venv\Scripts\python.exe review\card_v1\card_build.py split
venv\Scripts\python.exe review\card_v1\card_build.py build --map 0:0,1:1 --resize 960 --step 2
echo ================  DONE %date% %time%  ================
:end
echo The window stays open.
pause
