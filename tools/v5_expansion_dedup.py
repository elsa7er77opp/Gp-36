"""Screen staged additions against every current image and each other, original + standardized, 8 transforms."""
import csv,json,sys
from collections import Counter
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gp36data.hashing import dhash,phash
from new_data_forensics import DIHEDRAL
E=ROOT/'review/v5/expansion13000';upstream='--upstream' in sys.argv;O=E/'upstream_checks' if upstream else E;O.mkdir(exist_ok=True);C=E/('upstream_candidates' if upstream else 'rdd_candidates');prefix='u' if upstream else 'c';rows=[r for r in map(json.loads,(C/'candidate_ledger.jsonl').read_text().splitlines()) if not r['leak_check']['hit']]
if upstream:assert (C/'PREPARATION_REPORT.json').exists(),'Candidate preparation must finish first'
base=np.load(ROOT/'review/v5/no_leak_gate/current_pixel_hashes.npz',allow_pickle=False)
BD=base['dhash'][:,:,0].reshape(-1);BP=base['phash'][:,:,0].reshape(-1)
ids=[str(split)+':'+str(image) for split,image in zip(base['split'],base['image']) for v in range(2)]
protected=np.load(ROOT/'review/new_data_r3/protected_hashes.npz',allow_pickle=False);mask=np.array([not str(x).startswith('train:') for x in protected['id']])
BD=np.concatenate([BD,protected['dhash'][mask]]);BP=np.concatenate([BP,protected['phash'][mask]]);ids.extend(map(str,protected['id'][mask]))
cache=O/'candidate_pixel_hashes.npz'
def work(r):
 ds=[];ps=[]
 for path in [C/f"{prefix}{r['candidate']:04}.jpg",Path(r['manifest']['orig_image'])]:
  with Image.open(path) as im:
   im.draft('RGB',(512,512));im=im.convert('RGB');ts=[im if t is None else im.transpose(t) for t in DIHEDRAL]
   ds.append([dhash(x) for x in ts]);ps.append([phash(x) for x in ts])
 return ds,ps
if cache.exists():
 z=np.load(cache);D=z['dhash'];P=z['phash'];assert z['candidate'].tolist()==[r['candidate'] for r in rows]
else:
 hp=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for i,h in enumerate(pool.map(work,rows),1):
   hp.append(h)
   if i%500==0:print('Candidate hashes',i,'/',len(rows),flush=True)
 D=np.array([h[0] for h in hp],dtype=np.uint64);P=np.array([h[1] for h in hp],dtype=np.uint64)
 np.savez_compressed(cache,dhash=D,phash=P,candidate=np.array([r['candidate'] for r in rows]))
matches=[];internal=[]
for i,r in enumerate(rows):
 seen=set()
 for view in range(2):
  for t in range(8):
   dd=np.bitwise_count(BD^D[i,view,t]);ks=np.flatnonzero(dd<=4)
   for k in ks:
    p=int(np.bitwise_count(BP[k]^P[i,view,t]))
    if p<=10 and ids[k] not in seen:
     seen.add(ids[k]);matches.append(dict(candidate=r['candidate'],reference=ids[k],view=view,transform=t,dhash=int(dd[k]),phash=p))
 # All other candidates, both identity views. Each pair written once.
 seen=set();nd=D[i+1:,:,0].reshape(-1);np_=P[i+1:,:,0].reshape(-1)
 for view in range(2):
  for t in range(8):
   dd=np.bitwise_count(nd^D[i,view,t]);ks=np.flatnonzero(dd<=4)
   for k in ks:
    p=int(np.bitwise_count(np_[k]^P[i,view,t]));j=i+1+int(k)//2
    if p<=10 and j not in seen:
     seen.add(j);internal.append(dict(candidate=r['candidate'],reference=rows[j]['candidate'],view=view,transform=t,dhash=int(dd[k]),phash=p))
 if (i+1)%400==0:print('Compared',i+1,'/',len(rows),'current-reference matches',len(matches),'internal',len(internal),flush=True)
for filename,data in [('current_reference_matches.csv',matches),('within_candidate_matches.csv',internal)]:
 with (O/filename).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['candidate','reference','view','transform','dhash','phash']);w.writeheader();w.writerows(data)
summary=dict(candidates=len(rows),current_reference_match_pairs=len(matches),current_reference_candidate_images=len({r['candidate'] for r in matches}),protected_eval_candidate_images=len({r['candidate'] for r in matches if not r['reference'].startswith('train:')}),within_candidate_pairs=len(internal),note='Potential matches require visual adjudication. This screen does not accept any image or certify annotations. Source and standardized pixels, all eight transforms; dHash<=4 and pHash<=10 in same transform.')
(O/'DEDUP_REPORT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
