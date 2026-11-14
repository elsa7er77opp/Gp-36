"""Read-only source-quality, leakage and label checks before a new training run."""
import csv,json,sys
from pathlib import Path
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gp36data.hashing import dhash,phash,hamming_to_all
DATA=ROOT/'road_hazards_v5_all_corrected_final';OUT=ROOT/'review/v5/pretrain';OUT.mkdir(exist_ok=True)
rows=list(csv.DictReader((DATA/'manifest.csv').open()));low=list(csv.DictReader((DATA/'low_confidence_review.csv').open()));byimage={r['out_image']:r for r in rows}
def write(name,rs,fields):
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)
quality=[]
for d in low:
 m=byimage[d['image']];p=Path(m['orig_image']);p=p if p.is_absolute() else ROOT/p
 with Image.open(p) as im:W,H=im.size
 quality.append(dict(q=d['q'],image=d['image'],source=m['source'],original=str(p.resolve()),original_w=W,original_h=H,standardized_w=960,standardized_h=720,has_more_source_pixels=int(W*H>960*720),group_id=m['group_id']))
write('source_quality.csv',quality,list(quality[0]))
def hashes(m):
 with Image.open(DATA/m['out_image']) as im:return dhash(im),phash(im)
with ThreadPoolExecutor(max_workers=4) as pool:hp=list(pool.map(hashes,rows))
D=np.array([x[0] for x in hp],dtype=np.uint64);P=np.array([x[1] for x in hp],dtype=np.uint64)
near=[];within=Counter();group=defaultdict(set);exact=defaultdict(set)
for i,m in enumerate(rows):
 if m['group_id']:group[m['group_id']].add(m['split'])
 exact[m['out_sha256']].add(m['split'])
 dd=hamming_to_all(int(D[i]),D[i+1:]);cand=np.flatnonzero(dd<=4)
 if not len(cand):continue
 pd=hamming_to_all(int(P[i]),P[i+1+cand])
 for c,pd0 in zip(cand,pd):
  if pd0>10:continue
  j=i+1+int(c);n=rows[j]
  if m['split']==n['split']:within[m['split']]+=1;continue
  near.append(dict(image_a=m['out_image'],split_a=m['split'],image_b=n['out_image'],split_b=n['split'],dhash=int(dd[c]),phash=int(pd0),source_a=m['source'],source_b=n['source']))
write('cross_split_candidates.csv',near,['image_a','split_a','image_b','split_b','dhash','phash','source_a','source_b'])
summary=dict(images=len(rows),low_confidence_images=len(low),larger_originals=sum(r['has_more_source_pixels'] for r in quality),source_shapes=dict(Counter(f"{r['original_w']}x{r['original_h']}" for r in quality)),cross_split_group_ids={g:sorted(s) for g,s in group.items() if len(s)>1},exact_cross_split_hashes=sum(len(s)>1 for s in exact.values()),near_cross_split_candidates=len(near),near_within_split_pairs=dict(within),note='Perceptual matches are candidates, not automatic proof of leakage. No images removed and no detector predictions used.')
(OUT/'audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
