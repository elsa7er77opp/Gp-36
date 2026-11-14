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

## F. Cloud session 2 (2026-11-04 afternoon): network open, Kaggle token + Roboflow connector
Full write-up: `review/new_data_r3/CLOUD_REPORT.md` §0 and §7. Tools: `tools/vet_source.py` (rule v2),
`tools/sample_sheet.py`, a per-family leak/box breakdown (family = known re-upload family or the name pattern).
Roboflow: the API key in the VM env was a publishable `rf_` key (401 on downloads); public Universe projects were
instead **forked into the owner's workspace `refyy-i` through the Roboflow connector**, and one version per fork was
generated with **no augmentation and no resize** (auto-orient only), so each export holds the source originals
(one copy per image). Laptop reference = `refyy-i/<fork>` version 1, format yolov8.

### F1. Accepted (part built here with the protected hashes; counts VERIFIED from the cloud build)
| part | source | what it is | leak (rule v2) | counts (train / val / test) | status |
|---|---|---|---|---|---|
| `dmd` | GitHub dm-druid/SpeedBumps-Detection (MIT) | China campus, marked rubber bumps (§E1.1) | 0 eval | 277 img / 319 bump · — · — | ACCEPT (train only) |
| `egy` | Roboflow `road-damage-detection-wgjj4/rdd-6706t` (CC BY 4.0) → fork `refyy-i/rdd-6706t-8szyz` v1 | **Egypt** (city not verified; "Alexandria" in an earlier draft had no evidence): iPhone dashcam behind the windscreen (11 videos), WhatsApp dash clips (4), phone photos `Egypt_*`; classes Crack (→ ignore), Pothole | 0 eval, 0 r2-train | train 1,118 img (427 crack-only negatives) / 835 pothole · val 147 / 66 · test 105 / 52 (split by video) | **PROVISIONAL ACCEPT** (potholes): some "Pothole" boxes are on manhole covers (`Egypt_00087`, `WhatsApp…14_41_20_mp4-0102`) → review the val/test boxes before use |
| `ens` | Roboflow `ensam-wyp9x/total-jcwvt` (CC BY 4.0) → fork `refyy-i/total-jcwvt-f9ffa` v1, family = bare numeric names ≥ 100 | forward-view campus roads, South Asia (probably Bangladesh), white-painted raised humps, plus some rubber bumps; classes 0 marked / 1 unmarked → speed_bump | 0 eval, 1 r2-train | 414 img / 422 bump · — · — | **PROVISIONAL ACCEPT** (train only): names have the same numeric style as rf8; not pixel copies (0 hits) but same-video neighbours are not excluded → laptop must look at `vet/ens/sequence_check_pairs.csv` (40 closest pairs) before use. Frames are consecutive (one 258-frame near-duplicate chain) |
| `pol` | Roboflow `sca5a-kelompok-5-zus60/deteksi-polisi-tidur` (CC BY 4.0) → fork `refyy-i/deteksi-polisi-tidur-tblnr` v1 | **Indonesia**, residential alleys, forward view at low height, 1920×1080 video frames; classes `PolisiTidurPolos` (**plain / unmarked concrete humps**, 270) and `PolisiTidurWarna` (painted rubber, 730) → speed_bump | 0 eval, 0 r2-train | every 2nd frame: train 375 / 375 bump · val 100 / 100 · test 25 / 25 (groups = 50-frame blocks joined by near-duplicates) | **ACCEPT**, own val/test (unmarked bumps, new country). Single neighbourhood, consecutive frames → few physical bumps |
| `red` | Roboflow `rompe-j2aun/reductor-w4anu` (CC BY 4.0) → fork `refyy-i/reductor-w4anu-q04yg` v1 | **Latin America** (Spanish labels), 4K camera mounted low (motorbike-style) on roads with yellow-painted reducers; class 3 `REDUCTOR` → speed_bump; per-stripe paint condition `Bueno/Aceptable/Malo` → ignore | 0 eval, 0 r2-train | train 334 / 338 bump (2 neg) · val 69 / 68 · test 35 / 40 (group = video / frame-thousand block) | **ACCEPT** (marked bumps) |
| `ng8` | Roboflow `speedbreakerdatalabelling/speed-breaker-detection-ng8ne` (CC BY 4.0) → fork `refyy-i/speed-breaker-detection-ng8ne-pmyzk` v1, families `VID_20250802_*` + `IMG_*` only | **India** (city roads, autorickshaws), portrait phone video, forward view; black/white painted raised breakers; **many hazard-free frames** | families used: 0 eval; dropped family `speedbreaker_N` (113 eval hits) and known families | train 278 / 145 bump / 133 neg · val 67 / 20 / 47 neg · test 39 / 12 / 27 neg (group = video) | **ACCEPT**; PROVISIONAL on D1/D2 for the striped breakers that look like zebra tables |
| `hmp` | Roboflow `thesis-grzdh/road-hazard-detection-6` (CC BY 4.0) → fork `refyy-i/road-hazard-detection-6-g5pbz` v1, family `humps-v*-_N` only | **India**, mostly **night** dashcam (timestamp overlay, hump warning signs) + some web photos; `humps` → speed_bump, `pothole` → pothole, animals / pedestrian / roadworks → ignore | family used: 0 eval; dropped bare-numeric family (17 eval hits) | train 357 / 374 bump · val 62 / 67 · test 12 / 17 (2 exact duplicates, 2 FAR_TINY removed) | **ACCEPT**; some loose boxes and web photos inside the family (PROVISIONAL label quality) |

