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
