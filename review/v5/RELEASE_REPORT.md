# Stage 40 release — 2026-11-12

Delivered:
- `road_hazards_v5_curated_10000`: exactly **10,000 train images**, covering **all 15 sources**. Includes the original **830 val + 323 test** images and labels unchanged.
- `road_hazards_v5_corrected_20261112`: **10,562 train + 830 val + 323 test = 11,715 images**; every original image preserved.
- Older `road_hazards_v5_fixed` remains an obsolete 177-correction checkpoint. Use the release folders above.

Review:
- Forward pass finished through sheet **916/916** (5,493 Stage 40 images, in addition to 5,069 previously accepted Stage 39a train images).
- **988** uncertain cases rechecked: **342 retained, 214 corrected, 432 still unresolved**.
- **522 unique image label replacements** in total. After final geometry overlays, **3 additional QA flags** bring the excluded unresolved total to **435**.
- Curated selection: **10,000 selected + 127 eligible reserves + 435 unresolved = 10,562**. No unresolved case is selected. Selection is deterministic and proportional across source and class-presence groups.
- AI visual labelling (Claude/Codex), without detector predictions. This is not human ground truth or a claim of perfect annotations. The unresolved cases remain available with their labels in the complete release.

Verification: **PASS**. Every complete-release image was decoded and checked for 960×720 dimensions and SHA-256 equality to the original/manifest. Every label was checked for valid classes, finite in-bounds coordinates, exact replacement serialization, unchanged bytes elsewhere, and agreement with manifest counts. Every curated image and label pair was checked byte-for-byte. Directory counts, YAML paths and standard-frame evaluation lists also passed. No training or model benchmark evaluation was run.

Use `data.yaml` or `data_stdframe.yaml` inside the chosen release folder. Class 0 = pothole; class 1 = speed_bump. Empty labels are negative road images.

Audit files:
- `fixes.jsonl`: complete replacements and reasons.
- `forward_review_codex.csv`, `unsure_recheck_codex.csv`, `final_recheck_codex.csv`: decisions.
- `final_qa_flags_codex.csv`: additional geometry QA holds.
- `release_selection_codex.csv`: every train image's delivery status and hashes.
- `RELEASE_REPORT.json`: machine-readable counts and content fingerprint.
- `views/final_geometry`: 53 nonempty corrections after the old checkpoint visually inspected; the duplicate at 417/4 was merged and separately verified.
