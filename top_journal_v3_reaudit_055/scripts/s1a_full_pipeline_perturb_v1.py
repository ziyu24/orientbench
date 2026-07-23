"""S1a — full-pipeline constrained angle perturbation from RAW predictions (v1).
Runs a real VOC-style OBB evaluator (re-matches ALL predictions, computes real
AP50/AP75/mAP) on baseline vs constrained-angle-perturbed predictions.
- perturbation applied ONLY to predictions that are TP@0.5 (matched to a GT),
  by their per-instance eps_max (keeps rIoU>0.5 with matched gt, away direction);
  FP and unmatched preds unchanged; scores/classes/NMS set preserved.
No matched-only mAP=1.000 proxy. No training, no threshold/split change.
Usage: python s1a_full_pipeline_perturb_v1.py CELL   (CELL e.g. DIOR-R/22)
"""
import json, csv, sys, os, math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1"
FMT={r["cell_id"]:r for r in csv.DictReader(open("top_journal_v3/reports/full_matched_tables_052.csv"))}

def poly(o):
    w,h=o["obb_w"],o["obb_h"]
    p=Polygon([(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)])
    p=affinity.rotate(p,math.degrees(o["obb_theta"]),origin=(0,0),use_radians=False)
    return affinity.translate(p,o["obb_cx"],o["obb_cy"])
def aabb(o):
    # conservative axis-aligned bound (radius = half-diagonal)
    r=0.5*math.hypot(o["obb_w"],o["obb_h"]); return (o["obb_cx"]-r,o["obb_cy"]-r,o["obb_cx"]+r,o["obb_cy"]+r)
def iou(pa,pb):
    try:
        i=pa.intersection(pb).area; u=pa.area+pb.area-i; return i/u if u>0 else 0.0
    except: return 0.0
def long_axis(o): return o["obb_theta"] if o["obb_w"]>=o["obb_h"] else o["obb_theta"]+math.pi/2
def ang_err(a,b):
    d=abs(long_axis(a)-long_axis(b))%math.pi; return math.degrees(min(d,math.pi-d))
def rot(o,ddeg):
    o2=dict(o); o2["obb_theta"]=o["obb_theta"]+math.radians(ddeg); return o2
GRID=np.arange(1.0,70.0,1.0)
def eps_max(po,go,direction):
    gp=poly(go); best=0.0
    for dd in GRID:
        if iou(poly(rot(po,direction*dd)),gp)>0.5: best=dd
        else: break
    return best

def ap_all_points(tp, scores, n_gt):
    if n_gt==0: return float("nan")
    order=np.argsort(-np.asarray(scores),kind="stable"); tp=np.asarray(tp)[order]
    fp=1-tp; ctp=np.cumsum(tp); cfp=np.cumsum(fp)
    rec=ctp/n_gt; prec=ctp/np.maximum(ctp+cfp,1e-9)
    # all-points interpolation (VOC2010+)
    mrec=np.concatenate([[0],rec,[1]]); mpre=np.concatenate([[0],prec,[0]])
    for i in range(len(mpre)-1,0,-1): mpre[i-1]=max(mpre[i-1],mpre[i])
    idx=np.where(mrec[1:]!=mrec[:-1])[0]
    return float(np.sum((mrec[idx+1]-mrec[idx])*mpre[idx+1]))

def build(records):
    by={}  # (image, class) -> list of dict(obb, score, ar, poly, aabb, idx)
    for i,r in enumerate(records):
        o=dict(obb_cx=r["obb_cx"],obb_cy=r["obb_cy"],obb_w=r["obb_w"],obb_h=r["obb_h"],obb_theta=r["obb_theta"])
        by.setdefault((r["image_id"],r["class_name"]),[]).append(dict(o=o,score=r.get("score",1.0),idx=i))
    return by

def evaluate(preds, gts, taus=(0.5,0.75), record_tp_tau=0.5):
    """preds/gts: raw record lists. Returns dict AP per tau, mAP, and TP-map at record_tp_tau."""
    P=build(preds); G=build(gts)
    gt_count={}  # class -> n_gt
    for (img,cls),lst in G.items(): gt_count[cls]=gt_count.get(cls,0)+len(lst)
    # precompute polys/aabb lazily
    classes=set(c for _,c in P)|set(gt_count)
    ap={t:{} for t in taus}; tpmap={}  # pred_idx -> gt (record) at record_tp_tau
    fp_count={t:0 for t in taus}
    for cls in classes:
        # gather preds of this class across images, sort by score desc
        pl=[(img,p) for (img,c),lst in P.items() if c==cls for p in lst]
        pl.sort(key=lambda x:-x[1]["score"])
        # per-image gt polys for this class
        gpolys={}
        for (img,c),lst in G.items():
            if c!=cls: continue
            gpolys[img]=[(gg,poly(gg["o"]),aabb(gg["o"])) for gg in [dict(o=dict(obb_cx=x["o"]["obb_cx"],obb_cy=x["o"]["obb_cy"],obb_w=x["o"]["obb_w"],obb_h=x["o"]["obb_h"],obb_theta=x["o"]["obb_theta"])) for x in lst]]
        for t in taus:
            used={img:[False]*len(gpolys.get(img,[])) for img in gpolys}
            tp=[]; sc=[]
            for img,p in pl:
                pa=poly(p["o"]); ab=aabb(p["o"]); best=-1; bj=-1
                for j,(gg,gp,gab) in enumerate(gpolys.get(img,[])):
                    if used[img][j]: continue
                    if ab[2]<gab[0] or ab[0]>gab[2] or ab[3]<gab[1] or ab[1]>gab[3]: continue
                    v=iou(pa,gp)
                    if v>best: best=v; bj=j
                if best>=t and bj>=0:
                    used[img][bj]=True; tp.append(1);
                    if t==record_tp_tau: tpmap[p["idx"]]=gpolys[img][bj][0]["o"]
                else:
                    tp.append(0); fp_count[t]+=1
                sc.append(p["score"])
            ap[t][cls]=ap_all_points(tp,sc,gt_count.get(cls,0))
    mAP={t:float(np.nanmean([v for v in ap[t].values() if v==v])) if ap[t] else float("nan") for t in taus}
    return ap, mAP, tpmap, fp_count

