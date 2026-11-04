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

## E. Cloud session search (2026-11-04, no GPU, no project data)
Full write-up and laptop steps: `review/new_data_r3/CLOUD_REPORT.md`.

**Access in the cloud VM (VERIFIED by request results, 2026-11-04):** the environment's network policy returns
HTTP 403 (proxy CONNECT refused) for kaggle.com, zenodo.org, figshare.com, huggingface.co, roboflow.com,
data.mendeley.com, ieee-dataport.org, arxiv.org and mdpi.com. `KAGGLE_API_TOKEN` and `ROBOFLOW_API_KEY` are not
set. Only GitHub (git clone, API, release assets) and PyPI are reachable. So only GitHub-hosted data could be
downloaded and leak-checked here; every other candidate below is **LAPTOP-VET** (download + `tools/vet_source.py`
on the laptop).

**Leak rule change found by the new tests (VERIFIED, `tests/test_leak_check.py`):** the old rule compared the
pHash of the *unrotated* candidate only, so a horizontally flipped copy of a protected image had dHash 2 but
pHash 32 and was **not** a hit. `tools/leak_check.py` and `tools/build_part.py` now compare both hashes under
the same flip/rotation (rule v2). On the rejected E1.2 set, rule v2 finds 328 eval hits where rule v1 found 229
(VERIFIED, cloud leak runs). Parts built before this change must be re-checked (CLOUD_REPORT §3, step 0).

