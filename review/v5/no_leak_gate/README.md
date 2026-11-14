# Leakage review, 12 November 2026

All 11,715 current release images were hashed in standardized and original views, under eight flips/rotations. Training was compared with both current validation/test and protected external/part-held-out references. Exact original/output hashes, manifest groups and explicit video identifiers were also checked.

Two potential flipped matches were inspected visually. Both are false positives between different roads: train has steel electricity pylons and plain humps, while validation has a painted striped hump, marked centre line and different tree-lined kerbs. Identical large grey letterbox bars explain the approximate hash similarity. See `two_matches_visual_adjudication.jpg` and per-pair decision ledger.

Raw screen remains false in REPORT.json because it found candidates. REVIEWED_REPORT.json records all candidates adjudicated, zero confirmed leakage, and the limitations. No images were removed. This report does not certify semantic labels, make the release train-ready, or cover future additions. Re-run on any changed image composition.
