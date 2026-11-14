# GP36 — Data search and data parts (round r3, 2–8 Nov 2026)

Every number below comes from a file in the project. The file is named next to it.
- Full candidate table: `review/new_data_r3/CANDIDATES.md`.
- Part build reports: `parts_r3/<part>/build_info.json`.

## 1. How the search was done
- **Sources searched:**
  - Kaggle: web search, plus the public Kaggle listing API with 8 search terms → 159 unique datasets.
  - Roboflow Universe, Mendeley Data, Zenodo, Figshare, Hugging Face, IEEE DataPort.
  - Datasets released with papers: SBP-YOLO, Peralta-López 2023, Bučko 2022, iWatchRoad.
- **Search terms:** pothole, road damage, road anomaly, speed bump / breaker / hump, unmarked bump, Egypt road.
- **Access limits on the project laptop:**
  - **Kaggle downloads need an API token** (the anonymous request returns 404).
  - **Roboflow needs an API key.**
  - Neither was available, so those candidates are listed as BLOCKED, not rejected.
  - Zenodo serves ~10–40 KB/s per connection, so only selected files of the 13.2 GB RSID archive were fetched, using HTTP range requests (`tools/remote_zip.py`).

## 2. Validation gate (applied to every accepted source, `tools/build_part.py`)
1. **Integrity:** the image decodes, and there is no EXIF rotation.
2. **Explicit class mapping per source:** an unmapped class is a build error. Manholes, cracks, patches and repairs are mapped to *ignore* and become background (owner rules D1–D6).
3. **FAR_TINY rule:** hazard boxes with √(w·h) < 2 % of the image are removed. An image whose hazard boxes are all removed this way is dropped.
4. **Leakage guard against the frozen internal benchmark (r2, all splits):**
   - exact SHA-256 match, or
   - perceptual near-duplicate: dHash over 8 flips/rotations ≤ 4 **and** pHash ≤ 10.
5. **Sequence / family exclusion:**
   - A whole source family that shares scenes with our val/test is excluded. Example: the South-African GoPro `G00…` frames inside RSID, which are the same family as the rf8 val/test group.
   - Each new source gets its **own** train/val/test split by drive, video, day or location, never by frame.
6. **Visual spot checks:** contact sheets in `review/new_data_r3/`.

New data never enters the internal val/test. New sources go to train, or to their own separate val/test.

## 3. Parts built

| Part | Source (licence) | Region / camera | Split rule | Train | Val | Test | Gate result |
|---|---|---|---|---|---|---|---|
| `rsid` | Road Surface Irregularities Dataset, Zenodo 18789662 (CC BY 4.0) | Vilnius, Lithuania: FHD dashcam, phone, ZED2; plus another dashcam family | by drive sequence / recording day; ≤ 4 frames per bump; hard negatives (manhole-only, empty frames) | 773 img (421 bump, 76 pothole boxes; 318 negatives) | 252 (140 bump) | 234 (141 bump) | 0 leak hits; GoPro family (5,215) and unknown-provenance images (235) excluded |
| `bucko` | Bučko et al. 2022, Figshare 21214400 (CC BY 4.0) | Slovakia, FHD dashcam, clear / sunset / evening / night / rain | by location (Ca, Pd → train; Pr → val/test); every 4th frame | 282 (357 pothole) | 125 (186 pothole) | 120 (232 pothole) | 0 leak hits; undocumented class 1 (manhole covers) → ignore |
| `rdd_ji` | RDD2022 Japan + India D40 (CC BY-SA 4.0) | dashcam / phone | train only | 2,920 (5,428 pothole); capped at 500 in v3b_A | — | — | 0 leak hits; 3,791 crack/manhole/repair boxes ignored |
| `rdd_cz` | RDD2022 Czech D40 | dashcam | external test only | — | — | 154 (197 pothole) | 0 leak hits |

## 4. Rejected or blocked, with the reason (short; the full table is in CANDIDATES.md)
- **Rejected:**
  - New Roboflow speed-bump zips from 31 Oct: `sub5`, `qub1`, `qub2` share scenes with our val/test or are augmented copies (`review/new_data_r2b/VALIDATION_REPORT.md`).
  - Nienaber South-Africa sets on Kaggle: the same family as our val/test.
  - Bangladesh Mendeley sets: classification folders with no boxes, and augmented.
  - Pakistan Zenodo anomaly set: CCTV view; accident/fight classes.
  - Hugging Face pothole sets: small re-uploads.
- **Blocked:**
  - 15+ Kaggle speed-bump / pothole sets, including `object-detection-for-autonomous-cars-egypt` (Egyptian street objects), `speedregulator-road-hazards-and-speed-bumps` (updated Oct 2026) and BharatPotHole.
  - All Roboflow Universe bump projects.
  - EGY_PDD (request to the supervisor pending).

