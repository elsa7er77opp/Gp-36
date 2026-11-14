# egy box audit (cloud session 3, 2026-11-04)

Scope: every `Pothole` box of the Roboflow fork `refyy-i/rdd-6706t-8szyz` v1, all export splits: 954 boxes
(`box_audit.csv`, one row per box; `Crack` boxes are already `ignore` in the part and were not audited).

Method:
- Pass 1: numbered context crops (box × 2.2) with a thumbnail of the full frame, 40 per sheet, 24 sheets.
- Pass 2: every box left `uncertain` after pass 1 (309) was re-checked at higher zoom (box × 1.7, 330 px tiles).
- `note` starts with the pass that set the verdict.
- Sheets were kept outside git.
- Rules: D5 (manhole / utility cover / drain grate / crack / patch / wet patch → background). Boxes were never resized: a box that covers a cover plus a broken collar around it was removed when the box is centred on the cover. It was kept when the cover lies outside the box.

## Verdicts (VERIFIED: counted from `box_audit.csv`)
| verdict | all | export train | export valid |
|---|---|---|---|
| keep | 540 | 388 | 152 |
| remove_manhole (covers, drain grates, utility boxes) | 270 | 220 | 50 |
| remove_not_pothole (cracks, patches, stains, sand, milled surface, debris) | 111 | 72 | 39 |
| remove_bad_box (shadow, motion blur, box on nothing) | 19 | 12 | 7 |
| uncertain | 14 | 10 | 4 |
| **total** | **954** | 672 | 282 |

So 400 of 954 boxes (42 %) are not potholes by our rules, and **270 (28 %) are manhole covers or drain grates**. The
export splits are Roboflow's; our part splits are by video (below).

## Effect on the part (VERIFIED: `tools/apply_box_corrections.py` run in the VM on the cloud build of `egy`; `expected_build_info_egy_v2.json`)
| part split | pothole boxes before (`expected_build_info.json`) | after (`egy_v2`) | removed: manhole / not pothole / bad box | uncertain (kept in train, removed in val/test) | images that became negatives |
|---|---|---|---|---|---|
| train | 835 | 500 | 222 / 94 / 19 | 14 kept | 270 |
| val | 66 | 30 | 27 / 9 / 0 | 0 | 34 |
| test | 52 | 23 | 21 / 8 / 0 | 0 | 27 |

All 14 uncertain boxes fall in part-train (the val/test videos had none left after pass 2). One audited box is in an image that is not in the part.

**Consequences**
- egy val/test become small: 30 and 23 pothole boxes. They are usable as an Egyptian part-val only with that caveat.
- The 270 + 34 + 27 images that are now negatives are mostly frames showing a manhole or a grate with no pothole box. These are exactly the hard negatives the FSM needs, because the object is in view and labelled as background.
- The train split drops from 835 to 500 pothole boxes. The v3b_C arithmetic in `CLOUD_REPORT.md` §3 must use `egy_v2`. The recipe itself is not changed here.
