# egm: Egyptian Mapillary street frames, an UNLABELLED labelling pool (cloud session 5, 2026-11-04)

Status: **PARTIAL / needs human labels.** No box from this source is counted anywhere until a person has labelled the
frames (D1–D6). Pseudo-labels are not allowed.

## Source (VERIFIED from the API replies, 2026-11-04)
- Kaggle `yassienwasfy/egyptian-streets-dashcam`: 39.3 GB, licence field "Apache 2.0", created 2026-10-23.
  Description: "Street-level images of Egypt from Mapillary … Mirrors huggingface.co/datasets/masterofaudio2077/egyptian-streets".
- Hugging Face mirror: 249 tar files `data/<x>_<y>/r*.tar` (sum 39.55 GB, file list in the cloud scratchpad). Each tar
  holds `<mapillary id>.jpg` (full size, e.g. 4032×3024) and `<id>.json` (sequence id, creator, lon/lat, capture time,
  is_pano, camera make).
- Licence caveat: the mirror says Apache-2.0, but Mapillary imagery is CC BY-SA 4.0. Treat it as CC BY-SA 4.0 and keep
  attribution ("© Mapillary contributors"). PROVISIONAL until Ahmed confirms it is fine for a graduation project.
- Tile grid, fitted on 3 downloaded tiles (VERIFIED for those three): x ≈ floor(12.5·lon), y ≈ floor(12.5·lat).
  Cairo/Giza = `390_375`, `391_375` (11 tars, 6.07 GB); Alexandria = `374_390`.

## What the cloud saw (one Cairo-east tar, `391_375/r0.tar`, 1,299 frames)
- All non-panoramic phone frames; 64 sequences, 4 creators. Cameras: Apple 829, Infinix 226, Motorola 178,
  Xiaomi 66.
- A 36-frame contact sheet (one frame per sequence, outside git) shows real **windscreen forward views** on Egyptian
  streets: unpaved residential roads, desert highways, night driving with glare. Some frames are tilted to the sky.
  This is exactly the domain where the model fails (unmarked bumps, STATUS Stage 5).
- Leak check, rule v2, against `protected_hashes.npz`: **0 eval hits, 0 r2-train hits** among the 1,299 frames
  (`tools/leak_check.py`).
- `tools/make_egm_pool.py` on the 1,428 downloaded frames (3 tiles) keeps 694 frames (≥ 15 m apart, ≤ 40 per
  sequence): train pool 574 (5 creators), eval pool 120 (2 creators).

## Why it is not a part yet
1. No labels. Unmarked Egyptian bumps are the hardest case. A frame we *assume* is hazard-free but that holds an
   unmarked bump would teach the model to ignore it. So frames are not even used as negatives without a full-res check.
2. Hence the target "≥ 1,000 clean hazard-free frames from the same regions" is **not met** by the cloud. It is met
   only after Ahmed labels them. The pool is ready for that.

## Laptop / Ahmed (in order)
```
rem 1. download the Cairo/Giza tiles (6.1 GB) from the HF mirror into ..\GP36_Dataset\raw_v3\egm\<tile>_<r>\
rem    (huggingface-cli download masterofaudio2077/egyptian-streets --repo-type dataset --include "data/390_375/*" "data/391_375/*")
rem    then untar each r*.tar into its own folder
python -I tools/make_egm_pool.py --tiles ..\GP36_Dataset\raw_v3\egm --out review\new_data_r3\items\egm_pool.csv
python -I tools/leak_check.py ..\GP36_Dataset\raw_v3\egm review\new_data_r3\vet\egm\leak_egm.csv
rem 2. label in CVAT / Roboflow (private project), ALL frames of a sequence that is opened, by D1-D6:
rem    speed_bump (incl. unmarked asphalt humps), pothole; everything else background. Mark "unsure" frames, do not guess.
rem 3. pool "eval"  -> a NEW Egyptian benchmark `egm_eval` (never trained on; one test use per model via tools/test_ledger.py)
rem    pool "train" -> part `egm` (train only), built with tools/build_part.py like every other part
```
The pool split (by creator) is fixed by the tool before anyone looks at the frames. It is never changed after labelling.

## 7 Nov 2026: laptop steps ready (Ahmed chose local labelling, no upload)
- `run_egm_step1.bat`: `tools/egm_download.py` downloads Cairo/Giza tiles 390_375 + 391_375 from the HF mirror (stdlib,
  resumes, tar files kept) into `..\GP36_Dataset\raw_v3\egm`, then `make_egm_pool.py` (pool split by creator, fixed
  before anyone looks) and `leak_check.py`.
- `run_egm_label.bat`: `tools/egm_label.py`, an OpenCV labelling window. Writes YOLO labels to
  `..\GP36_Dataset\labels_egm\<pool>\<id>.txt` and an append-only decision log
  `review/new_data_r3/egm_labels/status_<pool>.csv` (done / unsure / unusable). Eval pool first, completely.
- Use after labelling (not before, and only with rules written in STATUS first): eval pool -> new Egyptian benchmark
  `egm_eval` (one test use per model, ledger); train pool -> part `egm` via build_part.py. "unsure" frames are used
  neither as negatives nor for scoring.
