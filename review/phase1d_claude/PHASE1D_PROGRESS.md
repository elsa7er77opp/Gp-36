# GP36 — Phase 1d progress (30 Oct 2026, Claude review session)

Scope of this session: **read-only review + proposals**. No original image or label was changed, nothing was trained, deleted or committed. `ANNOTATION_AUDIT.csv` is untouched — every proposal waits for the owner's confirmation.

## 1. Conflicting duplicate pairs in Roboflow v8 — all 225 reviewed
Method: `review/phase1d_claude/make_pairs.py` renders each byte-identical pair side by side, **zoomed on the road area** (the 291 Phase 1c contact sheets were too small to judge boxes). Every one of the 225 pairs was looked at. Output: `review/phase1d_claude/pairs/` (225 images + index CSV) and the proposals file `phase1d_proposals_conflicts.csv` (pair_no, proposal, keep_copy, fix_note, confidence, reason).

Owner rule applied (30 Oct): **FAR_TINY = (a)** — a box on a far spot that is not visibly a pothole is dropped.

| Proposal | Pairs | Meaning |
|---|---|---|
| KEEP (one copy) | 130 | Keep the better copy's labels; the other copy → REJECTED `duplicate` |
| QUARANTINE | 91 | Neither copy is reliable → kept out of v3 (both copies) |
| FIX | 3 | Keep a copy after a specific box edit (#4, #5, #28) |
| REJECT | 1 | #217: same box labelled pothole in one copy and speed bump in the other on a blurry image |
Confidence: 3 high, 55 medium, 167 low — **low means the owner should confirm**, not that the proposal is random.

### Error patterns found (counts are pairs whose note names the pattern)
| Pattern | Pairs | Example | Ontology rule |
|---|---|---|---|
| Dense distress: a badly broken road where the two annotators boxed different subsets of cavities | 58 | #49–#72, #187–#199 (G00665xx, G00902xx sequences) | No consistent ground truth → QUARANTINE |
| Far tiny boxes on spots not visibly potholes | 47 | #33, #40, #140 (7 far boxes), #210 | FAR_TINY (a) → drop |
| Patch / milled / repaired area boxed as pothole | 12 | #16, #144, #145 | D5 → background |
| Shadow / dark stain boxed as pothole | 10 | #8, #39, #171 (car shadow) | D5 |
| Glare-washed image | 7 | #10, #101, #132 | QUARANTINE if boxes unverifiable |
| Alligator-crack area boxed as pothole | 6 | #166, #218 | D5 crack → background (owner to confirm) |
| Localisation offset (box beside the cavity) | 5 | #5, #6, #100, #109 | keep the copy whose box is on the cavity |
| Windshield sticker / bonnet / wiper boxed | 4+ | #82, #102, #211 | invalid → drop |
| **Manhole cover boxed as pothole** | 3 | #27, #28, #29 | D5 manhole → background |
| Litter / paper boxed as pothole | 3 | #76, #107 | drop |
| **Raised speed hump missing in one copy** | 4 | #164, #165 (yellow-black hump, D2) | keep the copy that has it |
| Painted flat crosswalk boxed as speed bump | 1 | #4 (= G0040808 test copy) | D1 → background |

**Consequence:** if the proposals are accepted, Roboflow v8 loses about 91 + (rejected duplicate copies) images and gains consistent labels for 133 images. The 91 quarantined images are mostly from a few dense-distress video sequences — removing them also removes heavy leakage groups.

## 2. Roboflow speed-bump-detection v15 — forensics done
Full notes: `review/v15_forensics/V15_NOTES.md`. Summary:
- 1,692 images (1,014 / 339 / 339), CC BY 4.0, exported 14 Feb 2025, **stretched to 640×640**.
- **Two classes: `Rumble Strip` (691 boxes) and `Speed-Bump` (1,076 boxes).** Rumble Strip = painted transverse line sets on highways → decision **D6 needed**.
- Label integrity clean (0 missing/empty/malformed, 0 exact duplicates, no box < 6 px).
- **Leakage:** all images are video frames (`frame0-HH-MM-SS…`); 250 adjacent-frame pairs (≤2 s) sit in different splits; 61 multi-copy stems cross splits. Must be re-split by time blocks.
- Domain: Indonesian residential streets (mostly unpainted asphalt humps, many far) and highways.

## 3. Not done yet (next session)
1. Owner confirmation of the 225 proposals (start with the 91 QUARANTINE and the 167 low-confidence rows) → then they are written into `ANNOTATION_AUDIT.csv`.
2. D6 decision (rumble strips) — affects v15 and Roboflow v8.
3. Remaining Phase 1d sheets: 161 minor-difference duplicate pairs, 191 crowd-sourced potholes, 370 speed-bump video frames, near-dup threshold sheets.
4. RDD2022 download (S3 links blocked for the user's network? — to check; figshare mirror available) and its forensics.
5. Phase 1e build only after the above.
