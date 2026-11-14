# hmp label audit (cloud session 3, 2026-11-04; CORRECTED in session 4)

> **Correction (session 4).** The session-3 crop sheets read YOLO **polygon** lines as `xc yc w h`. The hmp export has 713 polygon lines, and 20 of the audited rows were polygons. All 6 test "box errors" (and 3 of 4 train errors) were artefacts of that bug. All 20 polygon rows were re-judged with the correct bounding box; their `note` starts with `redo(polygon)`. They are real rubber speed bumps (mostly night), apart from 2 bump pieces lying along the kerb and 1 unclear wet edge, which are now `uncertain`. Corrected rates (VERIFIED from `box_audit.csv`): **val 0 %, test 0 % remove / 5.9 % with uncertain, train 1 % remove / 4 % with uncertain**. The table below is the session-3 original, kept for the record.

Scope (`box_audit.csv`, same columns as egy plus `part_split` and `sample`):
- **every** box in the images of the hmp part val and test (84 boxes: val 67, test 17);
- **100 random train boxes** (seed 0, drawn from the original-label boxes of class 1 humps or 3 pothole in part-train images).

Part splits are taken from the cloud build manifest (`expected_build_info.json`). Crops were reviewed by eye, and the sheets were kept outside git.
The verdict names are the egy names. For hmp, `remove_bad_box` = the box is not on a speed bump (corner, car, gutter, crack, or a bump outside the box).
`note` tags image-level problems that are not box errors:
- `IMG:rotated_copy`: rotation-augmented copy with black or white corners;
- `IMG:product_photo`: rubber bump photographed on a white background;
- `IMG:stock_watermark`: shutterstock or gettyimages watermark;
- `IMG:close_up`;
- `IMG:photo_of_photo`.

## Results (VERIFIED, counted from `box_audit.csv`)
| part split | audited boxes | box errors (`remove_*`) | box error rate | uncertain | images not forward-view (IMG tags) | images with other bumps not labelled |
|---|---|---|---|---|---|---|
| val | 67 | 0 | 0.0 % | 0 | 34 (50.7 %) | 6 |
| test | 17 | 6 | **35.3 %** | 0 | 0 | 0 |
| train (sample) | 100 | 4 | 4.0 % | 1 | 17 (17.0 %) | 1 |

Further finding: the same scene appears in more than one split of the part.
- Driveway scene: `humps-v3-_622/_624` in val, `_627` in train.
- Rubber-bump road: `_501` in val, `_634/_635` in train.

These are small-angle rotations and crops of one photo. Rule v2 cannot match them because it covers only flips and 90° turns, so the within-part guard did not catch them.

## Recommendation (session 4 status)
The box-error argument no longer applies. The train-only recommendation still stands on the other two findings: half of val is product, stock or rotated photos, and the same scenes appear across splits through small-angle rotated copies. The laptop has already adopted `hmpt` (train-only).

## Recommendation (session 3, original)
- The test box error rate is 35.3 % (above 10 %).
- The val set is half product, stock and rotated photos.
- Val and train share scenes.

**Make hmp train-only** (rebuild it with every image in train). Do not use its val/test for any decision. In train, the 17 % non-forward-view and stock-watermarked images are a licence and domain risk.
A stricter option is to drop the images tagged `IMG:` and keep only the night dashcam frames (`humps-v2-*` and the night `humps-v3-` 100–430 range). That needs a rule fixed before use, e.g. a name-range include. It is not done here.