### F2. Rejected or not usable (reason)
| source | reason |
|---|---|
| Roboflow `qassim-university-rgdar/unmarked-bumps` (fork `refyy-i/unmarked-bumps-dkmuf`) | 401 of 598 images are our known families (MVI_15xx 209, speedbreakerrefinedone 130, newonetrwww 45, VID_20190924 16); 24 eval hits; `VIDEON_N` hits eval; only ~59 new originals (`imggeN`) |
| Roboflow `pothole-detection-1nczj/speed-unmarked-bumb` (2,217 img) | re-upload of rf8/sb15 families (Image-N 221 eval hits, MVI_15xx, VID_20190924, speedbreakerrefinedone, newonetrwww) |
| Roboflow `road-safety/speed-bump-tonyt` | = ensam numeric family + rf8/sb15 families (96 eval hits on Image-N); the usable part is already `ens` |
| Roboflow `speed-bump-takqu/speed-bump-yiaek` (1,000 img, 0 hits) | top-down phone photos taken standing on the bump (feet visible): not forward view |
| Roboflow `speedbumpdetection-l6bis/speed-bump-detection-pwqpb` | rf8 families (Image-N 76 + MVI_15xx 29 eval hits) |
| Roboflow `ceta-kdm8t/speed-bump-vl46b` | `Image000xx` family (rf8/sb15) + small web family |
| Roboflow `uthm-vequj/speed-bump-jvyxp` | web/stock product photos of rubber bumps, not forward view |
| Roboflow `yokoso/pothole-speed-bump` | few real originals behind many copies; web images + known families |
| Roboflow `robo-krtba/speed-bump-detection-xd07j` | forked, not downloaded: 327 images but only 45 bump boxes |
| Kaggle `khadijazarriq/road-hazard-detection` | **synthetic** (game-engine city), polygon labels |
| Kaggle `leeyuil/speedbump` | Kakao Map road-view captures (third-party imagery, licence unknown), rotation-augmented, 640×640 stretched |
| Kaggle `sannyshankaranml/pothole-and-speed-breaker-dataset` (cse400B, §D VALIDATE) | `SpeedBreaker--N-` family: 321 eval hits (rf8 val) → whole bump family would go |
| Kaggle `jayaprakashpondy/speedbumps` (§D VALIDATE) | = ens numeric family + rf8/sb15 families (149 eval hits on Image-N) |
| Kaggle `belmanasoufyane/pothole-speedbumps` (§D VALIDATE) | renamed `train_N`/`valid_N` merge; 178 eval hits spread over one family |
| Kaggle `drdewangandeepak/speed-bump` (§D VALIDATE) | `Image N` family (rf8/sb15), VOC |
| Kaggle `cloudymts/road-hazard-dataset` = `venkataakshay299/road-dataset` | augmented copy of Roboflow `thesis-grzdh/road-hazard-detection-6`; its `humps-v*` family (0 eval hits) is being taken from the source fork instead (F3) |
| Kaggle `mrongsubho/…speedbraker…yolov5` | only 13 breaker boxes |
| Kaggle `david2do/road-anomaly-ds` | merge of rf8 families (Image-N 225 eval hits, MVI_15xx, VID_20190924) + potholes |
| Kaggle `sannyshankaranml/pothole-and-speed-breaker-detection`, `…/speed-breaker-v3i` | no bump class / 7 boxes |
| Kaggle `anjnaymahajan/…`, `machinelearninguyo/…`, `programmerrdai/…`, `sarfaraznatha/…`, `amlyasser/generated-speed-bumps`, `shakilsikder/…`, `rahavg/…`, `hasanhejleh/…` | classification folders / no boxes / empty / generated |
| Kaggle `orvile/road-anomaly-detection` | RAD frames (= sr `rad_` family, bump labels judged unusable in Stage 18) + accident/fight classes |
| Hugging Face `Hanno100/RoadDamageDetection-Egypt` | = augmented export (mosaic, flips, 640 stretch) of the Roboflow project used for `egy` |
| Roboflow `object-detection-ajwfo/hump-detection-uac1m` | bare-numeric family with 165 eval hits |
| Roboflow `amier-haziq-dwre4/hump-16nup` | forked, not downloaded in time (982 img, Hump + traffic-sign classes) → laptop candidate |
| Roboflow `speedbreakerdatalabelling/speed-breaker-detection-ng8ne` family `speedbreaker_N` | 113 eval hits (the rest of the project is part `ng8`) |

