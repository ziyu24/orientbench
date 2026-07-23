"""A5 / P5 — downstream redesign: counterfactual angle-induced rIoU drop (055).
For each masked (ar>=1.6) matched instance:
  Delta_rIoU = rIoU(pred box with GT angle) - rIoU(pred box with pred angle)
This isolates the ANGLE contribution to localization (unlike 053's 1-rIoU which is
dominated by center/scale error). Downstream risk = Delta_rIoU (recoverable IoU loss
from angle error). Question: does a reliability selector (trained on D_cal angle error)
keep predictions with LOW Delta_rIoU, i.e. reduce downstream angle-induced loss vs
score-only / size-linear? Risk-coverage on Delta_rIoU.
Real 052 artifacts; shapely; GBR/linear trained only on D_cal."""
import json, csv, sys, os, math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
AR=1.6; CAP=6000; rng=np.random.RandomState(55)
CELLS=[("DIOR-R","22","DIOR#22"),("FAIR1M-v1.0","24","FAIR1M#24"),("SODA-A","23","SODA#23"),
       ("DIOR-R","3","DIOR#3"),("DIOR-R","61","DIOR#61"),("SODA-A","4","SODA#4")]
def poly(o):
    w,h=o["obb_w"],o["obb_h"]
    p=Polygon([(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)])
    p=affinity.rotate(p,math.degrees(o["obb_theta"]),origin=(0,0),use_radians=False)
    return affinity.translate(p,o["obb_cx"],o["obb_cy"])
def iou(a,b):
    try:
        i=a.intersection(b).area; u=a.area+b.area-i; return i/u if u>0 else 0.0
    except: return 0.0
rows=[]
for ds,bid,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r["aspect_ratio"]>=AR and r["d_cal_daudit_split_flag"] in("D_cal","D_audit")]
    sp=np.array([r["d_cal_daudit_split_flag"] for r in recs])
    aud_idx=np.where(sp=="D_audit")[0]
    if len(aud_idx)>CAP: aud_idx=rng.choice(aud_idx,CAP,replace=False)
    cal_idx=np.where(sp=="D_cal")[0]
    if len(cal_idx)>CAP: cal_idx=rng.choice(cal_idx,CAP,replace=False)
    use=np.concatenate([cal_idx,aud_idx]); recs=[recs[i] for i in use]
    is_aud=np.array([1]*len(cal_idx)+[0]*len(aud_idx))==0
    is_cal=~is_aud
    sc=np.array([r["score"] for r in recs]); er=np.array([r["angle_error"] for r in recs])
    ar=np.array([r["aspect_ratio"] for r in recs]); sz=np.array([r["size"] for r in recs])
    dvals=[]
    for r in recs:
        po=r["pred_obb"]; go=r["gt_obb"]
        pred_iou=iou(poly(po),poly(go))
        po_gt=dict(po); po_gt["obb_theta"]=go["obb_theta"]  # substitute GT angle, keep pred center/size
        gt_ang_iou=iou(poly(po_gt),poly(go))
        dvals.append(max(0.0, gt_ang_iou-pred_iou))
    dR=np.array(dvals)  # downstream angle-induced recoverable IoU loss
    X=np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)])
    g=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(X[is_cal],er[is_cal])
    lin=LinearRegression().fit(X[is_cal],er[is_cal])
    scores={"detection_score":sc,"size_linear":-lin.predict(X),"geometry_selector":-g.predict(X)}
    dRa=dR[is_aud]
    base=float(dRa.mean())
    for sn,sv in scores.items():
        sva=sv[is_aud]
        nr=nrc_auc(sva,dRa)["nrc_auc"]
        rows.append(dict(cell=name,selector=sn,risk="angle_induced_dIoU",n_audit=int(is_aud.sum()),
            base_mean_dIoU=round(base,4),
            AURC=round(aurc(sva,dRa),4),
            risk_at70=round(risk_at_coverage(sva,dRa,0.7),4),
            risk_at90=round(risk_at_coverage(sva,dRa,0.9),4),
            NRC=round(nr,4) if nr==nr else ""))
    # deltas vs score-only / size-linear at coverage 0.7
    r70={r["selector"]:r["risk_at70"] for r in rows if r["cell"]==name}
    print(f"{name}: base_dIoU={base:.4f} NRC det/size/geo="
          f"{[r['NRC'] for r in rows if r['cell']==name]} r@70={r70}",flush=True)
with open(f"{OUT}/p5_downstream_redesign_055.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("WROTE p5_downstream_redesign_055.csv")
