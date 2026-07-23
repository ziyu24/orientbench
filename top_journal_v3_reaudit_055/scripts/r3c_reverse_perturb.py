"""R3c — reverse perturbation (appendix): fix ANGLE, perturb center/scale, run full
evaluator. Shows AP can change while angle-risk structure stays fixed -> the other
half of the two-way separation (mAP != orientation reliability). Real evaluator, raw preds."""
import json, csv, sys, os, math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports"
FMT={r["cell_id"]:r for r in csv.DictReader(open("top_journal_v3/reports/full_matched_tables_052.csv"))}
def poly(o):
    w,h=o["obb_w"],o["obb_h"]
    p=Polygon([(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)])
    p=affinity.rotate(p,math.degrees(o["obb_theta"]),origin=(0,0),use_radians=False)
    return affinity.translate(p,o["obb_cx"],o["obb_cy"])
def aabb(o):
    r=0.5*math.hypot(o["obb_w"],o["obb_h"]); return (o["obb_cx"]-r,o["obb_cy"]-r,o["obb_cx"]+r,o["obb_cy"]+r)
def iou(pa,pb):
    try: i=pa.intersection(pb).area; u=pa.area+pb.area-i; return i/u if u>0 else 0.0
    except: return 0.0
def long_axis(o): return o["obb_theta"] if o["obb_w"]>=o["obb_h"] else o["obb_theta"]+math.pi/2
def ang_err(a,b):
    d=abs(long_axis(a)-long_axis(b))%math.pi; return math.degrees(min(d,math.pi-d))
def ap_all_points(tp,scores,n_gt):
    if n_gt==0: return float("nan")
    o=np.argsort(-np.asarray(scores),kind="stable"); tp=np.asarray(tp)[o]
    ctp=np.cumsum(tp); cfp=np.cumsum(1-tp); rec=ctp/n_gt; prec=ctp/np.maximum(ctp+cfp,1e-9)
    mrec=np.concatenate([[0],rec,[1]]); mpre=np.concatenate([[0],prec,[0]])
    for i in range(len(mpre)-1,0,-1): mpre[i-1]=max(mpre[i-1],mpre[i])
    idx=np.where(mrec[1:]!=mrec[:-1])[0]
    return float(np.sum((mrec[idx+1]-mrec[idx])*mpre[idx+1]))
def build(recs):
    by={}
    for i,r in enumerate(recs):
        o=dict(obb_cx=r["obb_cx"],obb_cy=r["obb_cy"],obb_w=r["obb_w"],obb_h=r["obb_h"],obb_theta=r["obb_theta"])
        by.setdefault((r["image_id"],r["class_name"]),[]).append(dict(o=o,score=r.get("score",1.0),idx=i))
    return by
def evaluate(preds,gts,taus=(0.5,0.75)):
    P=build(preds); G=build(gts); gt_count={}
    for (im,c),l in G.items(): gt_count[c]=gt_count.get(c,0)+len(l)
    ap={t:{} for t in taus}
    for cls in set(c for _,c in P)|set(gt_count):
        pl=[(im,p) for (im,c),l in P.items() if c==cls for p in l]; pl.sort(key=lambda x:-x[1]["score"])
        gp={}
        for (im,c),l in G.items():
            if c==cls: gp[im]=[(poly(x["o"]),aabb(x["o"])) for x in l]
        for t in taus:
            used={im:[False]*len(gp.get(im,[])) for im in gp}; tp=[]; sc=[]
            for im,p in pl:
                pa=poly(p["o"]); ab=aabb(p["o"]); best=-1;bj=-1
                for j,(g,gab) in enumerate(gp.get(im,[])):
                    if used[im][j]: continue
                    if ab[2]<gab[0] or ab[0]>gab[2] or ab[3]<gab[1] or ab[1]>gab[3]: continue
                    v=iou(pa,g)
                    if v>best: best=v;bj=j
                if best>=t and bj>=0: used[im][bj]=True; tp.append(1)
                else: tp.append(0)
                sc.append(p["score"])
            ap[t][cls]=ap_all_points(tp,sc,gt_count.get(cls,0))
    return {t:float(np.nanmean([v for v in ap[t].values() if v==v])) for t in taus}
rng=np.random.RandomState(59)
rows=[]
for cell in (sys.argv[1:] or ["DIOR-R/3","DIOR-R/22"]):
    fm=FMT[cell]; preds=[json.loads(l) for l in open(fm["schema_path"])]; gts=[json.loads(l) for l in open(fm["gt_path"])]
    base=evaluate(preds,gts)
    # reverse perturbation: fix angle, shift center by frac*sqrt(area), shrink scale by 10%
    for frac,scl in [(0.10,1.0),(0.20,1.0),(0.0,0.85)]:
        pert=[]
        for r in preds:
            o=dict(r); s=math.sqrt(max(o["obb_w"]*o["obb_h"],1.0))
            ang=rng.uniform(0,2*math.pi)
            o["obb_cx"]=r["obb_cx"]+frac*s*math.cos(ang); o["obb_cy"]=r["obb_cy"]+frac*s*math.sin(ang)
            o["obb_w"]=r["obb_w"]*scl; o["obb_h"]=r["obb_h"]*scl  # angle untouched
            pert.append(o)
        pap=evaluate(pert,gts)
        rows.append(dict(cell=cell,perturb=f"center_shift={frac}*sqrt(area),scale={scl}",angle_touched="no",
            base_AP50=round(base[0.5],4),pert_AP50=round(pap[0.5],4),dAP50=round(pap[0.5]-base[0.5],4),
            base_AP75=round(base[0.75],4),pert_AP75=round(pap[0.75],4),dAP75=round(pap[0.75]-base[0.75],4),
            angle_risk_change="0 (angle unchanged)"))
        print(f"{cell} {frac}/{scl}: AP50 {base[0.5]:.4f}->{pap[0.5]:.4f} (d={pap[0.5]-base[0.5]:+.4f}), angle untouched",flush=True)
with open(f"{OUTd}/r3_reverse_perturbation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("WROTE r3_reverse_perturbation.csv")
