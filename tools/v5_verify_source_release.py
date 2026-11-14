"""Verify complete source-review checkpoint; explicitly gate unresolved labels."""
import csv,hashlib,io,json,shutil,sys
from collections import Counter,defaultdict
from pathlib import Path
import yaml
from PIL import Image
from v5_build_release import read_csv,write_csv,sha,lab,expected_label,verify_labels
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';P=R/'pretrain';BASE=ROOT/'road_hazards_v5_all';OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'road_hazards_v5_source_review_20261112')
ds=[json.loads(s) for s in (P/'source_review_decisions.jsonl').read_text().splitlines()]
prior={r['q']:r for r in map(json.loads,(R/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
assert len(ds)==343 and len({r['q'] for r in ds})==343
assert {r['q'] for r in ds}=={q for q,r in prior.items() if r['confidence']=='low'}
merged=dict(prior);merged.update({r['q']:r for r in ds});pending=[r for r in ds if r['status']=='unresolved']
fixes={r['image']:r for r in map(json.loads,(P/'source_review_fixes.jsonl').read_text().splitlines())}
assert all(r['image'].startswith('images/train/') for r in fixes.values())
for r in merged.values():
 actual=[]
 for line in lab(OUT,r['image']).read_text().splitlines():
  c,x,y,w,h=map(float,line.split());actual.append([int(c),x-w/2,y-h/2,x+w/2,y+h/2])
 assert len(actual)==len(r['boxes']),('box count differs from decision',r['q'])
 # Earlier keep ledgers round xyxy to four decimals; source bytes retain six-decimal xywh.
 assert all(a[0]==b[0] and max(abs(x-y) for x,y in zip(a[1:],b[1:]))<=.000101 for a,b in zip(actual,r['boxes'])),('decision geometry differs from built label',r['q'])
stats=defaultdict(Counter);fingerprint=hashlib.sha256();original={r['out_image']:r for r in read_csv(BASE/'manifest.csv')}
manifest=read_csv(OUT/'manifest.csv')
for n,r in enumerate(manifest,1):
 image=r['out_image'];raw=(OUT/image).read_bytes();digest=sha(raw)
 assert digest==sha((BASE/image).read_bytes())==original[image]['out_sha256'],image
 with Image.open(io.BytesIO(raw)) as im:assert im.size==(960,720);im.load()
 label=lab(OUT,image).read_bytes();expected=expected_label(fixes[image]['boxes']) if image in fixes else lab(BASE,image).read_bytes()
 assert label==expected,image
 counts=verify_labels(label);assert counts[0]==int(r['n_pothole']) and counts[1]==int(r['n_speed_bump']),image
 stats[r['split']].update(images=1,pothole_boxes=counts[0],speed_bump_boxes=counts[1],empty=int(not counts))
 fingerprint.update((image+digest+sha(label)).encode())
 if n%2000==0:print('Verified',n,'/',len(manifest),flush=True)
assert {k:v['images'] for k,v in stats.items()}==dict(train=10562,val=830,test=323)
for split,stat in stats.items():
 assert len(list((OUT/'images'/split).glob('*')))==stat['images']
 assert len(list((OUT/'labels'/split).glob('*.txt')))==stat['images']
for name in ['data.yaml','data_stdframe.yaml']:
 config=yaml.safe_load((OUT/name).read_text());config['path']=str(OUT.resolve())
 (OUT/name).write_text(yaml.safe_dump(config,sort_keys=False))
 assert config['names']=={0:'pothole',1:'speed_bump'} or config['names']==['pothole','speed_bump']
 for split in ['train','val','test']:assert (OUT/config[split]).exists()
for name in ['val_stdframe.txt','test_stdframe.txt']:
 for line in (OUT/name).read_text().splitlines():assert (OUT/line).exists()
quality={int(r['q']):r for r in read_csv(P/'source_quality.csv')}
unresolved=[]
for r in pending:
 q=quality[r['q']];unresolved.append(dict(q=r['q'],image=r['image'],source=q['source'],confidence=r['confidence'],reason=r['reason'],original=q['original'],evidence=r['evidence']))
write_csv(P/'unresolved_review.csv',unresolved)
byimage={r['image']:r for r in merged.values()};audit=[]
for r in manifest:
 if r['split']!='train':continue
 d=byimage.get(r['out_image']);audit.append(dict(image=r['out_image'],source=r['source'],included=1,confidence=d['confidence'] if d else 'prior_review',review_basis='original_source' if d and d.get('reviewer')=='codex_original_pixels' else 'prior_visual_review',label_sha256=sha(lab(OUT,r['out_image']).read_bytes())))
write_csv(OUT/'review_status.csv',audit)
summary=dict(dataset=str(OUT),date='2026-11-12',integrity='PASS',train_ready=False,source_rechecks=len(ds),source_pass_changed_images=sum(r['action']=='replace' for r in ds),cumulative_replacement_records=len(fixes),unresolved_images=len(pending),unresolved_by_source=dict(Counter(quality[r['q']]['source'] for r in pending)),confidence_counts=dict(Counter(r['confidence'] for r in merged.values())),splits={k:dict(v) for k,v in stats.items()},content_fingerprint=fingerprint.hexdigest(),training_started=False,test_evaluated=False,limitations='AI visual labels; 146 provisional images (use unresolved_images field as authoritative). No zero-error guarantee. All original training images retained. Structural checks do not certify semantic truth. Training waits for unresolved labels to be adjudicated with adequate evidence. Benchmark validation/test images and labels unchanged.',expansion_target_train_images=13000,additional_images_required=2438)
summary['limitations']=summary['limitations'].replace('146 provisional images',f'{len(pending)} provisional images')
for src in [P/'source_review_decisions.jsonl',P/'source_review_fixes.jsonl',P/'unresolved_review.csv',P/'audit.json']:
 shutil.copyfile(src,OUT/src.name)
(OUT/'release_info.json').write_text(json.dumps(summary,indent=2)+'\n')
(P/'SOURCE_RELEASE_REPORT.json').write_text(json.dumps(summary,indent=2)+'\n')
report=f'''# Source-review checkpoint — not fully adjudicated

All 10,562 training images retained; 830 validation and 323 test images/labels unchanged.

343 previously low-confidence images rechecked against original pixels. {summary['source_pass_changed_images']} images changed in this pass; {len(fixes)} cumulative full-label replacement records relative to the base. All changed images received before/after visual inspection; revisions are preserved in ledger history.

{len(pending)} images remain provisional. Confidence over the 435 difficult cases: {summary['confidence_counts']}. AI adjudication is not human ground truth and does not guarantee zero errors. Unresolved data has not been silently marked clean.

Integrity PASS: all 11,715 image hashes, dimensions and decodes; every annotation versus explicit decision or unchanged source; classes and bounds; counts; YAML/list paths. Split audit found zero exact or perceptual cross-split candidates at dHash <= 4 AND pHash <= 10, and zero shared group IDs. This does not prove absence of every possible correlated scene.

Fingerprint: `{summary['content_fingerprint']}`.

Training has NOT started. The remaining cases need evidence sufficient to decide class and boundaries. Extra 2,438 vetted training images are being sought for the newly requested 13,000-image target. Existing images are not deleted to reach the target.

Do not use old `run_v5_2_train_fixed_visible.bat`: it points to an obsolete label checkpoint. Generic `train.py` also evaluates test automatically, which is outside the current authorization.
'''
(P/'SOURCE_RELEASE_REPORT.md').write_text(report)
(OUT/'README_STAGE40.md').write_text(report)
for dest in [R/'PROGRESS.md',ROOT/'review/clean_r2/STATUS_for_claude.md']:
 with dest.open('a',encoding='utf-8') as f:f.write('\n\n'+report+'\nDataset: '+str(OUT)+'\n')
print(json.dumps(summary,indent=2),flush=True)