### E1. Downloaded and checked in the cloud VM (GitHub)
| # | Source | What it is | Leak check (rule) | Verdict |
|---|---|---|---|---|
| E1.1 | [dm-druid/SpeedBumps-Detection](https://github.com/dm-druid/SpeedBumps-Detection) (MIT, 2018) | YOLO txt, id 0 = speed bump (yellow/black rubber bumps, Chinese campus, phone at windscreen height, one day "0620"), id 1 = person (mostly Pascal-VOC web photos). **Augmented:** every original appears 10× as brightness/contrast copies (index period 279), spread over its own train AND val. 5,983 images → 2,770 road images → **277 originals, 319 bump boxes** (34 pedestrian boxes → ignore) | 0 eval hits, 0 r2-train hits on all 5,983 images (rule v1) and on the 277 originals (rule v2) | **ACCEPT** (train only, originals only): `tools/make_items_dmdruid.py`. Visual check of 20 random originals below |
| E1.2 | [sanapala-krishnakanth/pothole-speedbeaker-detection-system](https://github.com/sanapala-krishnakanth/pothole-speedbeaker-detection-system) = README "Speed_breakers&Pothole v8", Roboflow `akash-kumbar/speed_breakers-pothole` (CC BY 4.0) = CANDIDATES A13 | 6,045 Roboflow images, 1,395 bases with 2–8 rf. copies; families `Image-N-`, numeric, `potholesN` | rule v1: **229 eval hits** (val rf8 140, test rf8 58, ghpot val/test 31) + 158 r2-train hits; rule v2: **328 eval hits** + 258 r2-train hits (the 99 extra eval hits are flipped copies the old rule missed) | **REJECT** (leak into r2 val/test; augmented). Same files in `RitheeshReddy078/…` and `DineshReddyNarra/…-master` (same tree, 12,485 files) → REJECT |
| E1.3 | [Mohamed20384/Speed-Bump-Detection-marked-unmarked](https://github.com/Mohamed20384/Speed-Bump-Detection-marked-unmarked) (no licence) | graduation project, **unmarked bumps on Egyptian streets**, own collection: 6 raw input videos (`bump1-6.mp4`, `bump_challenge.mp4`, day + night) + a YOLOv8 `best.pt`. **No labels published** | not run (no labelled images) | **REQUEST** (highest value for our main failure): ask the author for permission and the labelled frames. Without labels, the videos could be hand-labelled into an *Egyptian part-val* (never train on our only Egyptian eval). No licence → no use without written permission |
| E1.4 | [eid-abdelrihem/Unmarked-Bump-Detection-by-Hybrid-Architecture](https://github.com/eid-abdelrihem/Unmarked-Bump-Detection-by-Hybrid-Architecture) | notebooks only; data = Roboflow `ensam-wyp9x/total-jcwvt` v5, classes marked / non-marked speed bump, 628 / 181 / 75 images; README: only 39 non-marked vs 666 marked train boxes | — | **LAPTOP-VET** with Ahmed's own Roboflow key (the notebook contains someone else's key; it was **not** used and is not recorded) |
| E1.5 | `li-peiyun/Detection-and-Distance-Measurement-of-Speedbumps`, `MinmusLin/…`, `359jxf/…` (Tongji campus course projects) | 857 frames + drawn result images, no label files (5 xml are calibration) | — | REJECT (no boxes) |
| E1.6 | `Santhanalakshmimano/SpeedBump_detection_usingCV` | 463 VOC xml, names `Image00xxx` | family Image000xx | REJECT (known re-upload family) |
| E1.7 | `Dip556/AI-Road-Shield`, `MK-DEV369/AEGIS-RS`, `rautshreya1610/pothole-road-hump-detection`, `Benadict-Git/speed` (SBP-YOLO clone) | Roboflow re-exports (`N_jpg.rf.`, `potholesN`, `pic-N-`, `img-N`); SBP-YOLO clone has results only | not run | REJECT (known families / augmented / no data) |
| E1.8 | `AGV-IIT-KGP/SpeedBumpDetection`, `VaradSalunke2808/…`, `DivyasreeN31/Speed-breaker-` | classification folders / frames without boxes | — | REJECT (no boxes) |
| E1.9 | `lonlonago/…speed-bump…974-images`, `the-chet/…`, `jeetgoyal80/…`, `Kbsurendra/…`, `PrasadCodesML/…`, `YashGang/…`, `a-b-h-a-y…`, `lkampoli/…`, `Rahulp-24/…`, `ImagingLab-HCL/Hump_Detection`, `ArunaK-netizen/…`, `maarhmaa/…`, `rajeshkumarswain1976/…` | preview images, results plots, code or videos only | — | REJECT (no dataset in the repo) |
| E1.10 | `Androidest/Speed_Bump_Detection` | = our `ghsb` source | — | already used |

Visual check E1.1 (20 random originals, seed 0, sheet kept outside git): all 20 are road scenes; boxes are on
yellow/black (and one black/yellow striped) rubber speed bumps, tight around the bump; 16 forward views at low
height with near and far bumps (thin far boxes, e.g. ≈ 0.8 × 0.03 of the frame, none below FAR_TINY), 3 close
views pointing down at the bump (`xqq062000200`, `…218`, `…261`), 1 oblique (`…157`); zebra crossings are visible in
`xqq062000076` and `…160` and are **not** labelled (consistent with D1); one pedestrian
box (id 1 → ignore); no rumble strips, manholes or potholes labelled. These are *marked* bumps, not the unmarked
Egyptian kind, so the expected gain is for bumps in general, not the main failure mode.

### E2. Found by web search, not downloadable from the cloud VM (LAPTOP-VET or REQUEST)
| # | Source | What is known (search results, not verified) | Next step |
|---|---|---|---|
| E2.1 | **DriveIndia** (arXiv 2507.19912; IEEE 11423478), TiHAN IIT Hyderabad | 66,986 images, YOLO txt, 24 classes incl. **unmarked speed bump, marked speed bump, rumble strips, zebra crossing**; India; academic non-commercial; "will be released via tihan.iith.ac.in/tiand-datasets" | **REQUEST** (Ahmed): check the TiHAN portal / email. If granted: rumble strip → ignore (D6), zebra → ignore (D1), both bump classes → speed_bump; group by drive/sequence id |
| E2.2 | Roboflow `qassim-university-rgdar/unmarked-bumps` (Saudi Arabia) | unmarked bumps | LAPTOP-VET (Roboflow key) |
| E2.3 | Roboflow `qu-j2rlc/speed-unmarked-bumps` | classes Manhole Pothole, Speed Bump, Unmarked Bump | LAPTOP-VET; "Manhole Pothole" needs a visual check (D5) |
| E2.4 | Roboflow `alia-khalifa/unmarked-speed-bumps`, `alia-khalifa/speed-bumps`, `alia-khalifa/detecting-speed-bumps` (v4, marked) | listed in A13 as BLOCKED, never vetted | LAPTOP-VET |
| E2.5 | Roboflow `emirhan-ilhan/speed-bump-hump-unmarked`, `…-marked` (443 img, speedbump + pothole, CC BY 4.0) | 2021 | LAPTOP-VET |
| E2.6 | Roboflow `speedbumps-detection-using-yolov8/speedbumps-detection` (≈2,200–2,650 img, CC BY 4.0), `speed-bumps-8qvol/speed-bump-low-light`, `uthm-vequj/speed-bump-detection` (Malaysia) | — | LAPTOP-VET (likely partly re-uploads: run `vet_source.py` first) |
| E2.7 | Roboflow `ensam-wyp9x/total-jcwvt` v5 (E1.4) | marked + non-marked bumps | LAPTOP-VET |
| E2.8 | Giordani et al. 2026, *Sci. Rep.* 16:15318 (doi 10.1038/s41598-026-46679-4), Italy, GoPro + phone | > 2,000 images: potholes, 2,519 cracks, 957 maintenance holes | REQUEST/LAPTOP-VET: potholes + crack/manhole **hard negatives**; check overlap with part `sr` family `kg_` (also Italian) |
| E2.9 | Mendeley `ypm4h4z25c` RoadDamageVision, Mendeley `c43y93xswd` multi-class road surface | unknown viewpoint / boxes | LAPTOP-VET (low priority) |
| E2.10 | Peralta-López 2023 (A11), Point-cloud bump paper (490 marked/unmarked images, segmentation) | not public | UNRESOLVED (email authors) |
