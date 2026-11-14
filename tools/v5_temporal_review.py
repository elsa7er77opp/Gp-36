"""Show neighboring original frames without predictions or neighboring annotations."""
import csv,json,re,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5/pretrain';O=R/'context_views';O.mkdir(exist_ok=True)
ms=list(csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open()));meta={r['out_image']:r for r in ms}
ds={r['q']:r for r in map(json.loads,(R/'source_review_decisions.jsonl').read_text().splitlines())}
def frame(path):
 name=Path(path).name
 m=re.search(r'_f(\d+)',name) or re.search(r'frame_(\d+)',name)
 if m:return int(m[1])
 m=re.search(r'frame(\d+)-(\d+)-(\d+)-(\d+)',name)
 return sum(int(v)*w for v,w in zip(m.groups(),[360000,6000,100,1])) if m else None
index=[]
def video_key(r):
 name=Path(r['orig_image']).name
 if r['source']=='sb15':
  m=re.match(r'frame\d+-\d+-\d+-\d+(.*?)_jpg',name)
  return m[1] if m else name
 return re.sub(r'(_f\d+|frame_\d+).*','',name)
for q in map(int,sys.argv[1:]):
 d=ds[q];m=meta[d['image']];f=frame(m['orig_image']);assert f is not None
 same=sorted([r for r in ms if r['group_id']==m['group_id'] and r['split']=='train' and video_key(r)==video_key(m) and frame(r['orig_image']) is not None],key=lambda r:frame(r['orig_image']))
 earlier=[r for r in same if frame(r['orig_image'])<f];later=[r for r in same if frame(r['orig_image'])>f]
 picked=earlier[-2:]+[m]+later[:2]
 canvas=Image.new('RGB',(len(picked)*384,1050),(25,25,25));draw=ImageDraw.Draw(canvas)
 for k,r in enumerate(picked):
  im=Image.open(r['orig_image']).convert('RGB');rot=int(r.get('rotate_cw') or 0)
  if rot:im=im.rotate(-rot,expand=True)
  W,H=im.size;full=ImageOps.contain(im,(384,650));canvas.paste(full,(k*384+(384-full.width)//2,0))
  road=im.crop((0,int(H*.46),W,int(H*.88)));road=ImageOps.contain(road,(384,330));canvas.paste(road,(k*384,680))
  draw.text((k*384+3,653),f"Q{q} {'TARGET' if r==m else 'context'} frame {frame(r['orig_image'])}",fill='yellow' if r==m else 'white')
 canvas.save(O/f'q{q:03}.jpg',quality=95)
 index.append({'q':q,'target_frame':f,'frames':[{'frame':frame(r['orig_image']),'path':r['orig_image']} for r in picked]})
(O/'index.json').write_text(json.dumps(index,indent=2));print('Rendered',len(index),'temporal comparisons')
