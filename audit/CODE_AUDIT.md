# GP36 — CODE_AUDIT (Phase 0, read-only)

Scripts present: `prepare_dataset.py` (7.7 KB, modified 2026-10-29 20:15) and `train.py` (1.9 KB, modified 2026-10-29 19:15).
**`detect_stream.py` does not exist** anywhere in `GP36_AI`, `GP36_Dataset`, `Desktop/graduation project` or `Desktop/New folder` (searched). There is also no ESP32 firmware, UDP code, tracking code or fusion code in the AI project folders.

Status labels: CONFIRMED = demonstrated with evidence; SUSPECTED = plausible but not demonstrated; VERIFIED-OK = tested and correct; NOT_TESTED.

---

## 1. `prepare_dataset.py`

### 1.1 Multi-period filename bug (the mandatory historical investigation)

* **Current code — VERIFIED-OK on the current data.** `save_as_jpg()` *appends* the extension (`Path(str(dst) + suffix)`) instead of replacing it, and the label uses `f.stem` with the same prefix. In the built `road_hazards_v2`:
  * all 3,804 images have exactly one label and vice versa (0 orphans in any split);
  * all 3,434 `rf_`/`pot_` label files match the raw source labels within 1e-4 (the remaining differences are the 6-decimal rounding on write);
  * all 3,243 Roboflow filenames contain extra dots (`103_jpg.rf.<hash>.jpg`).
* **Historical failure mechanism — INFERRED, not reproducible.** The buggy version was overwritten, so it cannot be inspected. The symptom in the log was 158 validation instances instead of about 1,136. That symptom fits a `with_suffix()`-style rename: it treats `.<hash>` as the extension and collapses `rf_103_jpg.rf.<hash>` to `rf_103_jpg.rf.jpg`. Several images then overwrite each other, while their labels keep the full hash name, so no image finds its label.
* **Residual risks in the current code:**
  * **CONFIRMED (latent) — `f.stem[:60]` truncation** for Roboflow names. There are no collisions today: the longest stem is 56 characters and the image/label counts match exactly. Any stem longer than 60 characters that shares a 60-character prefix would silently overwrite another image and its label. The code has no collision check.
  * **CONFIRMED — silent `except Exception: return`** in `save_as_jpg()`. If an image cannot be opened, no image is written, but `write_labels()` still writes its label. The result is an orphan label and nothing is logged. It was not triggered this time (0 unreadable images).
  * **CONFIRMED — the image extension is not normalised.** 8 PNG files named `.jpg` in the pothole set are copied unchanged as PNG data with a `.jpg` name. Ultralytics reads them by content, so the impact is low, but the pipeline's integrity checks cannot detect it.
  * **Regression tests needed:** names with 0, 1, 3 and 6 dots; Unicode and space characters; stems longer than 60 characters that share a prefix; `.JPG` vs `.jpg` case clashes; a WEBP or PNG file disguised as `.jpg`; an unreadable image (must fail loudly and write no label).

### 1.2 Other findings

