"""Verify every image and annotation in the all-images release; retain confidence audit."""
import csv,hashlib,io,json,shutil
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image
from v5_build_release import read_csv,write_csv,sha,lab,expected_label,verify_labels
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';BASE=ROOT/'road_hazards_v5_all';OUT=ROOT/'road_hazards_v5_all_corrected_final'
decisions=[json.loads(s) for s in (R/'all_images_resolution_decisions.jsonl').read_text().splitlines()]
queue=read_csv(R/'all_images_resolution_queue.csv')
assert len(decisions)==len(queue)==435 and {r['image'] for r in decisions}=={r['image'] for r in queue}
assert {r['q'] for r in decisions}==set(range(1,436))
fixes={r['image']:r for r in map(json.loads,(R/'all_images_fixes.jsonl').read_text().splitlines())}
assert all(r['image'].startswith('images/train/') for r in fixes.values())
manifest=read_csv(OUT/'manifest.csv');original={r['out_image']:r for r in read_csv(BASE/'manifest.csv')}
stats=defaultdict(Counter);fingerprint=hashlib.sha256();sources=Counter()
for n,r in enumerate(manifest,1):
 image=r['out_image'];raw=(OUT/image).read_bytes();digest=sha(raw)
 assert digest==sha((BASE/image).read_bytes())==original[image]['out_sha256'],image
 with Image.open(io.BytesIO(raw)) as im:assert im.size==(960,720);im.load()
 label=lab(OUT,image).read_bytes();expected=expected_label(fixes[image]['boxes']) if image in fixes else lab(BASE,image).read_bytes()
 assert label==expected,image
 counts=verify_labels(label)
 assert counts[0]==int(r['n_pothole']) and counts[1]==int(r['n_speed_bump']),image
 stats[r['split']].update(images=1,pothole_boxes=counts[0],speed_bump_boxes=counts[1],empty=int(not counts))
 if r['split']=='train':sources[r['source']]+=1
 fingerprint.update((image+digest+sha(label)).encode())
 if n%2000==0:print(f'Verified {n}/{len(manifest)}',flush=True)
assert {k:v['images'] for k,v in stats.items()}==dict(train=10562,val=830,test=323)
for split,stat in stats.items():
 assert len(list((OUT/'images'/split).glob('*')))==stat['images']
 assert len(list((OUT/'labels'/split).glob('*.txt')))==stat['images']
import yaml
for name in ['data.yaml','data_stdframe.yaml']:
 config=yaml.safe_load((OUT/name).read_text());assert Path(config['path']).resolve()==OUT.resolve()
 assert config['names']=={0:'pothole',1:'speed_bump'} or config['names']==['pothole','speed_bump']
 for split in ['train','val','test']:assert (OUT/config[split]).exists()
for name in ['val_stdframe.txt','test_stdframe.txt']:
 for line in (OUT/name).read_text().splitlines():assert (OUT/line).exists(),line
byimage={r['image']:r for r in decisions};prior={r['image']:r for r in read_csv(R/'release_selection_codex.csv')};audit=[]
for r in manifest:
 if r['split']!='train':continue
 image=r['out_image'];d=byimage.get(image)
 audit.append(dict(image=image,source=r['source'],release_status='included',review_basis='all_images_visual_recheck' if d else prior[image]['review_basis'],confidence=d['confidence'] if d else 'prior_review',action=d['action'] if d else 'prior_review',reason=d['reason'] if d else '',image_sha256=r['out_sha256'],label_sha256=sha(lab(OUT,image).read_bytes())))
write_csv(OUT/'review_status.csv',audit)
summary=dict(date='2026-11-12',dataset=str(OUT),excluded_train_images=0,rechecked_images=435,additional_label_changes=sum(r['action']=='replace' for r in decisions),cumulative_replacement_records=len(fixes),confidence_counts=dict(Counter(r['confidence'] for r in decisions)),splits={k:dict(v) for k,v in stats.items()},train_sources=dict(sources),content_fingerprint=fingerprint.hexdigest(),verification='PASS: all image bytes/dimensions/decodes; all labels versus source or explicit replacements; all label classes/bounds; manifest counts; split counts; YAML/list paths.',limitations='AI visual review, no detector predictions. Low-confidence records are included with their best-available existing annotations, not certified correct. Review completion does not mean ambiguity was eliminated. Validation/test bytes unchanged; no training or evaluation run.')
for name in ['all_images_resolution_decisions.jsonl','all_images_fixes.jsonl']:shutil.copyfile(R/name,OUT/name)
(OUT/'release_info.json').write_text(json.dumps(summary,indent=2)+'\n')
(R/'ALL_IMAGES_RELEASE_REPORT.json').write_text(json.dumps(summary,indent=2)+'\n')
report='# All-images corrected release\n\n'+f'All 10,562 training images included; 830 validation and 323 test images unchanged. No image excluded.\n\n435 ambiguous cases visually rechecked; {summary["additional_label_changes"]} additional label changes. Cumulative replacement records: {len(fixes)}.\n\n'+f'Recheck confidence: {summary["confidence_counts"]}. Low-confidence labels remain best-available annotations, not confirmed ground truth.\n\n'+summary['verification']+'\n\n'+summary['limitations']+'\n'
(OUT/'README_STAGE40.md').write_text(report);(R/'ALL_IMAGES_RELEASE_REPORT.md').write_text(report)
for dest in [R/'PROGRESS.md',ROOT/'review/clean_r2/STATUS_for_claude.md']:
 with dest.open('a',encoding='utf-8') as f:f.write('\n\n## 2026-11-12 all-images follow-up\n'+report.replace('# All-images corrected release\n','')+'\nOutput: '+str(OUT)+'\n')
print(json.dumps(summary,indent=2),flush=True)
