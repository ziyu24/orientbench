import json,os,math,csv,sys,pickle
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from orientbench.core.geometry import canonical_longside_theta
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from mmengine.config import Config
PREDS="/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds"; GTD="/dev/shm/cqc/orientbench/predictions"; OUT=f"{ROOT}/measure_fix_v2/reports"
# (cell_dir, dataset, baseline_id, detector_family, config_for_classes)
CELLS=[("DIOR-R_61","DIOR-R","61","rtmdet","/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py"),
       ("FAIR1M-v1.0_5","FAIR1M-v1.0","5","orcnn","/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py")]
GEO=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]; RTTA=GEO+["real_tta_consistency"]
rng=np.random.RandomState(46)
def cls(cfg): return list(Config.fromfile(cfg).test_dataloader["dataset"]["metainfo"]["classes"])
def load(cell,tf):
    p=f"{PREDS}/{cell}/{tf}.pkl"; return pickle.load(open(p,"rb")) if os.path.isfile(p) else None
def dets(rec,unflip=None):
    pi=rec["pred_instances"]; bb=np.asarray(pi["bboxes"]); sc=np.asarray(pi["scores"]); lb=np.asarray(pi["labels"])
    H,W=rec.get("ori_shape",(1024,1024)); out=[]
    for b,s,l in zip(bb,sc,lb):
        cx,cy,w,h,t=[float(x) for x in b[:5]]
        if unflip=="h": cx=W-cx; t=-t
        elif unflip=="v": cy=H-cy; t=-t
        out.append((cx,cy,w,h,t,float(s),int(l)))
    return out
def adiff(a,b): return abs(((a-b+math.pi/2)%math.pi)-math.pi/2)
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def pdelta(sa,sb,r,B=300):
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(sa[i],r[i])-nrc(sb[i],r[i])
        if math.isfinite(v): d.append(v)
    return [round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
rows=[]
for cell,ds,bid,fam,cfg in CELLS:
    ident=load(cell,"identity"); hf=load(cell,"hflip"); vf=load(cell,"vflip")
    if not(ident and hf and vf): print("missing",cell,flush=True); continue
    CLS=cls(cfg); gts=[json.loads(l) for l in open(f"{GTD}/{ds}/{ds}_fullval_gt.jsonl")]
    dh={r["img_id"]:r for r in hf}; dv={r["img_id"]:r for r in vf}
    schema=[]
    for r in ident:
        img=r["img_id"]
        for (cx,cy,w,h,t,s,l) in dets(r):
            if s<0.30: continue
            schema.append({"image_id":img,"class_name":CLS[l] if l<len(CLS) else str(l),"obb_cx":cx,"obb_cy":cy,"obb_w":w,"obb_h":h,"obb_theta":t,"score":s})
    m=match_dataset(schema,gts); rec=[]
    for pi_i,gj,_ in m["matched_pairs"]:
        p=schema[pi_i]; gg=gts[gj]
        c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]; w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if not math.isfinite(e) or ar<1.6: continue
        img=p["image_id"]; cx,cy=p["obb_cx"],p["obb_cy"]; th0=canonical_longside_theta(p["obb_w"],p["obb_h"],p["obb_theta"])
        disag=[]
        for src,uf in ((dh.get(img),"h"),(dv.get(img),"v")):
            if src is None: continue
            best=None;bd=40
            for (tx,ty,tw,th2,tt,ts,tl) in dets(src,unflip=uf):
                if ts<0.30: continue
                dd=math.hypot(tx-cx,ty-cy)
                if dd<bd: bd=dd; best=(tw,th2,tt)
            if best is not None:
                thq=canonical_longside_theta(*best)
                if math.isfinite(thq): disag.append(adiff(thq,th0))
        rtc=float(np.mean(disag)) if disag else math.pi/4
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        rec.append({"img":img,"score":p["score"],"log_ar":math.log(ar),"log_sqrt_area":math.log(math.sqrt(max(1.0,w*h))),
                    "gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],"real_tta_consistency":rtc,"n_tta":len(disag),"err":e,"split":assign_split(img)})
    cal=[r for r in rec if r["split"]=="D_cal"]; aud=[r for r in rec if r["split"]=="D_audit"]
    if len(cal)<100 or len(aud)<100: print("too few",cell,len(cal),len(aud),flush=True); continue
    ya=np.array([r["err"] for r in aud])
    def Xof(rs,fs): return np.array([[r[k] for k in fs] for r in rs])
    sB=np.array([r["score"] for r in aud])
    sSZ=-LinearRegression().fit(Xof(cal,["score","log_ar","log_sqrt_area"]),np.array([r["err"] for r in cal])).predict(Xof(aud,["score","log_ar","log_sqrt_area"]))
    sC=-GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,GEO),np.array([r["err"] for r in cal])).predict(Xof(aud,GEO))
    sR=-GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,RTTA),np.array([r["err"] for r in cal])).predict(Xof(aud,RTTA))
    ci_sz=pdelta(sSZ,sR,ya); ci_geo=pdelta(sC,sR,ya)
    row={"dataset":ds,"baseline_id":bid,"detector":fam,"n_audit":len(aud),"tta_match_frac":round(float(np.mean([r["n_tta"]>0 for r in rec])),3),
         "mean_rtc_deg":round(float(np.degrees(np.mean([r["real_tta_consistency"] for r in rec]))),2),
         "NRC_score":round(nrc(sB,ya),4),"NRC_sizelin":round(nrc(sSZ,ya),4),"NRC_geo":round(nrc(sC,ya),4),"NRC_realTTA":round(nrc(sR,ya),4),
         "realTTA_beats_sizelin":bool(ci_sz[0]>0),"realTTA_beats_geo":bool(ci_geo[0]>0),"ci_sz":ci_sz,"ci_geo":ci_geo}
    rows.append(row)
    print(f"{ds}/{bid}({fam}): match={row['tta_match_frac']} realTTA={row['NRC_realTTA']} sizelin={row['NRC_sizelin']} geo={row['NRC_geo']} beats_sz={row['realTTA_beats_sizelin']} beats_geo={row['realTTA_beats_geo']}",flush=True)
cols=["dataset","baseline_id","detector","n_audit","tta_match_frac","mean_rtc_deg","NRC_score","NRC_sizelin","NRC_geo","NRC_realTTA","realTTA_beats_sizelin","realTTA_beats_geo"]
with open(f"{OUT}/real_tta_nonpsc_046.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("NONPSC DONE",flush=True)
