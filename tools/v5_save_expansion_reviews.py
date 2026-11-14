"""Save observed review decisions and actual YOLO labels for a small inspected addition batch.

This is a review staging area, not a released training dataset. It must pass full current-train dedup.
"""
import csv,json,os,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/v5/expansion13000';C=O/'rdd_candidates';OUT=O/'reviewed_additions'
for sub in ['images','labels','annotated']: (OUT/sub).mkdir(parents=True,exist_ok=True)
ledger={r['candidate']:r for r in map(json.loads,(C/'candidate_ledger.jsonl').read_text().splitlines())}
first=json.loads((O/'rdd_first_visual_review.json').read_text())['candidate_decisions']
extra={
19:('reject_addition','Broad intact dusty entrance or road patches; no clear cavity.'),20:('reject_addition','Dark small patches do not expose clear cavity boundaries.'),
21:('needs_individual_source_view','Small defect lies on road joint; crack versus pit unclear.'),22:('reject_addition','Roadside dark repair and shoulder region; no clear broken rim.'),
23:('reject_addition','Pale fine aggregate patch appears filled; depth unclear.'),24:('needs_individual_source_view','Dark foreground damage needs a closer check.'),
25:('negative_candidate_pending_full_review','Box covers narrow longitudinal cracking.'),26:('reject_addition','Alligator cracking and repair texture; bounded cavity unclear.'),
27:('reject_addition','Coarse broad filled or weathered surface; no confident open cavity.'),28:('reject_addition','Box covers dusty intact road and shadow.'),
29:('reject_addition','Broad sandy roadside surface and crack.'),30:('reject_addition','Distant roadside coarse spot unclear.'),
31:('visual_approved_pending_current_train_dedup','Localized broken surface with jagged rim across painted centre line; reviewed individual 960x720 image.'),
32:('reject_addition','Small dark mark insufficiently clear.'),33:('visual_approved_pending_current_train_dedup','Two separate visible open asphalt-loss cavities; checked individual 960x720 image.'),
34:('reject_addition','Broad intact fine-textured filled patch; same scene as candidate 37.'),35:('needs_individual_source_view','Full frame shows a road-joint crack; tiny widening is not sufficiently clear as a pothole.'),
36:('reject_addition','Distant tiny dark spot unclear.'),37:('reject_addition','Same filled repair as candidate 34.'),38:('reject_addition','Small coarse road patch not confidently open.'),
39:('visual_approved_pending_current_train_dedup','Visible open asphalt-loss depression with broken edge; checked individual image.'),40:('negative_candidate_pending_full_review','Boxed foreground area shows alligator cracking.'),
41:('negative_candidate_pending_full_review','Boxed region shows cracks without a clear cavity.'),42:('reject_addition','Boxes include filled or cracked surface and shadows; depth ambiguous.')}
dec={r['candidate']:r for r in first}
existing=O/'rdd_visual_review_decisions.jsonl'
if existing.exists():raise SystemExit('Initial review already recorded. Use append/amend workflows to preserve individual rechecks and exports.')
if existing.exists():dec.update({r['candidate']:r for r in map(json.loads,existing.read_text().splitlines()) if r['candidate']>42})
for i,(status,reason) in extra.items():dec[i]=dict(candidate=i,decision=status,reason=reason,evidence=f'rdd_candidates/sheet_{((i-1)//6)*6+1:04}.jpg')
# Full-image rechecks are stricter than preliminary contact-sheet impressions.
for i,reason in {
1:'Near pale patch could be filled while the right pit is clearer; hold image until both regions are settled.',
4:'Individual frame also has an uncertain unboxed rough region beside grate; exhaustive image labels need more review.',
11:'Foreground pit is clear, but a possible unboxed distant defect requires review before approval.',
18:'Tiny dark mark among exposed aggregate is not sufficiently clear for high-purity admission.',
17:'Individual full frame confirms broken asphalt cavity beside gutter; existing region includes adjacent connected material loss.'}.items():
 dec[i].update(decision='visual_approved_pending_current_train_dedup' if i==17 else 'needs_individual_source_view',reason=reason,evidence=f'rdd_candidates/c{i:04}.jpg')
# Individually compared candidate 39 with the current release: same worker, fence,
# factory, red steel structure and damaged road, at an adjacent camera position.
dec[39].update(decision='reject_addition_same_scene_as_current_train',reason='Same road, worker, green fence, factory and red steel structure as current train rdd_ji__4984ed69fad1716e.jpg (Japan_011077). Adjacent view of the same defect, not an independent addition.',duplicate_reference='images/train/rdd_ji__4984ed69fad1716e.jpg',evidence='rdd_candidates/c0039.jpg and current release reference')
for d in dec.values():
 d.setdefault('evidence',f"rdd_candidates/sheet_{((d['candidate']-1)//6)*6+1:04}.jpg")
 d['reviewer']='codex_visual';d['accepted_into_training_release']=False
(O/'rdd_visual_review_decisions.jsonl').write_text(''.join(json.dumps(dec[i])+'\n' for i in sorted(dec)))
manifest=[]
for i,d in sorted(dec.items()):
 if d['decision'] not in ['visual_approved_pending_current_train_dedup','reject_addition_same_scene_as_current_train']:continue
 row=ledger[i];boxes=row['proposed_boxes'];name=f'rddnew_c{i:04}'
 image=OUT/'images'/f'{name}.jpg';src=C/f'c{i:04}.jpg'
 if not image.exists():os.link(src,image)
 assert image.read_bytes()==src.read_bytes()
 label=''.join(f'{int(c)} {(x+X)/2:.6f} {(y+Y)/2:.6f} {X-x:.6f} {Y-y:.6f}\n' for c,x,y,X,Y in boxes)
 p=OUT/'labels'/f'{name}.txt';tmp=p.with_suffix('.tmp');tmp.write_text(label);tmp.replace(p)
 with Image.open(image) as raw:
  assert raw.size==(960,720);im=raw.convert('RGB')
 dr=ImageDraw.Draw(im)
 for j,(c,x,y,X,Y) in enumerate(boxes):
  assert c==0 and 0<=x<X<=1 and 0<=y<Y<=1
  dr.rectangle((x*960,y*720,X*960,Y*720),outline='lime',width=2);dr.text((x*960,y*720),str(j),fill='red')
 im.save(OUT/'annotated'/f'{name}.jpg',quality=96)
 manifest.append(dict(candidate=i,image=str(image.relative_to(ROOT)),label=str(p.relative_to(ROOT)),source='rdd_ji',orig_image=row['manifest']['orig_image'],orig_sha256=row['manifest']['orig_sha256'],group_id=row['manifest']['group_id'],boxes=len(boxes),confidence='medium',status='rejected_same_scene_duplicate' if i==39 else 'visual_reviewed_pending_full_dedup',evidence=d['evidence']))
with (OUT/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
(OUT/'README.md').write_text('# Visually reviewed additions — staging only\n\n4 reviewed image/label pairs, 5 pothole boxes, all 960x720, YOLO class 0. Candidate 39 is REJECTED after visual confirmation of the same road/worker/defect already in current train (Japan_011077); its files are retained as evidence, not an eligible addition. Only candidates 17, 31 and 33 remain provisionally eligible (4 boxes); final scene-family checks are still required. Read manifest status per image. Raw pixels, YOLO .txt labels and annotated previews are separate. AI labels with medium confidence, not zero-error certification. No image has been merged into the training release.\n')
print('Saved',len(dec),'visual decisions;',len(manifest),'staged images;',sum(r['boxes'] for r in manifest),'YOLO boxes; released additions: 0')
