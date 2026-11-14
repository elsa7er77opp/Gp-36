# Source-review checkpoint — not fully adjudicated

All 10,562 training images retained; 830 validation and 323 test images/labels unchanged.

343 previously low-confidence images rechecked against original pixels. 92 images changed in this pass; 683 cumulative full-label replacement records relative to the base. All changed images received before/after visual inspection; revisions are preserved in ledger history.

149 images remain provisional. Confidence over the 435 difficult cases: {'low': 149, 'medium': 286}. AI adjudication is not human ground truth and does not guarantee zero errors. Unresolved data has not been silently marked clean.

Integrity PASS: all 11,715 image hashes, dimensions and decodes; every annotation versus explicit decision or unchanged source; classes and bounds; counts; YAML/list paths. Split audit found zero exact or perceptual cross-split candidates at dHash <= 4 AND pHash <= 10, and zero shared group IDs. This does not prove absence of every possible correlated scene.

Fingerprint: `a4eb58dc61bebf829e9d892fe3bdbf9a928dca56d0c90e58fc21021c7b67150e`.

Training has NOT started. The remaining cases need evidence sufficient to decide class and boundaries. Extra 2,438 vetted training images are being sought for the newly requested 13,000-image target. Existing images are not deleted to reach the target.

Do not use old `run_v5_2_train_fixed_visible.bat`: it points to an obsolete label checkpoint. Generic `train.py` also evaluates test automatically, which is outside the current authorization.
