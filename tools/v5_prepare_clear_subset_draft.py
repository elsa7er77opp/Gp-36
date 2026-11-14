"""Prepare a concrete optional training subset, without deleting any image or starting training.

The full 10,562-image train release is preserved. User's data-scope choice is still needed.
"""
import csv,hashlib,json,os,shutil
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image
import yaml
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'road_hazards_v5_source_review_20261112_u4k';OUT=ROOT/'road_hazards_v5_clear_subset_draft_20261112';R=ROOT/'review/v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pending=list(csv.DictReader((R/'pretrain/unresolved_review.csv').open()));excluded={r['image'] for r in pending}
assert len(excluded)==149
assert not OUT.exists(),'Refuse to overwrite draft'
OUT.mkdir()
rows=list(csv.DictReader((BASE/'manifest.csv').open()));selected=[r for r in rows if r['out_image'] not in excluded]
assert all(r['split']=='train' for r in rows if r['out_image'] in excluded)
stats=defaultdict(Counter);fingerprint=hashlib.sha256()
for i,r in enumerate(selected,1):
 image=r['out_image'];p=Path(image);label=Path('labels')/p.parent.name/(p.stem+'.txt')
 for rel in [Path(image),label]:
  target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True);os.link(BASE/rel,target)
  assert sha(BASE/rel)==sha(target)
 with Image.open(OUT/image) as im:assert im.size==(960,720);im.load()
 lines=(OUT/label).read_text().splitlines()
 assert len(lines)==int(r['n_pothole'])+int(r['n_speed_bump'])
 stats[r['split']].update(images=1,pothole_boxes=int(r['n_pothole']),speed_bump_boxes=int(r['n_speed_bump']),empty=not lines)
 fingerprint.update((image+sha(OUT/image)+sha(OUT/label)).encode())
 if i%3000==0:print('Verified draft',i,'/',len(selected),flush=True)
with (OUT/'manifest.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(selected)
for name in ['data.yaml','data_stdframe.yaml']:
 config=yaml.safe_load((BASE/name).read_text());config['path']=str(OUT.resolve());(OUT/name).write_text(yaml.safe_dump(config,sort_keys=False))
for name in ['val_stdframe.txt','test_stdframe.txt']:
 shutil.copyfile(BASE/name,OUT/name)
 for line in (OUT/name).read_text().splitlines():assert (OUT/line).exists()
shutil.copyfile(R/'pretrain/unresolved_review.csv',OUT/'excluded_from_draft_only.csv')
assert {s:c['images'] for s,c in stats.items()}==dict(train=10413,val=830,test=323)
info=dict(dataset=str(OUT),status='optional_draft_requires_data_scope_choice',full_dataset_preserved=str(BASE),full_train_images=10562,excluded_from_draft_only=149,splits={s:dict(c) for s,c in stats.items()},integrity='PASS',content_fingerprint=fingerprint.hexdigest(),resolution=[960,720],training_started=False,train_ready=False,scope_choice_required=True,validation_test_unchanged=True,addition_candidates_included=0,notes='Not automatically selected for training. User requested all images; draft only demonstrates the alternative of holding unresolved examples out of training while preserving all originals. Hash/scene checks apply to superset; subsets cannot introduce train-eval overlaps. Existing AI visual labels are not a zero-error guarantee.')
(OUT/'release_info.json').write_text(json.dumps(info,indent=2)+'\n')
(OUT/'README.md').write_text('# Optional clear-label subset draft\n\nNot the selected training release. Full original release is preserved. 149 unresolved images are omitted ONLY from this draft train split and listed in excluded_from_draft_only.csv; none is deleted. 10,413 train / 830 validation / 323 test, all 960x720. Validation/test pixels and labels identical to full release. No training started. Data-scope choice required because user previously requested every image remain in training. This subset does not reach 13,000 train images.\n')
print(json.dumps(info,indent=2),flush=True)
