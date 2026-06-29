# Offline GT-free consistency features (geometry + local-angle-consistency neighbor disagreement) for 6 cells.
import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.core.geometry import canonical_longside_theta
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
SC="/dev/shm/cqc/orientbench/predictions"; ART=f"{ROOT}/measure_fix_v2/artifacts/features_v2"; os.makedirs(ART,exist_ok=True)
def fs(ds,bid):
    for d in (f"{SC}/{ds}/{bid}/schema",f"{SC}/_archive/{ds}/{bid}/schema"):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".jsonl"): return os.path.join(d,f)
def gtp(ds):
    p=f"{SC}/{ds}/{ds}_fullval_gt.jsonl"
    if os.path.isfile(p): return p
    p2=f"{ROOT}/outputs/predictions/{ds}/_dcal_subset/gt_mmrotate.jsonl"
    return p2 if os.path.isfile(p2) else None
CELLS=[("FAIR1M-v1.0","24","psc"),("SODA-A","23","psc"),("DIOR-R","22","psc"),
       ("DIOR-R","3","orcnn"),("DIOR-R","10","lsknet"),("DOTA-v1.0","20","psc")]
def adiff(a,b): return abs(((a-b+math.pi/2)%math.pi)-math.pi/2)
for ds,bid,det in CELLS:
    out=f"{ART}/{ds}_{bid}.jsonl"
    if os.path.isfile(out): print("cached",ds,bid,flush=True); continue
    sch=fs(ds,bid); g=gtp(ds)
    if not(sch and g): print("skip",ds,bid,flush=True); continue
    preds=[json.loads(l) for l in open(sch)]; gts=[json.loads(l) for l in open(g)]
    gids={x["image_id"] for x in gts}; pset=[p for p in preds if p.get("score",1)>=0.30 and p["image_id"] in gids]
    byimg={}
    for p in pset: byimg.setdefault(p["image_id"],[]).append(p)
    m=match_dataset(pset,gts); rec=[]
    for pi,gj,_ in m["matched_pairs"]:
        p,gg=pset[pi],gts[gj]; c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]
        w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if not math.isfinite(e) or ar<1.6: continue
        th0=canonical_longside_theta(p["obb_w"],p["obb_h"],p["obb_theta"]); cx,cy=p["obb_cx"],p["obb_cy"]
        diffs=[]
        for q in byimg[p["image_id"]]:
            if q is p: continue
            if math.hypot(q["obb_cx"]-cx,q["obb_cy"]-cy)<200:
                thq=canonical_longside_theta(q["obb_w"],q["obb_h"],q["obb_theta"])
                if math.isfinite(thq) and math.isfinite(th0): diffs.append(adiff(thq,th0))
        lac=float(np.median(diffs)) if diffs else math.pi/4
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        rec.append({"img":p["image_id"],"cx":p["obb_cx"],"cy":p["obb_cy"],"theta":p["obb_theta"],
                    "score":p["score"],"log_ar":math.log(ar),"log_sqrt_area":math.log(math.sqrt(max(1.0,w*h))),
                    "gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],"local_angle_consistency":lac,
                    "err":e,"split":assign_split(p["image_id"])})
    with open(out,"w") as f:
        for r in rec: f.write(json.dumps(r)+"\n")
    print(f"enriched {ds}/{bid} n={len(rec)}",flush=True)
print("ENRICH DONE",flush=True)
