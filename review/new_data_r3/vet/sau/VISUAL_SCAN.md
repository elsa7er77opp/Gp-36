# sau: SaudiRD forward-view hard negatives, visual scan (cloud session 5, 2026-11-04)

Source: Roboflow `refyy-i/saudird-luumi` v1 (fork of SaudiRD, CC BY 4.0; classes 0 Crack, 1 Pothole, 2 Rut),
auto-orient only. 1,171 images, 1,171 Roboflow bases (no augmentation), 0 eval hits and 0 r2-train hits under rule v2
(`vet.json`).

Gate decisions:
- Pothole images of SaudiRD (IMG_2xxx, DATA-WORKATTACH-FILE-MOMRA*) are mostly top-down / close-up phone photos:
  REJECTED for the pothole class (not the pod's forward view).
- Kept: windscreen frames IMG_8000-IMG_9999 (`--include 'IMG_[89]\d{3}'`), train only, as hard negatives
  (cracks are D5 = background; Crack and Rut boxes -> ignore).
- SaudiRD has NO speed-bump class, so every one of the 473 frames was looked at (14 contact sheets, outside git) for
  an unlabelled bump or pothole. 12 frames were EXCLUDED because they show a transverse row of road studs or a
  grooved / milled transverse band that could be a stud-type speed hump (D2) or a rumble strip (D6); we do not guess:
  IMG_8898, IMG_8995, IMG_8996, IMG_8997, IMG_8998, IMG_9001, IMG_9041, IMG_9042, IMG_9043, IMG_9192, IMG_9196, IMG_9234.
- Longitudinal lane studs (cat's eyes along lane lines), manhole covers and kerbs remain = background (D5).
- About 25 frames (IMG_8931-8953) are close-range shots of cracked asphalt, not windscreen views; kept as negatives.
- Result (`expected_build_info.json`): 461 train images, 459 hazard-free, 2 pothole boxes, 800 ignored boxes,
  31 groups (25-name blocks + rule-v2 clusters), 0 leak drops.

Status: VERIFIED by cloud visual scan for "no visible unlabelled bump/pothole"; PROVISIONAL for the effect on
training (a hard-negative part must be tested by the laptop A/B, see CLOUD_REPORT §0-S5).

Laptop:
    python -I tools/rf_download.py refyy-i/saudird-luumi 1 ..\GP36_Dataset\raw_v3\rf_saudird
    python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_saudird\x --part sau ^
        --cmap "{\"0\":\"ignore\",\"1\":\"pothole\",\"2\":\"ignore\"}" --include "IMG_[89]\d{3}" ^
        --exclude "IMG_(8898|8995|8996|8997|8998|9001|9041|9042|9043|9192|9196|9234)" --all-train ^
        --out review\new_data_r3\items\items_sau.csv
    python -I tools/build_part.py --items review\new_data_r3\items\items_sau.csv --part sau --out parts_r3\sau
    (compare parts_r3\sau\build_info.json with vet\sau\expected_build_info.json and keep_list.csv)
