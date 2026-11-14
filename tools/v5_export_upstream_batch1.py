"""Persist individual source-pixel adjudication of four upstream cases; export two clear negatives."""
import csv,json,os
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000';C=E/'upstream_candidates';OUT=E/'reviewed_upstream_batch1'
for sub in ['images','labels','annotated']:(OUT/sub).mkdir(parents=True,exist_ok=True)
source={r['candidate']:r for r in map(json.loads,(C/'candidate_ledger.jsonl').read_text().splitlines())}
p=E/'upstream_visual_review_decisions.jsonl';rows=[json.loads(s) for s in p.read_text().splitlines()]
notes={10:('reject_addition','Native source crop shows a narrow transverse raised/joint-like strip. Hump versus flat joint is not reliably settled, so do not admit as a negative.', 'upstream_native_rois/u0010.jpg'),16:('reject_addition','Native crop shows two uniformly sand-coloured regions. Fill/repair versus open depression remains uncertain; do not claim a confirmed negative or positive.','upstream_native_rois/u0016.jpg'),22:('visual_approved_negative','Full standardized frame shows shadows from trees and poles across intact asphalt, not an elevated hump or open cavity.','upstream_candidates/u0022.jpg'),33:('visual_approved_negative','Native crop resolves small dark marks as raised debris/droppings on intact asphalt, not holes. Full road view has no visible target hazard.','upstream_native_rois/u0033.jpg')}
matches=list(csv.DictReader((E/'upstream_checks/current_reference_matches.csv').open()));within=list(csv.DictReader((E/'upstream_checks/within_candidate_matches.csv').open()))
manifest=[];decisions=[]
for r in rows:
 i=r['candidate']
 if i not in notes:continue
 status,reason,evidence=notes[i];r.setdefault('history',[]).append({k:v for k,v in r.items() if k!='history'});r.update(decision=status,reason=reason,evidence=evidence,reviewer='codex_visual_individual',merged_into_training=False)
 if status!='visual_approved_negative':continue
 assert not source[i].get('source_box_map_issues')
 assert not any(int(x['candidate'])==i for x in matches)
 assert not any(int(x['candidate'])==i or int(x['reference'])==i for x in within)
 r.update(boxes=[],confidence='medium',protected_and_current_reference_matches=0,within_candidate_matches=0);decisions.append(r)
 name=f'upstream_u{i:04}';image=OUT/'images'/f'{name}.jpg';label=OUT/'labels'/f'{name}.txt'
 if not image.exists():os.link(C/f'u{i:04}.jpg',image)
 t=label.with_suffix('.tmp');t.write_text('');t.replace(label)
 with Image.open(image) as raw:assert raw.size==(960,720);raw.load();im=raw.convert('RGB')
 ImageDraw.Draw(im).text((8,8),f'U{i:04}: reviewed negative, 0 boxes',fill='yellow');im.save(OUT/'annotated'/f'{name}.jpg',quality=96)
 m=source[i]['manifest'];manifest.append(dict(candidate=i,image=str(image.relative_to(ROOT)),label=str(label.relative_to(ROOT)),source='bpo_upstream',orig_image=m['orig_image'],orig_sha256=m['orig_sha256'],group_id=m['group_id'],video_id=source[i]['video_id'],boxes=0,confidence='medium',status='visual_reviewed_negative_dedup_screen_pass',evidence=evidence))
with (OUT/'manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
(OUT/'final_visual_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in decisions))
t=p.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in rows));t.replace(p)
(OUT/'README.md').write_text('# Upstream batch 1: two reviewed hard negatives\n\nU0022: tree/pole shadows on intact road. U0033: raised debris/droppings, resolved in native source pixels. Empty YOLO labels are intentional. No eight-transform matches to current/protected references or other upstream candidates. Exact upstream SHA audit found zero protected/current or within-pool exact duplicates. 960x720; images, actual labels and annotated previews separate. AI medium confidence, not proof of zero error. No image merged into training. U0010 and U0016 rejected as unresolved, with source crops and history retained.\n')
print('Saved 4 individual adjudications and 2 reviewed upstream negatives; no training started.')
