"""A4 / P4 — uncertainty-branch comparison under the FROZEN masked protocol (055).
On masked ar>=1.6 D_audit, compare NRC(selection score -> angle_error) for:
  detection_score, geometry_selector (GBR on D_cal), tta_neg_circular_var,
  intrinsic_phase_mod (PSC). Paired bootstrap on NRC differences.
Answers: does geometry selector beat TTA (Fix story) or tie (recommend TTA+conformal)?
Real 052 artifacts; no training of detectors; GBR selector trains only on D_cal."""
import json, csv, sys, os, math
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from sklearn.ensemble import GradientBoostingRegressor
OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
TTA=f"{ROOT}/top_journal_v3/reports/tta_circular_variance_full_052.csv"
PM=f"{ROOT}/top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv"
AR=1.6; rng=np.random.RandomState(55)
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
print("index TTA",flush=True); TTAi=index_csv(TTA,"circular_variance")
print("index PM",flush=True); PMi=index_csv(PM,"phase_mod")
def nrc(s,e):
    v=nrc_auc(s,e)["nrc_auc"]; return v
rows=[]; rows_pair=[]
for ds,bid,fam,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r["aspect_ratio"]>=AR and r["d_cal_daudit_split_flag"] in("D_cal","D_audit")]
    sp=np.array([r["d_cal_daudit_split_flag"] for r in recs])
    sc=np.array([r["score"] for r in recs]); er=np.array([r["angle_error"] for r in recs])
    ar=np.array([r["aspect_ratio"] for r in recs]); sz=np.array([r["size"] for r in recs])
    img=[r["image_id"] for r in recs]; pid=[r["pred_id"] for r in recs]
    cal=sp=="D_cal"; aud=sp=="D_audit"
    X=np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)])
    g=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(X[cal],er[cal])
    scores={"detection_score":sc,"geometry_selector":-g.predict(X)}
    tta=TTAi.get(f"{ds}/{bid}",{})
    if len(tta)>0.5*len(img): scores["tta_neg_circular_var"]=-np.array([tta.get((img[i],pid[i]),np.nan) for i in range(len(img))])
    if fam=="PSC":
        pm=PMi.get(f"{ds}/{bid}",{})
        if len(pm)>0.5*len(img): scores["intrinsic_phase_mod"]=np.array([pm.get((img[i],pid[i]),np.nan) for i in range(len(img))])
    # NRC on D_audit masked
    ea=er[aud]; nrcs={}
    for sn,sv in scores.items():
        va=aud&np.isfinite(sv)
        if va.sum()<100: continue
        nrcs[sn]=nrc(sv[va],er[va]);
        rows.append(dict(cell=name,detector=fam,selector=sn,protocol="masked_ar1.6_Daudit",
                         n=int(va.sum()),nrc=round(nrcs[sn],4)))
    # paired bootstrap: geometry vs tta, geometry vs detection (on common finite subset)
    def pair(a,b):
        va=aud&np.isfinite(scores[a])&np.isfinite(scores[b]); idx=np.where(va)[0]
        if len(idx)<200: return None
        d=[]
        for _ in range(300):
            bi=idx[rng.randint(0,len(idx),len(idx))]
            d.append(nrc(scores[a][bi],er[bi])-nrc(scores[b][bi],er[bi]))
        d=np.array(d); lo,hi=np.percentile(d,[2.5,97.5])
        return round(float(d.mean()),4),round(float(lo),4),round(float(hi),4)
    for a,b in [("geometry_selector","detection_score"),("geometry_selector","tta_neg_circular_var")]:
        if a in scores and b in scores:
            pr=pair(a,b)
            if pr: rows_pair.append(dict(cell=name,cmp=f"{a}_minus_{b}",delta_nrc=pr[0],ci_lo=pr[1],ci_hi=pr[2],
                                         a_better_sig=bool(pr[2]<0),tie=bool(pr[1]<0<pr[2])))
    print(f"{name}: "+" ".join(f"{k}={v:.3f}" for k,v in nrcs.items()),flush=True)
with open(f"{OUT}/p4_uncertainty_branch_055.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","detector","selector","protocol","n","nrc"]); w.writeheader(); w.writerows(rows)
with open(f"{OUT}/p4_selector_vs_tta_bootstrap_055.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","cmp","delta_nrc","ci_lo","ci_hi","a_better_sig","tie"]); w.writeheader(); w.writerows(rows_pair)
print("WROTE p4_uncertainty_branch_055.csv, p4_selector_vs_tta_bootstrap_055.csv")
