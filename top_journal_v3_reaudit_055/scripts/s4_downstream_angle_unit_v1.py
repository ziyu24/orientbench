"""S4 — angle-unit downstream selective prediction on REAL directional classes (v1).
HRSC real detector preds unavailable (only synthetic) -> use directional classes
(ship / harbor / large-vehicle / plane) from real 052 matched tables. Risk = angle
error in DEGREES (angle unit, not dIoU). Report coverage / Risk@70 / Risk@90 /
abstention for detection vs size-linear vs geometry selector. Masked ar>=1.6.
Only OBB long-axis geometric orientation (NOT semantic heading). No training of detectors.
"""
import json, csv, sys, os, math, hashlib
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
from orientbench.metrics.nrc_auc import nrc_auc
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
AR=1.6
DIRCLASS={"ship","harbor","large-vehicle","small-vehicle","plane","airplane","Ship","Harbor",
          "Boeing737","Boeing747","A220","A321","Cargo","Motorboat","Fishing","Warship"}
CELLS=[("SODA-A","4","SODA#4-ORCNN"),("DIOR-R","3","DIOR#3-ORCNN"),
       ("FAIR1M-v1.0","24","FAIR1M#24-PSC"),("DIOR-R","22","DIOR#22-PSC")]
def sub(i): return "D_fit" if int(hashlib.md5(str(i).encode()).hexdigest(),16)%2==0 else "D_calib"
rows=[]
for ds,bid,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r["aspect_ratio"]>=AR and (r["class"] in DIRCLASS or str(r["class"]).lower() in {c.lower() for c in DIRCLASS})]
    if len(recs)<800:
        print(f"{name}: only {len(recs)} directional-class instances, skip",flush=True); continue
    split=np.array([r["d_cal_daudit_split_flag"] for r in recs])
    img=np.array([r["image_id"] for r in recs])
    subf=np.array([sub(img[k]) if split[k]=="D_cal" else "D_audit" for k in range(len(recs))])
    fit=subf=="D_fit"; aud=subf=="D_audit"
    sc=np.array([r["score"] for r in recs]); er=np.array([r["angle_error"] for r in recs])
    ar=np.array([r["aspect_ratio"] for r in recs]); sz=np.array([r["size"] for r in recs])
    X=np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)])
    if fit.sum()<200 or aud.sum()<200: continue
    g=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(X[fit],er[fit])
    lin=LinearRegression().fit(X[fit],er[fit])
    scores={"detection_score":sc,"size_linear":-lin.predict(X),"geometry_selector":-g.predict(X)}
    classes=sorted(set(r["class"] for r in recs))
    base=float(er[aud].mean())
    for sn,sv in scores.items():
        sva=sv[aud]; ea=er[aud]
        nr=nrc_auc(sva,ea)["nrc_auc"]
        rows.append(dict(cell=name,classes=";".join(classes)[:60],selector=sn,risk="angle_error_deg",
            n_audit=int(aud.sum()),base_mean_deg=round(base,3),
            Risk_at70_deg=round(risk_at_coverage(sva,ea,0.7),3),
            Risk_at90_deg=round(risk_at_coverage(sva,ea,0.9),3),
            AURC_deg=round(aurc(sva,ea),3),NRC=round(nr,4) if nr==nr else ""))
    r70={r["selector"]:r["Risk_at70_deg"] for r in rows if r["cell"]==name}
    print(f"{name}: n_dir={len(recs)} base={base:.2f} R@70 {r70}",flush=True)
if rows:
    with open(f"{OUTd}/s4_downstream_angle_unit_v1.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("WROTE s4_downstream_angle_unit_v1.csv")
else:
    print("no cell had enough directional-class instances")
