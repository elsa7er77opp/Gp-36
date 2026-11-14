"""Record actual upstream-pixel observations; ambiguous texture remains unresolved."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'review/v5/pretrain'
rows={r['q']:r for r in map(json.loads,(R/'source_review_decisions.jsonl').read_text().splitlines())}
notes={
1:([0],'low','Near box has localized coarse material loss but fill versus open depression remains uncertain; second box is a windshield/surface streak.'),
2:([0],'low','Near coarse dark defect could be asphalt loss; far light mark lacks a broken rim. Higher-pixel copy does not settle near defect depth.'),
3:([0,1],'low','Near localized rough depression contradicts previous confident negative; distant small dark mark remains ambiguous. Restore best-available boxes pending stronger evidence.'),
9:(None,'low','Near water-covered coarse road damage is visible; distant narrow openings remain crack-versus-pothole ambiguous.'),
15:(None,'medium','Individual upstream crops show exposed aggregate, cavities and broken pavement rims in all five regions; retain five boxes.'),
17:(None,'medium','Full upstream scene places these gravel/debris regions in the unpaved entrance outside asphalt; retain negative.'),
22:([2,3,4,5],'low','Boxes zero and one include light debris or a light surface strip without a cavity; remaining wet aggregate and water hide depression boundaries.'),
26:([0,1,2,3],'low','Road-edge water regions have broken asphalt boundaries, but exact water-covered extent remains uncertain; fifth region lacks an asphalt cavity.'),
28:(None,'low','Upstream image remains too dark to distinguish open asphalt loss from filled coarse repairs reliably.'),
40:([0,1],'medium','Both upstream crops show dark cavities with broken asphalt rims; reverse previous negative based on lower-detail copy.'),
41:(None,'low','Several small water-filled cavities have visible edges, but broad roadside water and shoulder regions remain ambiguous; no blanket confirmation.'),
43:([0,1,2,3,4],'low','Upstream crops reveal localized dark depressions and aggregate edges, contradicting prior confident negative; filled-versus-open state remains uncertain for some regions.'),
48:(None,'low','Large region crosses windshield obstruction and litter; visible dark road area does not settle asphalt-loss extent.'),
51:([2,3,4,5,6,7],'low','Exclude broad unpaved shoulder pools zero and one; remaining regions have broken pavement edges but water obscures depth and exact limits.'),
58:(None,'low','Small localized dark defects are visible but blur and blue windshield cast prevent reliable open-versus-filled adjudication.')}
out=[]
for q,(keep,confidence,reason) in notes.items():
 r=dict(q=q,confidence=confidence,reason=reason,evidence=f'upstream_source_full_and_individual_rois:upstream_box_views/q{q:03}.jpg')
 if keep is None:r['boxes']=rows[q]['boxes']
 else:r['keep']=keep
 out.append(r)
(R/'amend_upstream_4k.json').write_text(json.dumps(out,indent=2))
print('Prepared',len(out),'documented upstream reviews')
