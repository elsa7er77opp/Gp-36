"""Save the specific visual adjudication of two padding-dominated perceptual matches."""
import csv,hashlib,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/v5/no_leak_gate';DATA=ROOT/'road_hazards_v5_source_review_20261112_u4k'
rows=list(csv.DictReader((O/'cross_split_candidates.csv').open()))
expected={'images/train/rf8__c9d730a125d33938.jpg','images/train/rf8__b9483dc48f025387.jpg'}
assert len(rows)==2 and {r['image'] for r in rows}==expected
assert all(r['protected_id']=='val:images/val/rf8__c91a18a00d6829a2.jpg' and r['transform']=='1' for r in rows)
canvas=Image.new('RGB',(1920,750),'#222222');dr=ImageDraw.Draw(canvas)
paths=[rows[0]['image'],rows[1]['image'],'images/val/rf8__c91a18a00d6829a2.jpg']
for i,p in enumerate(paths):
 with Image.open(DATA/p) as im:
  if i<2:im=ImageOps.mirror(im)
  canvas.paste(im.resize((640,480)),(i*640,0))
 dr.text((i*640+3,490),('TRAIN mirrored' if i<2 else 'VALIDATION original')+' '+Path(p).name,fill='white')
dr.text((5,530),'Different locations: train has electricity pylons, dirt shoulders and a plain dark hump.',fill='white')
dr.text((5,555),'Validation has a painted striped hump, centre markings, tree-lined kerbs, and no pylon.',fill='white')
dr.text((5,580),'Wide identical grey letterbox bars dominate low-frequency hashes. Both source-pixel comparisons were non-matches.',fill='white')
canvas.save(O/'two_matches_visual_adjudication.jpg',quality=96)
decisions=[]
for r in rows:decisions.append({**r,'decision':'false_positive_different_scene','reviewer':'codex_visual','reason':'Train scene has a steel electricity pylon, unpainted dark hump, dirt shoulder, and different buildings. Validation scene has a striped painted hump, centre paint, tree-lined kerbs and no pylon. Horizontal mirroring does not align landmarks; identical grey padding creates hash similarity.','evidence':'two_matches_visual_adjudication.jpg'})
(O/'candidate_adjudications.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in decisions))
raw=json.loads((O/'REPORT.json').read_text());assert raw['cross_split_candidate_pairs']==2
review=dict(dataset=raw['dataset'],manifest_sha=raw['manifest_sha'],raw_hash_screen_pass=raw['screen_pass'],raw_candidate_pairs=2,visually_rejected_false_positive_pairs=2,confirmed_leak_pairs=0,unreviewed_candidate_pairs=0,exact_cross_split_hashes=raw['exact_cross_split_hashes'],cross_split_groups=raw['cross_split_groups'],cross_split_explicit_video_keys=raw['cross_split_explicit_video_keys'],reviewed_gate_pass=True,limitations='No confirmed leakage under these checks. This is not proof of absence of all shared scenes or original collection routes. Generic filenames cannot certify video identities. Current annotations and additions have independent unresolved gates. No test inference performed.')
(O/'REVIEWED_REPORT.json').write_text(json.dumps(review,indent=2)+'\n')
(O/'README.md').write_text('# Leakage review, 12 November 2026\n\nAll 11,715 current release images were hashed in standardized and original views, under eight flips/rotations. Training was compared with both current validation/test and protected external/part-held-out references. Exact original/output hashes, manifest groups and explicit video identifiers were also checked.\n\nTwo potential flipped matches were inspected visually. Both are false positives between different roads: train has steel electricity pylons and plain humps, while validation has a painted striped hump, marked centre line and different tree-lined kerbs. Identical large grey letterbox bars explain the approximate hash similarity. See `two_matches_visual_adjudication.jpg` and per-pair decision ledger.\n\nRaw screen remains false in REPORT.json because it found candidates. REVIEWED_REPORT.json records all candidates adjudicated, zero confirmed leakage, and the limitations. No images were removed. This report does not certify semantic labels, make the release train-ready, or cover future additions. Re-run on any changed image composition.\n')
print(json.dumps(review,indent=2))
