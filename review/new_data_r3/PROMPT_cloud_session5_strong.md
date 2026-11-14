GP36 — CLOUD SESSION 5: FULL EFFORT TOWARD 0.90, HONESTLY

You have a large budget: use it. Work through ALL tasks below, in order, without stopping early. If a task is blocked, record why and move to the next one.

Commit and push after every finished sub-task, on a new branch `claude/r3-cloud-data5` created from `claude/r3-cloud-data4` (or from the newest branch, if you already started session 5). Open ONE PR and keep updating its description.

If you already did some of these tasks from an earlier session-5 prompt, skip them and say so.

## Context (read first)
- `review/clean_r2/STATUS_for_claude.md`, Stages 20–25.
- `review/new_data_r3/CLOUD_REPORT.md`.
- `review/new_data_r3/CANDIDATES.md`.
- `supervisor_2026-11-08/`.

Current honest numbers (val; files cited in STATUS):
- r2-val mAP50 ≈ 0.655–0.665; per class, pothole ≈ 0.60 and speed_bump ≈ 0.71–0.74.
- The r2 TEST bump AP50 was 0.294.
- New-country part-vals: RSID bump 0.663, Bučko pothole 0.572.
- Image-level accuracy (ImgAcc) is already ≈ 0.90 for potholes and 0.82–0.89 for bumps.

The main failure is Egyptian / Middle-East UNMARKED speed bumps and small, far potholes in Egyptian dashcam frames. The goal is to get each per-class metric as close to 0.90 as possible by **legitimate** means only.

## Non-negotiable rules (unchanged)
- No leakage: rule v2, guards, group/sequence splits.
- The test split is never used for a choice.
- No invented numbers; every number cites a file.
- No keys printed or stored. No project images uploaded or committed.
- `perception/` is not changed.
- Any new metric is DEFINED and written into the docs before it is computed, and is always shown NEXT TO full mAP50, never instead of it.

## Task A: data for the main failure (≈ 40 % of the effort; the biggest lever)
Target: forward-view (dashcam or phone on the windscreen) data from Egypt or MENA.
1. **Unmarked speed bumps:** ≥ 800 boxes.
2. **Potholes:** ≥ 1,500 boxes from ≥ 2 more independent sources.
3. **Hazard-free road frames:** ≥ 1,000 clean frames from the same regions (hard negatives).

Search everywhere, systematically, and log every query and result:
- **Roboflow Universe**, through the connector: search in English, Arabic, French, Turkish, Urdu, Indonesian and Persian. Terms: speed bump, speed hump, speed breaker, unmarked bump, road hump, pothole, road damage, مطب, مطبات, حفرة, حفر الطريق, dos d'âne, nid de poule, kasis, çukur, polisi tidur, jalan berlubang. Filter by country names: Egypt, Cairo, Giza, Alexandria, Saudi, Riyadh, Jordan, Amman, Iraq, Morocco, Algeria, Tunisia, Libya, UAE, Oman, Qatar, Kuwait, Turkey, Pakistan, Iran.
- **Kaggle API**, with the same terms.
- **GitHub:** repository and code search, including Egyptian university graduation projects (Cairo, Ain Shams, Alexandria, Mansoura, Zagazig, Helwan, AAST, GUC, AUC, Nile University). Look for README links to Drive or Mega datasets.
- **Other hosts:** Hugging Face datasets, Zenodo, Figshare, Mendeley Data, IEEE DataPort, PapersWithCode, and Google Scholar / arXiv papers with "dataset available" (e.g. Saudi road damage, Jordan potholes, KFUPM, Egyptian roads).

Gate (same as before): one copy per Roboflow base; KNOWN_FAMILIES; rule-v2 leak check against `protected_hashes.npz`; group split by video; visual D1–D6 check; a box audit for any val/test you propose. Reject top-down or close-up photos, synthetic data, pseudo-labels and re-uploads.
- For each accepted source, write `vet/<part>/` (expected_build_info, keep_list, box_audit for val/test) and the laptop commands.
- For each source that needs the authors: write the exact request email text in `review/new_data_r3/REQUESTS.md`, for Ahmed to send.
- Record everything in CANDIDATES.md §I.
- **Also vet SaudiRD** (`refyy-i/saudird-luumi`).

