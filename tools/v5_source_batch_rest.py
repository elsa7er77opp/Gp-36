"""Record the second visual pass of native-source sheets T1--T206.

Unsettled scenes remain low confidence, never silently promoted by this helper.
"""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'review/v5/pretrain'
quality=[r for r in csv.DictReader((R/'source_quality.csv').open()) if r['has_more_source_pixels']=='0']
keep_medium={124,131,156,157,158,159,163,164,168,169,171,172,174,194,195,199,200,212,213,218,226,230,243,244,245,247,251,266,276,277,279,280,285,298,389,397,426}
keeps={
 1:[],2:[],3:[],15:[3],17:[],40:[],43:[],
 126:[0],160:[],161:[],165:[1],166:[0],173:[0,1,3],177:[0],178:[],
 182:[0],183:[],184:[],185:[2],187:[],188:[0],189:[0],
 201:[],204:[],206:[],208:[],211:[],215:[0,1,2,3,4],217:[],
 232:[0],240:[],250:[],254:[],259:[],261:[],262:[2],264:[0,2,3,4],267:[],269:[0],
 271:[0,1,4,5],273:[],274:[],275:[],281:[0],282:[0],284:[],286:[0,1],287:[],291:[],293:[],294:[0,3],296:[],299:[],300:[],301:[0,1,2],302:[1],304:[3],306:[0],
 325:[],342:[],346:[],412:[0],414:[]
}
reasons={
1:'Both boxes cover intact/filled surface or windshield reflection; no broken asphalt boundary.',
2:'Flat dark repair and tiny road marking are not open cavities.',
3:'Two small marks lack material loss and lie on intact asphalt.',
15:'Retain the near right broken road-edge cavity; other boxes are thin cracks or utility/repair marks.',
17:'Boxes cover unpaved gravel shoulder/entrance, outside the paved road cavity definition.',
40:'Boxes cover curbside dirt/stain on a closed road surface.',
43:'Small boxed regions are road marks on otherwise intact asphalt, without a visible cavity.',
100:'Exposed aggregate on transverse repair is visible but flat-versus-recessed cannot be settled.',
109:'Broad transverse repair has rough texture but its elevation is not established.',
122:'Same broad pale repair; open depression versus filled rough repair remains unsettled.',
126:'Retain broom-side cavity with broken rim; remove flat filled repair and raised loose gravel pile.',
128:'Many clear cavities, but the long overlapping foreground boxes require boundary adjudication.',
133:'Foreground coarse asphalt patch may be filled; distant small boxes cannot all be verified at native resolution.',
136:'Plant-filled circular opening has an asphalt rim, but plant/soil obscures whether this is a pothole or installed planter.',
160:'Box is a closed fine-aggregate asphalt repair, without missing surface.',
161:'Both boxes cover closed flat repairs; no localized exposed lower layer.',
165:'Remove small utility fitting; retain small broken-asphalt cavity beside the alligator cracks.',
166:'Retain foreground material loss; remove tiny rectangular utility fitting.',
173:'Retain three localized missing-asphalt patches; broad foreground box is intact fine aggregate.',
177:'Retain broken-rim pale cavity; neighboring broad box covers closed intact surface.',
178:'Pale region is continuous intact fine-aggregate road surface.',
182:'Retain upper cavity with broken edge; foreground neighboring region is closed filled repair.',
183:'Three boxes follow flat filled repair seams/light patches, without open cavities.',
184:'Single narrow linear road crack, not a localized cavity.',
185:'Retain upper localized rough material loss; remove long narrow linear cracks.',
187:'Both boxes cover intact asphalt; no localized missing material visible.',
188:'Retain upper exposed aggregate bounded by missing asphalt; foreground closed repair removed.',
189:'Retain upper localized pit; remove narrow left linear crack.',
201:'Boxes follow longitudinal/transverse linear cracks, not potholes.',
204:'Dark mark lies on closed intact road; no broken boundary.',
206:'Large region has a closed continuous fine-aggregate repair surface.',
208:'Broad roughened region beneath car is intact closed surface.',
211:'Right linear crack and left closed repair are not open potholes.',
215:'Retain localized material-loss regions; remove giant foreground intact pale patch.',
217:'All three boxes cover intact alligator-cracked asphalt and dust; no open cavity.',
220:'Several left boxes overlap a continuous worn region; exact object boundaries remain uncertain.',
222:'Tiny rough/rectangular patches could include repairs or utility fittings; native source cannot settle all.',
224:'Foreground material loss is visible but connected-versus-separate object boundaries need further evidence.',
232:'Retain left local material loss; remove right intact alligator-cracked asphalt.',
240:'Closed asphalt/utility repair surface with embedded rectangular fitting, not an open cavity.',
250:'Dark closed asphalt repair and pale filled insert, no visible open cavity.',
253:'Boxed fine-aggregate region appears closed; completeness also uncertain because small unboxed dark defects are visible.',
254:'Large box covers a closed continuous asphalt repair surface.',
259:'Circular utility fitting/cover within a repaired road region, not a pothole.',
261:'All three boxes cover closed dark asphalt repair patches.',
262:'Retain large local material loss; remove three narrow transverse/longitudinal cracks.',
264:'Remove broad intact fine-aggregate foreground region; retain separate smaller material-loss cavities.',
267:'Thin crack and closed asphalt patch; neither is an open pothole.',
269:'Retain upper bounded material-loss pit; giant left region is closed repaired road.',
271:'Retain bounded asphalt-loss patches; remove longitudinal crack and broad intact foreground patch.',
273:'White road paint/mark has no broken asphalt rim.',
274:'Thin road crack and flat pale surface mark, no localized cavity.',
275:'Two boxes cover flat intact fine-aggregate pavement.',
281:'Retain broad foreground asphalt-layer loss with broken right rim; remove small flat distant mark.',
282:'Retain bounded upper material loss; giant foreground region is closed repair.',
284:'Distant broad patch is closed intact road, without a visible broken cavity edge.',
286:'Retain two bounded asphalt-loss pits; remove thin paint/markings and intact alligator cracks.',
287:'Closed filled roadside asphalt repair; its perimeter crack does not make the interior a cavity.',
291:'Broad new asphalt repair is closed and continuous.',
293:'Three regions are intact asphalt/filled repair and litter, without open cavity.',
294:'Retain two bounded exposed-material cavities; remove broad intact road regions and long crack.',
296:'Four boxes cover closed filled aggregate/asphalt repairs.',
299:'Small rectangular utility fitting is not a pothole.',
300:'Box follows a long narrow road crack.',
301:'Retain three bounded distant asphalt-loss defects; remove small foreground closed patch.',
302:'Retain small near cavity; remove utility repair outline and flat left patch.',
304:'Retain right local asphalt loss; remove rectangular closed utility repair and narrow cracks.',
306:'Retain bounded upper cavity; broad lower region is intact fine aggregate/dust.',
325:'Roadside leaves, loose debris and bare shoulder do not show an open paved-road cavity.',
331:'Motorcycles occlude the alleged bump; original does not reveal its contour.',
342:'Same roadside debris/leaf piles, no separate paved-road cavity.',
346:'Boxes cover loose leaves and roadside rubble, not visible open asphalt cavities.',
389:'Flat brick-paved intersection with utility covers; negative retained.',
397:'Raised crossing approach edge/platform is visible; retain speed-bump/platform class.',
412:'Retain small dark broken-edge pit; large pale closed concrete/asphalt repair removed.',
414:'Pale closed repairs and transverse narrow joint do not establish open potholes.',
425:'Foreground white rectangular utility fitting and two tiny dark patches cannot all be classified reliably.',
426:'Foreground coarse cavity has missing asphalt and a broken boundary.',
}
rows=[]
for item in quality:
 q=int(item['q']);confidence='medium' if q in keep_medium or q in keeps else 'low'
 if item['source']=='bpo':default='Full native frame and enlarged ROI inspected. Water, glare or tiny closed surface marks prevent reliable broken-rim confirmation for all existing boxes.'
 elif item['source']=='sb15':default='Several neighboring frames show the same pale transverse features, but raised bump versus flat repair/apron is not reliably established for every box.'
 elif item['source']=='sr':default='Full native image inspected; blur, glare or repair texture prevents reliable cavity adjudication for every box.'
 else:default='Native source and context inspected. Some areas appear to be asphalt-layer loss, but closed repair versus cavity or complete boundaries cannot be settled reliably.'
 if q in keep_medium and q not in reasons:default='Native pixels show localized exposed lower road material with broken asphalt boundaries; retained material-loss defects.'
 row=dict(q=q,confidence=confidence,reason=reasons.get(q,default),evidence='native_source_full_and_roi')
 if q in keeps:row['keep']=keeps[q]
 rows.append(row)
(R/'batch_source_rest.json').write_text(json.dumps(rows,indent=2))
print('Prepared',len(rows),'individual native-source rechecks')