### F3. In progress / for the laptop
| source | state |
|---|---|
| Kaggle `zgpttai/road-hazard` (MIT) | **REJECT** (checked): Sri Lanka dashcam potholes, 0 eval hits, but the two folders share 303 identical images with different label sets per "operating sensitivity τ = 0.30 / 0.15" (README) → labels look model-generated (pseudo-labels), so they are unusable as ground truth or as clean negatives |
| Roboflow `amier-haziq-dwre4/hump-16nup` → fork `refyy-i/hump-16nup-4bmvs` v1 (export ready, 1.09 GB) | 982 images, only 218 `Hump` boxes (rest: parking/handicap/turn signs, obstacles); not downloaded; low priority laptop candidate (`tools/rf_download.py refyy-i/hump-16nup-4bmvs 1 …`, then `vet_source.py`) |
| Kaggle `mohamedaminebelasri7/roadscan-dataset` | mostly RDD India (held) + `vlcsnap` video frames; 3 pothole severities; check overlap with part `sr` |
| Kaggle `mukul2427/pothole-detection-dashcam-dataset` | US YouTube dashcam potholes, OBB labels; low priority |
| Kaggle `shuaifanpi/urban-road-hazard-datasetyolo-format` | China, manhole/pit classes in separate folders; low priority |

## G. Cloud session 3 (2026-11-04 evening): potholes first, hard negatives, Mapillary
Gate: `vet_source.py` / per-family leak breakdown (rule v2, merged eval-hit preference), `KNOWN_FAMILIES`, one copy per Roboflow base, visual check.
Roboflow forks were made through the connector, each with a version that has no augmentation and no resize.

