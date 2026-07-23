"""A2 — P1 constrained angle perturbation (055).
Real 052 matched pred_obb/gt_obb. For each matched instance find eps_max = largest
angle perturbation keeping rIoU(pred_rotated, gt) > 0.5, inject it, recompute angle
risk / IoU. Demonstrates: mAP@0.5 (IoU>0.5 survival) stable by construction while
orientation risk rises; AP75 (IoU>0.75) sensitive. Stratified by ar-bin.
No detector training/inference; read-only artifacts; shapely rotated IoU."""
import json, csv, sys, os, math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
CELLS=[("DIOR-R","22","DIOR#22"),("FAIR1M-v1.0","24","FAIR1M#24"),
       ("SODA-A","23","SODA#23"),("DIOR-R","3","DIOR#3"),
       ("DIOR-R","61","DIOR#61"),("SODA-A","4","SODA#4")]
CAP=4000; rng=np.random.RandomState(55)
GRID=np.arange(1.0,70.0,1.0)  # degrees

def obb_poly(o):
    cx,cy,w,h,th=o["obb_cx"],o["obb_cy"],o["obb_w"],o["obb_h"],o["obb_theta"]
    p=Polygon([(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)])
    p=affinity.rotate(p, math.degrees(th), origin=(0,0), use_radians=False)
    return affinity.translate(p, cx, cy)
def iou(a,b):
    try:
        i=a.intersection(b).area; u=a.area+b.area-i
        return i/u if u>0 else 0.0
    except: return 0.0
def rot_pred(o,ddeg):
    o2=dict(o); o2["obb_theta"]=o["obb_theta"]+math.radians(ddeg); return o2
def long_axis(o):
    # canonical long-side orientation: theta if w>=h else theta+90deg
    return o["obb_theta"] if o["obb_w"]>=o["obb_h"] else o["obb_theta"]+math.pi/2
def ang_err_o(predo,gto):
    d=abs(long_axis(predo)-long_axis(gto))%math.pi
    return math.degrees(min(d,math.pi-d))

def eps_max(predo,gto,direction=1.0):
    """largest grid delta with IoU(rotate pred by direction*delta, gt)>0.5 (direction-aware
    so the injected perturbation is guaranteed to keep IoU>0.5 => mAP@0.5 match preserved)."""
    gp=obb_poly(gto); best=0.0
    for dd in GRID:
        if iou(obb_poly(rot_pred(predo,direction*dd)),gp)>0.5: best=dd
        else: break
    return best

def arbin(ar):
    if ar<1.3: return "near_square"
    if ar<1.6: return "moderate_low"
    if ar<3.0: return "elongated"
    return "very_elongated"

rows=[]; rows_bin=[]
for ds,bid,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r.get("d_cal_daudit_split_flag")=="D_audit"]
    if len(recs)>CAP:
        idx=rng.choice(len(recs),CAP,replace=False); recs=[recs[i] for i in idx]
    score=np.array([r["score"] for r in recs]); ar=np.array([r["aspect_ratio"] for r in recs])
    base_err=[]; pert_err=[]; base_iou=[]; pert_iou=[]; epsm=[]
    for r in recs:
        po=r["pred_obb"]; go=r["gt_obb"]
        be=ang_err_o(po,go); base_err.append(be)
        biou=iou(obb_poly(po),obb_poly(go)); base_iou.append(biou)
        # signed long-axis diff -> perturb AWAY from gt (worst-case within IoU>0.5 tolerance)
        s0=((long_axis(po)-long_axis(go)+math.pi/2)%math.pi)-math.pi/2
        direction=1.0 if s0>=0 else -1.0
        em=eps_max(po,go,direction); epsm.append(em)   # eps_max in the injection direction
        po2=rot_pred(po,direction*em)  # inject constrained perturbation, away from gt (IoU stays >0.5)
        pert_err.append(ang_err_o(po2,go))
        pert_iou.append(iou(obb_poly(po2),obb_poly(go)))
    base_err=np.array(base_err); pert_err=np.array(pert_err)
    base_iou=np.array(base_iou); pert_iou=np.array(pert_iou); epsm=np.array(epsm)
    def frac(x,t): return float((x>t).mean())
    def nrc(e):
        v=nrc_auc(score,e)["nrc_auc"]; return round(v,4) if v==v else ""
    rows.append(dict(cell=name,n=len(recs),
        mean_eps_max=round(float(epsm.mean()),2),
        base_mAP50_proxy=round(frac(base_iou,0.5),4), pert_mAP50_proxy=round(frac(pert_iou,0.5),4),
        base_AP75_proxy=round(frac(base_iou,0.75),4), pert_AP75_proxy=round(frac(pert_iou,0.75),4),
        base_mean_risk=round(float(base_err.mean()),3), pert_mean_risk=round(float(pert_err.mean()),3),
        delta_risk=round(float((pert_err-base_err).mean()),3),
        base_NRC=nrc(base_err), pert_NRC=nrc(pert_err)))
    for b in ["near_square","moderate_low","elongated","very_elongated"]:
        m=np.array([arbin(a)==b for a in ar])
        if m.sum()<30: continue
        dR=float((pert_err[m]-base_err[m]).mean())
        dM=frac(pert_iou[m],0.5)-frac(base_iou[m],0.5)
        rows_bin.append(dict(cell=name,ar_bin=b,n=int(m.sum()),mean_eps_max=round(float(epsm[m].mean()),2),
            base_risk=round(float(base_err[m].mean()),3),pert_risk=round(float(pert_err[m].mean()),3),
            delta_risk=round(dR,3),delta_mAP50_proxy=round(dM,4),
            delta_AP75_proxy=round(frac(pert_iou[m],0.75)-frac(base_iou[m],0.75),4),
            risk_per_mAP=("inf" if abs(dM)<1e-6 else round(dR/abs(dM),1))))
    print(f"{name}: n={len(recs)} eps_max={epsm.mean():.1f} mAP50 {frac(base_iou,0.5):.3f}->{frac(pert_iou,0.5):.3f} "
          f"AP75 {frac(base_iou,0.75):.3f}->{frac(pert_iou,0.75):.3f} risk {base_err.mean():.2f}->{pert_err.mean():.2f}",flush=True)

with open(f"{OUT}/p1_constrained_angle_perturb_055.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(f"{OUT}/p1_ar_bin_dose_response_055.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows_bin[0].keys())); w.writeheader(); w.writerows(rows_bin)
print("WROTE p1_constrained_angle_perturb_055.csv, p1_ar_bin_dose_response_055.csv")
