"""S1b — selector-fit / conformal-calibration independence fix (v1).
Problem: geometry selector was trained on D_cal AND conformal threshold calibrated
on the SAME D_cal -> overlap -> invalid guarantee.
Fix (does NOT change frozen D_cal/D_audit membership): sub-partition D_cal by
md5(image_id) into D_fit (train selector) and D_calib (conformal threshold);
D_audit unchanged (report). selector-fit / conformal-calib / audit are disjoint.
Also Method-B corroboration: geometry selector trained on OTHER cells (leave-dataset).
Masked ar>=1.6. No detector training, no threshold/split-file change.
"""
import json, csv, sys, os, math, hashlib
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from sklearn.ensemble import GradientBoostingRegressor
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
TTA=f"{ROOT}/top_journal_v3/reports/tta_circular_variance_full_052.csv"
PM=f"{ROOT}/top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv"
AR=1.6; TAIL=5.0
CELLS=[("DIOR-R","22","PSC","DIOR#22"),("FAIR1M-v1.0","24","PSC","FAIR1M#24"),
       ("SODA-A","23","PSC","SODA#23"),("DIOR-R","3","ORCNN","DIOR#3"),
       ("DIOR-R","61","RTMDet","DIOR#61"),("SODA-A","4","ORCNN","SODA#4")]
WANT=set(f"{ds}/{bid}" for ds,bid,_,_ in CELLS)
def index_csv(path,valcol):
    idx={}
    with open(path) as fh:
        r=csv.reader(fh); h=next(r); ci=h.index("cell_id");ii=h.index("image_id");pi=h.index("pred_id");vi=h.index(valcol)
        for row in r:
            if row[ci] not in WANT: continue
            try: idx.setdefault(row[ci],{})[(row[ii],int(row[pi]))]=float(row[vi])
            except: pass
    return idx
print("index TTA/PM",flush=True); TTAi=index_csv(TTA,"circular_variance"); PMi=index_csv(PM,"phase_mod")
def sub(image_id):
    return "D_fit" if int(hashlib.md5(str(image_id).encode()).hexdigest(),16)%2==0 else "D_calib"
def nrc(s,e): return nrc_auc(s,e)["nrc_auc"]
def gbr(): return GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0)
def conformal_thr(sc,loss,alpha,slack):
    o=np.argsort(-sc,kind="stable"); l=loss[o]; run=np.cumsum(l)/np.arange(1,len(l)+1)
    ok=run+slack<=alpha
    if not ok.any(): return None
    return sc[o][np.max(np.where(ok)[0])]

def load(ds,bid):
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl") if 1]
    recs=[r for r in recs if r["aspect_ratio"]>=AR]
    return recs

# preload all cells' masked features for method-B pooling
ALL={}
for ds,bid,fam,name in CELLS: ALL[name]=(ds,bid,fam,load(ds,bid))

def feats(recs):
    sc=np.array([r["score"] for r in recs]); ar=np.array([r["aspect_ratio"] for r in recs]); sz=np.array([r["size"] for r in recs])
    return np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)]), sc

rows=[]; conf=[]
for ds,bid,fam,name in CELLS:
    recs=ALL[name][3]
    split=np.array([r["d_cal_daudit_split_flag"] for r in recs])
    img=[r["image_id"] for r in recs]; pid=[r["pred_id"] for r in recs]
    err=np.array([r["angle_error"] for r in recs])
    X,sc=feats(recs)
    subf=np.array([sub(i) if split[k]=="D_cal" else "D_audit" for k,i in enumerate(img)])
    fit=subf=="D_fit"; cal=subf=="D_calib"; aud=subf=="D_audit"
    # Method A: geometry selector trained on D_fit only
    gA=gbr().fit(X[fit],err[fit]); geoA=-gA.predict(X)
    # Method B: geometry selector trained on POOLED OTHER cells' D_cal (leave-cell)
    Xo=[]; yo=[]
    for nm,(d2,b2,f2,rr2) in ALL.items():
        if nm==name: continue
        sp2=np.array([r["d_cal_daudit_split_flag"] for r in rr2])
        Xr,_=feats(rr2); m2=sp2=="D_cal"
        Xo.append(Xr[m2]); yo.append(np.array([r["angle_error"] for r in rr2])[m2])
    Xo=np.vstack(Xo); yo=np.concatenate(yo)
    if len(Xo)>150000:
        ridx=np.random.RandomState(1).choice(len(Xo),150000,replace=False); Xo=Xo[ridx]; yo=yo[ridx]
    gB=gbr().fit(Xo,yo); geoB=-gB.predict(X)
    # scores
    scores={"detection_score":sc,"geometry_selector_methodA_Dfit":geoA,"geometry_selector_methodB_leavecell":geoB}
    tta=TTAi.get(f"{ds}/{bid}",{})
    if len(tta)>0.5*len(img): scores["tta_neg_circular_var"]=-np.array([tta.get((img[i],pid[i]),np.nan) for i in range(len(img))])
    if fam=="PSC":
        pm=PMi.get(f"{ds}/{bid}",{})
        if len(pm)>0.5*len(img): scores["intrinsic_phase_mod"]=np.array([pm.get((img[i],pid[i]),np.nan) for i in range(len(img))])
    # NRC on D_audit
    for sn,sv in scores.items():
        va=aud&np.isfinite(sv)
        if va.sum()<100: continue
        rows.append(dict(cell=name,detector=fam,selector=sn,protocol="masked_ar1.6_Daudit_independent",
                         n_audit=int(va.sum()),nrc=round(nrc(sv[va],err[va]),4)))
    # conformal (tail P(err>5)<=alpha): calibrate on D_calib, report on D_audit  -- VALID (fit/calib disjoint)
    tl=(err>TAIL).astype(float); ncal=int(cal.sum()); hoeff=math.sqrt(math.log(1/0.1)/(2*max(ncal,1)))
    for alpha in [0.03,0.05]:
        for sn in ["detection_score","geometry_selector_methodA_Dfit","tta_neg_circular_var"]:
            if sn not in scores: continue
            sv=scores[sn]; c=cal&np.isfinite(sv); a=aud&np.isfinite(sv)
            if c.sum()<200 or a.sum()<100: continue
            t=conformal_thr(sv[c],tl[c],alpha,hoeff)
            if t is None: conf.append(dict(cell=name,selector=sn,alpha=alpha,coverage=0,emp_tail="",violation="",note="infeasible")); continue
            keep=sv[a]>=t; cov=float(keep.mean()); rate=float(tl[a][keep].mean()) if keep.sum() else float("nan")
            conf.append(dict(cell=name,selector=sn,alpha=alpha,n_calib=ncal,coverage=round(cov,4),
                             emp_tail=round(rate,4) if rate==rate else "",violation=bool(rate>alpha) if rate==rate else "",note="fit!=calib"))
    print(f"{name}: geoA={[r['nrc'] for r in rows if r['cell']==name and 'methodA' in r['selector']]} "
          f"det={[r['nrc'] for r in rows if r['cell']==name and r['selector']=='detection_score']}",flush=True)
with open(f"{OUTd}/s1b_score_menu_resplit_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","detector","selector","protocol","n_audit","nrc"]); w.writeheader(); w.writerows(rows)
with open(f"{OUTd}/s1b_conformal_independent_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","selector","alpha","n_calib","coverage","emp_tail","violation","note"],extrasaction="ignore"); w.writeheader(); w.writerows(conf)
print("WROTE s1b_score_menu_resplit_v1.csv, s1b_conformal_independent_v1.csv")
