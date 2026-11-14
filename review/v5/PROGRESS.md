# Stage 40 label fixing — progress (labeller = claude, AI labels; no model output used)

- Build check (2026-11-11): `road_hazards_v5_all` train 10,562 / val 830 / test 323; all 11,715 images 960x720;
  train boxes pothole 6,968, speed_bump 3,982 (same as `road_hazards_v3b_C`); val/test label text identical to `road_hazards_v4_std`.
- `todo.csv`: bad_in_review 1,599, not_reviewed 3,894, accepted (not listed) 5,069 -> 5,493 images, 916 sheets (`review/v5/sheets`).
- Files: `fixes.jsonl` (one line per changed image), `unsure.csv` (image,sheet,cell,reason).
- How to resume: continue from the first sheet after the last "sheets done" line below.

## Batches
- 2026-11-11 batch 1: sheets 0001-0010 done (60 images, all bpo bad_in_review). Fixes so far: 9 images (all to no-box: kerb, expansion joint, roadside drain/ditch/dirt). Unsure so far: 39. Rest left unchanged.
  Method: every 6-image sheet is read; full-size pairs with the 10 % grid (`review/v5/pairs/pNNNNa-c.jpg`) are made when a box cannot be judged on the sheet.
- 2026-11-12 batch 2: sheets 0011-0020 done (bpo bad_in_review). Totals after sheet 0020: 120 images looked at, 18 fixed (17 to no-box, 1 kept 2 of 4 boxes), 83 unsure rows, rest unchanged.
  Puddle rule (Ahmed, in chat, 12 Nov): a puddle on the asphalt or at its edge stays a pothole; a puddle on the dirt shoulder off the road, or a water sheen on a sound road, loses its box.
  A1 finished: v5 val all 0.649 / pothole 0.622 / bump 0.677 (C: 0.674 / 0.626 / 0.722), from runs/*_VALv5.txt. GPU idle. Next sheet: 0021.
- 2026-11-12 batch 3: sheets 0021-0040 done (bpo bad_in_review). Totals after sheet 0040: 240 images looked at, 29 fixed, 182 unsure rows, rest unchanged. Next sheet: 0041.
- 2026-11-12 batch 4: sheets 0041-0060 done (bpo bad_in_review). Next sheet: 0061.
- 2026-11-12 batch 5: sheets 0061-0076 done. bpo is finished (sheets 0001-0074, 442 images); bucko started (night frames logged as unsure). Totals after sheet 0076: 456 images looked at, 44 fixed, 326 unsure rows. Next sheet: 0077.
  Source ranges (sheet numbers): bpo 1-74, bucko 74-82, dmd 82-106, egy 106-201, ens 201-269, ghpot 270-284, hmpt 284-335, ng8 336-382, pol 382-409, rdd_ji 409-493, red 493-548, rf8 548-631, rsid 631-654, sb15 654-805, sr 806-916.
- 2026-11-12 batch 6: sheets 0077-0106 done. bucko finished (night frames -> unsure), dmd finished (boxes correct; 2 images got a missing second-bump box). Totals after sheet 0106: 636 images looked at, 46 fixed, 352 unsure rows. Next sheet: 0107 (egy).
- 2026-11-12 batch 7: sheets 0107-0114 done (egy bad_in_review). Totals after sheet 0114: 684 images looked at, 49 fixed, 373 unsure rows, rest unchanged. Next sheet: 0115 (egy runs to 0201).
  STOPPED here (usage limit). Not done yet: sheets 0115-0916, apply -> road_hazards_v5_fixed, 30 spot-check views, STATUS Stage 40a. A1 result is not yet written in STATUS either.
  Helper scripts used (session scratchpad, may be gone): log.py (appends to fixes.jsonl / unsure.csv from sheet/cell keys), pairs.py (full-size pairs). fixes.jsonl and unsure.csv are complete up to sheet 0114.
- 2026-11-12 batch 8: sheets 0115-0146 done (egy bad_in_review). Totals after sheet 0146: 876 images looked at, 59 fixed, 415 unsure rows. Next sheet: 0147.
- 2026-11-12 batch 9: sheets 0147-0166 done (egy; not_reviewed part starts at sheet 0149). Totals after sheet 0166: 996 images looked at, 59 fixed, 453 unsure rows. Next sheet: 0167.
- 2026-11-12 batch 10: sheets 0167-0175 done (egy not_reviewed). Totals after sheet 0175: 1,050 images looked at, 60 fixed, 473 unsure rows. Next sheet: 0176 (egy runs to 0201).
  STOPPED here (usage limit). Not done yet: sheets 0176-0916, apply -> road_hazards_v5_fixed, 30 spot-check views, STATUS Stage 40a (and the A1 result is not yet in STATUS).
- 2026-11-12 batch 11: sheets 0176-0201 done; egy is finished (sheets 0106-0201, 569 images). Totals after egy (image 3 of sheet 0201): 1,203 images looked at, 60 fixed, 543 unsure rows. Next: ens (sheets 0201/4 - 0269).
  ens rule (Ahmed, in chat, 12 Nov): boxes on painted (white-striped) speed bumps in ens stay as they are; only a clearly misplaced box or a box on a clear pedestrian crossing is changed.
- 2026-11-12 sheets done 0201 (cells 4-6)-210; 1260 images looked at, 66 images fixed so far, 543 unsure so far. Next sheet: 211.
- 2026-11-12 sheets done 211-220; 1320 images looked at, 77 images fixed so far, 543 unsure so far. Next sheet: 221.
  Codex re-review (owner delegated judgment): standing water alone is insufficient; keep a pothole box when a visible broken rim or depression supports it. Ambiguous surfaces stay unsure. Historical unsure rows are preserved; outcomes in unsure_recheck_codex.csv. New fixes carry fixed_by=codex.
  Codex unsure re-review through 0010/6: 39/543 checked, 20 fixed, 19 still unsure, 0 confirmed unchanged. Total fixed 97; outstanding unsure 523. Resume unsure at 0011/2; forward sheet 0221.
  Codex unsure re-review through 0020/6: 83/543 checked, 46 fixed, 35 still unsure, 2 confirmed unchanged. Total fixed 123; outstanding unsure 495. Resume unsure at 0021/1; forward sheet 0221.
  Codex unsure re-review through 0030/6: 134/543 checked, 62 fixed, 67 still unsure, 5 confirmed unchanged. Total fixed 139; outstanding unsure 476. Resume unsure at 0031/1; forward sheet 0221.
  Codex unsure re-review through 0040/6: 182/543 checked, 76 fixed, 100 still unsure, 6 confirmed unchanged. Total fixed 153; outstanding unsure 461. Resume unsure at 0041/1; forward sheet 0221.
  Codex unsure re-review through 0045/6: 207/543 checked, 78 fixed, 123 still unsure, 6 confirmed unchanged. Total fixed 155; outstanding unsure 459. Resume unsure at 0046/1; forward sheet 0221.
  Codex unsure re-review through 0055/6: 257/543 checked, 86 fixed, 163 still unsure, 8 confirmed unchanged. Total fixed 163; outstanding unsure 449. Resume unsure at 0056/1; forward sheet 0221.
  Codex unsure re-review through 0065/6: 304/543 checked, 95 fixed, 201 still unsure, 8 confirmed unchanged. Total fixed 172; outstanding unsure 440. Resume unsure at 0066/1; forward sheet 0221.
  Codex unsure re-review through 0074/6 (bpo historical unsure pass complete): 315/543 checked, 97 fixed, 210 still unsure, 8 confirmed unchanged. Total fixed 174; outstanding unsure 438. Resume unsure at 0075/1; forward sheet 0221.
  Codex unsure re-review through 0200/6: 541/543 checked, 100 fixed, 405 still unsure, 36 confirmed unchanged. Total fixed 177; outstanding unsure 407. Resume unsure at 0201/1; forward sheet 0221. Owner requested dataset build at this checkpoint.

## Stage 40a — corrected dataset checkpoint through unsure sheet 0200 (2026-11-12)
- Owner requested re-review through sheet 0200 and building the corrected dataset at this checkpoint.
- Built road_hazards_v5_fixed from road_hazards_v5_all using all 177 records in review/v5/fixes.jsonl. AI visual labels by Claude and Codex. No detector predictions used.
- Re-review now covers 541 of 543 historical unsure images. Outcomes are 100 fixed, 36 confirmed unchanged, and 405 still unsure. Two historical rows remain unchecked at sheet 0201. Resume unsure at 0201/1. Forward review remains at sheet 0221 of 0916.
- This build includes all corrections already recorded by forward review through sheet 0220. It is a checkpoint build with review still in progress.
- Train 10,562 images with 6,729 pothole boxes and 3,985 speed-bump boxes. Val 830 images, test 323 images. All 11,715 image files match the source content and are 960x720.
- Verified all applied replacements and label coordinates. All other label files, including val and test, match the source byte for byte.
- Visually inspected 30 before/after samples. Sample index and sheets are in review/v5/views/spotcheck_fixed_0200.
- F1 training has not started.

- 2026-11-12 sheets done 0221-0269, 294 images visually checked. 12 images corrected for partial/split bump boxes. Total fixes 189. Next forward sheet 0270. Full dataset correction remains active per owner request.
- 2026-11-12 sheets done 0270-0335, 396 images visually checked. 16 images corrected, 28 newly unsure. Total fixes 205. Next forward sheet 0336. Newly added boxes await verification overlay.
  Overlay verification corrected the added distant-bump extents in 0285/3, 0290/4, 0296/3 and 0298/5.
- 2026-11-12 sheets done 0336-0409, 444 images visually checked. ng8 and pol existing bump labels retained. 12 images unsure about possible missing pothole boxes. Total fixes 205. Next forward sheet 0410.
- 2026-11-12 sheets done 0410-0433. 144 images checked in full-frame and enlarged-box views, 10 corrected, 42 confirmed unchanged, 92 unsure. Total fixes 215. Next forward sheet 0434.

- 2026-11-12 sheets done 0434-0457. 144 images checked in full-frame and enlarged-box views; 16 corrected, 35 confirmed unchanged, 93 unsure. Total fixes 231. Next forward sheet 0458.

- 2026-11-12 sheets done 0458-0481: {'unchanged': 58, 'unsure': 77, 'fixed': 9}. Total fixes 240. Next forward sheet 0482.

- 2026-11-12 sheets done 0482-0493: {'unsure': 27, 'unchanged': 37, 'fixed': 8}. Total fixes 248. Next forward sheet 0494.

- 2026-11-12 sheets done 0494-0548: {'unchanged': 328, 'fixed': 1, 'unsure': 1}. Total fixes 249. Next forward sheet 0549.

- 2026-11-12 sheets done 0549-0578: {'unchanged': 127, 'unsure': 49, 'fixed': 4}. Total fixes 254. Next forward sheet 0579.

- 2026-11-12 sheets done 0579-0608: {'unchanged': 131, 'unsure': 47, 'fixed': 2}. Total fixes 256. Next forward sheet 0609.

- 2026-11-12 sheets done 0609-0631: {'unchanged': 95, 'unsure': 40, 'fixed': 3}. Total fixes 259. Next forward sheet 0632.

- 2026-11-12 sheets done 0632-0654: {'unchanged': 117, 'unsure': 20, 'fixed': 1}. Total fixes 260. Next forward sheet 0655.

- 2026-11-12 sheets done 0655-0684: {'unsure': 8, 'unchanged': 172}. Total fixes 260. Next forward sheet 0685.

- 2026-11-12 sheets done 0685-0717: {'unchanged': 194, 'unsure': 4}. Total fixes 260. Next forward sheet 0718.

- 2026-11-12 sheets done 0718-0730: {'unchanged': 77, 'unsure': 1}. Total fixes 260. Next forward sheet 0731.

- 2026-11-12 sheets done 0731-0763: {'unchanged': 192, 'unsure': 6}. Total fixes 260. Next forward sheet 0764.

- 2026-11-12 sheets done 0764-0805: {'unchanged': 239, 'unsure': 13}. Total fixes 260. Next forward sheet 0806.

- 2026-11-12 sheets done 0806-0823: {'unchanged': 81, 'unsure': 22, 'fixed': 5}. Total fixes 265. Next forward sheet 0824.

- 2026-11-12 sheets done 0824-0859: {'unchanged': 187, 'unsure': 16, 'fixed': 13}. Total fixes 278. Next forward sheet 0860.

- 2026-11-12 sheets done 0860-0895: {'unchanged': 178, 'fixed': 21, 'unsure': 17}. Total fixes 299. Next forward sheet 0896.

- 2026-11-12 sheets done 0896-0916: {'unchanged': 105, 'unsure': 9, 'fixed': 9}. Total fixes 308. Next forward sheet 0917.

- 2026-11-12 final queue rows done 0001-0090: {'unsure': 34, 'unchanged': 49, 'fixed': 7}. Total fixes 315. Next final queue row 0091.

- 2026-11-12 final queue rows done 0091-0180: {'unchanged': 51, 'unsure': 24, 'fixed': 15}. Total fixes 330. Next final queue row 0181.

- 2026-11-12 final queue rows done 0181-0270: {'unchanged': 63, 'unsure': 18, 'fixed': 9}. Total fixes 339. Next final queue row 0271.

- 2026-11-12 final queue rows done 0271-0360: {'unchanged': 30, 'unsure': 31, 'fixed': 29}. Total fixes 368. Next final queue row 0361.

- 2026-11-12 final queue rows done 0361-0450: {'unchanged': 25, 'unsure': 50, 'fixed': 15}. Total fixes 383. Next final queue row 0451.

- 2026-11-12 final queue rows done 0451-0540: {'fixed': 32, 'unchanged': 10, 'unsure': 48}. Total fixes 415. Next final queue row 0541.

- 2026-11-12 final queue rows done 0541-0630: {'fixed': 37, 'unsure': 38, 'unchanged': 15}. Total fixes 452. Next final queue row 0631.

- 2026-11-12 final queue rows done 0631-0720: {'unsure': 55, 'unchanged': 10, 'fixed': 25}. Total fixes 477. Next final queue row 0721.

- 2026-11-12 final queue rows done 0721-0810: {'unsure': 59, 'fixed': 17, 'unchanged': 14}. Total fixes 494. Next final queue row 0811.

- 2026-11-12 final queue rows done 0811-0900: {'unsure': 41, 'unchanged': 40, 'fixed': 9}. Total fixes 503. Next final queue row 0901.

- 2026-11-12 final queue rows done 0901-0988: {'unsure': 34, 'unchanged': 35, 'fixed': 19}. Total fixes 522. Next final queue row 0989.

## Stage 40 release delivered — 2026-11-12

Forward review DONE 916/916; final queue DONE 988/988. 522 unique corrections. 435 unresolved cases excluded from curated 10,000 train images (15 sources), preserved in full 10,562 train release. All structural/content checks PASS. See RELEASE_REPORT.md. Previous road_hazards_v5_fixed is an obsolete 177-fix checkpoint.


## 2026-11-12 all-images follow-up

All 10,562 training images included; 830 validation and 323 test images unchanged. No image excluded.

435 ambiguous cases visually rechecked; 71 additional label changes. Cumulative replacement records: 592.

Recheck confidence: {'low': 343, 'medium': 92}. Low-confidence labels remain best-available annotations, not confirmed ground truth.

PASS: all image bytes/dimensions/decodes; all labels versus source or explicit replacements; all label classes/bounds; manifest counts; split counts; YAML/list paths.

AI visual review, no detector predictions. Low-confidence records are included with their best-available existing annotations, not certified correct. Review completion does not mean ambiguity was eliminated. Validation/test bytes unchanged; no training or evaluation run.

Output: C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v5_all_corrected_final


# Source-review checkpoint — not fully adjudicated

All 10,562 training images retained; 830 validation and 323 test images/labels unchanged.

343 previously low-confidence images rechecked against original pixels. 92 images changed in this pass; 683 cumulative full-label replacement records relative to the base. All changed images received before/after visual inspection; revisions are preserved in ledger history.

146 images remain provisional. Confidence over the 435 difficult cases: {'medium': 289, 'low': 146}. AI adjudication is not human ground truth and does not guarantee zero errors. Unresolved data has not been silently marked clean.

Integrity PASS: all 11,715 image hashes, dimensions and decodes; every annotation versus explicit decision or unchanged source; classes and bounds; counts; YAML/list paths. Split audit found zero exact or perceptual cross-split candidates at dHash <= 4 AND pHash <= 10, and zero shared group IDs. This does not prove absence of every possible correlated scene.

Fingerprint: `0110277003952df398621b92d08f60b54b5ada087604af459dae28ec5f24de00`.

Training has NOT started. The remaining cases need evidence sufficient to decide class and boundaries. Extra 2,438 vetted training images are being sought for the newly requested 13,000-image target. Existing images are not deleted to reach the target.

Do not use old `run_v5_2_train_fixed_visible.bat`: it points to an obsolete label checkpoint. Generic `train.py` also evaluates test automatically, which is outside the current authorization.

Dataset: C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v5_source_review_20261112


# Source-review checkpoint — not fully adjudicated

All 10,562 training images retained; 830 validation and 323 test images/labels unchanged.

343 previously low-confidence images rechecked against original pixels. 92 images changed in this pass; 683 cumulative full-label replacement records relative to the base. All changed images received before/after visual inspection; revisions are preserved in ledger history.

149 images remain provisional. Confidence over the 435 difficult cases: {'low': 149, 'medium': 286}. AI adjudication is not human ground truth and does not guarantee zero errors. Unresolved data has not been silently marked clean.

Integrity PASS: all 11,715 image hashes, dimensions and decodes; every annotation versus explicit decision or unchanged source; classes and bounds; counts; YAML/list paths. Split audit found zero exact or perceptual cross-split candidates at dHash <= 4 AND pHash <= 10, and zero shared group IDs. This does not prove absence of every possible correlated scene.

Fingerprint: `a4eb58dc61bebf829e9d892fe3bdbf9a928dca56d0c90e58fc21021c7b67150e`.

Training has NOT started. The remaining cases need evidence sufficient to decide class and boundaries. Extra 2,438 vetted training images are being sought for the newly requested 13,000-image target. Existing images are not deleted to reach the target.

Do not use old `run_v5_2_train_fixed_visible.bat`: it points to an obsolete label checkpoint. Generic `train.py` also evaluates test automatically, which is outside the current authorization.

Dataset: C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v5_source_review_20261112_u4k


## Saved resumable state 2026-11-12T19:29:21.293298+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 42; staged additions 4 (5 boxes), merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started.


## Saved resumable state 2026-11-12T19:29:36.715005+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 42; staged additions 4 (5 boxes), merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started.


## Saved resumable state 2026-11-12T19:30:36.858630+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 42; staged additions 4 (5 boxes), merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started.


## Saved resumable state 2026-11-12T20:05:08.441383+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 90; staged additions 4 (5 boxes), including 1 rejected same-scene duplicate; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; data-scope choice pending when optional subset exists.


## Saved resumable state 2026-11-12T20:06:06.527680+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 90; staged additions 4 (5 boxes), including 1 rejected same-scene duplicate; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; data-scope choice pending when optional subset exists.


## Saved resumable state 2026-11-12T20:51:42.704428+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 90; staged additions 4 (5 boxes), including 1 rejected same-scene duplicate; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; data-scope choice pending when optional subset exists.


## Saved resumable state 2026-11-12T20:55:25.558380+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 114; staged review records 7, including 1 rejected same-scene duplicate and 3 reviewed hard negatives; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; policy: wait_for_13000_reviewed_train_images.


## Saved resumable state 2026-11-12T21:14:30.568675+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 162; staged review records 11, including 1 rejected same-scene duplicate and 5 reviewed hard negatives; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; policy: wait_for_13000_reviewed_train_images.


## Saved resumable state 2026-11-12T21:18:41.566967+00:00
See START_HERE_STAGE40.md and review/v5/PROJECT_STATE.json. Current train 10562; provisional existing labels 149; proposed addition labels 2420; visual screens 162; staged review records 11, including 1 rejected same-scene duplicate and 5 reviewed hard negatives; merged 0. Current release leakage candidates 2, both visually rejected as different scenes. Training not started; policy: wait_for_13000_reviewed_train_images.
