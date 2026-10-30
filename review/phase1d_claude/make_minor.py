"""Phase 1d helper (read-only on data): minor-difference duplicate pairs. Both copies' boxes drawn on ONE
zoomed road crop (copy A: red/blue thick, copy B: yellow/cyan thin), 4 pairs per sheet."""
import csv, os
from collections import defaultdict
from PIL import Image, ImageDraw
HOME=os.path.expanduser("~"); BASE=os.path.join(HOME,"mnt","Desktop","GP36_AI")
AUD=os.path.join(BASE,"review","phase1c_2026-10-30","ANNOTATION_AUDIT.csv")
OUT=os.path.join(BASE,"review","phase1d_claude","minor"); os.makedirs(OUT,exist_ok=True)
FLAG="EXACT_DUP_LABEL_MINOR_DIFF"
def wp(p): return p.replace("C:\\Users\\ahmed\\Desktop",os.path.join(HOME,"mnt","Desktop")).replace("\\","/")
def lp(img):
    d,f=os.path.split(img); return os.path.join(os.path.dirname(d),"labels",f.rsplit(".",1)[0]+".txt")
def boxes(p):
    out=[]
    for l in open(p,encoding="utf-8"):
        t=l.split()
        if not t: continue
        c=int(float(t[0])); v=[float(x) for x in t[1:]]
        if len(v)==4: xc,yc,w,h=v
        else:
            xs,ys=v[0::2],v[1::2]; xc,yc=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2; w,h=max(xs)-min(xs),max(ys)-min(ys)
        out.append((c,xc,yc,w,h))
    return out
rows=list(csv.DictReader(open(AUD,encoding="utf-8")))
g=defaultdict(list)
for r in rows:
    if FLAG in r["auto_flags"]: g[r["sha256"]].append(r)
pairs=sorted(g.values(),key=lambda rs:rs[0]["sample_id"])
with open(os.path.join(OUT,"index_minor.csv"),"w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh); w.writerow(["pair_no","copy","sample_id","boxes"])
    for i,rs in enumerate(pairs,1):
        for k,r in enumerate(rs): w.writerow([i,"ABCD"[k],r["sample_id"],len(boxes(lp(wp(r["image"]))))])
PW,PH=700,330
for s in range(0,len(pairs),4):
    sheet=Image.new("RGB",(2*PW+10,2*(PH+18)+10),(30,30,30)); d=ImageDraw.Draw(sheet)
    for j,rs in enumerate(pairs[s:s+4]):
        i=s+j+1; im=Image.open(wp(rs[0]["image"])); im.draft("RGB",(im.width//2,im.height//2)); im=im.convert("RGB"); W,H=im.size
        bs=[boxes(lp(wp(r["image"]))) for r in rs]; fl=[b for x in bs for b in x]
        x1=min(b[1]-b[3]/2 for b in fl); x2=max(b[1]+b[3]/2 for b in fl); y1=min(b[2]-b[4]/2 for b in fl); y2=max(b[2]+b[4]/2 for b in fl)
        cx1,cx2,cy1,cy2=max(0,x1-.1),min(1,x2+.1),max(0,y1-.1),min(1,y2+.1)
        if cx2-cx1<.4: m=(cx1+cx2)/2; cx1,cx2=max(0,m-.2),min(1,m+.2)
        if cy2-cy1<.25: m=(cy1+cy2)/2; cy1,cy2=max(0,m-.125),min(1,m+.125)
        cr=im.crop((int(cx1*W),int(cy1*H),int(cx2*W),int(cy2*H))); sc=min(PW/cr.width,PH/cr.height); cr=cr.resize((int(cr.width*sc),int(cr.height*sc)))
        dd=ImageDraw.Draw(cr)
        for k,b_ in enumerate(bs[:2]):
            for c,xc,yc,w,h in b_:
                col=[(255,40,40),(40,140,255)][c] if k==0 else [(255,255,0),(0,255,255)][c]
                dd.rectangle([((xc-w/2)-cx1)*W*sc,((yc-h/2)-cy1)*H*sc,((xc+w/2)-cx1)*W*sc,((yc+h/2)-cy1)*H*sc],outline=col,width=3 if k==0 else 1)
        x0=(j%2)*(PW+10); y0=(j//2)*(PH+28)
        sheet.paste(cr,(x0,y0+18)); d.text((x0+3,y0+3),f"#{i} A:{len(bs[0])} B:{len(bs[1])} {rs[0]['sample_id'][4:40]}",fill=(255,255,255))
    sheet.save(os.path.join(OUT,f"minor_{s//4+1:03d}.jpg"),quality=82)
print("pairs",len(pairs),"sheets",(len(pairs)+3)//4)
