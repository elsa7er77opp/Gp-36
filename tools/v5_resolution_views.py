import csv,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance,ImageStat
root=Path(__file__).resolve().parents[1];start,end=map(int,sys.argv[1:3]);rows=list(csv.DictReader(open(root/'review/v5/all_images_resolution_queue.csv')))[start-1:end];outdir=root/'review/v5/views/all_images_resolution';outdir.mkdir(exist_ok=True)
for off in range(0,len(rows),3):
 out=Image.new('RGB',(1280,1515));d=ImageDraw.Draw(out)
 for n,r in enumerate(rows[off:off+3]):
  im=Image.open(root/'road_hazards_v5_all'/r['image']).convert('RGB');bs=json.loads(r['current_boxes']);bright=ImageStat.Stat(im).mean;enhanced=sum(bright)/3<65
  if enhanced: im=ImageEnhance.Brightness(im).enhance(1.8)
  dr=ImageDraw.Draw(im)
  for c,x,y,X,Y in bs:dr.rectangle((x*960,y*720,X*960,Y*720),outline='magenta' if c else 'lime',width=2)
  if bs:
   x0=min(b[1] for b in bs)*960;y0=min(b[2] for b in bs)*720;x1=max(b[3] for b in bs)*960;y1=max(b[4] for b in bs)*720;w=min(960,max(190,x1-x0+70,(y1-y0+70)*4/3));h=min(720,w*3/4);l=max(0,min(960-w,(x0+x1-w)/2));t=max(0,min(720-h,(y0+y1-h)/2));crop=im.crop((int(l),int(t),int(l+w),int(t+h)))
  else:crop=im.crop((0,240,960,720)).resize((960,720))
  y=n*505;out.paste(im.resize((640,480)),(0,y));out.paste(crop.resize((640,480)),(640,y));d.text((3,y+483),f"Q{start+off+n}  {int(r['sheet'])}/{r['cell']} {r['source']} full | enlarged"+(' BRIGHTENED VIEW' if enhanced else ''),fill='white')
 out.save(outdir/f'q{start+off:04}.jpg',quality=96)
print(len(rows),'images rendered')
