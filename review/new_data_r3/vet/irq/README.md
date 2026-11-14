# irq: IRDD, Iraqi Road Damage Dataset (Zenodo record 21167531, CC BY 4.0), cloud session 5

## Source (VERIFIED from the Zenodo record and the downloaded files)
- 8,479 smartphone-dashcam images from Wasit Governorate, Iraq; 848×464 or 1920×1080 (some portrait).
- Labels: YOLO OBB (class + 8 corner coordinates). Classes D00 / D10 / D20 (cracks) and D40 (pothole).
- Its own split (5,935 / 1,271 / 1,272) is "iterative multi-label stratification", i.e. by image, not by sequence.
  That split is IGNORED (it leaks: 8,479 images form only 4,763 rule-v2 near-duplicate clusters, `vet.json`).
- File names `IRDD_Img_moblileNNNN` are in capture order. Groups = 100-name blocks ∪ near-duplicate clusters.

## Gate results
| step | result |
|---|---|
| class map | 0 / 1 / 2 → ignore (D5 cracks), 3 → pothole |
| KNOWN_FAMILIES | none |
| leak check, rule v2 vs `protected_hashes.npz` | **0 eval hits, 0 r2-train hits** (`vet.json`) |
| OBB → box | `gp36data.labels` turns the 8 corners into an axis-aligned box. **642 images dropped** by the existing strict rule `POLY_OUT_OF_RANGE` (corners slightly outside [0,1], e.g. 1.012). They hold only 51 of the 2,169 pothole boxes (41 images); the gate was not changed for this source |
| exact duplicates in part | 35 dropped |
| visual (24 random pothole frames, own sheet outside git) | true windscreen forward views of Iraqi urban and suburban streets; manhole covers visible but unlabelled (correct by D5) |
| box audit, sample of 48 val/test boxes of the split variant (`box_audit_sample_valtest.csv`) | 29 keep, 15 uncertain (puddles, faint marks, oval rings), 4 remove (3 alligator-crack texture, 1 manhole-like) → **8.3 % remove, 39.6 % with uncertain** |

## Decision: **ACCEPT, train only** (`--all-train`), PROVISIONAL until the laptop A/B
- 39.6 % (with uncertain) is far above the 0–6 % of the decision part-vals (`VALTEST_AUDIT_S4.md`). So IRDD val/test
  is **not** used for any decision before a full audit of its 576 val/test boxes (split variant:
  `build_info_split_variant_cloud.json`; 345 val + 231 test boxes).
- Train-only build (`expected_build_info.json`): **7,802 images, 2,118 pothole boxes, 6,348 hazard-free images,
  48 groups**, 0 leak drops.
- The FAR_TINY rule removed 0 boxes; the images are small (848 px wide), so the potholes are mid-size.
- Risk: train label noise of about 8 % definite errors, plus puddle boxes. Judge it with the A/B: v3b_C + irq vs
  v3b_C on Bučko val and egy_v2 val (pothole AP50). Keep irq only if pothole AP50 ≥ +0.02 on at least one of them
  and does not drop by more than 0.02 on the other, and r2 val bump stays ≥ −0.02.
- About 81 % of the kept images are hazard-free (cracks only) Iraqi street frames. That partly covers the
  "≥ 1,000 clean frames from MENA" target as **pothole**-negatives only: IRDD does not label speed bumps, and a
  bump-free check was **not** done here. `TODO(laptop)`: scan a sample of the irq negatives for bumps, as was done for
  `sau`. Until then the bump class may see unlabelled bumps as background in these frames.

## Laptop
```
mkdir ..\GP36_Dataset\raw_v3\zen_irdd
curl -L -o ..\GP36_Dataset\raw_v3\zen_irdd\irdd.zip "https://zenodo.org/records/21167531/files/IRDD_v1.0_final.zip?download=1"
python -I tools/intake_zip.py ..\GP36_Dataset\raw_v3\zen_irdd\irdd.zip ..\GP36_Dataset\raw_v3\zen_irdd\x   (or unzip into x)
python -I tools/make_items_yolo_export.py --root ..\GP36_Dataset\raw_v3\zen_irdd\x --part irq ^
    --cmap "{\"0\":\"ignore\",\"1\":\"ignore\",\"2\":\"ignore\",\"3\":\"pothole\"}" --block 100 --all-train ^
    --out review\new_data_r3\items\items_irq.csv
python -I tools/build_part.py --items review\new_data_r3\items\items_irq.csv --part irq --out parts_r3\irq
(compare parts_r3\irq\build_info.json with vet\irq\expected_build_info.json and keep_list.csv)
```
