# Cross-source duplicates among the new parts (cloud session 3, 2026-11-04)

Tool: `tools/cross_source_dups.py`, run on the cloud builds of dmd, pol, red, ng8, hmp, ens and egy (all splits, 3,814 images) and on `protected_hashes.npz`.
- Rule v2: dHash ≤ 4 and pHash ≤ 10 under the same flip or 90° rotation, as in `leak_check.py`. Pairs inside one part are not counted.
- A looser rule (dHash ≤ 10 and pHash ≤ 16) is also reported, for a visual check only.

## Result (VERIFIED, `cross_source_pairs.csv`, `cross_source_drop_valtest.csv`)
- **Rule v2 pairs across sources: 2.**
  - Both are train/train: dm-druid `xqq062000157.jpg` = hmp `humps-v3-_461` and `humps-v3-_462` (dHash 0, pHash 0).
  - So hmp re-uses web copies of other datasets.
  - This is not a val/test leak: dmd is train-only, and both hmp images are part-train. It double-counts one image in train.
- **Rule v2 hits on the protected eval hashes: 0.**
- **val/test drop list: empty** (header only).
- Loose pairs: 115. The 44 that touch a val or test image were looked at side by side. All are different scenes, mostly near-uniform road surfaces with a crossing or hump (e.g. red/test ~ ens/train, ens/train ~ egy/test), so none is a duplicate.
- Limitation (see `hmp/BOX_AUDIT.md`): rule v2 does not catch small-angle rotations or crops. hmp has such same-scene copies across its own splits. That is one more reason to make hmp train-only.
