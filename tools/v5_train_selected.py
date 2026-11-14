"""Train the explicitly selected label policy after integrity and leakage gates.

No test inference. Run --preflight to check the saved choice without starting training.
"""
import argparse,csv,hashlib,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image
import yaml
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';O=R/'training';O.mkdir(exist_ok=True)
FULL=ROOT/'road_hazards_v5_source_review_20261112_u4k';CLEAR=ROOT/'road_hazards_v5_clear_subset_draft_20261112'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');args=ap.parse_args()
 policy_path=O/'TRAINING_POLICY.json'
 if policy_path.exists():
  selected_policy=json.loads(policy_path.read_text())
  if selected_policy.get('mode')=='wait_for_13000_reviewed_train_images':
   raise SystemExit('User selected waiting for 13,000 reviewed training images. Current releases do not satisfy that requirement. Training not started.')
 choice_path=O/'DATA_CHOICE.json'
 if not choice_path.exists():raise SystemExit('No data-scope choice recorded. Full release retains 149 provisional images; optional clear-only draft omits them from training. Training not started.')
 choice=json.loads(choice_path.read_text());data=Path(choice['dataset']).resolve();policy=choice['label_policy']
 assert data in [FULL.resolve(),CLEAR.resolve()]
 assert (data==FULL.resolve() and policy=='provisional_full') or (data==CLEAR.resolve() and policy=='clear_only')
 leak=json.loads((R/'no_leak_gate/REVIEWED_REPORT.json').read_text());assert leak['reviewed_gate_pass'] and leak['confirmed_leak_pairs']==0 and leak['unreviewed_candidate_pairs']==0
 assert leak['manifest_sha']==digest(FULL/'manifest.csv')
 info=json.loads((data/'release_info.json').read_text());rows=list(csv.DictReader((data/'manifest.csv').open()));base={r['out_image']:r for r in csv.DictReader((FULL/'manifest.csv').open())}
 full_splits={s:{r['out_image'] for r in base.values() if r['split']==s} for s in ['train','val','test']}
 pending={r['image'] for r in csv.DictReader((R/'pretrain/unresolved_review.csv').open())};assert len(pending)==149
 selected={s:{r['out_image'] for r in rows if r['split']==s} for s in full_splits}
 assert selected['val']==full_splits['val'] and selected['test']==full_splits['test']
 assert selected['train']==(full_splits['train'] if policy=='provisional_full' else full_splits['train']-pending)
 fp=hashlib.sha256()
 for n,r in enumerate(rows,1):
  rel=r['out_image'];p=Path(rel);label=Path('labels')/p.parent.name/(p.stem+'.txt')
  sha=digest(data/rel);lsha=digest(data/label)
  assert sha==r['out_sha256']==base[rel]['out_sha256'] and lsha==digest(FULL/label),rel
  with Image.open(data/rel) as im:assert im.size==(960,720)
  for line in (data/label).read_text().splitlines():
   c,x,y,w,h=map(float,line.split());assert c in [0,1] and all(math.isfinite(v) for v in [x,y,w,h]) and w>0 and h>0 and min(x-w/2,y-h/2)>=-.000002 and max(x+w/2,y+h/2)<=1.000002
  fp.update((rel+sha+lsha).encode())
  if n%3000==0:print('Preflight verified',n,'/',len(rows),flush=True)
 assert fp.hexdigest()==info['content_fingerprint']
 config=yaml.safe_load((data/'data.yaml').read_text());config.pop('test',None);config['path']=str(data)
 train_yaml=O/('data_'+policy+'_val_only.yaml');train_yaml.write_text(yaml.safe_dump(config,sort_keys=False))
 params=dict(data=str(train_yaml),epochs=70,patience=20,imgsz=960,batch=8,workers=2,device=0,cache='disk',seed=0,deterministic=True,optimizer='auto',close_mosaic=10,amp=True,val=True,split='val',plots=True,project=str(ROOT/'runs/detect'),name='v5_'+policy+'_11n_960_s0_20261112',exist_ok=False)
 result=dict(checked_utc=datetime.now(timezone.utc).isoformat(),dataset=str(data),label_policy=policy,integrity='PASS',train_images=len(selected['train']),unresolved_labels_in_training=len(selected['train']&pending),excluded_from_training_only=len(full_splits['train']-selected['train']),training_started=False,test_inference=False,content_fingerprint=fp.hexdigest(),choice=choice,params=params)
 (O/'PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
 if args.preflight:return
 import torch
 from ultralytics import YOLO
 assert torch.cuda.is_available(),'CUDA unavailable'
 assert not (ROOT/'runs/detect'/params['name']).exists(),'Refuse run overwrite/resume'
 weights=ROOT/'yolo11n.pt';model=YOLO(str(weights));assert len(model.names)==80,'Require clean COCO-pretrained starting weights'
 result.update(training_started=True,start_utc=datetime.now(timezone.utc).isoformat(),weights_sha256=digest(weights),gpu=torch.cuda.get_device_name(0),status='running')
 (O/'RUN_STATUS.json').write_text(json.dumps(result,indent=2)+'\n')
 try:
  trained=model.train(**params)
  result.update(status='complete',finished_utc=datetime.now(timezone.utc).isoformat(),save_dir=str(model.trainer.save_dir),metrics=trained.results_dict if trained is not None else {})
 except BaseException as e:
  result.update(status='failed',error=repr(e));raise
 finally:(O/'RUN_STATUS.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
if __name__=='__main__':main()
