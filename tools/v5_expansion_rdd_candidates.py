"""Stage unused RDD candidates with the established 960x720 transform, never auto-accept labels."""
import csv,json
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
from leak_check import load_protected,check_image
from std_dataset_v2 import read_boxes,label_path,plan,map_boxes,render
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/v5/expansion13000';PART=ROOT/'parts_r3/rdd_ji'
base=list(csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open()))
used={r['orig_sha256'] for r in base};held={r['group_id'] for r in base if r['split']!='train'}
candidates=[r for r in csv.DictReader((PART/'manifest.csv').open()) if r['split']=='train' and r['orig_sha256'] not in used and r['group_id'] not in held]
RD,RP,ids,shas=load_protected(ROOT/'review/new_data_r3/protected_hashes.npz')
a=SimpleNamespace(tw=960,th=720,min_keep=.5)
out=O/'rdd_candidates';out.mkdir(exist_ok=True);rows=[];tiles=[]
ledger=out/'candidate_ledger.jsonl'
assert not ledger.exists(),'Refuse to overwrite candidate ledger'
with ledger.open('w') as f:
 for i,r in enumerate(candidates,1):
  p=PART/r['out_image'];hit=check_image(p,RD,RP,ids,shas)
  row=dict(candidate=i,source='rdd_ji',manifest=r,leak_check=hit,status='rejected_protected_match' if hit['hit'] else 'pending_visual_and_current_train_dedup')
  if not hit['hit']:
   with Image.open(p) as original:im=original.convert('RGB')
   boxes=read_boxes(label_path(PART,r['out_image']));mode,win,keep=plan(*im.size,boxes,a);mapped,_=map_boxes(boxes,*im.size,mode,win,a)
   std=render(im,mode,win,a);row.update(mode=mode,window=win,original_size=im.size,proposed_boxes=mapped)
   std.save(out/f'c{i:04}.jpg',quality=95)
   d=ImageDraw.Draw(std)
   for k,(c,x,y,X,Y) in enumerate(mapped):d.rectangle((x*960,y*720,X*960,Y*720),outline='lime',width=2);d.text((x*960,y*720),str(k),fill='red')
   tile=std.resize((640,480));tiles.append((i,tile))
   if len(tiles)==6:
    sheet=Image.new('RGB',(1280,1530),'#222222');dr=ImageDraw.Draw(sheet)
    for k,(n,t) in enumerate(tiles):
     xx=(k%2)*640;yy=(k//2)*510;sheet.paste(t,(xx,yy));dr.text((xx+3,yy+482),f'C{n:04} pending visual review; box indices 0-based',fill='white')
    sheet.save(out/f'sheet_{tiles[0][0]:04}.jpg',quality=95);tiles=[]
  f.write(json.dumps(row)+'\n');f.flush();rows.append(row)
  if i%100==0:print('Screened',i,'/',len(candidates),'eligible',sum(not r['leak_check']['hit'] for r in rows),flush=True)
 if tiles:
  sheet=Image.new('RGB',(1280,1530),'#222222');dr=ImageDraw.Draw(sheet)
  for k,(n,t) in enumerate(tiles):
   xx=(k%2)*640;yy=(k//2)*510;sheet.paste(t,(xx,yy));dr.text((xx+3,yy+482),f'C{n:04} pending visual review',fill='white')
  sheet.save(out/f'sheet_{tiles[0][0]:04}.jpg',quality=95)
print('Done:',len(rows),'candidates; accepted: 0; visual review and current-train near-duplicate checks still required',flush=True)
