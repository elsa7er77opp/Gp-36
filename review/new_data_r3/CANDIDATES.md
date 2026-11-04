# New data candidates — round r3 (search started 2026-11-02)

How the search was done:
- web search (Kaggle, Roboflow Universe, Mendeley, Zenodo, Figshare, Hugging Face, papers);
- the anonymous Kaggle listing API with these terms: speed bump, speed breaker, speed hump, speedbump, pothole, road damage, road anomaly, egypt road. 159 unique datasets; raw output in the session scratchpad, re-runnable.

Access on this machine (2026-11-02):
- **Kaggle download needs a token** (HTTP 404 without one) → BLOCKED until `%USERPROFILE%\.kaggle\kaggle.json` exists.
- **Roboflow needs `ROBOFLOW_API_KEY`** (not set) → BLOCKED.
- Zenodo, Figshare, Mendeley and Hugging Face work anonymously. Zenodo is slow (≈ 5–40 KB/s per connection, rate-limited).

Verdicts:
- **ACCEPT-CANDIDATE**: download and validate.
- **VALIDATE**: download only to check whether it is a re-upload, or for a small part.
- **REJECT**: with the reason.
- **BLOCKED**: with what is missing.

Every accepted set still has to pass the standard gate before use:
- SHA-256, plus dihedral dHash and pHash, against everything owned;
- family/sequence exclusion against r2 val/test;
- label rules D1–D6 and FAR_TINY;
- no augmented copies;
- a visual spot check.