def main(cell):
    fm=FMT[cell]; ds,bid=cell.split("/")
    preds=[json.loads(l) for l in open(fm["schema_path"])]
    gts=[json.loads(l) for l in open(fm["gt_path"])]
    print(f"[{cell}] preds={len(preds)} gts={len(gts)}",flush=True)
    ap0,m0,tpmap,fp0=evaluate(preds,gts)
    print(f"[{cell}] BASE AP50={m0[0.5]:.4f} AP75={m0[0.75]:.4f} FP@0.5={fp0[0.5]}",flush=True)
    # perturb TP@0.5 preds by eps_max (constrained, away from matched gt)
    ars=[]; be=[]; pe=[]; epsm=[]
    pert=[dict(r) for r in preds]
    for idx,go in tpmap.items():
        po=dict(obb_cx=preds[idx]["obb_cx"],obb_cy=preds[idx]["obb_cy"],obb_w=preds[idx]["obb_w"],obb_h=preds[idx]["obb_h"],obb_theta=preds[idx]["obb_theta"])
        s0=((long_axis(po)-long_axis(go)+math.pi/2)%math.pi)-math.pi/2
        d=1.0 if s0>=0 else -1.0
        em=eps_max(po,go,d);
        pert[idx]["obb_theta"]=po["obb_theta"]+math.radians(d*em)
        ar=max(po["obb_w"],po["obb_h"])/max(min(po["obb_w"],po["obb_h"]),1e-6)
        ars.append(ar); be.append(ang_err(po,go)); pe.append(ang_err(rot(po,d*em),go)); epsm.append(em)
    ap1,m1,_,fp1=evaluate(pert,gts)
    ars=np.array(ars); be=np.array(be); pe=np.array(pe); epsm=np.array(epsm)
    print(f"[{cell}] PERT AP50={m1[0.5]:.4f} AP75={m1[0.75]:.4f} FP@0.5={fp1[0.5]} | angle {be.mean():.2f}->{pe.mean():.2f}",flush=True)
    row=dict(cell=cell,detector=fm["detector"],n_pred=len(preds),n_gt=len(gts),n_tp_perturbed=len(be),
             base_AP50=round(m0[0.5],4),pert_AP50=round(m1[0.5],4),dAP50=round(m1[0.5]-m0[0.5],4),
             base_AP75=round(m0[0.75],4),pert_AP75=round(m1[0.75],4),dAP75=round(m1[0.75]-m0[0.75],4),
             base_angle=round(float(be.mean()),3),pert_angle=round(float(pe.mean()),3),d_angle=round(float((pe-be).mean()),3),
             base_FP50=fp0[0.5],pert_FP50=fp1[0.5],d_FP50=fp1[0.5]-fp0[0.5],mean_eps_max=round(float(epsm.mean()),2))
    # ar-bin dose response
    dose=[]
    def arbin(a): return "near_square" if a<1.3 else "moderate" if a<1.6 else "elongated" if a<3 else "very_elongated"
    bl=np.array([arbin(a) for a in ars])
    for b in ["near_square","moderate","elongated","very_elongated"]:
        m=bl==b
        if m.sum()<20: continue
        dose.append(dict(cell=cell,ar_bin=b,n=int(m.sum()),mean_eps_max=round(float(epsm[m].mean()),2),
                         base_angle=round(float(be[m].mean()),3),pert_angle=round(float(pe[m].mean()),3),
                         d_angle=round(float((pe[m]-be[m]).mean()),3)))
    return row,dose

if __name__=="__main__":
    cells=sys.argv[1:] or ["DIOR-R/22"]
    rows=[]; doses=[]
    for c in cells:
        r,d=main(c); rows.append(r); doses.extend(d)
    # append-safe write
    mf=f"{OUTd}/s1a_full_pipeline_perturbation_v1.csv"; df=f"{OUTd}/s1a_dose_response_v1.csv"
    def dump(path,newrows,keyfn):
        newkeys=set(keyfn(r) for r in newrows); old=[]
        if os.path.isfile(path): old=[r for r in csv.DictReader(open(path)) if keyfn(r) not in newkeys]
        allr=old+[{k:str(v) for k,v in r.items()} for r in newrows]
        cols=list(newrows[0].keys())
        with open(path,"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(allr)
    if rows: dump(mf,rows,lambda r:str(r["cell"]))
    if doses: dump(df,doses,lambda r:(str(r["cell"]),str(r["ar_bin"])))
    print("WROTE",mf,df,flush=True)