## 5. Composed training versions
| Version | Contents | Train images | Train boxes pothole / bump | File |
|---|---|---|---|---|
| r2 (baseline) | rf8 + ghpot + sb15, cleaned | 3,035 | 2,570 / 1,404 | `road_hazards_v3a_r2/build_info.json` |
| v3b_A | r2 + rsid + bucko + rdd_ji (500) | 4,590 (1,124 negatives) | 3,930 / 1,825 | `road_hazards_v3b_A/build_info.json` |

The val and test of every version are the r2 val/test, unchanged.

## 6. New parts, sessions 2–4 (cloud), with their gates

Counts are from the cloud builds (`tools/build_part.py` / `tools/apply_box_corrections.py`, run against `review/new_data_r3/protected_hashes.npz`). Each row cites its file under `review/new_data_r3/vet/<part>/`. **TODO(laptop):** the laptop build must confirm every count (compare its `build_info.json` with the expected file).

Columns per split: images / pothole boxes / speed-bump boxes / hazard-free images.

| part | source | author | licence | region / viewpoint | train | val | test | file |
|---|---|---|---|---|---|---|---|---|
| dmd | dm-druid/SpeedBumps-Detection, GitHub (github.com/dm-druid/SpeedBumps-Detection) | lyqun / dm-druid (GitHub) | MIT | China, campus roads; phone at windscreen height, forward | 277 / 0 / 319 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | `vet/dmd/expected_build_info.json` |
| pol | Roboflow `sca5a-kelompok-5-zus60/deteksi-polisi-tidur` (fork `refyy-i/deteksi-polisi-tidur-tblnr` v1) | SCA5A Kelompok 5 (Roboflow workspace) | CC BY 4.0 | Indonesia, residential alleys; forward, low camera; unmarked concrete + painted humps | 375 / 0 / 375 / 0 | 100 / 0 / 100 / 0 | 25 / 0 / 25 / 0 | `vet/pol/expected_build_info_pol_v2.json` |
| red | Roboflow `rompe-j2aun/reductor-w4anu` (fork `refyy-i/reductor-w4anu-q04yg` v1) | ROMPE (Roboflow workspace) | CC BY 4.0 | Latin America (Spanish labels); 4K camera mounted low; painted reducers | 334 / 0 / 338 / 2 | 69 / 0 / 68 / 1 | 35 / 0 / 40 / 0 | `vet/red/expected_build_info_red_v2.json` |
| ng8 | Roboflow `speedbreakerdatalabelling/speed-breaker-detection-ng8ne` (fork `refyy-i/speed-breaker-detection-ng8ne-pmyzk` v1), families VID_/IMG_ only | SpeedBreakerDataLabelling (Roboflow workspace) | CC BY 4.0 | India; portrait phone dash video; painted breakers + hazard-free frames | 278 / 0 / 145 / 133 | 67 / 0 / 20 / 47 | 38 / 0 / 12 / 26 | `vet/ng8/expected_build_info_ng8_v2.json` |
| ens | Roboflow `ensam-wyp9x/total-jcwvt` (fork `refyy-i/total-jcwvt-f9ffa` v1), numeric names ≥ 100 | ENSAM (Roboflow workspace) | CC BY 4.0 | South Asia (probably Bangladesh) campus roads; forward; painted raised humps | 414 / 0 / 422 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | `vet/ens/expected_build_info.json` |
| egy_v2 | Roboflow `road-damage-detection-wgjj4/rdd-6706t` (fork `refyy-i/rdd-6706t-8szyz` v1) | RDD (Roboflow workspace) | CC BY 4.0 | Egypt (file family `Egypt_*`; city not verified); iPhone dashcam + WhatsApp dash clips + phone photos | 1118 / 500 / 0 / 697 | 147 / 30 / 0 / 117 | 105 / 23 / 0 / 84 | `vet/egy/expected_build_info_egy_v2.json` |
| bpo | Roboflow `rahul-tripathi/bharatpothole` (fork `refyy-i/bharatpothole-udcit` v1); upstream `yolo-ewrwa/dashcam-mg6en` | Rahul Tripathi (re-upload) / "YOLO" workspace (upstream) | CC BY 4.0 | India; car dashcam behind the windscreen, monsoon (recommended train-only, `vet/VALTEST_AUDIT_S4.md`) | 442 / 1413 / 0 / 2 | 102 / 214 / 0 / 0 | 93 / 202 / 0 / 1 | `vet/bpo/expected_build_info.json` |
| hmpt | Roboflow `thesis-grzdh/road-hazard-detection-6` (fork `refyy-i/road-hazard-detection-6-g5pbz` v1), family `humps-v*` | thesis-grzdh (Roboflow workspace) | CC BY 4.0 | India, mostly night dashcam + some web photos | 431 / 0 / 458 / 0 (all hmp splits moved to train; sum of `vet/hmp/expected_build_info.json` splits; TODO(laptop): hmpt build) | — | — | `vet/hmp/expected_build_info.json` |

