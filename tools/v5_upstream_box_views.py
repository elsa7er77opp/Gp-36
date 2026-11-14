"""Show each baseline box against actual upstream pixels for source adjudication."""
import csv,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5'
meta={r['out_image']:r for r in csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open())}
dec={r['image']:r for r in map(json.loads,(R/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
out=R/'pretrain/upstream_box_views';out.mkdir(exist_ok=True)
for item in csv.DictReader((R/'pretrain/upstream_quality.csv').open()):
 if item['has_more_source_pixels']!='1':continue
 m=meta[item['image']];bs=dec[item['image']]['boxes'];im=Image.open(item['original']).convert('RGB')
 rot=int(m.get('rotate_cw') or 0)
 if rot:im=im.rotate(-rot,expand=True)
 W,H=im.size;sw,sh=float(m['std_src_w']),float(m['std_src_h'])
 x0,y0,cw,ch=map(float,m['std_window'].split(','))
 def inv(x,y):
  if m['std_mode']=='crop':return ((x0+x*cw)/sw*W,(y0+y*ch)/sh*H)
  s=min(960/sw,720/sh);return ((x*960-(960-sw*s)/2)/s/sw*W,(y*720-(720-sh*s)/2)/s/sh*H)
 canvas=Image.new('RGB',(1500,math.ceil(len(bs)/3)*440),'#222222');dr=ImageDraw.Draw(canvas)
 for i,(_,x,y,X,Y) in enumerate(bs):
  a,b=inv(x,y);A,B=inv(X,Y);pad=max(22,min(90,(A-a+B-b)*.12))
  l,t=max(0,int(a-pad)),max(0,int(b-pad));rr,bb=min(W,int(A+pad)),min(H,int(B+pad))
  crop=im.crop((l,t,rr,bb));d=ImageDraw.Draw(crop);d.rectangle((a-l,b-t,A-l,B-t),outline='lime',width=2)
  crop=ImageOps.contain(crop,(490,400));u,v=(i%3)*500,(i//3)*440
  canvas.paste(crop,(u,v+30));dr.text((u+3,v+5),f"Q{item['q']} box {i} original ROI {rr-l}x{bb-t}",fill='white')
 canvas.save(out/f"q{int(item['q']):03}.jpg",quality=97)
print(out)
