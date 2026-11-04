# GP36 — NEXT PHASE: REACH ≥ 0.90 HONESTLY (deadline: next supervisor meeting, ~8 Nov 2026)

You are continuing GP36 (Perception Pod, Project #36, student Ahmed Elreefy, supervisor Dr. Peter Makeen) in
`C:\Users\ahmed\Desktop\GP36_AI` (Windows, RTX 5050, `venv\Scripts\python`, `venv\Scripts\yolo`, Ultralytics 8.4.192).
Talk to Ahmed in Egyptian Arabic, short. Supervisor-facing files in English.

## 0. Read first (do not redo finished work)
- `HANDOFF-2026-10-31.md`, `HANDOFF-claude-code-2026-10-31.md`, `review/clean_r2/STATUS_for_claude.md` (Stages 1–6),
  `review/new_data_r2b/VALIDATION_REPORT.md`, `review/new_data/NEW_DATA_REPORT.md`, `audit/CLASS_MAPPING.md` (rules D1–D6, FAR_TINY),
  `audit/RDD2022_NOTES.md`, `supervisor_2026-11-01/README.md`.
- Verified state (from output files):
  - v1 (YOLO11n, v3a_r1): test mAP50 0.507 (pothole 0.660, bump 0.354) on the r1 test (324 img).
  - Run A (YOLO11n, v3a_r2, 3 seeds): val mAP50 0.665 / 0.686 / 0.673 (mean ≈ 0.675). Test, used once on s0: 0.462 (r2 test, 323 img).
  - External BD test (87 img): Run A 0.367, v1 0.328 (bumps).
  - Val error analysis (Run A, conf 0.35): bump precision 0.90 / recall 0.56; pothole precision 0.70 / recall 0.53.
    141 of 168 missed bumps come from 2 Egyptian dash-cam groups (r1g2418, r1g589). Many missed potholes are tiny and far (GoPro group r1g1132).
  - Pipeline latency on the laptop: ≈ 36 ms/frame p50 (both models).
- Conclusion already reached: more training on the SAME data gives < 0.02. The gain must come from data, task definition and model size.
- The supervisor said there is no need to record our own footage now. The focus is a much wider search for existing data
  (he mentioned Kaggle explicitly).

## 1. The target, defined so it cannot be faked
The supervisor wants "above 90" by next week. "90%" is meaningless unless the metric is fixed, so:
1. Report these four **separately for every class** (never only the average), on the internal val and (once, at the end)
   on the frozen test: **Precision (P), Recall (R), mAP50 and Accuracy**. Also keep mAP50-95 and F1 in the tables.
   Detection has no built-in "accuracy", so define it in writing before measuring and use the same definition everywhere:
   - box-level Accuracy = TP / (TP + FP + FN) at the chosen confidence threshold and IoU 0.5, per class;
   - image-level Accuracy = share of images where the "class present / not present" decision is correct
     (this needs hazard-free images in the evaluation set).
   Add `tools/metrics_report.py`, which writes all of these per class into one table from saved predictions.
2. Primary target: **mAP50 ≥ 0.90 per class (pothole, speed_bump) on a leak-free evaluation set.**
3. If that is not reachable by next week, say so with evidence. Then report which honest, clearly named metrics do reach 0.90
   (for example image-level accuracy, near-range recall within the pod's stopping distance, or precision at a fixed recall).
   Each must be defined in writing BEFORE you look at its value.
4. Never present a number ≥ 0.90 that came from leakage, test-set tuning, dropping hard images, or a random frame split.
   If a 0.90 needs one of these, it does not count.

## 2. Each class on its own (كل ناتج لوحده)
- Report every class separately, everywhere: pothole, speed_bump, and each COCO class used by the pipeline
  (person, bicycle, car, motorcycle, bus, truck, dog). For COCO, build a small labelled val set of our own road images,
  or state clearly that only the COCO benchmark number is available.
- Run a controlled experiment: **one single-class model per hazard** (pothole-only, bump-only) vs the 2-class model,
  same data, same settings, compared on val. Keep whichever is better per class, and check that the live pipeline
  (`perception/`) can run the chosen setup with acceptable latency. Do not change the FSM safety logic.

## 3. Split the data into manageable parts (نقسم الداتا)
The supervisor's point: do not throw a huge dataset at the laptop that it cannot train on. Instead:
- **Budget:** the RTX 5050 laptop must finish one training run in about 3–4 hours at most. Measure images/hour on the current
  setup and size each training set to fit (for example 6,000–10,000 train images at imgsz 960, fewer at 1280).
- **Curate, don't dump:** from every large source take a filtered, de-duplicated, balanced subset. Cap the images per
  source/video/group, keep the pothole/bump balance near 1:1, keep only boxes that pass D1–D6/FAR_TINY, and prefer images that
  add new places, cameras and conditions over more frames of the same scene.
- **Split into parts:** keep each new source as a separate, versioned part (part A, part B, ...), each with its own manifest.
  Train in steps: base model on r2 + part A, then fine-tune with part B, and so on. Keep a step only if val improves.
  This also shows which part actually helps.
- **Sequence-aware splits:** any new source gets its own train/val/test split by video/drive/group. The frozen r2 test is never
  changed or merged. Report val per part and per subset (source, Egyptian vs not, day vs night, marked vs unmarked bump,
  box size, near vs far), so it is clear where the model fails.

## 4. Data — this is where the gain must come from (search, download, filter, fix)
Priorities, highest value first:
1. **Search wide, Kaggle included (top priority).** Search Kaggle (kaggle.com/datasets; use the Kaggle API if a token exists in
   `%USERPROFILE%\.kaggle\kaggle.json`, never print it), Roboflow Universe (ROBOFLOW_API_KEY), Mendeley Data, Zenodo, Figshare,
   IEEE DataPort, Hugging Face datasets, GitHub, and datasets released with papers. Search terms: pothole, road damage, road anomaly,
   speed bump, speed breaker, speed hump, unmarked bump, and Egypt / Arab / Middle East roads. Keep a table of every candidate
   (link, images, classes, licence, augmentation, region, viewpoint, verdict) in `review/new_data_r3/CANDIDATES.md`.
   Many Kaggle sets are re-uploads of Roboflow or RDD data: detect this with hashes and filenames before counting them as new.
2. **Potholes at scale:** RDD2022 D40 (Japan/India already extracted, Czech kept apart as unseen test) and other large, documented
   pothole sets. Filter by D5/FAR_TINY, by box size and by visual spot checks, and check near-duplicates against r2.
3. **Speed bumps:** re-check the candidates already found (qubo needs relabel; ≈185 sub5 originals need relabel; Varma Mendeley set;
   Peralta-López Mexico set; SBP-YOLO repo data, which likely overlaps Roboflow). Find new, independent forward-view bump sets.
   Same validation as before: SHA-256 + dHash/pHash vs everything owned, family/sequence exclusion vs val/test, label check vs D1/D6,
   reject augmented copies, sideways images and crosswalk-like stripes.
4. **Hard negatives:** add hazard-free frames and crosswalk / manhole / patch / shadow frames as background images to train.
   Add a representative hazard-free subset to the NEW val/test splits, so false alarms and image-level accuracy are measured.
5. Fix clear label issues found in review (for example missing pothole labels that show up as "false positives" in
   `review/clean_r2/failure_val_runA/`). Use a new corrections file, the existing builder pattern, and a new dataset version
   (`v3b_*`). Never edit existing versions.

## 5. Model and training (only after the data gates pass)
Change one thing at a time and compare on val (mean of ≥ 2 seeds where the difference is small):
- Data effect first: same YOLO11n settings on the new parts.
- Then model size: YOLO11s, and YOLO11m if latency allows (the pipeline must stay ≤ ~50 ms/frame p50 on the laptop for both models).
- Then resolution / small-object tools: imgsz 1280, or a P2 head (SBP-YOLO reports that P2 + NWD loss helped small, far targets).
- Then the confidence threshold, chosen on val per class, optimising the recall the safety case needs.
- Report P, R, mAP50 and Accuracy per class for every candidate in one table.
- Use the frozen r2 test and the external BD test ONCE per final candidate, after selection on val. Log every test use in STATUS.

## 6. Rules (unchanged, non-negotiable)
- Full autonomy: do not ask Ahmed for permission. Decide, execute, document; he reviews at the end.
- Never delete or overwrite datasets, runs, weights, logs or reports. New versions go to new folders.
- No leakage: hash + perceptual near-duplicate checks across splits, and sequence/source grouping for anything video-derived.
- The test set is never used for any choice. One evaluation per model per benchmark version.
- Do not change `perception/` safety logic or thresholds to improve metrics.
- No invented numbers. Every number cites its output file. Use VERIFIED / PROVISIONAL / UNRESOLVED / BLOCKED.
- Never print or store API keys or tokens. Never upload project images anywhere.
- Never run two trainings at once on the GPU.

## 7. Deliverables
- Keep `review/clean_r2/STATUS_for_claude.md` updated (new "Stage 7+" sections).
- `supervisor_2026-11-08/`:
  - `README.md` (English, one page);
  - `METRICS.md`: per-class P / R / mAP50 / Accuracy tables for v1, Run A and new candidates, val sub-reports per part and
    subset, test and external tests with sample counts;
  - `DATA.md`: every source searched, accepted or rejected and why, with the size of each part;
  - key figures (confusion matrices, PR curves, failure sheets);
  - an honest statement of whether ≥ 0.90 was reached, and on which metric.

Start now. Re-read the state, write a short plan with the expected gain of each step in STATUS, then execute.