| # | Finding | Status | Impact |
|---|---|---|---|
| C1 | `if out.exists(): shutil.rmtree(out)` with no confirmation. The default `--out road_hazards` would delete the v1 dataset. | CONFIRMED | Destructive overwrite risk. |
| C2 | The **Roboflow split is trusted as-is**. 140 byte-identical image groups cross train/val/test (see DATA findings). | CONFIRMED | Test and validation leakage. |
| C3 | **Image-level random split** for the crowd-sourced potholes, with no duplicate check. `pothole_076` (train) and `pothole_151` (test) are near-identical (dHash distance 0). | CONFIRMED | Leakage. |
| C4 | Speed-bump frames are split in time order with no gap at the boundaries. Adjacent frames 259/260 and 332/333 sit across splits. | CONFIRMED (minor) | 2 near-duplicates across the val/test boundary. |
| C5 | `split_list` float rounding: `int(370*0.9)` = 332, so the speed-bump split is 259/73/38 instead of 259/74/37. | CONFIRMED (cosmetic) | Different from the 70/20/10 the documentation states. |
| C6 | **ROI crop is applied to the speed-bump source only** (1920×1080 → 960×540, 2× zoom). At inference the ESP32-CAM frames will not be cropped, so this source teaches the model a scale it will not see live. | CONFIRMED (design) | Train/inference distribution mismatch. The crop policy must be applied consistently at inference or removed. |
| C7 | `read_labels()` **ignores the source class ID** and forces 0 (pothole) or 1 (speed bump) for the GitHub sources. Every source label is class 0 today (verified), so there is no damage yet. | CONFIRMED (latent) | Would silently relabel classes if a source ever had more than one class. |
| C8 | Polygon/bbox detection by token count: a 5-token line is always read as a bbox, and there is no check for ≥3 points or the [0,1] range. One Roboflow polygon (`219_jpg…`) was converted correctly. | CONFIRMED (latent) | A degenerate polygon would be misparsed. |
| C9 | No coordinate validation or clipping, no zero-area check, no duplicate-box check. All current labels pass geometry checks. | CONFIRMED (missing feature) | No guard against future bad labels. |
| C10 | No manifest, no checksums, no source traceability file, no log of rejected samples. `data.yaml` contains an absolute path. | CONFIRMED | Not reproducible or traceable. |
| C11 | PIL opens images without `ImageOps.exif_transpose`. All 4,374 raw images have EXIF orientation 1, so there is no impact today. | VERIFIED-OK (current data) | Latent risk for phone-camera datasets. |
| C12 | The script is not idempotent or atomic: it writes directly into the output folder, so an interruption leaves a half-built dataset. | CONFIRMED | Fix: build in a temp folder, then rename. |
| C13 | Speed-bump images are re-encoded as JPEG q95 after cropping. | CONFIRMED (minor) | Small generation loss. |
| C14 | 15 speed-bump frames (`lin061–lin090`, all in train) have empty labels and become negatives. It is not known whether they truly contain no bump. | NEEDS_REVIEW | Possible missing annotations. |

## 2. `train.py`

| # | Finding | Status |
|---|---|---|
| T1 | **`train.py` did not produce runs 3–5.** Their `args.yaml` show `patience=30, workers=2, cache=disk, batch=8, hsv_v=0.4, degrees=0.0, close_mosaic=10`, which are Ultralytics defaults from the `yolo` CLI. `train.py` hard-codes `hsv_v=0.5, degrees=3.0, close_mosaic=5, patience=15` and has no `workers` or `cache` arguments. | CONFIRMED |
| T2 | **The run-2 vs run-4 comparison is confounded.** The log says "only the image size changed". In fact image size, epochs (50→150), patience (15→30), batch (16→8), workers (8→2), `hsv_v` (0.5→0.4), `degrees` (3→0), `close_mosaic` (5→10) and disk caching all changed. The conclusion "image size is what helps" is not isolated. | CONFIRMED |
| T3 | Every training run automatically evaluates on `split="test"`, and the test score was then used to choose a model (run 4) and to analyse per-source errors. The historical test set is therefore **development-contaminated**. | CONFIRMED |
| T4 | `--device` defaults to `cpu`. | CONFIRMED (usability) |
| T5 | `workers` is not set, so it falls back to the Ultralytics default of 8. That caused the documented RAM crash. | CONFIRMED |
| T6 | Nothing is logged about the dataset version or checksum, git state, environment or seed list. The single seed 0 means no variance estimate is possible. | CONFIRMED |
| T7 | The run name is not unique by default (`gp36_road_hazards`). Ultralytics appends a number, so runs are not overwritten, but the names are not traceable. | CONFIRMED (minor) |

## 3. Inference, tracking, fusion and communication code

| Component | Status |
|---|---|
| `detect_stream.py` | **BLOCKED — does not exist** |
| Shared-frame dual-model pipeline (COCO YOLO11n + Hazard) | NOT_TESTED (not implemented) |
| Namespaced class IDs (`coco:*` / `hazard:*`) | NOT_TESTED (not implemented) |
| Tracking (ByteTrack/BoT-SORT) | NOT_TESTED (not implemented) |
| ESP32-CAM ingestion, UDP 4210 schema, heartbeats | NOT_TESTED (not implemented, no firmware in these folders) |
| Sensor fusion / SAFE-WARNING-STOP policy | NOT_TESTED (not implemented) |

## 4. Verified working components

* Ultralytics training and evaluation with the current stack: 5 runs completed, and the 4 v2 runs reproduce exactly (PROJECT_AUDIT §5).
* Image↔label matching in `road_hazards_v2`: 3,804/3,804.
* Class mapping, Roboflow `['Pothole','Speed Bump']` → `0 pothole, 1 speed_bump`: verified against `GP36_Dataset/roboflow/data.yaml`.
* WEBP/GIF → JPEG conversion: 27 WEBP and 1 GIF disguised as `.jpg` were all converted. v2 contains only JPEG, plus 8 PNG files with a `.jpg` name.
