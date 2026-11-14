PR #2 was reviewed on the laptop. The new tool files and the vet folders are applied there, and STATUS Stage 23 has the review. Thank you, good work. Same rules as before: no leakage, nothing invented, every number cites a file, no keys printed or stored, no images in git. `perception/` stays unchanged.

Work on a NEW branch `claude/r3-cloud-data3` from `claude/r3-cloud-data2`. Open a new PR. Commit after each task so partial work is not lost.

Do NOT change the v3b_C recipe. The laptop fixes it after the D2 result. The open question is whether to keep `rdd_ji`, because pothole is our weakest class (r2 val 0.597).

## Task 1 (highest priority): egy box audit, ALL splits
Manhole covers labelled "Pothole" are also in TRAIN, not only val/test. A manhole labelled as a pothole teaches our FSM to brake for manholes.
- Look at every Pothole box of the egy export (~954), using crops or contact sheets kept outside git.
- Write `review/new_data_r3/vet/egy/box_audit.csv` with these columns:
  - `file` (Roboflow file name)
  - `label_sha256` (of the original label file)
  - `line` (0-based line in the label file)
  - `class_id`
  - `verdict` = keep / remove_manhole / remove_not_pothole / remove_bad_box / uncertain
  - `note`
- Rules:
  - Do not resize boxes. Remove or keep only.
  - "uncertain" counts as keep in train and remove in val/test.
- Add `tools/apply_box_corrections.py`:
  - input: a built part plus box_audit.csv;
  - output: a NEW part folder (e.g. `parts_r3/egy_v2`), never editing the old one;
  - it checks `label_sha256` before applying anything, writes its own manifest, checksums and build_info, and logs every change;
  - include tests.
- Report the counts per split: kept, removed by reason, uncertain.

## Task 2: hmp label audit (sample)
- Check all hmp val/test boxes and 100 random train boxes (seed 0). Use the same CSV format: `vet/hmp/box_audit.csv`.
- Report the error rate per split. If val/test errors are above 10 %, recommend that hmp be train-only.

## Task 3: cross-source duplicates among the new sources
Use all images of dmd, pol, red, ng8, hmp, ens and egy (all splits), plus the protected hashes.
- Do a pairwise rule-v2 check ACROSS sources. Any new-part val/test image that is near any image of another source counts.
- Write the result to `review/new_data_r3/vet/cross_source_pairs.csv`.
- Also write a drop list for val/test, `vet/cross_source_drop_valtest.csv`.
- Within-source pairs are already handled by the split rule.

## Task 4: more data, POTHOLES first (bump target is met)
- Target: ≥ 1,500 new forward-view (dashcam / phone-on-windscreen) pothole boxes from ≥ 3 independent sources.
  - Region priority: Egypt / MENA, then South Asia, then other.
  - Use the same gate and tools: `vet_source.py`, the leak check, KNOWN_FAMILIES, one copy per Roboflow base, group split, and an expected_build_info + keep_list per accepted part.
  - Reject top-down or close-up photos, synthetic images, pseudo-labels, and re-uploads of rf8/sb15/ghpot/andrewmvd.
- Also look for:
  - a clean set of hazard-free forward-view road frames, ideally from the same regions (hard negatives);
  - whether Mapillary Vistas v2 has pothole / manhole / speed-bump classes usable under its licence (report only, do not download it).
- Every candidate, accepted or rejected, goes in CANDIDATES.md §G with a reason.
- List any new Roboflow forks you create, and say which can be deleted.

## Output
- Update CLOUD_REPORT.md with a new §0 for session 3: the laptop commands for any new part, in the same style as §3.
- Run the full test suite.
- Push and open the PR. Write a short summary with each task's status.
