"""Append actual visual decisions and build cumulative replacement file; preserve prior releases."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';P=R/'pretrain/source_review_decisions.jsonl'
base={r['q']:r for r in map(json.loads,(R/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
old=[json.loads(s) for s in P.read_text().splitlines()] if P.exists() else [];seen={r['q'] for r in old};batch=json.loads(Path(sys.argv[1]).read_text());new=[]
for item in batch:
 q=item['q'];assert q not in seen;seen.add(q);b=base[q];bs=b['boxes'];keep=item.get('keep');boxes=item.get('boxes',bs if keep is None else [bs[i] for i in keep])
 for c,x,y,X,Y in boxes:assert c in (0,1) and 0<=x<X<=1 and 0<=y<Y<=1
 new.append(dict(q=q,image=b['image'],boxes=boxes,action='replace' if boxes!=bs else 'keep',confidence=item['confidence'],status='unresolved' if item['confidence']=='low' else 'ai_adjudicated',reason=item['reason'],reviewer='codex_original_pixels',evidence=item.get('evidence','original_source_roi')))
allrows=sorted(old+new,key=lambda r:r['q']);tmp=P.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r)+'\n' for r in allrows));tmp.replace(P)
fixes={r['image']:r for r in map(json.loads,(R/'all_images_fixes.jsonl').read_text().splitlines())}
for r in allrows:
 if r['action']=='replace':fixes[r['image']]=dict(image=r['image'],boxes=r['boxes'],why=r['reason'])
p=R/'pretrain/source_review_fixes.jsonl';tmp=p.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r)+'\n' for r in fixes.values()));tmp.replace(p)
print('Source rechecks:',len(allrows),'new replacements:',sum(r['action']=='replace' for r in allrows),'remaining unresolved in reviewed:',sum(r['status']=='unresolved' for r in allrows),flush=True)
