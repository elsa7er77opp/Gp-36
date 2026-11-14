"""Audit original and standardized pixels under all 8 flips/rotations, without model output.

Matches are review candidates, never automatic proof of leakage. Save hashes for addition screening.
"""
import csv,hashlib,json,re,sys
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gp36data.hashing import dhash,phash
from new_data_forensics import DIHEDRAL
DATA=ROOT/'road_hazards_v5_source_review_20261112_u4k';OUT=ROOT/'review/v5/no_leak_gate';OUT.mkdir(exist_ok=True)
rows=list(csv.DictReader((DATA/'manifest.csv').open()));cache=OUT/'current_pixel_hashes.npz'
fingerprint=hashlib.sha256((DATA/'manifest.csv').read_bytes()).hexdigest()
def work(r):
 paths=[DATA/r['out_image'],Path(r['orig_image'])]
 if not paths[1].is_absolute():paths[1]=ROOT/paths[1]
 ds=[];ps=[]
 for p in paths:
  with Image.open(p) as im:
   im.draft('RGB',(512,512));im=im.convert('RGB')
   transforms=[im if t is None else im.transpose(t) for t in DIHEDRAL]
   ds.append([dhash(x) for x in transforms]);ps.append([phash(x) for x in transforms])
 return ds,ps
if cache.exists():
 z=np.load(cache);assert str(z['manifest_sha'])==fingerprint;D=z['dhash'];P=z['phash']
else:
 hp=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for i,h in enumerate(pool.map(work,rows),1):
   hp.append(h)
   if i%1000==0:print('Hashed original and standardized views',i,'/',len(rows),flush=True)
 D=np.array([h[0] for h in hp],dtype=np.uint64);P=np.array([h[1] for h in hp],dtype=np.uint64)
 np.savez_compressed(cache,dhash=D,phash=P,manifest_sha=fingerprint,image=np.array([r['out_image'] for r in rows]),split=np.array([r['split'] for r in rows]))
# Identity of both original and standard views, compared to all query orientations.
indices=np.array([i for i,r in enumerate(rows) if r['split']!='train'])
BD=D[indices,:,0].reshape(-1);BP=P[indices,:,0].reshape(-1)
bank=[(rows[i]['split']+':'+rows[i]['out_image'],v) for i in indices for v in ['standard','original']]
protected=np.load(ROOT/'review/new_data_r3/protected_hashes.npz',allow_pickle=False)
mask=np.array([not str(x).startswith('train:') for x in protected['id']])
BD=np.concatenate([BD,protected['dhash'][mask]]);BP=np.concatenate([BP,protected['phash'][mask]])
bank.extend((str(x),'protected_original') for x in protected['id'][mask])
hits=[]
for i,r in enumerate(rows):
 if r['split']!='train':continue
 seen=set()
 for view in range(2):
  for t in range(8):
   dd=np.bitwise_count(BD^D[i,view,t]);cand=np.flatnonzero(dd<=4)
   if not len(cand):continue
   pp=np.bitwise_count(BP[cand]^P[i,view,t])
   for k,pdist in zip(cand,pp):
    if pdist>10 or bank[k][0] in seen:continue
    seen.add(bank[k][0]);hits.append(dict(image=r['out_image'],source=r['source'],query_view=['standard','original'][view],transform=t,protected_id=bank[k][0],protected_view=bank[k][1],dhash=int(dd[k]),phash=int(pdist)))
 if i%2000==0:print('Compared',i,'/',len(rows),'matches',len(hits),flush=True)
with (OUT/'cross_split_candidates.csv').open('w',newline='') as f:
 fields=['image','source','query_view','transform','protected_id','protected_view','dhash','phash'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(hits)
groups=defaultdict(set);exact=defaultdict(set);videos=defaultdict(set)
for r in rows:
 if r.get('group_id'):groups[r['group_id']].add(r['split'])
 for key in ['orig_sha256','out_sha256']:
  if r.get(key):exact[r[key]].add(r['split'])
 stem=Path(r['orig_image']).stem
 # Only explicit video names, not generic numeric frame counters or photo IDs.
 for pat in [r'(VID[_-]\d{8}[_-]\d{6})',r'(MVI[_-]\d{4})',r'(IMG_\d+)[_-].*MOV',r'^(\d{14}_\d+)_frame']:
  match=re.search(pat,stem,re.I)
  if match:videos[match.group(1).upper()].add(r['split']);break
summary=dict(dataset=str(DATA),images=len(rows),manifest_sha=fingerprint,views=['standardized','original'],transforms_per_view=8,dhash_threshold=4,phash_threshold=10,protected_reference_count=len(bank),cross_split_candidate_pairs=len(hits),candidate_train_images=len({h['image'] for h in hits}),cross_split_groups={g:sorted(v) for g,v in groups.items() if len(v)>1},cross_split_explicit_video_keys={g:sorted(v) for g,v in videos.items() if len(v)>1},exact_cross_split_hashes=sum(len(v)>1 for v in exact.values()),note='Review all candidates before training. Zero matches cannot prove every possible shared scene is absent. Generic filenames do not identify videos reliably; no semantic or training-readiness certification.')
summary['screen_pass']=not (hits or summary['cross_split_groups'] or summary['cross_split_explicit_video_keys'] or summary['exact_cross_split_hashes'])
(OUT/'REPORT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