## Task B: evaluation and inference levers, as code that is tested and ready for the laptop GPU (≈ 30 %)
Each lever is a SEPARATE reported row; none replaces the plain model. Each comes with a pre-registered hypothesis written into `CLOUD_REPORT.md` §0-S5 before the laptop runs it.
1. **Range-aware metric (STATUS L5).**
   - Add to `tools/metrics_report.py` an option `--care near` with the KITTI/COCO "ignore region" semantics: GT boxes outside the care range become ignore; a prediction matched to an ignore GT is neither TP nor FP; an unmatched prediction whose box lies fully outside the care range is ignored.
   - Care range = the existing NearR definition (y2 ≥ 0.6·H and sqrt(area) ≥ 0.05, in `metrics_report.py`).
   - Report AP50 / P / R / BoxAcc for "near" next to "all".
   - Write a short justification: the pod brakes for near hazards, and the FSM needs a confirmation distance.
   - Unit tests on toy cases.
2. **Weighted Boxes Fusion ensemble.** `tools/wbf_ensemble.py`: input two or more `predictions.json` (different seeds or models) → a fused `predictions.json`. Implement WBF yourself (no new dependency unless it is pip-installable and pinned). Tests.
3. **Sliced (tiled) inference for far, small objects.** `tools/sliced_predict.py`: full frame plus overlapping tiles, merged by NMS or WBF, writing `predictions.json` in the same format as Ultralytics `save_json`. It runs on the laptop with the Ultralytics weights. Measure its latency overhead on the laptop.
4. **TTA** (Ultralytics `augment=True`): the laptop command only.
5. **Training-recipe research** (no runs here): read the Ultralytics docs and recent papers on small-object road-hazard detection. Then write 2–3 concrete `yolo train` argument sets for an 8 GB RTX 5050, ≤ 4 h each: imgsz, epochs, close_mosaic, copy_paste, scale, mixup, multi_scale, and the P2 head; YOLO11n vs 11s, with latency in mind. Each set gets a reason and a hypothesis.

## Task C: deliverables for the supervisor (≈ 20 %)
1. **`tools/make_supervisor_tables.py`.**
   - Input: `review/metrics_r3/<name>/report.json` files (read `metrics_report.py` for the schema) plus a small table spec.
   - Output: Markdown tables per class with P, R, F1, mAP50, mAP50-95, BoxAcc, ImgAcc, NearR, P@R50 and near-range AP50, both at the val-chosen threshold and at deploy conf 0.35, with the source file and the image/box counts.
   - Also PNG figures (matplotlib, Agg).
   - It formats only, never computes. It refuses to call a report "test" unless its split is test.
   - Tests.
2. **`tools/test_ledger.py`** and `review/metrics_r3/TEST_LEDGER.csv`.
   - One test use per model per benchmark; `check` exits non-zero on a repeat.
   - Back-fill past test uses from STATUS with the stage; mark unclear ones UNRESOLVED.
   - Tests.
3. **Draft `supervisor_2026-11-08/README.md` "Honest 0.90 statement".** Say:
   - which metrics can reach about 0.90 (ImgAcc, near-range AP, P@R50), with the evidence files;
   - which cannot by 8 Nov (full mAP50 per class), and why: data scarcity for Egyptian unmarked bumps, tiny far potholes, and label noise found by the audits;
   - what would get there with more time (DriveIndia, the Egyptian video request, own labelled Egyptian footage).
   - Use `TODO(laptop)` where final numbers go.

## Task D: quality (≈ 10 %)
- Run the full test suite.
- Re-read your own new code for bugs; the polygon bug last time was found this way.
- List any risk to the laptop pipeline in `CLOUD_REPORT.md` §0-S5 "Risks".

## Final PR summary
Give a table of tasks with done / partial / blocked; new data boxes per class with sources; new tools; the laptop commands in run order; and the hypotheses.