| source | what it is | check | verdict |
|---|---|---|---|
| Kaggle `mohamedaminebelasri7/roadscan-dataset` (5,837 img) | `DN_India_*` = RDD India (held); `*_vlcsnap-2025-02-*` = Italian dashcam with an orange hood, the same recordings as part `sr` family `kg_` (dates 2025-02-18/19/26, 2025-03-16, as in `sr` groups) | 195 eval hits, 173 of them on `parts_r3/sr` val/test | **REJECT** (duplicate of `sr` + RDD) |
| Kaggle `haseebarani/indian-road-pothole-v2-yolov8` (2,722 img, 4,729 pothole boxes) | Roboflow export, families `paN` and `img-N` | 183 eval hits spread over both families (161 in `paN`, 22 in `img-N`); 419 r2-train hits | **REJECT** (the eval hits cannot be removed by dropping a family without dropping everything) |
| Kaggle `ammanaveen/custom-multitask-indian-road-dataset-cmird` (CC BY-NC-SA 4.0) | Kerala, India: motorbike-mounted forward video (`video_NN_frame_N`, 2,789) + `anomaly_vlcsnap-2025-02-26` (500, the same Italian `kg_` dashcam as `sr`) + Cityscapes-style `leftImg8bit` (404); 10 numeric detection classes with **no class-name file** (sheet: 0 auto-rickshaw, 1 motorcycle, 2 bus, 3 car, 6 person; 4/5/7/9 on broken road / water) | not leak-checked (stopped at the class-name issue) | **REQUEST** (class names from the authors) + NC licence; the `anomaly_vlcsnap` family must go (= `sr`) |
| Kaggle `harshlokhande7/pothole-dataset-indian-indian-road-dataset` (3.3 GB) | 933 frames/photos, **no label files** | — | **REJECT** (no boxes) |
| Kaggle `zgpttai/road-hazard` (Sri Lanka) | — | see §F3 | REJECT (pseudo-labels) |
| Roboflow `lms-workspace-t8iih/pothole-dashcam` → fork `refyy-i/pothole-dashcam-57vla-vrt0p` | 316 img, 1,017 boxes; 157 are the Nienaber GoPro `G00…` family | 52 eval hits in `G00…`, 7 in `GN` | **REJECT** (remaining non-family images ≈ 60 with ~200 boxes, not worth a part) |
| Roboflow `rahul-tripathi/bharatpothole` (CC BY 4.0) → fork `refyy-i/bharatpothole-udcit` v1 | **India dashcam** (car, windscreen, rain/monsoon, wipers; 85 videos named `<yyyymmddhhmmss>_0060_frame_N` + `signal-2025-06-26-*`); 4,082 images = 1,342 originals with 1–4 Roboflow copies; 640×640 (resized by the uploader); one class `pothole`, many water-filled and tiny far potholes | **0 eval hits, 0 r2-train hits** (rule v2, all 4,082 images) | **ACCEPT (PROVISIONAL)** as part `bpo`: every 2nd frame, one copy per base, group = video, own val/test. Visual check (20 random): forward view, boxes on real potholes and water-filled potholes; some boxes on puddles over unclear surface; a sticker/watermark at the lower centre of the windscreen |
| Roboflow `yolo-ewrwa/dashcam-mg6en` → fork `refyy-i/dashcam-mg6en-0fwjp` v1 (7,106 img, 12,290 pothole boxes) | export is 3.8 GB (over the ~3 GB per-source limit) | not downloaded | **LAPTOP-VET** (`tools/rf_download.py refyy-i/dashcam-mg6en-0fwjp 1 …` then `vet_source.py`) |
| Roboflow `nids-de-poule/nid-de-poules` → fork `refyy-i/nid-de-poules-lolub` | 687 img; 665 are `potholesN` (andrewmvd) | 22 eval hits | **REJECT** (re-upload) |
| Roboflow `rakeshkumars-workspace/road-guard-pothole` → fork `refyy-i/road-guard-pothole-iir8e` | 958 img; 554 `potholesN` + YouTube/stock | 22 eval hits | **REJECT** (re-upload) |
| Roboflow `dimitri-farot-vxsds/nid-de-poule*`, `detection-eqrqu/nid-de-poule-1002-images`, `memory-akgoi/poule` | RDD class names (`D40`, `D00rotation`…) → RDD re-packs with rotation copies | — | REJECT (RDD, held) |
| Kaggle `mukul2427/pothole-detection-dashcam-dataset` (MIT) | US/UK **YouTube dashcam compilations** (`DASH_CAM_…_Miles_of_Potholes`, `Dangerously-Dodging-Potholes…`), OBB labels, 2,946 img / ~960 bases | 0 eval hits | **REJECT for now**: third-party YouTube footage (the uploader's MIT licence cannot cover it) and OBB labels need conversion; reconsider only if the owner accepts the licence risk |

**Hard negatives (hazard-free forward-view frames):** no new clean set found.
- The best available ones are inside parts already built: `egy_v2` now has 697 / 117 / 84 negative frames (train / val / test), many showing manhole covers or grates that are labelled as background (`vet/egy/expected_build_info_egy_v2.json`), and `ng8` has 207.
- RoadScan `BG_vlcsnap` frames are the `sr` Italian family (already used).
- The Sri Lankan background frames are pseudo-labelled.

**Mapillary Vistas v2.0 (report only, not downloaded).** By the class lists published in third-party code, the 124 v2.0 classes include `Pothole`, `Manhole` and `Catch Basin`, as segmentation masks (Pothole as a stuff class, Manhole and Catch Basin as instances); no speed-bump class was seen there. Images are street-level, mostly forward-facing, from many countries. The licence is stated by an aggregator as non-commercial research; the official Mapillary terms were **not verified (UNRESOLVED)**. Use would need the masks converted to boxes, and an owner decision on the licence.

**Roboflow forks created in session 3** (workspace `refyy-i`):
- kept for the laptop: `bharatpothole-udcit` (part `bpo`) and `dashcam-mg6en-0fwjp` (LAPTOP-VET);
- can be deleted: `pothole-dashcam-57vla-vrt0p`, `nid-de-poules-lolub`, `road-guard-pothole-iir8e`.

## H. Cloud session 4 (2026-11-04 late): pothole sources, d7k pre-check, CMIRD class IDs
| source | what was found | verdict |
|---|---|---|
| Roboflow `yolo-ewrwa/dashcam-mg6en` (d7k; fork `refyy-i/dashcam-mg6en-0fwjp`) | 7,106 images, 1 class `pothole`, CC BY 4.0. Created 2025-06, 22 versions. 4K originals plus 640 copies of the same frames. **Same drives as bpo** (BharatPotHole is a later re-upload of part of it). Details: `vet/d7k/PRECHECK.md` | **LAPTOP-VET**, train-only, use instead of bpo (not together); only the 4K `.jpg` originals |
| Kaggle `ammanaveen/custom-multitask-indian-road-dataset-cmird` (CMIRD) | Class IDs, from the evidence below: **0 auto-rickshaw, 1 bike, 2 bus, 3 car, 4 crack, 5 manhole, 6 person, 7 pothole, 8 speed bump, 9 waterlogging**. Evidence: (a) `yashshree7054/road-hazard-yolov8` `src/prepare_cmird.py`, comment "alphabetical order of the class names; checked on sample images"; (b) the author repo `ShehsaathVS/Custom-Multitask-Indian-Road-Dataset` README says "10 detection classes" but gives no names; (c) my visual check of 8 boxes per ID matches 0, 1, 2, 3, 6 (session 3) and **5 manhole, 8 speed bump, 9 waterlogging** (session 4); **IDs 4 and 7 both show cracks and potholes mixed**, so crack vs pothole cannot be confirmed. The student repo reports test AP 0.137 (pothole) and 0.040 (crack), which fits that confusion. Paper: "Safety-aware transformer-enhanced unified multi-task perception …" (PubMed 42410140). Viewpoint: motorbike-mounted (mirror and handlebar visible), Kerala. Licence CC BY-NC-SA 4.0 | **UNRESOLVED** for potholes (IDs 4/7). Possible later use: ID 5 manhole as hard negatives, ID 8 speed bump (95 boxes), after a vet run. The `anomaly_vlcsnap` family must go (= `sr`) |
| HRP4K, *Scientific Data* 2026 (doi 10.1038/s41597-026-07317-w) | Per search snippet: 6,003 perspective-view images, 7,217 potholes, YOLO + COCO. www.nature.com cannot be reached from this VM, so region, licence and download are not verified | **LAPTOP-VET** (read the paper, check the region and its overlap with RDD/andrewmvd) |
| KFUPM / Al Khobar pothole + depth set (arXiv 2504.13648) | Per search snippet: 981 dashboard-camera images at 1920×1080, Saudi Arabia, manually annotated; download not found | **REQUEST** (authors), MENA |

## I. Cloud session 5 (2026-11-04 night): systematic MENA / forward-view search, all queries logged
Gate for every source:
- one copy per Roboflow base;
- the KNOWN_FAMILIES filter;
- rule-v2 leak check against `protected_hashes.npz`;
- a group split by video or sequence;
- a visual D1–D6 check;
- a box audit before any val/test use.

Rejected on sight: top-down or close-up photos, synthetic data, pseudo-labels, re-uploads.
Status words: ACCEPT / REJECT / PARTIAL / REQUEST / NOT-VETTED (time).

### I1. Query log
**Roboflow Universe** (connector `universe_search`, datasets):
| query | relevant results (images, licence) | outcome |
|---|---|---|
| speed bump egypt | nothing Egyptian; only projects already in §A–§H | — |
| speed hump egypt cairo | `pothole-ishrc/hump-licby` (2,931, MIT; classes Humps + speed_breaker_alert, same size as ztskn below), `emirhan-ilhan/speed-bump-hump-*` (§E2.5), small `hump` sets (32–78 img) | nothing new from Egypt |
| road hump saudi riyadh | `road-hump-detection/road-hump` (821, CC BY 4.0) | forked → I2 |
| مطب, مطبات, حفرة, حفر الطريق (Arabic) | API error "Query contained no valid search terms after sanitization" | BLOCKED (the API rejects non-Latin text) |
| dos d'ane ralentisseur | only unrelated "DOS" projects | — |
| nid de poule route | `dimitri-farot-vxsds/nid-de-poule*`, `detection-eqrqu/nid-de-poule-1002-images`, `memory-akgoi/poule` = RDD re-packs (§G); `nids-de-poule/nid-de-poules` = andrewmvd re-upload (§G) | REJECT (known) |
| kasis çukur yol (Turkish) | `lanfers-place/yol-3ooes` (1,442 pothole, no licence) | REJECT (no licence) |
| polisi tidur / jalan berlubang lubang jalan (Indonesian) | `sca5a-kelompok-5-zus60/deteksi-polisi-tidur(-2)` (= part `pol`); small pothole sets `pi-q6ova/lubang-jalan` 665, rifkys `lubang-jalan` 690, anugrah 246 | `pol` already accepted; the rest NOT-VETTED (generic pothole, not MENA) |
| speed breaker pakistan road | `pothole-ztskn/speed-breaker-icar5` (2,930 / 5,304 boxes), `sakib-t1srr/speed-breaker-ii4pj` (1,061, seg), `yolov7-tipdu/speed-breaker-ffvo0` (497), `uiu-oeego/pothole-speed-breaker` (5,348), `janhavee/speed-breaker-detection-x1o0d` (790) | vetted → I2 |
| pothole morocco | none from Morocco (generic pothole sets only) | — |
Not reached by Universe search (no results named after them): Jordan, Iraq, Algeria, Tunisia, Libya, UAE, Oman, Qatar, Kuwait, Iran (Persian terms are non-Latin, rejected like Arabic).

**Kaggle API** (`datasets/list`, 39 terms, Bearer token from env; full list in the cloud scratchpad `ks5.tsv`, 14 unique hits):
- terms: "speed bump egypt", "speed hump egypt", "pothole egypt", "egypt road", "cairo road", "egyptian roads",
  مطب, مطبات, حفرة, حفر الطريق, "dos d'ane", "nid de poule", "ralentisseur", "kasis", "cukur yol", "polisi tidur",
  "jalan berlubang", "speed breaker pakistan", "pothole pakistan", "saudi road damage", "pothole saudi",
  "speed bump saudi", "road damage jordan", "pothole iraq", "pothole morocco", "pothole algeria", "pothole tunisia",
  "pothole uae", "road damage oman", "pothole qatar", "pothole kuwait", "pothole turkey", "speed bump turkey",
  "pothole iran", "speed bump iran", "unmarked speed bump", "speed breaker dashcam", "speed bump dashcam",
  "road hump".
- Hits not seen in earlier sessions: `yassienwasfy/egyptian-streets-dashcam` → I2 (egm);
  `bensemanemohamedreda/speedregulator-road-hazards-and-speed-bumps` = **part `sr`, already held**;
  `mohamedra9ab/object-detection-for-autonomous-cars-egypt` = a BDD100K re-pack (road users, no hazards);
  `abdulrahmanksaeed/pothole-patrol-normalized-dataset` (Lahore, COCO polygons, Roboflow-augmented, 137 MB, MIT);
  `latief18/data-jalan-berlubang-mk-cnn` (Indonesian classification); traffic-sign sets.

**GitHub** (`gh api search/repositories`): "speed bump detection egypt", "speed hump egypt yolo", "pothole egypt yolo",
"مطب" (Persian results: doctor's office apps), "egyptian roads dataset", "graduation project speed bump",
"ain shams speed bump", "speed bump detection dataset drive.google.com", "unmarked speed bump dataset", and
"speed bump / speedbump yolo / speed breaker yolo dataset" pushed after 2026-06-01. Nothing new with data. The leads
already in §E1 remain (Mohamed20384 → REQUESTS.md R2). Searches for Cairo / Alexandria / Mansoura / Zagazig / Helwan /
AAST / GUC / AUC / Nile University projects returned no repository with a labelled forward-view set (session 2 §E covered
about 60 repositories).

**Hugging Face** (`/api/datasets?search=`): "speed bump", "speed-bump", "speed breaker" → 0 datasets. "pothole" → 15
generic sets (keremberke / manot / adhisetiawan, Roboflow re-exports). "road damage" / "egypt road" →
`Hanno100/RoadDamageDetection-Egypt` = `road-damage-detection-wgjj4/rdd-6706t` **v8 augmented export** (data.yaml names
it; families IMG_N-N-_MOV / Egypt_N / WhatsApp-Video) = **same project as part `egy`** → REJECT (duplicate);
`masterofaudio2077/egyptian-streets` → I2 (egm).

**Zenodo** (`/api/records`, type dataset): "speed bump dataset", "speed hump images", "pothole dataset egypt",
"road damage egypt", "speed breaker images annotated", "unmarked speed bump". The one relevant hit is **IRDD**
(record 21167531) → I2. **Figshare** (`articles/search`): "speed bump", "pothole egypt" → nothing relevant
(RoadSens-4M is sensor data).

Not searched this session (time): Mendeley Data, IEEE DataPort, PapersWithCode, Scholar/arXiv full-text. §E–§H
cover them from sessions 1–4; KFUPM (arXiv 2504.13648) and HRP4K stay as REQUEST / LAPTOP-VET.

### I2. Sources checked in session 5
| source | facts (cloud, VERIFIED unless marked) | outcome |
|---|---|---|
| **SaudiRD** `refyy-i/saudird-luumi` v1 (CC BY 4.0; Crack / Pothole / Rut) | 1,171 img, 0 eval / 0 r2-train hits (`vet/sau/vet.json`). Pothole images are top-down / close-up phone photos. Windscreen frames IMG_8000–9999: 473, all scanned by eye, 12 excluded (rows of studs / grooved bands = possible stud hump or rumble strip) | **ACCEPT as part `sau`**: 461 train images, 459 hazard-free, 2 pothole boxes (hard negatives, Riyadh-area roads); `vet/sau/` |
| `pothole-ztskn/speed-breaker-icar5` → fork `refyy-i/speed-breaker-icar5-fwayv` v1 | 2,930 img, 5,304 boxes; families: 1,999 `speedbreakerrefinedone` + 40 `newonetrwww` + 13 `newtwoonweee` (train split); vet: 2,857 rejected-family images | **REJECT** (re-upload of the rejected `speedbreakerrefinedone` family) |
| `sakib-t1srr/speed-breaker-ii4pj` → `refyy-i/speed-breaker-ii4pj-rpmqq` v1 (instance seg) | 1,061 img; 1,026 `speedbreakerrefinedone`, 23 `newonetrwww` | **REJECT** (same family) |
| `yolov7-tipdu/speed-breaker-ffvo0` → `refyy-i/speed-breaker-ffvo0-an0ni` v1 | 497 img, one family `SpeedBreaker-N-`; **59 eval hits on rf8 val**, 47 r2-train hits | **REJECT** (rf8 re-upload); family added to `KNOWN_FAMILIES` |
| `uiu-oeego/pothole-speed-breaker` (5,348) | fork by slug and by URL: "Source project not found" | BLOCKED (connector) |
| Kaggle `bensemanemohamedreda/speedregulator…` | 10,156 img; families rdd_, kg_, rad_, dz_, rf_, night_, aug_ = the merged set behind part `sr` (`tools/make_items_sr.py`) | already held (no new data) |
| HF `Hanno100/RoadDamageDetection-Egypt` | 3,563 img, RDD v8 export of the `egy` project | REJECT (duplicate of `egy`) |
| **egm** = Kaggle `yassienwasfy/egyptian-streets-dashcam` / HF `masterofaudio2077/egyptian-streets` | 39.6 GB of Egyptian Mapillary phone frames with sequence / creator / GPS metadata; Cairo sample of 1,299 frames: forward windscreen views, 0 eval hits | **PARTIAL**: unlabelled → labelling pool (`tools/make_egm_pool.py`, `vet/egm/README.md`); no boxes counted |
| **IRDD**, Zenodo 21167531 (CC BY 4.0) | 8,479 smartphone-dashcam images, Wasit Governorate, Iraq; OBB labels D00 / D10 / D20 / D40 (pothole); pre-split 5,935 / 1,271 / 1,272 (stratified, not by sequence) | **ACCEPT train-only as part `irq`**: 7,802 img, **2,118 pothole boxes**, 6,348 crack-only frames, 0 leak hits; val/test held back (sample audit 8.3 % remove / 39.6 % incl. uncertain); `vet/irq/README.md` |
| `road-hump-detection/road-hump` → `refyy-i/road-hump-egz2f` (821, CC BY 4.0) | 821 img / 825 boxes, 0 leak hits; sheet: every image is a cropped close-up strip (aspect 2–6 : 1) of a **painted** hump (India) | **REJECT** (close-up crops, not forward view; marked bumps only) |

### I3. Session 5 totals against the targets (VERIFIED from the `expected_build_info.json` files)
| target (brief) | result | status |
|---|---|---|
| ≥ 800 **unmarked** speed-bump boxes (forward view, Egypt / MENA) | **0**. Every bump candidate found was a re-upload (`speedbreakerrefinedone`, rf8), a duplicate, or close-up crops. Leads that need the authors: DriveIndia (R1), the Egyptian videos (R2); the own-labelling pool egm (`vet/egm/README.md`) | **NOT MET**: BLOCKED by data availability |
| ≥ 1,500 pothole boxes from ≥ 2 more independent sources | **2,118** from 1 new source (IRDD, part `irq`, train-only) + 2 from SaudiRD | **PARTIAL**: box count met, only 1 source |
| ≥ 1,000 clean hazard-free frames from the same regions | `sau` 459 (Saudi, scanned by eye for bumps and potholes) + `irq` 6,348 crack-only frames (Iraq; pothole-free by label, **bump scan pending**) | **PARTIAL**: 459 fully checked |

Roboflow forks made this session (all in `refyy-i`, auto-orient only): `saudird-luumi`, `speed-breaker-icar5-fwayv`,
`speed-breaker-ii4pj-rpmqq`, `speed-breaker-ffvo0-an0ni`, `road-hump-egz2f`. The last four are rejected and can be deleted.

## J. Search 2026-11-07 (claude.ai session, after the final tests): new unmarked-bump sources
Goal: more forward-view **near, unmarked** speed bumps (C misses most of them: near-bump recall 0.250 on r2 test).
Searched: web (extended), Mendeley, IEEE DataPort, Egypt-specific papers, Roboflow Universe (connector: "unmarked bump",
"speed hump class:hump", "speed breaker/speed bump sort:updated", "updated:60d/120d"). Family check = file names read
through the connector after forking into `refyy-i` (no download).

| source | facts | verdict |
|---|---|---|
| Roboflow `qassim-university-rgdar/unmarked-bumps2` → fork `refyy-i/unmarked-bumps2-nbzeh` (820 img) | names: MVI_15xx, newonetrwww, speedbreakerrefinedone, VID_20190924, VIDEO0012, Image00398, imgge, bare numbers = the same families as the rejected `unmarked-bumps` (§F2) | **REJECT** (known families) |
| Roboflow `speedbumps-detection-using-yolov8/speedbumps-detection-2` → fork `refyy-i/speedbumps-detection-2-znzop` (2,122 img; E2.6) | merge of Image000xx (rf8/sb15), speedbreakerrefinedone, SpeedBreaker-N (59 eval hits in §I2), newonetrwww, imgge, web/product photos (`Economy-Speed-Hump…`, `download-N`) | **REJECT** (re-upload merge) |
| Roboflow `project-6qddw/bump-catcf` → fork `refyy-i/bump-catcf-fawye` (1,343 img, class `bump`; v1 = auto-orient only, generated 7 Nov) | one family `frame_inv_000001…001463.png`, all **640×240** strips → one video, cropped/possibly transformed view; not seen yet | **LAPTOP-VET** (`run_r3_J_vet.bat`); likely reject if the strips are not a forward camera view |
| Roboflow `amier-haziq-dwre4/hump-16nup` (fork `refyy-i/hump-16nup-4bmvs` v1, §F3) | 982 img, only 218 `Hump` boxes | **LAPTOP-VET** (`run_r3_J_vet.bat`) |
| Roboflow `qassim-university-oxvmm/unmarked-bumbs-gzg68` (642, instance seg) | same university as the rejected Qassim sets | not forked; low priority (likely the same families) |
| Roboflow `emirhan-ilhan/speed-bump-hump-unmarked` (86 img), `alia-khalifa/unmarked` (66), `yeotu/bump-*` (197–872), `rubayed-h9qzh/only-bump` (composite defects, not roads) | tiny or off-topic | REJECT / not worth a part |
| EGY_PDD (Port Said University, psu.edu.eg) | 14,612+ 2D images, YOLO boxes, 11 distress classes incl. Potholes and "Bumps & Sags" (no speed-bump class stated); academic licence, signed agreement + request form | **REQUEST** (A14): the form needs an authorised signature (supervisor) |
| DriveEdgeAI (MDPI *Computers* 15(7):403, 2026; Chaman et al., Morocco) | own set of 17,061 images incl. potholes and speed bumps; no public link found | **REQUEST** (authors; North-Africa roads) |
| Gupta et al. 2025 review (IJSSE 15(6)) | lists Dewangan & Sahu (3,450 augmented) and Xiang et al. (drone) bump sets, neither public | no lead |

Result: **no new public source with near, unmarked bumps passed the family check.** Remaining routes: the requests
(EGY_PDD, DriveIndia R1, Egyptian videos R2, DriveEdgeAI) and hand-labelling the Egyptian `egm` pool.
