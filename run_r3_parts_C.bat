@echo off
rem Items + parts for the cloud-PR-2 sources (CLOUD_REPORT.md section 3, steps 2-3; STATUS Stage 23).
rem CPU/RAM job: run only when no training is running. Every tool refuses to overwrite.
cd /d %~dp0
%SystemRoot%\System32\tasklist.exe /fi "imagename eq yolo.exe" | %SystemRoot%\System32\find.exe /i "yolo.exe" >nul && (echo a training is running - not starting & exit /b 1)
set PY=venv\Scripts\python -I
set RAW=..\GP36_Dataset\raw_v3
set IT=review\new_data_r3\items
%PY% tools/make_items_dmdruid.py --src %RAW%\github_dmdruid_speedbumps --out %IT%/items_dmd.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_polisi\x --part pol --cmap "{\"0\": \"speed_bump\", \"1\": \"speed_bump\"}" --block 50 --include "frame_\d*[02468]" --out %IT%/items_pol.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_reductor\x --part red --cmap "{\"0\": \"ignore\", \"1\": \"ignore\", \"2\": \"ignore\", \"3\": \"speed_bump\"}" "--group-regex=-frame_(VID_\d{8}_\d{6}|\d{3})" --out %IT%/items_red.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_ng8ne\x --part ng8 --cmap "{\"0\": \"speed_bump\"}" --include "(VID_\d+_\d+_frame_\d+|IMG_\d+_\d+(_\d+)?)" --group-regex "(VID_\d{8}_\d{6}|IMG_\d{8})" --out %IT%/items_ng8.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_humps\x --part hmp --cmap "{\"0\": \"ignore\", \"1\": \"speed_bump\", \"2\": \"ignore\", \"3\": \"pothole\", \"4\": \"ignore\"}" --include "humps-v\d+-_\d+" --out %IT%/items_hmp.csv
%PY% tools/make_items_egyrdd.py --src %RAW%\rf_egyrdd\x --out %IT%/items_egy.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_ensam\x --part ens --cmap "{\"0\": \"speed_bump\", \"1\": \"speed_bump\"}" --include "[0-9]{3,}" --all-train --out %IT%/items_ens.csv
set G=external_tests/bd_speedbreaker_v2_orig87 parts_r3/rsid:val,test parts_r3/bucko:val,test parts_r3/sr:val,test parts_r3/rdd_cz:test
for %%P in (dmd pol red ng8 hmp egy ens) do (
  echo ===== part %%P
  %PY% tools/build_part.py --items %IT%/items_%%P.csv --part %%P --out parts_r3/%%P --guard %G%
)
rem cloud session 3 (CLOUD_REPORT.md 0-S3, STATUS Stage 24): egy_v2 (audited boxes removed), hmpt (hmp train-only), bpo
echo ===== part egy_v2
%PY% tools/apply_box_corrections.py --part parts_r3/egy --audit review/new_data_r3/vet/egy/box_audit.csv --out parts_r3/egy_v2
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_humps\x --part hmpt --cmap "{\"0\": \"ignore\", \"1\": \"speed_bump\", \"2\": \"ignore\", \"3\": \"pothole\", \"4\": \"ignore\"}" --include "humps-v\d+-_\d+" --all-train --out %IT%/items_hmpt.csv
%PY% tools/make_items_yolo_export.py --root %RAW%\rf_bharat\x --part bpo --cmap "{\"0\": \"pothole\"}" --include ".*_frame_\d*[02468]" "--group-regex=^(\d{14}_\d{4}|signal-[\d-]+-\d{6}(?:_\d{3})?)" --out %IT%/items_bpo.csv
rem the later parts are also guarded against the new parts' val/test
set G2=%G% parts_r3/pol:val,test parts_r3/red:val,test parts_r3/ng8:val,test parts_r3/egy_v2:val,test
for %%P in (hmpt bpo) do (
  echo ===== part %%P
  %PY% tools/build_part.py --items %IT%/items_%%P.csv --part %%P --out parts_r3/%%P --guard %G2%
)
rem cloud session 4 (CLOUD_REPORT.md 0-S4, STATUS Stage 25): audited decision part-vals pol_v2, red_v2, ng8_v2
for %%P in (pol ng8 red) do (
  echo ===== part %%P_v2
  %PY% tools/apply_box_corrections.py --part parts_r3/%%P --audit review/new_data_r3/vet/%%P/box_audit.csv --drop-images review/new_data_r3/vet/%%P/valtest_missing_labels.csv --out parts_r3/%%P_v2
)
echo ===== parts done %date% %time%
