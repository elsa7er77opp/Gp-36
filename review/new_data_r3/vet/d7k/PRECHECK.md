# d7k pre-check: Roboflow `yolo-ewrwa/dashcam-mg6en` (fork `refyy-i/dashcam-mg6en-0fwjp`), no full export

Sources: Roboflow connector `projects_get` on the original and on BharatPotHole, and `images_search` (first 250 of 7,106 names) on the fork (cloud session 4, 2026-11-04). Nothing was downloaded.

| item | value |
|---|---|
| original project | `yolo-ewrwa/dashcam-mg6en`, name "DashCam", workspace "YOLO" (no personal author name in the metadata) |
| licence | CC BY 4.0 (Universe listing, session 3 search) |
| class | one: `pothole` (19,895 boxes across all images in the original; 12,290 in the fork version, per `versions_export`) |
| images | 7,106 (train 5,085 / valid 1,350 / test 671; Roboflow's own split, by image) |
| history | created 2025-06 (version 2, 1,108 images) and grown to 7,106 by version 21–22 (2026-02-19) |
| unannotated | 43,772 is reported by Roboflow (unannotated images held outside the versions); not part of the export |

## File-name families (sample of 250 names)
- `<yyyymmddhhmmss>_0060_frame_NNNNN.jpg` at **3840×2160**: 4K originals.
- `<same>_frame_NNNNN_jpg` at **640×640**: resized copies of the same frames (the same frame appears in both sizes, e.g. `20250528095119_0060_frame_00030.jpg` 3840×2160 and `20250528095119_0060_frame_00030_jpg` 640×640; some 640 names appear twice, e.g. `..._00011_jpg`).
- `signal-2025-06-2x-hhmmss_frame_NNNNN.jpg` at 480×848 (portrait phone), plus `_jpg` 640 copies.
- None matches `KNOWN_FAMILIES` (rf8, sb15, ghpot, Nienaber, RDD, sr).

## Key finding: d7k is the upstream of part `bpo`
The video ids are the same as in BharatPotHole. The sample shows `20250506175823_0060`, `20250525135447_0060`, `20250528094319_0060`, `20250626065534_0060`, `signal-2025-06-26-111944`, all of which are bpo videos (`vet/bpo/keep_list.csv`). BharatPotHole (`rahul-tripathi/bharatpothole`, created 2026-10-29, 4,082 images at 640×640) is a later re-upload of a part of this project.

Consequences:
1. d7k and bpo must **never be combined across splits**: they contain the same frames, at 4K and at 640. Use one or the other, and run the cross-source check before building.
2. If d7k is used, prefer the 4K `.jpg` originals and drop the `_jpg` 640 copies (one copy per frame). Group by video id. bpo's audit says this source family is weak in val/test (`vet/bpo/BOX_AUDIT.md`), so use it **train-only**.
3. d7k could replace bpo as a larger, higher-resolution train source from the same Indian dashcam drives. It adds more frames, not more places.

## Laptop steps
```
venv\Scripts\python -I tools/rf_download.py refyy-i/dashcam-mg6en-0fwjp 1 ..\GP36_Dataset\raw_v3\rf_dashcam7k
venv\Scripts\python -I tools/vet_source.py --name d7k --root ..\GP36_Dataset\raw_v3\rf_dashcam7k\x --out review/new_data_r3/vet/d7k/vet --sheet ..\GP36_Dataset\_sheets\sheet_d7k.jpg
venv\Scripts\python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\rf_dashcam7k\x --part d7k --cmap "{\"0\": \"pothole\"}" --include "\d{14}_\d{4}_frame_\d+" --exclude ".*_jpg" "--group-regex=^(\d{14}_\d{4})" --all-train --out review/new_data_r3/items/items_d7k.csv
```
- The `--include` regex keeps only the 4K names. `--exclude ".*_jpg"` drops the 640 copies (base names ending in `_jpg`).
- **TODO(laptop):** run `tools/cross_source_dups.py` with `parts_r3/bpo` and `parts_r3/d7k`, then decide between the two. Do not use both.
- **TODO(laptop):** sample box audit (100 boxes) before use. The labels are polygons in part (bpo had 357 polygon lines), so check them with the fixed `sample_sheet.py` / crop tools.
