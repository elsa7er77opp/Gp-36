"""Encode individual visual adjudications of source sheets S46--S137."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'review/v5/pretrain'
qs=[int(r['q']) for r in csv.DictReader((R/'source_quality.csv').open()) if r['has_more_source_pixels']=='1'][45:]
notes={
121:'Blurred filled repair and longitudinal seam; no distinct open cavity visible.',
123:'Block cracks and intact repair surface; no localized asphalt loss.',
124:'Cracks separate intact asphalt blocks, rather than an open pothole.',
127:'Water on gravel/asphalt boundary; original does not establish depression for all puddles.',
129:'Foreground alligator cracking is intact asphalt; retain the separate smaller material-loss defects.',
132:'Raised loose rubble/asphalt piles on the road are not open cavities.',
135:'Retain foreground broken-rim cavity; distant thin linear cracks are not separate potholes.',
308:'Original shows broken rims around the wet/snowy localized cavities.',
311:'Closed aggregate repair surface; dark adjoining stain does not establish an open hole.',
312:'Surface raveling versus shallow cavity remains uncertain in the original.',
314:'Elongated exposed aggregate areas show localized loss of asphalt surface.',
316:'Retain left rough cavity; broad right region is an intact filled asphalt repair.',
318:'Retain small dark pit; large right patch has a closed continuous repair surface.',
323:'One connected exposed-aggregate cavity; merge the overlapping boxes.',
324:'Retain round broken-rim cavity; remove long linear crack on the left.',
326:'Retain upper localized pit; large foreground region is intact alligator-cracked asphalt.',
328:'Retain left cavity; broad new asphalt patch is closed and filled.',
332:'Retain two left localized asphalt-loss defects; giant right box covers closed filled repair.',
333:'Remove circular utility fitting and closed foreground repair; retain broken-rim material-loss areas.',
335:'The four dark regions are closed filled asphalt repairs, not open cavities.',
337:'Broad box covers a closed filled asphalt repair and adjacent wet stain.',
338:'Retain small upper cavity; broad foreground region is a filled repair.',
341:'Original does not distinguish pale filled repairs from shallow asphalt loss reliably.',
344:'Tighten to the right localized asphalt-loss cavity, excluding the long adjoining crack.',
352:'Large region is a closed filled asphalt repair.',
354:'Retain left localized pit; remove large closed asphalt repair.',
355:'Retain right cavity; remove separate left transverse crack.',
358:'Near defect has missing asphalt and broken edges; distant small mark is not a visible cavity.',
359:'Remove circular utility fitting and flat closed repair; retain localized broken-rim defects.',
360:'Retain two left asphalt-loss cavities; curbside dirt/litter is not a separate road pothole.',
363:'Remove utility fitting and large closed foreground repair; retain other asphalt-loss defects.',
364:'Foreground exposed coarse aggregate has a clear continuous broken asphalt rim; add missing cavity.',
367:'Dark wet image retains visible rims and localized material loss around labelled cavities.',
369:'Remove utility cap and two overlapping boxes on closed foreground repair; retain visible cavities.',
370:'Remove utility cap and overlapping closed foreground repair boxes; retain the open asphalt-loss defects.',
371:'Four areas have localized exposed lower road material and broken asphalt boundaries.',
372:'Two labelled features are narrow linear/curved cracks in otherwise intact road.',
374:'Remove giant box covering a curved road crack; retain separate left asphalt-loss patch.',
376:'Original wet road contains additional water regions without enough visible rims to settle completeness.',
377:'Both boxes follow narrow linear cracks rather than localized cavities.',
379:'Long transverse joint/repair and shadows prevent reliable cavity boundary adjudication.',
384:'Raised crossing ramp edge is visible; retain speed-bump/platform class.',
385:'Raised crossing platform and approach edge are visible; retain class.',
386:'Same raised crossing with visible checker ramp edge in original.',
387:'Checker-marked ramp has a visible elevation edge ahead of the crossing.',
388:'Raised crossing approach ramp is visible; retain speed-bump/platform class.',
390:'Raised crossing approach edge is visible in the original road context.',
391:'Wet crossing glare and wiper obscure elevation; raised-versus-flat not settled.',
392:'Checker ramp and broad raised crossing platform visible in original.',
393:'Rain reflection and wiper hide crossing elevation; unresolved.',
394:'Crossing ramp edge alongside central island is visible; retain raised-platform class.',
416:'Saturated road pixels beneath vehicles do not reveal the claimed bump.',
418:'Headlight saturation and motion blur prevent a cavity-versus-mark decision.',
419:'Washed-out foreground road does not reveal the claimed bump elevation.',
420:'Motion-blurred shallow road wear cannot establish a cavity boundary.',
421:'Blurred dark spot could be stain or shallow road loss; original cannot distinguish.',
423:'Roadside transverse worn region may be repair or cavity; depth not visible.',
424:'Near dark region and distant bright band cannot both be settled from this blurred frame.',
428:'Transverse shadow/band may be a bump but no reliable elevation contour is visible.',
429:'Blurred circular region lacks a clear broken rim.',
430:'Overexposed road mark has no recoverable cavity edge.',
431:'Dark shallow region lacks a distinct broken rim in original.',
432:'Thin blurred dark line does not establish missing asphalt depth.',
}
keeps={129:list(range(2,9)),132:[],135:[0],311:[],316:[0],318:[0],324:[0],326:[0],328:[0],332:[0,2],333:list(range(2,9)),335:[],337:[],338:[1],352:[],354:[1],355:[0],358:[0],359:[0,2,3,4,5,6,7],360:[0,3],363:[0,3,4,5,6,7,8],369:[0,1,5,6,7,8,9],370:[0,1,4,5,7,8,9],372:[],377:[]}
low={127,312,341,376,379,391,393,416,418,419,420,421,423,424,428,429,430,431,432}
rows=[]
for q in qs:
 row=dict(q=q,confidence='low' if q in low else 'medium',reason=notes.get(q,'Original shows localized exposed aggregate bounded by missing asphalt edges; retain visible material-loss defects.'))
 if q in keeps:row['keep']=keeps[q]
 if q==323:row['boxes']=[[0,.0002,.1203,.7388,1.0]]
 if q==344:row['boxes']=[[0,.46,.20,.6421,.425]]
 if q==364:
  base={r['q']:r for r in map(json.loads,(R.parent/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
  row['boxes']=base[q]['boxes']+[[0,.126,.45,.876,1.0]]
 if q==374: # smaller left box is index 0, confirmed against native overlay
  row['keep']=[0]
 rows.append(row)
(R/'batch_source_046.json').write_text(json.dumps(rows,indent=2))
print('Prepared',len(rows),'visually reviewed cases')
