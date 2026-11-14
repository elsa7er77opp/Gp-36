"""Read dimensions of every release image; write an explicit resolution audit."""
import json
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'road_hazards_v5_source_review_20261112_u4k'
report={'dataset':str(DATA),'required_size':[960,720],'splits':{},'mismatches':[],'unreadable':[]}
for split in ['train','val','test']:
 sizes=Counter();files=sorted((DATA/'images'/split).glob('*'))
 for p in files:
  try:
   with Image.open(p) as im:wh=im.size
   sizes[f'{wh[0]}x{wh[1]}']+=1
   if wh!=(960,720):report['mismatches'].append({'image':str(p),'size':wh})
  except Exception as e:report['unreadable'].append({'image':str(p),'error':str(e)})
 report['splits'][split]={'images':len(files),'sizes':dict(sizes)}
report['total_images']=sum(r['images'] for r in report['splits'].values())
report['pass']=report['total_images']==11715 and not report['mismatches'] and not report['unreadable']
p=ROOT/'review/v5/pretrain/RESOLUTION_AUDIT.json';p.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['pass']
