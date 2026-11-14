"""Full standardized frame and original-pixel ROI; annotations stay in dataset coordinates."""
import csv,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance,ImageStat
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/v5';out=R/'pretrain/source_views';out.mkdir(parents=True,exist_ok=True)
meta={r['out_image']:r for r in csv.DictReader((ROOT/'road_hazards_v5_all/manifest.csv').open())}
ds={r['image']:r for r in map(json.loads,(R/'all_images_resolution_decisions.jsonl').read_text().splitlines())}
rest='--rest' in sys.argv
upstream='--upstream' in sys.argv
quality=list(csv.DictReader((R/('pretrain/upstream_quality.csv' if upstream else 'pretrain/source_quality.csv')).open()));quality=[r for r in quality if r['has_more_source_pixels']==('0' if rest else '1')]
start,end=map(int,sys.argv[1:3]);selected=quality[start-1:end]
for off in range(0,len(selected),3):
 canvas=Image.new('RGB',(1280,1515));draw=ImageDraw.Draw(canvas)
 for k,item in enumerate(selected[off:off+3]):
  m=meta[item['image']];d=ds[item['image']];bs=d['boxes'];im=Image.open(item['original']).convert('RGB');rot=int(m.get('rotate_cw') or 0)
  if rot:im=im.rotate(-rot,expand=True)
  W,H=im.size;sw,sh=float(m['std_src_w']),float(m['std_src_h']);win=list(map(float,m['std_window'].split(',')))
  un=json.loads((ROOT/'road_hazards_v5_all/build_info.json').read_text()).get('unstretch',{})
  if m['source'] in un:sw=round(sh*float(un[m['source']]))
  if m['std_mode']=='crop':
   x0,y0,cw,ch=win
   def inv(x,y):return ((x0+x*cw)/sw*W,(y0+y*ch)/sh*H)
  else:
   s=min(960/sw,720/sh);ox=(960-sw*s)/2;oy=(720-sh*s)/2
   def inv(x,y):return ((x*960-ox)/s/sw*W,(y*720-oy)/s/sh*H)
  native=[]
  for b in bs:
   c,x,y,X,Y=b;a,b0=inv(x,y);A,B=inv(X,Y)
   if min(W,A)>max(0,a) and min(H,B)>max(0,b0):native.append((c,max(0,a),max(0,b0),min(W,A),min(H,B)))
   else:print('Box outside original source:',item['q'],b,flush=True)
  dr=ImageDraw.Draw(im)
  for i,(c,x,y,X,Y) in enumerate(native):dr.rectangle((x,y,X,Y),outline='lime' if c==0 else 'magenta',width=max(2,W//700));dr.text((x,y),str(i),fill='red')
  if native:
   x=min(b[1] for b in native);y=min(b[2] for b in native);X=max(b[3] for b in native);Y=max(b[4] for b in native)
   w=min(W,max(250,X-x+W*.035,(Y-y+H*.035)*4/3));h=min(H,w*3/4);l=max(0,min(W-w,(x+X-w)/2));t=max(0,min(H-h,(y+Y-h)/2));crop=im.crop((int(l),int(t),int(l+w),int(t+h)))
  else:
   x,y=inv(0,.35);X,Y=inv(1,1);crop=im.crop((max(0,int(x)),max(0,int(y)),min(W,int(X)),min(H,int(Y))))
  full=Image.open(ROOT/'road_hazards_v5_all'/item['image']).convert('RGB');dr=ImageDraw.Draw(full)
  for i,(c,x,y,X,Y) in enumerate(bs):dr.rectangle((x*960,y*720,X*960,Y*720),outline='lime' if c==0 else 'magenta',width=2);dr.text((x*960,y*720),str(i),fill='red')
  z=k*505;canvas.paste(full.resize((640,480)),(0,z));canvas.paste(crop.resize((640,480)),(640,z));draw.text((2,z+483),f"S{start+off+k} Q{d['q']} {m['source']} | ORIGINAL ROI {W}x{H} indices 0-based",fill='white')
 canvas.save(out/f'{"u" if upstream else "t" if rest else "s"}{start+off:03}.jpg',quality=96)
print(f'Rendered original-pixel review {start}..{start+len(selected)-1}',flush=True)
