import json,os,math,hashlib,sys
GT=sys.argv[1]; SRC=sys.argv[2]; SUF=sys.argv[3]; FARM=sys.argv[4]
os.makedirs(f"{FARM}/images",exist_ok=True); os.makedirs(f"{FARM}/annfiles",exist_ok=True)
def corners(cx,cy,w,h,t):
    c,s=math.cos(t),math.sin(t); dx=[-w/2,w/2,w/2,-w/2]; dy=[-h/2,-h/2,h/2,h/2]
    return [(cx+dx[i]*c-dy[i]*s, cy+dx[i]*s+dy[i]*c) for i in range(4)]
gts=[json.loads(l) for l in open(GT)]
byimg={}
for g in gts: byimg.setdefault(g["image_id"],[]).append(g)
nsym=nann=nmiss=0
for img,gs in byimg.items():
    src=f"{SRC}/{img}.{SUF}"
    if not os.path.isfile(src): nmiss+=1; continue
    dst=f"{FARM}/images/{img}.{SUF}"
    if not os.path.exists(dst): os.symlink(src,dst); nsym+=1
    with open(f"{FARM}/annfiles/{img}.txt","w") as f:
        for g in gs:
            pts=corners(g["obb_cx"],g["obb_cy"],g["obb_w"],g["obb_h"],g["obb_theta"])
            f.write(" ".join(f"{p:.1f}" for xy in pts for p in xy)+f" {g['class_name'].replace(' ','-')} 0\n")
    nann+=1
print(f"farm {FARM}: symlinks={nsym} annfiles={nann} missing_img={nmiss} (of {len(byimg)} GT images)")
