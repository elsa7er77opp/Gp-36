# RDD2022 — acquisition, conversion and checks (30 Oct 2026)

**Download.** Figshare item 21431547 (`Downloads\21431547 (1).zip`, 13,267,425,313 bytes). It is a stored outer zip that holds `RDD2022_released_through_CRDDC2022.zip`, which in turn holds one stored zip per country. `label_map.pbtxt` lists D00, D10, D20, D40. Licence of the images: CC BY-SA 4.0 (sekilab/RoadDamageDetector).

**Extraction.** `tools/extract_rdd2022.py --only-with D40` reads the nested zips in place, scans every train XML in memory, and writes only the train images whose XML contains D40, together with their XMLs. Output: `GP36_Dataset\raw_v3\RDD2022_D40\` (report: `extract_report.json`). Norway (9.9 GB, panoramic) and China_Drone (top-down) were not extracted. Test folders have no labels.

| Country | Train XMLs | Images with D40 | D40 boxes | Image size | Other object names found |
|---|---|---|---|---|---|
| Japan | 10,506 | 1,390 | 2,243 | 600² / 1080² | D00, D10, D20, D43, D44, D50 |
| India | 7,706 | 1,530 | 3,187 | 720² | D00, D01, D10, D11, D20, D43, D44, D50, **D0w0 (typo)** |
| Czech | 2,829 | 154 | 197 | 600² | D00, D10, D20 |
| United_States | 4,805 | 116 | 135 | 640² | D00, D10, D20 |
| China_MotorBike | 1,977 | 164 | 235 | 512² | D00, D10, D20, **Repair** |

**Conversion.** `tools/convert_voc.py`, with names in this order: D00, D10, D20, D40, D01, D11, D43, D44, D50, D0w0, Repair (source id = index). Output: `raw_v3\RDD2022_D40_yolo\<Country>[_partK]`. **3,354 / 3,354 files converted, 0 errors.** No D40 box has a side under 6 px at 960. Ontology mapping in `configs/sources.yaml` (`rdd22`): **3 (D40) → pothole**. Everything else (cracks, blur, manhole D50, repair) → ignore, per D5. These objects remain in the images as background.

**Visual check** (25 random images, 5 per country, `review/rdd_forensics/rdd_d40_sample.jpg`):
- **Japan, India, Czech:** dash-cam or car viewpoint close to ours. Mostly plausible pothole boxes; India boxes cover large broken areas.
- **China_MotorBike:** a top-down view of the road surface. At least one D40 box lies along a long crack, and one sits next to a manhole. Questionable.
- **United_States:** Google Street View images carrying a "Google" watermark. Many tiny, far D40 boxes (FAR_TINY), some on cracks.
- Known limitation: RDD labels are not reviewed image by image here. Like v3a, they are "interim".

**Use in the dataset (single-variable experiment):**
- **v3b_full**: v3a, plus 2,920 Japan + India D40 images added to **train only**. Val and test are identical to v3a. This puts the pothole:bump ratio back to about **5.8 : 1**.
- **v3b_capped**: v3a, plus 791 random (seed 0) Japan + India images, which keeps train at about **3 : 1**.
- **Czech (154 images)** is kept aside as an unseen-country test (`manifests/v3b_unseen_country_czech.csv`).
- China_MotorBike and United_States are excluded after the visual check.
