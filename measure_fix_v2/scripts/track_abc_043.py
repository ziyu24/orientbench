import json,os,math,csv,sys,pickle
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
from sklearn.ensemble import GradientBoostingRegressor
DUMP="/dev/shm/cqc/orientbench/measure_fix_v2/track_a"; OUT=f"{ROOT}/measure_fix_v2/reports"
GTD="/dev/shm/cqc/orientbench/predictions"
CFGCLS={"DIOR-R":"/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
        "SODA-A":"/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
        "FAIR1M-v1.0":"/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
        "DOTA-v1.0":"/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/config.py"}
def classes(ds):
    from mmengine.config import Config
    return list(Config.fromfile(CFGCLS[ds]).test_dataloader["dataset"]["metainfo"]["classes"])
def gtpath(ds):
    for p in (f"{GTD}/{ds}/{ds}_fullval_gt.jsonl", f"{ROOT}/outputs/predictions/{ds}/_dcal_subset/gt_mmrotate.jsonl"):
        if os.path.isfile(p): return p
CELLS=[("DIOR-R","22"),("SODA-A","23"),("FAIR1M-v1.0","24"),("DOTA-v1.0","20")]
GEO=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]
rng=np.random.RandomState(43)
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def bootci(s,r,B=400):
    n=len(s); v=[]
    for _ in range(B):
        i=rng.randint(0,n,n); x=nrc(s[i],r[i])
        if math.isfinite(x): v.append(x)
    return [round(float(np.percentile(v,2.5)),4),round(float(np.percentile(v,97.5)),4)]
rows=[]
for ds,bid in CELLS:
    f=f"{DUMP}/{ds}_{bid}.pkl"
    if not os.path.isfile(f): print("no dump",ds,bid,flush=True); continue
    data=pickle.load(open(f,"rb")); CLS=classes(ds); gts=[json.loads(l) for l in open(gtpath(ds))]
    schema=[]
    for rec in data:
        img=rec["img_id"]; pi=rec["pred_instances"]
        bb=np.asarray(pi["bboxes"]); sc=np.asarray(pi["scores"]); lb=np.asarray(pi["labels"]); pm=np.asarray(pi["phase_mod"])
        for b,s,l,m in zip(bb,sc,lb,pm):
            if s<0.30: continue
            cx,cy,w,h,t=[float(x) for x in b[:5]]
            schema.append({"image_id":img,"class_name":CLS[int(l)] if int(l)<len(CLS) else str(int(l)),
                           "obb_cx":cx,"obb_cy":cy,"obb_w":w,"obb_h":h,"obb_theta":t,"score":float(s),"phase_mod":float(m)})
    m=match_dataset(schema,gts); rec=[]
    for pi_i,gj,_ in m["matched_pairs"]:
        p=schema[pi_i]; gg=gts[gj]
        c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]; w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if not math.isfinite(e) or ar<1.6: continue
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        rec.append({"img":p["image_id"],"score":p["score"],"phase_mod":p["phase_mod"],"log_ar":math.log(ar),
                    "log_sqrt_area":math.log(math.sqrt(max(1.0,w*h))),"gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],
                    "err":e,"split":assign_split(p["image_id"])})
    aud=[r for r in rec if r["split"]=="D_audit"]; cal=[r for r in rec if r["split"]=="D_cal"]
    if len(aud)<100: print("too few",ds,bid,flush=True); continue
    ya=np.array([r["err"] for r in aud])
    sA=np.array([r["phase_mod"] for r in aud])     # Track A: high phase_mod = confident
    sB=np.array([r["score"] for r in aud])         # Track B
    # Track C geometry selector (train D_cal)
    Xc=np.array([[r[k] for k in GEO] for r in cal]); yc=np.array([r["err"] for r in cal])
    g=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xc,yc)
    sC=-g.predict(np.array([[r[k] for k in GEO] for r in aud]))
    for tag,s in (("A_phase_mod_intrinsic",sA),("B_detection_score",sB),("C_geometry_selector",sC)):
        nr=nrc_auc(s,ya)
        rows.append({"dataset":ds,"baseline_id":bid,"track":tag,"n_audit":len(aud),"NRC":round(nr["nrc_auc"],4),
                     "NRC_ci":bootci(s,ya),"AURC":round(nr["aurc_model"],4),"Risk@70":round(risk_at_coverage(s,ya,0.7),3),
                     "Risk@90":round(risk_at_coverage(s,ya,0.9),3),"gt1_significant":bool(bootci(s,ya)[0]>1.0)})
    a=[r for r in rows if r["dataset"]==ds and r["track"].startswith("A")][0]
    b=[r for r in rows if r["dataset"]==ds and r["track"].startswith("B")][0]
    print(f"{ds}/{bid}: A(phase_mod) NRC={a['NRC']} ci={a['NRC_ci']} | B(score) NRC={b['NRC']} ci={b['NRC_ci']}",flush=True)
cols=["dataset","baseline_id","track","n_audit","NRC","NRC_ci","AURC","Risk@70","Risk@90","gt1_significant"]
with open(f"{OUT}/track_abc_results_043.csv","w",newline="") as fp:
    w=csv.DictWriter(fp,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
json.dump(rows,open(f"{OUT}/track_abc_results_043.json","w"),indent=2,default=str)
print("TRACKABC DONE",flush=True)
