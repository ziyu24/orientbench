# GT-free offline deployable proxy: local angle consistency (neighbors share orientation in aerial scenes).
# No GT used to BUILD proxy; GT only for final D_audit evaluation. No detector training, no TTA inference.
import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.metrics.nrc_auc import nrc_auc
SC="/dev/shm/cqc/orientbench/predictions"; OUT=f"{ROOT}/measure_fix_v2/reports"
def fs(ds,bid):
    for d in (f"{SC}/{ds}/{bid}/schema",f"{SC}/_archive/{ds}/{bid}/schema"):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".jsonl"): return os.path.join(d,f)
def gtp(ds):
    p=f"{SC}/{ds}/{ds}_fullval_gt.jsonl"; return p if os.path.isfile(p) else None
CELLS=[("FAIR1M-v1.0","24","psc"),("DIOR-R","3","orcnn")]  # 2 representative, smaller
rows=[]
for ds,bid,det in CELLS:
    sch=fs(ds,bid); g=gtp(ds)
    if not(sch and g): print("skip",ds,bid,flush=True); continue
    preds=[json.loads(l) for l in open(sch)]; gts=[json.loads(l) for l in open(g)]
    gids={x["image_id"] for x in gts}; pset=[p for p in preds if p.get("score",1)>=0.30 and p["image_id"] in gids]
    # group all preds by image for neighbor angle stats (GT-free)
    byimg={}
    for p in pset: byimg.setdefault(p["image_id"],[]).append(p)
    m=match_dataset(pset,gts); proxy=[]; err=[]; score=[]
    for pi,gj,_ in m["matched_pairs"]:
        p,gg=pset[pi],gts[gj]; c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]
        w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if not math.isfinite(e) or ar<1.6: continue
        # neighbor angle disagreement (GT-free): canonical long-side angle of nearby preds in same image
        nb=byimg[p["image_id"]]; cx,cy=p["obb_cx"],p["obb_cy"]
        from orientbench.core.geometry import canonical_longside_theta
        th0=canonical_longside_theta(p["obb_w"],p["obb_h"],p["obb_theta"])
        diffs=[]
        for q in nb:
            if q is p: continue
            d=math.hypot(q["obb_cx"]-cx,q["obb_cy"]-cy)
            if d<200:  # local radius px
                thq=canonical_longside_theta(q["obb_w"],q["obb_h"],q["obb_theta"])
                if math.isfinite(thq) and math.isfinite(th0):
                    dd=abs(((thq-th0+math.pi/2)%math.pi)-math.pi/2); diffs.append(dd)
        disag=float(np.median(diffs)) if diffs else math.pi/4  # no neighbor -> neutral
        proxy.append(-disag); err.append(e); score.append(p["score"])
    proxy=np.array(proxy); err=np.array(err); score=np.array(score)
    if len(err)<100: print("too few",ds,bid,flush=True); continue
    nrc_proxy=nrc_auc(proxy,err)["nrc_auc"]; nrc_score=nrc_auc(score,err)["nrc_auc"]
    rows.append({"cell":f"{ds}/{bid}({det})","n":len(err),"uses_GT_to_build_proxy":False,
                 "NRC_score_only":round(nrc_score,4),"NRC_local_angle_consistency_proxy":round(nrc_proxy,4),
                 "proxy_beats_score":bool(nrc_proxy<nrc_score),"proxy_better_than_random":bool(nrc_proxy<1.0)})
    print(f"TTAproxy {ds}/{bid}: NRC_proxy={nrc_proxy:.4f} NRC_score={nrc_score:.4f} proxy<score={nrc_proxy<nrc_score} proxy<1={nrc_proxy<1.0} n={len(err)}",flush=True)
with open(f"{OUT}/tta_proxy_hardening_040.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("TTAPROXY DONE",flush=True)
