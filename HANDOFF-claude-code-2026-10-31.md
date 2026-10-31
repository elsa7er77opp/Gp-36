# GP36 – Handoff for Claude Code (31 Oct 2026, 13:45)

You are continuing GP36 (Perception Pod, Project #36, student Ahmed Elreefy, supervisor Dr. Peter Makeen). Working folder: C:\Users\ahmed\Desktop\GP36_AI (Windows, RTX 5050, use venv\Scripts\python / venv\Scripts\yolo, Ultralytics 8.4.192). Raw data: C:\Users\ahmed\Desktop\GP36_Dataset. Talk to Ahmed in Egyptian Arabic.

## Rules (do not break)
1. No training, deleting or changing data without Ahmed's explicit OK. (Run A and the r2 build below are ALREADY approved.)
2. Each model is evaluated on the test set ONCE only. Model choice is made on val.
3. No invented numbers: every number you report must come from an output file (results.csv, the yolo val printout, summary json) and you say which file.
4. Fix, don't restart: never overwrite r1 or any existing dataset/run; new versions go to new folders.
5. Read HANDOFF-2026-10-31.md in this folder first for full rules and history.

## State at handoff
- Detector frozen at YOLO11n v1 = runs/detect/v3a_r1_11n_960_s0/weights/best.pt (v3a_r1: val mAP50 0.636; test mAP50 0.507, pothole 0.660, speed bump 0.354).
- Live pipeline written (detect_stream.py, perception/), 26 tests pass, not yet run on a camera.
- Cleaning round 2 done and APPROVED: review/clean_r2/corrections.csv (made by write_corrections.py). Builder tools/build_v3a_r2.py (dry run: train 3,035 / val 830 / test 323; train -103 pothole boxes, -9 bump boxes, 8 images dropped; val -58 pothole boxes, 2 pothole->bump, 40 images dropped; test -1 image IMG_4581 wrong rotation, approved).
- run_r2_step2.bat (approved) does: build r2 with --drop-test-image -> strict verify -> v1 val on corrected val (name=v3a_r1_11n_VAL_on_r2) -> Run A train (v3a_r2_11n_960_s0, same settings as v1: yolo11n.pt, epochs 150, imgsz 960, batch 8, workers 2, cache disk, patience 30, seed 0, deterministic).

## Your tasks, in order
1. Check what already ran: does road_hazards_v3a_r2 exist (read build_info.json fingerprint)? Do runs/detect/v3a_r1_11n_VAL_on_r2 and runs/detect/v3a_r2_11n_960_s0 exist? If the bat has not been run, run it (approved). If a step failed, read the error, fix the cause, rerun only from that step.
2. When Run A finishes: compare on the CORRECTED val: v1 (v3a_r1_11n_VAL_on_r2) vs Run A:
   venv\Scripts\yolo val model=runs\detect\v3a_r2_11n_960_s0\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=val imgsz=960 batch=8 name=v3a_r2_11n_VAL
   Report mAP50, mAP50-95, per-class P/R/mAP50 from the printouts.
3. Test Run A ONCE:
   venv\Scripts\yolo val model=runs\detect\v3a_r2_11n_960_s0\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=test imgsz=960 batch=8 name=v3a_r2_11n_960_s0_TEST
   Note: r2 test = r1 test minus 1 image, so v1's 0.507 is not exactly comparable. Do NOT re-test v1 on the r2 test without asking Ahmed.
4. New data: Ahmed is downloading datasets into GP36_Dataset\_downloads\<one folder per dataset> (YOLOv8 format). For each, read-only: count images/labels, class names, licence (README / data.yaml), exact duplicates (SHA-256) and near-duplicates vs GP36_Dataset sources and road_hazards_v3a_r2 (use gp36data.dedup / tools/run_forensics.py), look at ~30 samples by eye with boxes drawn, check against rules D1-D6 + FAR_TINY (audit/CLASS_MAPPING.md). Then PROPOSE (do not build) v3a_r2b = r2 + new clean speed-bump data in TRAIN only, with BD_speedbreaker kept apart as an unseen-bump test. Wait for Ahmed's OK before building or training Run B.
5. Write everything into review/clean_r2/STATUS_for_claude.md (what ran, exact numbers with their source files, errors and fixes, open decisions) so the next session can continue from it.
