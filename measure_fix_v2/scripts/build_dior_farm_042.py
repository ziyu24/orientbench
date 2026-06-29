import json,os,math,hashlib,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT)
GT="/dev/shm/cqc/orientbench/predictions/DIOR-R/DIOR-R_fullval_gt.jsonl"
SRC_IMG="/home/rspip/cqc/data/dataset/DIOR/images/trainval"
FARM="/dev/shm/cqc/orientbench/measure_fix_v2_tta/DIOR-R"
os.makedirs(f"{FARM}/images",exist_ok=True); os.makedirs(f"{FARM}/annfiles",exist_ok=True)
def corners(cx,cy,w,h,t):
    c,s=math.cos(t),math.sin(t); dx=[-w/2,w/2,w/2,-w/2]; dy=[-h/2,-h/2,h/2,h/2]
    return [(cx+dx[i]*c-dy[i]*s, cy+dx[i]*s+dy[i]*c) for i in range(4)]
gts=[json.loads(l) for l in open(GT)]
byimg={}
for g in gts: byimg.setdefault(g["image_id"],[]).append(g)
nsym=0; nann=0
for img,gs in byimg.items():
    src=f"{SRC_IMG}/{img}.jpg"
    if not os.path.isfile(src): continue
    dst=f"{FARM}/images/{img}.jpg"
    if not os.path.islink(dst) and not os.path.exists(dst):
        os.symlink(src,dst); nsym+=1
    with open(f"{FARM}/annfiles/{img}.txt","w") as f:
        for g in gs:
            pts=corners(g["obb_cx"],g["obb_cy"],g["obb_w"],g["obb_h"],g["obb_theta"])
            f.write(" ".join(f"{p:.1f}" for xy in pts for p in xy)+f" {g['class_name'].replace(' ','-')} 0\n")
    nann+=1
# manifest (no original dataset modified: we only symlink + write to scratch farm)
man={"dataset":"DIOR-R","source_image_dir":SRC_IMG,"source_gt":GT,"farm":FARM,
     "n_image_symlinks":nsym,"n_annfiles":nann,"original_dataset_modified":False,
     "evidence_no_dataset_write":"only os.symlink (read-only target) + writes confined to /dev/shm farm; no write under /home/rspip/cqc/data/dataset",
     "annfile_format":"DOTA poly8 x1 y1 x2 y2 x3 y3 x4 y4 class difficult","class_source":"GT jsonl class_name"}
os.makedirs(f"{ROOT}/measure_fix_v2/reports",exist_ok=True)
json.dump(man,open(f"{ROOT}/measure_fix_v2/reports/dior_farm_manifest_042.json","w"),indent=2)
print(f"DIOR farm: {nsym} symlinks, {nann} annfiles -> {FARM}")
