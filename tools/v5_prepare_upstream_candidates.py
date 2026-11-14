"""Prepare upstream candidates at 960x720, preserving source annotations as proposals only."""
import csv,hashlib,json,math,sys
from collections import defaultdict,deque,Counter
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
from std_dataset_v2 import read_boxes,plan,map_boxes,render
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000';OUT=E/'upstream_candidates';OUT.mkdir(exist_ok=True)
src=list(csv.DictReader((E/'upstream_candidates_inventory.csv').open()));ledger=OUT/'candidate_ledger.jsonl'
resume='--resume' in sys.argv
assert resume or not ledger.exists(),'Refuse candidate-ledger overwrite; use --resume after a stopped preparation'
previous=[json.loads(s) for s in ledger.read_text().splitlines()] if resume and ledger.exists() else []
assert [r['candidate'] for r in previous]==list(range(1,len(previous)+1))
groups=defaultdict(list)
for r in src:groups[r['video_id']].append(r)
# Interleave distinct videos and prefer their middle frame before nearby frames.
queues=[]
for key in sorted(groups,key=lambda k:(groups[k][0]['video_previously_in_training']=='True',k)):
 rs=sorted(groups[key],key=lambda r:r['frame_id']);order=[];q=deque([(0,len(rs))])
 while q:
  lo,hi=q.popleft()
  if lo>=hi:continue
  mid=(lo+hi)//2;order.append(rs[mid]);q.extend([(lo,mid),(mid+1,hi)])
 queues.append(deque(order))
ordered=[]
while any(queues):
 for q in queues:
  if q:ordered.append(q.popleft())
a=SimpleNamespace(tw=960,th=720,min_keep=.5);tiles=[];counts=Counter(r['mode'] for r in previous)
for row in previous[(len(previous)//6)*6:]:
 i=row['candidate'];std=Image.open(OUT/f'u{i:04}.jpg').convert('RGB');d=ImageDraw.Draw(std)
 for j,(c,x,y,X,Y) in enumerate(row['proposed_boxes']):d.rectangle((x*960,y*720,X*960,Y*720),outline='lime',width=2);d.text((x*960,y*720),str(j),fill='red')
 tiles.append((i,std.resize((640,480))))
with ledger.open('a' if previous else 'w') as f:
 for i,r in enumerate(ordered,1):
  if i<=len(previous):continue
  original=Path(r['original']);boxes=read_boxes(Path(r['original_label']))
  assert all(b[0]==0 and all(math.isfinite(v) for v in b[1:]) and 0<=b[1]<b[3]<=1 and 0<=b[2]<b[4]<=1 for b in boxes),r['frame_id']
  with Image.open(original) as raw:im=raw.convert('RGB')
  W,H=im.size;assert (W,H)==(int(r['width']),int(r['height']))
  mode,win,keep=plan(W,H,boxes,a);mapped,_=map_boxes(boxes,W,H,mode,win,a)
  # Extremely thin subpixel source proposals are not silently accepted as fixed labels.
  # Preserve source geometry and mark the whole image ineligible until individual relabeling.
  box_map_issue=len(mapped)!=len(boxes)
  std=render(im,mode,win,a);assert std.size==(960,720);std.save(OUT/f'u{i:04}.jpg',quality=95)
  row=dict(candidate=i,source='bpo_upstream',frame_id=r['frame_id'],video_id=r['video_id'],manifest=dict(orig_image=str(original),orig_label=r['original_label'],orig_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),group_id='bpo_upstream_video:'+r['video_id']),original_size=[W,H],mode=mode,window=win,proposed_boxes=mapped,source_boxes=boxes,status='requires_full_relabel_subpixel_source_boxes' if box_map_issue else 'pending_guard_hashes_current_train_dedup_and_visual',source_box_map_issues=int(box_map_issue),leak_check={'hit':None,'status':'NOT_RUN_USE_UPSTREAM_CHECKS_BEFORE_ADMISSION'})
  f.write(json.dumps(row)+'\n');f.flush();counts[mode]+=1
  labels=OUT/'proposed_labels';labels.mkdir(exist_ok=True)
  (labels/f'u{i:04}.txt').write_text(''.join(f'{int(c)} {(x+X)/2:.6f} {(y+Y)/2:.6f} {X-x:.6f} {Y-y:.6f}\n' for c,x,y,X,Y in mapped))
  d=ImageDraw.Draw(std)
  for j,(c,x,y,X,Y) in enumerate(mapped):d.rectangle((x*960,y*720,X*960,Y*720),outline='lime',width=2);d.text((x*960,y*720),str(j),fill='red')
  tiles.append((i,std.resize((640,480))))
  if len(tiles)==6 or i==len(ordered):
   sheet=Image.new('RGB',(1280,1530),'#222222');dr=ImageDraw.Draw(sheet)
   for k,(n,tile) in enumerate(tiles):
    x=(k%2)*640;y=(k//2)*510;sheet.paste(tile,(x,y));dr.text((x+3,y+482),f'U{n:04} source proposal ONLY; inspect upstream pixels before acceptance',fill='white')
   sheet.save(OUT/f'sheet_{tiles[0][0]:04}.jpg',quality=95);tiles=[]
  if i%200==0:print('Prepared upstream',i,'/',len(ordered),flush=True)
all_rows=[json.loads(s) for s in ledger.read_text().splitlines()]
for row in all_rows:row['leak_check']['hit']=None
tmp=ledger.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(row)+'\n' for row in all_rows));tmp.replace(ledger)
report=dict(candidates=len(ordered),videos=len(groups),resolution=[960,720],transform_counts=dict(counts),accepted=0,source_annotation_geometry_issue_images=sum(r.get('source_box_map_issues',0) for r in all_rows),guard_checks_completed=False,source_family='BPO upstream; not independent geography',status='prepared_proposals_only',notes='Source proposals, NOT visually confirmed labels. Video IDs interleaved to review distinct scenes first. Used canonical frame IDs and protected BPO videos excluded by inventory; full guard/current/within-candidate pixel checks remain mandatory. Source subpixel geometry issues make an image ineligible until full visual relabeling. No training started.')
(OUT/'PREPARATION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'README.md').write_text('# Upstream candidate proposals only\n\nImages uNNNN.jpg are 960x720. Proposed YOLO labels and annotated contact sheets are provided. Original higher-resolution frames and source boxes are in candidate_ledger.jsonl. No labels are visually approved by this preparation script. Do not train on this directory. Run upstream pixel dedup/held-out guards, manually review every admitted image and all its boxes, and rebuild a verified release.\n')
print(json.dumps(report,indent=2),flush=True)
