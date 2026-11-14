"""Export two individually inspected pothole annotations; retain source proposals and review history."""
import csv,json,os
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000';C=E/'rdd_candidates';OUT=E/'reviewed_additions_batch3'
for sub in ['images','labels','annotated']:(OUT/sub).mkdir(parents=True,exist_ok=True)
src={r['candidate']:r for r in map(json.loads,(C/'candidate_ledger.jsonl').read_text().splitlines())}
matches=list(csv.DictReader((E/'current_reference_matches.csv').open()));within=list(csv.DictReader((E/'within_candidate_matches.csv').open()))
spec={123:([0],'Full individual frame shows exposed broken asphalt and a muddy depression at the lower image boundary. Retain visible clipped pothole extent; no artificial extension beyond image.'),151:([0],'Left foreground beside manhole shows dark open asphalt-loss cavity with exposed aggregate. Retain left box; remove right box which follows intact cracked material around cover. Cover itself is not a pothole.')}
vpath=E/'rdd_visual_review_decisions.jsonl';visual=[json.loads(s) for s in vpath.read_text().splitlines()];manifest=[];final=[]
for i,(keep,reason) in spec.items():
 assert not src[i]['leak_check']['hit']
 assert not any(int(r['candidate'])==i for r in matches)
 assert not any(int(r['candidate'])==i or int(r['reference'])==i for r in within)
 boxes=[src[i]['proposed_boxes'][j] for j in keep];name=f'rddnew_c{i:04}';image=OUT/'images'/f'{name}.jpg';label=OUT/'labels'/f'{name}.txt'
 if not image.exists():os.link(C/f'c{i:04}.jpg',image)
 raw=''.join(f'{int(c)} {(x+X)/2:.6f} {(y+Y)/2:.6f} {X-x:.6f} {Y-y:.6f}\n' for c,x,y,X,Y in boxes)
 t=label.with_suffix('.tmp');t.write_text(raw);t.replace(label)
 with Image.open(image) as original:assert original.size==(960,720);im=original.convert('RGB')
 d=ImageDraw.Draw(im)
 for c,x,y,X,Y in boxes:d.rectangle((x*960,y*720,X*960,Y*720),outline='lime',width=2)
 im.save(OUT/'annotated'/f'{name}.jpg',quality=96)
 decision=dict(candidate=i,boxes=boxes,confidence='medium',decision='visual_approved_pothole',reason=reason,reviewer='codex_visual_individual',evidence=f'rdd_candidates/c{i:04}.jpg',protected_and_current_reference_matches=0,within_candidate_matches=0,merged_into_training=False)
 final.append(decision)
 for r in visual:
  if r['candidate']==i:
   r.setdefault('history',[]).append({k:v for k,v in r.items() if k!='history'});r.update(decision)
 m=src[i]['manifest'];manifest.append(dict(candidate=i,image=str(image.relative_to(ROOT)),label=str(label.relative_to(ROOT)),source='rdd_ji',orig_image=m['orig_image'],orig_sha256=m['orig_sha256'],group_id=m['group_id'],boxes=len(boxes),confidence='medium',status='visual_reviewed_pothole_dedup_screen_pass',evidence=decision['evidence']))
with (OUT/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
(OUT/'final_visual_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in final))
t=vpath.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in visual));t.replace(vpath)
(OUT/'README.md').write_text('# Batch 3: two individually reviewed pothole images\n\nCandidates 123 and 151, 2 pothole boxes, class 0, 960x720. Candidate 123 retains the visible image-clipped foreground cavity. Candidate 151 retains the left open defect and removes the right cracked-cover region. Original proposals and prior review decisions are preserved. No protected/current/within-candidate matches under the existing eight-transform screen. AI medium confidence, not zero-error certification. No image merged into training.\n')
print('Saved 2 reviewed pothole images and 2 actual YOLO boxes. Training remains stopped.')
