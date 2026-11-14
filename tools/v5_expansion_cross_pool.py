"""Check both new candidate pools against one another before any final merge."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'review/v5/expansion13000'
rdd=np.load(E/'candidate_pixel_hashes.npz',allow_pickle=False);up=np.load(E/'upstream_checks/candidate_pixel_hashes.npz',allow_pickle=False)
BD=rdd['dhash'][:,:,0].reshape(-1);BP=rdd['phash'][:,:,0].reshape(-1);RID=rdd['candidate'];UD=up['dhash'];UP=up['phash'];UID=up['candidate'];matches=[]
for i,uid in enumerate(UID):
 seen=set()
 for view in range(2):
  for t in range(8):
   dd=np.bitwise_count(BD^UD[i,view,t]);ks=np.flatnonzero(dd<=4)
   for k in ks:
    p=int(np.bitwise_count(BP[k]^UP[i,view,t]));cid=int(RID[int(k)//2])
    if p<=10 and cid not in seen:
     seen.add(cid);matches.append(dict(upstream_candidate=int(uid),rdd_candidate=cid,upstream_view=view,transform=t,dhash=int(dd[k]),phash=p))
with (E/'CROSS_POOL_MATCHES.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['upstream_candidate','rdd_candidate','upstream_view','transform','dhash','phash']);w.writeheader();w.writerows(matches)
report=dict(upstream_candidates=len(UID),rdd_candidates=len(RID),candidate_pairs=len(matches),views=['source','standardized'],transforms=8,thresholds=dict(dhash=4,phash=10),notes='Potential matches need visual adjudication. No candidate automatically accepted or deleted. Complements current/protected and within-pool checks.')
(E/'CROSS_POOL_REPORT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
