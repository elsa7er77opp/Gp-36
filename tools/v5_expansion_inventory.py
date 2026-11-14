"""Count unused local data parts without touching any labels or held-out split."""
import csv,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/v5/expansion13000';O.mkdir(exist_ok=True)
base=list(csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open()));used_sha={r['orig_sha256'] for r in base};held_groups={r['group_id'] for r in base if r['split']!='train'}
out=[]
for part in sorted((ROOT/'parts_r3').iterdir()):
 p=part/'manifest.csv'
 if not p.exists():continue
 rs=list(csv.DictReader(p.open()));tr=[r for r in rs if r['split']=='train'];unused=[r for r in tr if r.get('orig_sha256') not in used_sha and r.get('group_id') not in held_groups]
 out.append(dict(part=part.name,total=len(rs),train=len(tr),unused_train=len(unused),unused_pothole_images=sum(int(r.get('n_pothole') or 0)>0 for r in unused),unused_bump_images=sum(int(r.get('n_speed_bump') or 0)>0 for r in unused),unused_negative_images=sum(int(r.get('n_speed_bump') or 0)+int(r.get('n_pothole') or 0)==0 for r in unused),groups=len({r.get('group_id') for r in unused})))
(O/'inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
print('Current train sources:',dict(Counter(r['source'] for r in base if r['split']=='train')))
