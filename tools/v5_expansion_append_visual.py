"""Append individually observed visual decisions; no automatic confidence promotion."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'review/v5/expansion13000';upstream='--upstream' in sys.argv;P=R/('upstream_visual_review_decisions.jsonl' if upstream else 'rdd_visual_review_decisions.jsonl')
rows=[json.loads(x) for x in P.read_text().splitlines()];seen={r['candidate'] for r in rows}
for r in json.loads(Path(sys.argv[1]).read_text()):
 i=r['candidate'];assert i not in seen
 r.update(reviewer='codex_visual',evidence=f'{"upstream_candidates" if upstream else "rdd_candidates"}/sheet_{((i-1)//6)*6+1:04}.jpg',accepted_into_training_release=False)
 rows.append(r);seen.add(i)
t=P.with_suffix('.tmp');t.write_text(''.join(json.dumps(r)+'\n' for r in sorted(rows,key=lambda r:r['candidate'])));t.replace(P)
print('Visual decisions saved:',len(rows),'Next candidate:',max(seen)+1)
