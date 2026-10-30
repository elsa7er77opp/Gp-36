# GP36 — CLASS_MAPPING (Hazard Detector ontology, v0.1)

Decisions recorded 2026-10-30 from the project owner (Ahmed Elreefy). They are open to change by the supervisor, and any change must be recorded here with a date.

## Target classes
| ID | Name | Definition |
|---|---|---|
| 0 | `pothole` | A depression or cavity in the road surface where material is missing, on **paved or unpaved** roads. |
| 1 | `speed_bump` | A **raised** traffic-calming profile across the lane: a painted or **unpainted** hump, or a raised pedestrian crossing / speed table. |

COCO classes live in a separate detector and namespace (`coco:*`). Hazard IDs are always used as `hazard:pothole` / `hazard:speed_bump` outside this dataset.

## Decisions
| # | Question | Decision | Consequence for review |
|---|---|---|---|
| D1 | Painted zebra crossing **without** a raised profile | **Background** (not `speed_bump`) | Remove such boxes (e.g. `G0040808` test copy). Reason code `crosswalk_not_bump`. |
| D2 | Raised crossing / speed table; unpainted hump | **`speed_bump`** | Add boxes where they are missing. Reason code `missing_bump`. |
| D3 | Potholes on unpaved / dirt roads (e.g. `pothole_208`) | **`pothole`** | Keep. Note: an unpaved road has no clear "intact surface" reference, so expect lower label consistency there. |
| D4 | One defect with several cavities | **One box around the whole defect** | Merge multi-box annotations of one defect (e.g. `rf_209`, `rf_254`, `pot_128`). Reason code `merge_boxes`. |
| D5 | Asphalt patch, manhole/utility cover, crack (any type), shadow, wet patch | **Background, never `pothole`** (project rule) | Remove such boxes. Reason codes `patch`, `manhole`, `crack`, `shadow`. |
| D6 | Rumble strips (series of small transverse ridges) | **OPEN**: not decided yet | Mark `QUARANTINED` until decided. |

## Source mappings (`configs/sources.yaml`)
| Source | Source class | → Target | Note |
|---|---|---|---|
| `rf8` Roboflow v8 | 0 `Pothole` | `pothole` | |
| `rf8` Roboflow v8 | 1 `Speed Bump` | `speed_bump` | Contains crosswalk boxes, which D1 sends to background during review |
| `ghsb` Androidest | 0 `speed bump` | `speed_bump` | |
| `ghpot` biodatlab | 0 `pothole` | `pothole` | |

Any source class that is not in this table is a hard build error (`ClassMappingError`). Future sources (RDD2022 D00/D10/D20 cracks, EGY_PDD "Bumps & Sags", Nature-2026 manholes) must be added here explicitly before use. They may be listed as `ignore`, but are never mapped silently.

## Decision update — 2026-10-30 (Ahmed Elreefy)
| # | Question | Decision |
|---|---|---|
| D6 | Rumble strips (painted / thermoplastic transverse line sets, no raised hump) | **Not `speed_bump`.** Source class `Rumble Strip` (Roboflow speed-bump v15, class 0) → `ignore`. Any such box in other sources → background. |
| — | FAR_TINY boxes (far spot not visibly a pothole) | **Drop the box** (option a). |
Phase 1d: the 225 conflicting duplicate pairs were reviewed by Claude and the proposals approved by the owner; written to ANNOTATION_AUDIT.csv (backup: ANNOTATION_AUDIT_before_phase1d_2026-10-30.csv).
