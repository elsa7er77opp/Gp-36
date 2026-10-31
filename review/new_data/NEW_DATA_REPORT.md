# New speed-bump data – forensics (31 Oct 2026, read-only)
Zips (GP36_AI root) extracted to GP36_Dataset/raw_v3/roboflow_{bd_speedbreaker_v2,hump_marked_v2,kizmoya_speedbump_v2}. All CC BY 4.0.
Hashes: hashes.jsonl (sha256 + 64-bit dHash, also for rf8, sb15, ghsb). Scripts: hash_all.py, dup_report.py, sheets.py. Sheets: sheets/new_*.jpg.

| set | images | classes | preprocessing | finding |
|---|---|---|---|---|
| BD_speedbreaker v2 | 693 (train 606 / valid 58 / test 29) | SpeedBreaker | 640 stretch, auto-contrast; train = 3 augmented copies (flip, ±15° rotation, exposure) | 289 originals. Painted zebra humps, South Asian campus roads. Labels OK. Scene looks similar to rf8/hump campus (not proven). |
| speed-bump-hump-marked v2 | 450 | pothole(13 boxes), speedbump | 960 letterbox | 268 of 450 have the same source name (ImageNNNNN) as rf8 images -> already in our data. 182 new, same campus. Labels OK. 7 empty labels. |
| kizmoya speedbump v2 | 3,569 | speed-bump | 640 stretch | README says no augmentation, but images carry heavy noise, black cutout squares and rotation; 204 exact duplicates; ~289 name stems. Korean painted humps, mostly close/top-down views, boxes loose on rotated images. Painted stripes look like crosswalks -> conflicts with rule D1. |

Near-duplicates (dHash<=4): hump-rf8 225 pairs, hump-kiz 5, kiz-rf8 1, bd-other 0.

Recommendation (pending Ahmed's OK):
- hump: add the 182 non-rf8 images to TRAIN only, after near-dup removal against rf8/v3a_r2.
- BD: do NOT train on it. Use its valid+test originals (87 images, not augmented copies) as an external unseen-bump test, evaluated once per model; caveat: may be the same region as rf8.
- kiz: leave out of Run B (synthetic noise + crosswalk-like stripes would undo the D1 cleaning). Maybe later as a small hand-picked subset.
