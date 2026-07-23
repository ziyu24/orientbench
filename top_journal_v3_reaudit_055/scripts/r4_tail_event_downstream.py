"""R4 — tail-event downstream: severe orientation error (err>15deg) on directional
classes; compare severe-error rate at fixed coverage across scores. Geometric
orientation only (no semantic heading). Masked ar>=1.6. Real 052 tables. GBR on D_fit."""
import json, csv, sys, os, math, hashlib
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
AR=1.6; SEV=15.0
DIRC={"ship","harbor","large-vehicle","small-vehicle","plane","airplane","Warship","Motorboat","Boeing737","Boeing747","A220","A321","Cargo","Fishing"}
CELLS=[("SODA-A","4","SODA#4"),("DIOR-R","3","DIOR#3"),("FAIR1M-v1.0","24","FAIR1M#24"),("DIOR-R","22","DIOR#22")]
def sub(i): return "D_fit" if int(hashlib.md5(str(i).encode()).hexdigest(),16)%2==0 else "D_calib"
def sev_at_cov(score,sev,cov):
    o=np.argsort(-score,kind="stable"); k=max(1,int(round(cov*len(score))))
    return float(sev[o[:k]].mean())
rows=[]
for ds,bid,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r["aspect_ratio"]>=AR and (r["class"] in DIRC or str(r["class"]).lower() in {c.lower() for c in DIRC})]
    if len(recs)<800: continue
    sp=np.array([r["d_cal_daudit_split_flag"] for r in recs]); img=np.array([r["image_id"] for r in recs])
    subf=np.array([sub(img[k]) if sp[k]=="D_cal" else "D_audit" for k in range(len(recs))])
    fit=subf=="D_fit"; aud=subf=="D_audit"
    sc=np.array([r["score"] for r in recs]); er=np.array([r["angle_error"] for r in recs])
    ar=np.array([r["aspect_ratio"] for r in recs]); sz=np.array([r["size"] for r in recs])
    sev=(er>SEV).astype(float)
    X=np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)])
    if fit.sum()<200 or aud.sum()<200: continue
    g=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(X[fit],er[fit])
    lin=LinearRegression().fit(X[fit],er[fit])
    scores={"detection_score":sc[aud],"size_linear":-lin.predict(X)[aud],"geometry":-g.predict(X)[aud]}
    seva=sev[aud]; base=float(seva.mean())
    for sn,sv in scores.items():
        for cov in [0.5,0.7,0.9]:
            rows.append(dict(cell=name,selector=sn,base_severe_rate=round(base,4),coverage=cov,
                             severe_err_rate=round(sev_at_cov(sv,seva,cov),4),severe_def="err>15deg",n_audit=int(aud.sum())))
    r70={r["selector"]:r["severe_err_rate"] for r in rows if r["cell"]==name and r["coverage"]==0.7}
    print(f"{name}: base_severe={base:.4f} severe@70 {r70}",flush=True)
if rows:
    with open(f"{OUTd}/r4_tail_event_downstream.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("WROTE r4_tail_event_downstream.csv")
