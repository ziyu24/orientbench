# Extract REAL TTA consistency features (un-flip hflip/vflip, match base<->TTA) for DIOR cells.
import json,os,math,csv,sys,pickle
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.core.geometry import canonical_longside_theta
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
PREDS="/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds"
GTP="/dev/shm/cqc/orientbench/predictions/DIOR-R/DIOR-R_fullval_gt.jsonl"
CLS=json.load(open("measure_fix_v2/artifacts/dior_classes.json"))
ART=f"{ROOT}/measure_fix_v2/artifacts/features_real_tta"; os.makedirs(ART,exist_ok=True)
CELLS=[("DIOR-R","3","orcnn"),("DIOR-R","22","psc"),("DIOR-R","10","lsknet")]
def load(cell,tf):
    p=f"{PREDS}/{cell}/{tf}.pkl"
    return pickle.load(open(p,"rb")) if os.path.isfile(p) else None
def dets(rec,unflip=None):
    pi=rec["pred_instances"]; bb=np.asarray(pi["bboxes"]); sc=np.asarray(pi["scores"]); lb=np.asarray(pi["labels"])
    H,W=rec.get("ori_shape",(1024,1024))
    out=[]
    for b,s,l in zip(bb,sc,lb):
        cx,cy,w,h,t=[float(x) for x in b[:5]]
        if unflip=="h": cx=W-cx; t=-t
        elif unflip=="v": cy=H-cy; t=-t
        out.append((cx,cy,w,h,t,float(s),int(l)))
    return out,W,H
def adiff(a,b): return abs(((a-b+math.pi/2)%math.pi)-math.pi/2)
gts=[json.loads(l) for l in open(GTP)]
for ds,bid,det in CELLS:
    ident=load(f"{ds}_{bid}","identity"); hf=load(f"{ds}_{bid}","hflip"); vf=load(f"{ds}_{bid}","vflip")
    if not(ident and hf and vf): print("missing",ds,bid,flush=True); continue
    dh={r["img_id"]:r for r in hf}; dv={r["img_id"]:r for r in vf}
    # build base preds in schema for GT matching
    base_schema=[]; per_img_base={}
    for r in ident:
        img=r["img_id"]; bd,W,H=dets(r)
        per_img_base[img]=(bd,W,H)
        for (cx,cy,w,h,t,s,l) in bd:
            if s<0.30: continue
            base_schema.append({"image_id":img,"class_name":CLS[l] if l<len(CLS) else str(l),
                                 "obb_cx":cx,"obb_cy":cy,"obb_w":w,"obb_h":h,"obb_theta":t,"score":s})
    m=match_dataset(base_schema,gts)
    # index base_schema position -> its (img, cx,cy,t,l)
    rec=[]
    for pi_idx,gj,_ in m["matched_pairs"]:
        p=base_schema[pi_idx]; gg=gts[gj]
        c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]
        w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if not math.isfinite(e) or ar<1.6: continue
        img=p["image_id"]; cx,cy=p["obb_cx"],p["obb_cy"]; th0=canonical_longside_theta(p["obb_w"],p["obb_h"],p["obb_theta"])
        # real TTA consistency: match this base det to nearest un-flipped TTA det
        disag=[]
        for src,uf in ((dh.get(img),"h"),(dv.get(img),"v")):
            if src is None: continue
            td,_,_=dets(src,unflip=uf)
            best=None;bd=1e9
            for (tx,ty,tw,th2,tt,ts,tl) in td:
                if ts<0.30: continue
                d=math.hypot(tx-cx,ty-cy)
                if d<bd and d<40: bd=d; best=(tw,th2,tt)
            if best is not None:
                thq=canonical_longside_theta(best[0],best[1],best[2])
                if math.isfinite(thq): disag.append(adiff(thq,th0))
        rtc=float(np.mean(disag)) if disag else math.pi/4  # no TTA match -> neutral high
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        rec.append({"img":img,"score":p["score"],"log_ar":math.log(ar),"log_sqrt_area":math.log(math.sqrt(max(1.0,w*h))),
                    "gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],"real_tta_consistency":rtc,"n_tta_matched":len(disag),
                    "err":e,"split":assign_split(img)})
    with open(f"{ART}/{ds}_{bid}.jsonl","w") as f:
        for r in rec: f.write(json.dumps(r)+"\n")
    matched_frac=np.mean([r["n_tta_matched"]>0 for r in rec]) if rec else 0
    print(f"real_tta {ds}/{bid} n={len(rec)} tta_match_frac={matched_frac:.2f} mean_rtc_deg={np.degrees(np.mean([r['real_tta_consistency'] for r in rec])):.2f}",flush=True)
print("EXTRACT DONE",flush=True)
