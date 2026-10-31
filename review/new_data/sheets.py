import json,re,random
from pathlib import Path
from PIL import Image, ImageDraw
D=Path.home()/"mnt/GP36_Dataset/raw_v3"
ROOT={"bd":D/"roboflow_bd_speedbreaker_v2","hump":D/"roboflow_hump_marked_v2","kiz":D/"roboflow_kizmoya_speedbump_v2"}
R=[json.loads(l) for l in open("hashes.jsonl")]
def stem(p):
    n=p.rsplit("/",1)[-1]; m=re.match(r"(.+?)_(jpg|jpeg|png|JPG|JPEG|PNG)\.rf\.",n); return m.group(1) if m else n
rf={stem(r["p"]) for r in R if r["p"].startswith("rf8:")}
Path("sheets").mkdir(exist_ok=True)
random.seed(0); idx={}
for k,n in (("bd",24),("hump",24),("kiz",36)):
    pool=[r["p"] for r in R if r["p"].startswith(k+":")]
    if k=="hump": pool=[p for p in pool if stem(p) not in rf]
    pick=random.sample(pool,n); idx[k]=pick
    W=300; cols=6; rows=(n+cols-1)//cols; sheet=Image.new("RGB",(cols*W,rows*W),(30,30,30))
    for i,p in enumerate(pick):
        rel=p.split(":",1)[1]; ip=ROOT[k]/rel; lp=ROOT[k]/rel.replace("images/","labels/",1).rsplit(".",1)[0]
        im=Image.open(ip).convert("RGB"); w,h=im.size; dr=ImageDraw.Draw(im)
        for ln in open(str(lp)+".txt").read().split("\n"):
            t=ln.split()
            if len(t)<5: continue
            c,x,y,bw,bh=int(t[0]),*map(float,t[1:5])
            dr.rectangle([(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h],outline=(0,255,0) if c==0 else (0,160,255),width=4)
        im=im.resize((W,W)); ImageDraw.Draw(im).text((3,3),f"{k}{i}",fill=(255,255,0)); sheet.paste(im,((i%cols)*W,(i//cols)*W))
    sheet.save(f"sheets/new_{k}.jpg",quality=80)
json.dump(idx,open("sheets/index.json","w"),indent=0)
print("hump non-rf8 pool:",len([r for r in R if r["p"].startswith("hump:") and stem(r["p"]) not in rf]))