Citation: each Roboflow dataset is cited as "<project name>, Roboflow Universe, <workspace>, <year>, CC BY 4.0, https://universe.roboflow.com/<workspace>/<project>". dm-druid as "dm-druid/SpeedBumps-Detection, GitHub, 2018, MIT".

### 6.1 Gates passed by these parts
| gate | result | file |
|---|---|---|
| leak rule v2 vs every protected val/test/external image | 0 eval hits for the images kept in every part | `vet/<part>/vet.json` (`leak_hits_eval`), `vet/<part>/family_breakdown.md` |
| known re-upload families | dropped by name (e.g. `speedbreaker_N` in ng8: 113 eval hits; bare-numeric family in hmp: 17) | `vet/<part>/family_breakdown.md` |
| one copy per Roboflow base / no augmentation | Roboflow forks exported as a version with no augmentation and no resize | `CANDIDATES.md` §F |
| cross-source duplicates (7 parts) | 2 train/train pairs (dmd = hmp), 0 val/test drops | `vet/CROSS_SOURCE.md` |
| box audit egy (all 954 Pothole boxes) | 400 not potholes (270 manhole covers / grates) → `egy_v2` | `vet/egy/BOX_AUDIT.md` |
| box audit hmp (val/test + 100 train) | box errors val 0 %, test 0 % (5.9 % with uncertain), train 1 %; train-only because half of val is product/stock photos and scenes repeat across splits | `vet/hmp/BOX_AUDIT.md` |
| box audit bpo, pol, ng8, red (val/test + 100 train) | bpo val 12.0 % / test 19.4 % definite errors → **train-only**; pol, red 0 %; ng8 0 % (1 test image dropped for an unlabelled pothole) | `vet/VALTEST_AUDIT_S4.md` |

Decision part-vals after the audits: pol_v2, red_v2, ng8_v2 (bumps), egy_v2 and Bučko (potholes). bpo, hmpt, dmd and ens are train-only.

### 6.2 Rejected sources (summary; every row with its reason in `CANDIDATES.md` §E–§H)
- **Re-uploads of our own evaluation families** (rf8 / sb15 / ghpot / andrewmvd / Nienaber), found by name and by leak hits. These include most Roboflow and Kaggle "speed bump" sets: Qassim unmarked-bumps, speed-unmarked-bumb, speed-bump-tonyt, cse400B, jayaprakashpondy, david2do, haseebarani, nid-de-poule, road-guard, pothole-dashcam.
- **Duplicates of data we hold:** RoadScan and the CMIRD `anomaly_vlcsnap` frames are the same Italian dashcam as part `sr`; several "nid de poule" sets are RDD re-packs; BharatPotHole is a re-upload of the d7k drives.
- **Wrong viewpoint or content:** top-down photos taken standing on the bump (takqu), stock / product photos (uthm), a synthetic city (khadijazarriq), Kakao road-view captures (leeyuil), CCTV crime clips.
- **No boxes or pseudo-labels:** classification folders (several Kaggle sets); the Sri Lanka set (two folders with the same images and labels at different model thresholds).
- **Licence or access:** YouTube dashcam compilations (mukul2427); DriveIndia (not published); Mapillary Vistas (non-commercial terms unverified); CMIRD (class IDs 4/7 unclear, NC licence).

### 6.3 Leak-guard bug (rule v1) and its fix (rule v2)
- Until 2026-11-04 the near-duplicate rule compared the dHash under all 8 flips/rotations, but the pHash only for the unrotated image. A mirrored, re-encoded copy of an evaluation image therefore had dHash ≈ 2 but pHash ≈ 32, and was **not** caught.
- The fix (rule v2) compares both hashes under the same transform (`tools/leak_check.py`, `tools/build_part.py`).
- On one rejected Roboflow re-upload, rule v1 found 229 hits on our val/test images and rule v2 found 328 (`review/new_data_r3/vet/cloud_leak_summary.csv`).
- The parts used in training before the fix were re-checked with rule v2 on the laptop (STATUS Stage 21–24).
- A second tooling issue was found in session 4: the audit crop sheets misread polygon labels. The builds were not affected, only two audits, and both were corrected (`vet/VALTEST_AUDIT_S4.md`).
