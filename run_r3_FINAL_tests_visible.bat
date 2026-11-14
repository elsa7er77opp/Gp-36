@echo off
rem FINAL test uses (STATUS Stage 32, written before this window): candidates C and WBF(C, v1), ONE use each on
rem r2 test and external BD87. Thresholds come from the val report; nothing is chosen here. Every tool refuses to overwrite.
cd /d %~dp0
title GP36 FINAL tests: C and WBF(C,v1) on r2 test + BD87 (do not close)
set PY=venv\Scripts\python -I
set C=v3b_C_11n_960_s0_r2
set V1=v3a_r1_11n_960_s0
set WBF=WBF_%C%+%V1%
set THR=review\metrics_r3\val_r2_final\report.json
set BD=external_tests\bd_speedbreaker_v2_orig87_eval.yaml

echo ================================================================
echo  0/4 LEDGER CHECK (all 4 pairs, before any test image is read)   %date% %time%
echo ================================================================
for %%B in (r2_test bd87) do (
  %PY% tools\test_ledger.py check --model %C% --benchmark %%B || goto fail
  %PY% tools\test_ledger.py check --model %WBF% --benchmark %%B || goto fail
)
for %%N in (%C%_TEST_r2_json %V1%_TEST_r2_WBFinput %C%_EXT_bd87_json %V1%_EXT_bd87_WBFinput) do if exist runs\detect\%%N (
  echo runs\detect\%%N exists - refusing
  goto fail
)

echo ================================================================
echo  1/4 PREDICTIONS on r2 test and BD87 (conf 0.001, as on val)
echo ================================================================
venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=test imgsz=960 batch=8 save_json=True plots=True name=%C%_TEST_r2_json > runs\%C%_TEST_r2_json.txt 2>&1 || goto fail
venv\Scripts\yolo val model=runs\detect\%V1%\weights\best.pt data=road_hazards_v3a_r2\data.yaml split=test imgsz=960 batch=8 save_json=True plots=False name=%V1%_TEST_r2_WBFinput > runs\%V1%_TEST_r2_WBFinput.txt 2>&1 || goto fail
venv\Scripts\yolo val model=runs\detect\%C%\weights\best.pt data=%BD% split=test imgsz=960 batch=8 save_json=True plots=True name=%C%_EXT_bd87_json > runs\%C%_EXT_bd87_json.txt 2>&1 || goto fail
venv\Scripts\yolo val model=runs\detect\%V1%\weights\best.pt data=%BD% split=test imgsz=960 batch=8 save_json=True plots=False name=%V1%_EXT_bd87_WBFinput > runs\%V1%_EXT_bd87_WBFinput.txt 2>&1 || goto fail
echo (v1-alone numbers in the *_WBFinput logs are WBF inputs only - not reported, not used)

echo ================================================================
echo  2/4 WBF (iou 0.55, skip 0.001, equal weights - same as val)
echo ================================================================
%PY% tools\wbf_ensemble.py --pred runs\detect\%C%_TEST_r2_json\predictions.json --pred runs\detect\%V1%_TEST_r2_WBFinput\predictions.json --out runs\detect\WBF_C_v1_TEST_r2\predictions.json || goto fail
%PY% tools\wbf_ensemble.py --pred runs\detect\%C%_EXT_bd87_json\predictions.json --pred runs\detect\%V1%_EXT_bd87_WBFinput\predictions.json --out runs\detect\WBF_C_v1_EXT_bd87\predictions.json || goto fail

echo ================================================================
echo  3/4 METRICS (val thresholds) and COCO
echo ================================================================
%PY% tools\metrics_report.py --data road_hazards_v3a_r2 --split test --care near --by source --thresholds %THR% --pred C=runs\detect\%C%_TEST_r2_json\predictions.json --pred WBF_C_v1=runs\detect\WBF_C_v1_TEST_r2\predictions.json --out review\metrics_r3\test_r2_final || goto fail
%PY% tools\coco_eval.py --data road_hazards_v3a_r2 --split test --allow-test --pred C=runs\detect\%C%_TEST_r2_json\predictions.json --pred WBF_C_v1=runs\detect\WBF_C_v1_TEST_r2\predictions.json --out review\metrics_r3\coco_test_r2_final || goto fail
%PY% tools\metrics_report.py --data external_tests\bd87_eval_view --split test --care near --thresholds %THR% --pred C=runs\detect\%C%_EXT_bd87_json\predictions.json --pred WBF_C_v1=runs\detect\WBF_C_v1_EXT_bd87\predictions.json --out review\metrics_r3\test_bd87_final || goto fail
%PY% tools\coco_eval.py --data external_tests\bd87_eval_view --split test --allow-test --pred C=runs\detect\%C%_EXT_bd87_json\predictions.json --pred WBF_C_v1=runs\detect\WBF_C_v1_EXT_bd87\predictions.json --out review\metrics_r3\coco_test_bd87_final || goto fail

echo ================================================================
echo  4/4 LEDGER ADD
echo ================================================================
%PY% tools\test_ledger.py add --model %C% --benchmark r2_test --stage "Stage 32" --source review/metrics_r3/test_r2_final/report.md --note "final candidate 1 (best single on r2 val); thresholds from val_r2_final; log runs/%C%_TEST_r2_json.txt"
%PY% tools\test_ledger.py add --model %WBF% --benchmark r2_test --stage "Stage 32" --source review/metrics_r3/test_r2_final/report.md --note "final candidate 2, WBF of top-two singles on r2 val; v1 test preds used only as WBF input, v1-alone not reported"
%PY% tools\test_ledger.py add --model %C% --benchmark bd87 --stage "Stage 32" --source review/metrics_r3/test_bd87_final/report.md --note "final candidate 1; scored via external_tests/bd87_eval_view; log runs/%C%_EXT_bd87_json.txt"
%PY% tools\test_ledger.py add --model %WBF% --benchmark bd87 --stage "Stage 32" --source review/metrics_r3/test_bd87_final/report.md --note "final candidate 2; v1 BD87 preds used only as WBF input (v1 alone = use 3)"
echo.
type review\metrics_r3\coco_test_r2_final\report.md
type review\metrics_r3\coco_test_bd87_final\report.md
echo ================  ALL DONE %date% %time%  ================
goto end

:fail
echo === STOPPED: a step failed or a check refused; nothing after it was run
:end
echo (window stays open; reports in review\metrics_r3\test_*_final and coco_test_*_final)
