"""Export three visually inspected hard negatives, with source proposals preserved separately."""
import csv,json,os
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000';C=E/'rdd_candidates';OUT=E/'reviewed_additions_batch2'
for sub in ['images','labels','annotated']:(OUT/sub).mkdir(parents=True,exist_ok=True)
source={r['candidate']:r for r in map(json.loads,(C/'candidate_ledger.jsonl').read_text().splitlines())}
notes={5:'Full standardized image shows longitudinal/alligator cracks, intact filled repair slabs and round manholes. No distinct open pothole or raised speed bump.',78:'Full image shows a flat zebra crossing and regular rectangular filled/utility repair at the near right; no open asphalt-loss cavity or raised hump.',109:'Full image shows intact worn road, a manhole and white paint fragments in the source box. Paint is not a pothole; no raised hump.'}
matches=list(csv.DictReader((E/'current_reference_matches.csv').open()));within=list(csv.DictReader((E/'within_candidate_matches.csv').open()))
visual_path=E/'rdd_visual_review_decisions.jsonl';visual=[json.loads(s) for s in visual_path.read_text().splitlines()];final=[];manifest=[]
for i,reason in notes.items():
 assert not source[i]['leak_check']['hit']
 assert not any(int(r['candidate'])==i for r in matches)
 assert not any(int(r['candidate'])==i or int(r['reference'])==i for r in within)
 name=f'rddnew_c{i:04}';impath=OUT/'images'/f'{name}.jpg';label=OUT/'labels'/f'{name}.txt'
 if not impath.exists():os.link(C/f'c{i:04}.jpg',impath)
 with Image.open(impath) as raw:assert raw.size==(960,720);raw.load();im=raw.convert('RGB')
 tmp=label.with_suffix('.tmp');tmp.write_text('');tmp.replace(label)
 d=ImageDraw.Draw(im);d.text((8,8),f'C{i:04}: visually reviewed negative, 0 hazard boxes',fill='yellow');im.save(OUT/'annotated'/f'{name}.jpg',quality=96)
 entry=dict(candidate=i,boxes=[],confidence='medium',decision='visual_approved_negative',reason=reason,reviewer='codex_visual_individual',evidence=f'rdd_candidates/c{i:04}.jpg',protected_and_current_reference_matches=0,within_candidate_matches=0,merged_into_training=False)
 final.append(entry)
 for r in visual:
  if r['candidate']==i:
   r.setdefault('history',[]).append({k:v for k,v in r.items() if k!='history'});r.update(entry)
 m=source[i]['manifest'];manifest.append(dict(candidate=i,image=str(impath.relative_to(ROOT)),label=str(label.relative_to(ROOT)),source='rdd_ji',orig_image=m['orig_image'],orig_sha256=m['orig_sha256'],group_id=m['group_id'],boxes=0,confidence='medium',status='visual_reviewed_negative_dedup_screen_pass',evidence=entry['evidence']))
with (OUT/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
(OUT/'final_visual_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in final))
t=visual_path.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in visual));t.replace(visual_path)
(OUT/'README.md').write_text('# Batch 2: three reviewed hard negatives\n\nCandidates 5, 78 and 109: source pothole boxes removed after inspecting each full 960x720 frame. Final YOLO labels are empty files, intentionally: cracks, intact filled repairs, manholes/utility structures, flat zebra crossing and paint fragments are not either target class. Images retain original pixels, labels and annotated previews are separate. No matches against protected/current references or other candidates at the eight-transform dHash<=4 AND pHash<=10 screen. This is not proof of all scene independence or zero annotation error; AI confidence medium. No image merged into the training release. Source proposed labels remain untouched under rdd_candidates/proposed_labels.\n')
print('Saved 3 reviewed hard negatives and corrected empty YOLO labels; no training started.')
