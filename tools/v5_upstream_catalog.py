"""Find higher-resolution upstream copies by exact frame identity, not model output."""
import csv,json,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5/pretrain';D=ROOT.parent/'GP36_Dataset/raw_v3/rf_dashcam7k/x'
def canonical(name):
 s=Path(name).stem
 s=re.sub(r'(?:_jpg)?\.rf\.[0-9a-f]+$','',s)
 return re.sub(r'_jpg$','',s)
best={}
for p in D.rglob('*'):
 if p.suffix.lower() not in ['.jpg','.jpeg','.png']:continue
 with Image.open(p) as im:wh=im.size
 key=canonical(p.name)
 if key not in best or wh[0]*wh[1]>best[key][1][0]*best[key][1][1]:best[key]=(p,wh)
quality=list(csv.DictReader((R/'source_quality.csv').open()));found=[]
for q in quality:
 if q['source']!='bpo':continue
 match=best.get(canonical(q['original']))
 if match:
  p,wh=match
  found.append({**q,'previous_original':q['original'],'original':str(p.resolve()),'original_w':wh[0],'original_h':wh[1],'has_more_source_pixels':int(wh[0]*wh[1]>960*720)})
with (R/'upstream_quality.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(found[0]));w.writeheader();w.writerows(found)
(R/'upstream_catalog.json').write_text(json.dumps({k:{'path':str(v[0]),'size':v[1]} for k,v in best.items()}))
print('Unique upstream frame names:',len(best),'BPO matches:',len(found),'higher pixel count:',sum(r['has_more_source_pixels'] for r in found));print([(r['q'],r['original_w'],r['original_h']) for r in found])
