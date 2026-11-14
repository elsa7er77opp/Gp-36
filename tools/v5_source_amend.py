"""Apply documented visual-review revisions and preserve the prior decision in history."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'review/v5';P=R/'pretrain/source_review_decisions.jsonl'
rows=[json.loads(s) for s in P.read_text().splitlines()];changes={r['q']:r for r in json.loads(Path(sys.argv[1]).read_text())}
base={r['q']:r for r in map(json.loads,(R/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
for r in rows:
 if r['q'] not in changes:continue
 c=changes.pop(r['q']);history=r.get('history',[])+[{k:v for k,v in r.items() if k!='history'}]
 if 'keep' in c:c['boxes']=[base[r['q']]['boxes'][i] for i in c.pop('keep')]
 r.update(c);r['history']=history;r['status']='unresolved' if r['confidence']=='low' else 'ai_adjudicated';r['action']='replace' if r['boxes']!=base[r['q']]['boxes'] else 'keep'
assert not changes
t=P.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in rows));t.replace(P)
fixes={r['image']:r for r in map(json.loads,(R/'all_images_fixes.jsonl').read_text().splitlines())}
for r in rows:
 if r['action']=='replace':fixes[r['image']]={'image':r['image'],'boxes':r['boxes'],'why':r['reason']}
p=R/'pretrain/source_review_fixes.jsonl';t=p.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in fixes.values()));t.replace(p)
print('Revised decisions; unresolved:',sum(r['status']=='unresolved' for r in rows))
