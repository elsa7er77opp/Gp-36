"""Record explicit visual decisions; untouched queue rows are never auto-reviewed."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'review/v5'
queue=list(csv.DictReader((R/'all_images_resolution_queue.csv').open()))
p=R/'all_images_resolution_decisions.jsonl'
old=[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
byq={r['q']:r for r in old}
batch=json.loads(Path(sys.argv[1]).read_text())
pending=[]
for item in batch:
 q=item['q'];r=queue[q-1];bs=json.loads(r['current_boxes'])
 assert 1<=q<=len(queue) and q not in byq
 keep=item.get('keep')
 boxes=item.get('boxes',bs if keep is None else [bs[i] for i in keep])
 for c,x,y,X,Y in boxes:assert c in (0,1) and 0<=x<X<=1 and 0<=y<Y<=1
 pending.append(dict(q=q,image=r['image'],sheet=r['sheet'],cell=r['cell'],action='keep' if boxes==bs else 'replace',confidence=item['confidence'],reason=item['reason'],boxes=boxes,reviewer='codex_visual'))
assert len({r['q'] for r in pending})==len(pending)
out=sorted(old+pending,key=lambda r:r['q']);tmp=p.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r)+'\n' for r in out));tmp.replace(p)
fixes={r['image']:r for r in map(json.loads,(R/'fixes.jsonl').read_text().splitlines())}
for r in out:
 if r['action']=='replace':fixes[r['image']]=dict(image=r['image'],boxes=r['boxes'],why=r['reason'])
f=R/'all_images_fixes.jsonl';tmp=f.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r)+'\n' for r in fixes.values()));tmp.replace(f)
print(f'Reviewed {len(out)}/{len(queue)}; additional changed images {sum(r["action"]=="replace" for r in out)}; cumulative fixes {len(fixes)}')
