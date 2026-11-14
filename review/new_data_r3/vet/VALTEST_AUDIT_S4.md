# Val/test label audit of the decision part-vals bpo, pol, ng8, red (cloud session 4, 2026-11-04)

Scope:
- every box in the val/test images of each part (boxes of the ORIGINAL export labels, so boxes that the build later dropped by FAR_TINY are included);
- 100 random train boxes (seed 0);
- every val/test image checked full-frame for clearly visible but unlabelled hazards.

Files per part: `vet/<part>/box_audit.csv`, `vet/<part>/valtest_missing_labels.csv`, `vet/<part>/expected_build_info_<part>_v2.json`.

The expected v2 counts come from `tools/apply_box_corrections.py` (with `--drop-images`), run here on the cloud builds. Policy: `remove_*` is removed in all splits; `uncertain` is kept in train and removed in val/test; listed images are dropped from val/test only.

**Tooling bug found and fixed during this audit.**
- What happened: my crop-sheet script read YOLO **polygon** lines as `xc yc w h`. bpo has 357 polygon lines (the other four exports have 0).
- Effect: the first bpo pass showed "boxes covering most of the frame" that were really small polygons.
- Fix: all 25 affected bpo rows were re-judged with the correct bounding box (`note` starts with `redo(polygon)`).
- The build itself was not affected: `gp36data.labels` converts polygons correctly.
- The session-3 hmp audit was made with the same script. Its 6 test "errors" were all polygon artefacts; it is corrected in `vet/hmp/BOX_AUDIT.md` (test 35.3 % → 0 % remove / 5.9 % with uncertain). `hmpt` (train-only) still stands for its other reasons.

## Error rates (VERIFIED: counted from `box_audit.csv`)
"errors" = `remove_*` verdicts; "uncertain" counts as an error in val/test (it is removed there).

| part | split | audited boxes | remove_* | uncertain | error rate (remove) | val/test rate incl. uncertain | missing-label images |
|---|---|---|---|---|---|---|---|
| bpo | val | 266 | 32 | 128 | 12.0 % | **60.2 %** | 0 flagged |
| bpo | test | 217 | 42 | 73 | 19.4 % | **53.0 %** | 0 flagged |
| bpo | train (100) | 100 | 3 | 19 | 3.0 % | (19 % uncertain) | — |
| pol | val / test / train | 100 / 25 / 100 | 0 | 0 | 0 % | 0 % | 0 |
| ng8 | val / test / train | 20 / 12 / 100 | 0 | 0 / 0 / 5 | 0 % | 0 % | 1 (test: pothole left of centre, ng8 labels bumps only) |
| red | val / test / train | 68 / 40 / 100 | 0 | 0 | 0 % | 0 % | 0 |

Notes:
- **bpo:** the val/test boxes are mostly tiny (≤ 20 px at 640 px) marks on smooth or wet roads, wet glare, white markings, zebra crossings and the windscreen sticker. Many are plausible water-filled potholes, but too many cannot be confirmed. The missing-label check found no clear unlabelled potholes; the problem is extra boxes, not missing ones.
- **pol / red:** the boxes follow a consistent convention. red labels each yellow stripe (plus one whole-reducer box); pol labels one box per hump.
- **ng8:** the train sample has 5 uncertain boxes (faint stripes, raised profile not visible).

## Expected v2 counts (VERIFIED: `expected_build_info_<part>_v2.json`)
| part | train img / boxes | val img / boxes | test img / boxes |
|---|---|---|---|
| bpo_v2 | 442 / 1,413 pothole | 102 / 105 pothole (45 images now negative) | 93 / 106 pothole (40 now negative) |
| pol_v2 | 375 / 375 bump | 100 / 100 bump | 25 / 25 bump |
| ng8_v2 | 278 / 145 bump | 67 / 20 bump | 38 / 12 bump (1 image dropped) |
| red_v2 | 334 / 338 bump | 69 / 68 bump | 35 / 40 bump |

bpo train is unchanged: only 8 of the 100 sampled boxes were still in the part, and they are `keep` / `uncertain` (kept). The rest had been removed at build by FAR_TINY.

## Recommendations
- **bpo: train-only.** Its val/test error rate after the definite removals is 12.0 % / 19.4 % (above 10 %). With the uncertain boxes it is 60 % / 53 %. A corrected bpo_v2 val/test would hold only 105 / 106 boxes whose labels are still partly unverified. Use the Egyptian `egy_v2` val/test (30 / 23 boxes, `vet/egy/BOX_AUDIT.md`) and Bučko as the pothole part-vals instead.
- **pol, red, ng8:** keep their val/test as decision part-vals. For ng8 use `ng8_v2` (1 test image dropped). pol_v2 and red_v2 equal the original parts.
- **d7k** (see `vet/d7k/PRECHECK.md`): same drives as bpo, so the same train-only rule applies.