## A. Speed bumps (highest need)
| # | Name / link | Images | Classes | Licence | Region / view | Notes | Verdict |
|---|---|---|---|---|---|---|---|
| A1 | **Road Surface Irregularities Dataset (RSID)**, Zenodo [18789662](https://zenodo.org/records/18789662) (VGTU, 2026-02-26) | 18,542 (train 15,827 / val 1,358 / test 1,357) | pothole, manhole, speed-reducing bump | CC BY 4.0 | Vilnius (Lithuania) FHD dashcam, phone, ZED2. Plus a re-annotated subset of Nienaber (South Africa) GoPro and "random Roboflow datasets" | Archive listing in `rsid_zip_listing.csv`. 5,215 images are the GoPro `G00…` family, the **same family as r2 val/test (rf8 `r1g1132`)** → **exclude the whole family**. Its own split is by random frame (25 drive sequences span all three splits), so we re-split by sequence | **ACCEPT-CANDIDATE** (Vilnius + ZED + other families only; per-sequence split) |
| A2 | Kaggle `bensemanemohamedreda/speedregulator-road-hazards-and-speed-bumps` | ? (1.4 GB) | ? | CC BY-SA 4.0 | ? | updated 2026-10-20 | BLOCKED (Kaggle token) |
| A3 | Kaggle `amiragomaa/bump-detection` | ? (1.8 GB) | ? | Unknown | uploader name suggests Egypt; 2019 | licence unknown | BLOCKED (Kaggle token); then VALIDATE licence |
| A4 | Kaggle `ziya07/speed-bump-dataset` (1,894 MB) = `sannyshankaranml/speed-bump-dataset` = `huebitsvizg/speed-bump-pothole-dataset` (same size) | ? | bump/crack/pothole/road (folder classes) | CC0 / Unknown | ? | 3 uploads of the same size → re-uploads; looks like classification folders | BLOCKED; likely REJECT (no boxes) |
| A5 | Kaggle `saktheeswaranswan/yolov5-speed-breaker-detection-driver-alert-system` (914 MB) | ? | speed breaker | CC0 | India? | YOLO labels likely | BLOCKED (Kaggle token) |
| A6 | Kaggle `xiaxxx/geicar-pivoane` (7.2 GB) | ? | pedestrian, stop, 50, 30, speed_bump | Unknown | France (robot car) | too large for the link; licence unknown | BLOCKED; low priority |
| A7 | Kaggle `tejasrbagade/…`, `archanaa2310/…`, `sannyshankaranml/pothole-and-speed-breaker-*`, `titaniumblack/potholes-speedbumps-roads`, `belmanasoufyane/pothole-speedbumps`, `jayaprakashpondy/speedbumps`, `drdewangandeepak/speed-bump`, `leeyuil/speedbump` | small/unknown | bump ± pothole | mostly Unknown | ? | most look like Roboflow re-exports | BLOCKED; then VALIDATE (re-upload check) |
| A8 | Mendeley [7zzcmv2wz7](https://data.mendeley.com/datasets/7zzcmv2wz7) Bangladesh manhole + speed breaker | 1,425 files | folder classes, **no boxes** | CC BY 4.0 | Bangladesh street | classification only | REJECT for bump training (no boxes). Its manhole folders are a possible hard-negative source after a check for potholes in them |
| A9 | Mendeley [z3nx8n396g](https://data.mendeley.com/datasets/z3nx8n396g) BDRoad-Sense | 9,107 incl. augmentation (8 GB) | 5 folder classes | CC BY 4.0 | Bangladesh, phone | classification, augmented | REJECT |
| A10 | Mendeley [bvpt9xdjz8](https://data.mendeley.com/datasets/bvpt9xdjz8/1) marked speed breaker (India) | 969 | cropped bumps | — | India | crops, not scenes | REJECT |
| A11 | Peralta-López et al. 2023, Mexico (ZED camera), [MDPI](https://www.mdpi.com/2076-3417/13/14/8349) | 714 | pothole, speed bump | — | Celaya, Mexico | no public download found | UNRESOLVED (email the authors) |
| A12 | SBP-YOLO (arXiv 2508.01339) combined set | 7,500 | bump, pothole | — | mixed | built from Kaggle/Roboflow; not published separately | REJECT (no download; overlaps sources we have) |
| A13 | Roboflow Universe: many bump projects (rajaji/speedbreakers 2,660; akash-kumbar/speed_breakers-pothole 2,190; imagemaker8/speedbreaker 631; alia-khalifa/unmarked-speed-bumps; pv-aishwarya/mendeley_kaggle) | various | bump (± unmarked bump) | mostly CC BY 4.0 | India, Saudi, … | Roboflow sets already checked (sub5/qub) were largely the same families as rf8 | BLOCKED (no API key); then VALIDATE |
| A14 | EGY_PDD (Egyptian pothole/defect set with "Bumps & Sags") | ? | ? | ? | **Egypt** | owner/supervisor request pending | BLOCKED (request) |

## B. Potholes at scale
| # | Name / link | Images | Classes | Licence | Region / view | Notes | Verdict |
|---|---|---|---|---|---|---|---|
| B1 | **RDD2022 D40** (already on disk) | Japan 1,390 + India 1,530 with D40; Czech 154 kept apart | D40 → pothole; cracks etc. ignore | CC BY-SA 4.0 | dashcam/car | `review/rdd_forensics/RDD2022_NOTES.md`; US and China_MotorBike excluded | **ACCEPT** (part A, train only, filtered) |
| B2 | **Bučko et al. 2022**, Figshare [21214400](https://figshare.com/articles/figure/Potholes_dataset_with_YOLO_annotations/21214400) | 2,000+ | pothole | CC BY 4.0 | Slovakia, FHD dashcam, clear/sunset/evening/night/rain | 1.03 GB zip | **ACCEPT-CANDIDATE** (downloading) |
| B3 | Mendeley [tp95cdvgm8](https://data.mendeley.com/datasets/tp95cdvgm8) Kent water-filled + dry potholes | ~700 (2,143 files incl. txt/xml) | pothole (YOLO txt) | CC BY 4.0 | UK | small; many close-ups | VALIDATE (later, if time) |
| B4 | Kaggle `sovitrath/road-pothole-images-for-pothole-detection` (9.5 GB), `felipemuller5/nienaber-potholes-*` | — | pothole | CC0 / Unknown | South Africa (Nienaber GoPro) | **same family as r2 val/test (`G00…`)** | REJECT (leak risk into r2 val/test) |
| B5 | Kaggle `andrewmvd/pothole-detection`, `chitholian/annotated-potholes-dataset`, `atulyakumar98`, `sachinpatel21`, `rajdalsaniya`, `anggadwisunarto/potholes-detection-yolov8`, `muskanverma24/…` | 600–5,000 | pothole | various | web images, mixed | widely re-uploaded; `chitholian` / `andrewmvd` are the same 665-image set as our `ghpot` family; many web photos are not forward-view | BLOCKED (token); then VALIDATE for re-uploads |
| B6 | Kaggle BharatPotHole (iWatchRoad, arXiv 2508.10945) | 7,000+ frames | pothole | ? | India dashcam | ? | BLOCKED (Kaggle token); high value for potholes |
| B7 | Kaggle `rohitsuresh15/radroad-anomaly-detection` (7.8 GB), `cubeai/road-damage-detection-for-yolov8` (5.9 GB, CC BY-SA, likely RDD) | — | road anomalies | MIT / CC BY-SA | ? | large; RDD re-packs likely | BLOCKED; then VALIDATE |
| B8 | Zenodo [13832363](https://zenodo.org/records/13832363) Pakistan road anomalies | 1.8 GB | accident, fire, fighting, snatching, pothole | CC BY 4.0 | Pakistan, CCTV/mobile | mostly not road-surface view | REJECT (wrong viewpoint/classes) |
| B9 | Hugging Face: keremberke/pothole-segmentation (90), manot/pothole-segmentation2 (665), taroii/pothole-detection | small | pothole | CC BY 4.0 | web | re-exports of Roboflow `ghpot`-like sets | REJECT (re-uploads / tiny) |

## C. COCO-class road images (for a per-class COCO check)
| # | Name | Notes | Verdict |
|---|---|---|---|
| C1 | Kaggle `mohamedra9ab/object-detection-for-autonomous-cars-egypt` (8.6 GB, CC BY-SA 4.0) | Egyptian street scenes with object boxes: the only Egypt-specific road set found | BLOCKED (Kaggle token); high value for the per-class COCO check |
| C2 | `GP36_Dataset/yolo-automotive-dataset` (already on disk, 1.2 GB) | still to inspect | VALIDATE |

## D. Kaggle triage after the token was added (2026-11-04)
Tool: `tools/kaggle_dl.py`. It reads `%USERPROFILE%\.kaggle\access_token` and never prints it. File lists come from the authenticated `datasets/list` API (first page). Metadata files were read one at a time.

| Kaggle ref | What the files show | Verdict |
|---|---|---|
| `bensemanemohamedreda/speedregulator-road-hazards-and-speed-bumps` (CC BY-SA 4.0) | YOLO; classes `nid_de_poule` (pothole), `fissure` (crack), `bouche_egout` (manhole), `dos_dane` (speed bump); phone photos `kg_2025…` and video frames `vlcsnap…` (French class names, North Africa) | **ACCEPT-CANDIDATE**: downloading. Map 0 → pothole, 3 → speed_bump, 1 and 2 → ignore (D5) |
| `mohamedra9ab/object-detection-for-autonomous-cars-egypt` | readme: "Enhanced BDD100K Clean Dataset", BDD100K plus added images. Some file names are COCO ids (`000000000071_jpg…`) | **REJECT** for the COCO road check: not Egyptian streets, and it contains COCO images (the COCO model was trained on them → leakage) |
| `amiragomaa/bump-detection` | classification folders `test/bump/…`, no boxes | **REJECT** |
| `drdewangandeepak/speed-bump` | same image files as `amiragomaa` (identical names and byte sizes, e.g. `1.jpg` 450,915 B), plus VOC `.xml` boxes | **VALIDATE** (downloading; web images?) |
| `sannyshankaranml/pothole-and-speed-breaker-dataset` = `tejasrbagade/…` = `archanaa2310/…` | the same Roboflow export "Pothole and Speed Breaker Dataset-400B v3" (workspace `cse400b`, 5,503 images, CC BY 4.0) | **VALIDATE**, one copy downloaded. **Risk:** workspace `cse400` is also the source of our external BD87 test, so build with `--guard external_tests/bd_speedbreaker_v2_orig87` |
| `jayaprakashpondy/speedbumps` | Roboflow, numeric names (`1122_jpg.rf…`) like the rf8 numeric family | **VALIDATE** (downloading) |
| `belmanasoufyane/pothole-speedbumps` (CC0) | `merged_dataset/…` | **VALIDATE** (downloading) |
| `titaniumblack/potholes-speedbumps-roads` | 4 Roboflow-augmented copies per image (`Bump_Images_-1-_jpg.rf.<4 hashes>`) | **REJECT** (augmented copies) |
| `saktheeswaranswan/yolov5-speed-breaker-…` | the `newonetrwww (N).jpg` family, also inside sub5 (31 Oct) | **REJECT** (known family, few originals) |
| `youssefhany100/road-damage-detection` | an RDD2022 re-pack + model files | **REJECT** (we have RDD2022) |
| `hosen42/pothole-data` | classification folders (`Plain/`) | **REJECT** |
| `rohitsuresh15/radroad-anomaly-detection` (7.8 GB, MIT) | dashcam video frames `01_10072023_mp4-31…`; data.yaml not readable by single-file request | later, if time allows |
