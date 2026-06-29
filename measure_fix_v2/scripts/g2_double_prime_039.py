import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"
sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc,risk_at_coverage
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
SC="/dev/shm/cqc/orientbench/predictions"
OUT=f"{ROOT}/measure_fix_v2/reports"
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
CELLS=[("DOTA-v1.0","20","psc"),("DIOR-R","22","psc"),("FAIR1M-v1.0","24","psc"),("SODA-A","23","psc"),
       ("SODA-A","4","orcnn"),("DIOR-R","3","orcnn"),("DIOR-R","10","lsknet")]
FEATS=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]
rng=np.random.RandomState(7)
def build(ds,bid):  # match once, ar>=1.3 minimum
    sch=fs(ds,bid); g=gtp(ds)
    if not(sch and g): return None
    preds=[json.loads(l) for l in open(sch)]; gts=[json.loads(l) for l in open(g)]
    gids={x["image_id"] for x in gts}
    pset=[p for p in preds if p.get("score",1)>=0.30 and p["image_id"] in gids]
    m=match_dataset(pset,gts); rec=[]
    for pi,gj,_ in m["matched_pairs"]:
        p,gg=pset[pi],gts[gj]; c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]
        if not math.isfinite(e): continue
        w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if ar<1.3: continue
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        area=max(1.0,w*h)
        rec.append({"img":p["image_id"],"score":p["score"],"log_ar":math.log(ar),"ar":ar,
                    "log_sqrt_area":math.log(math.sqrt(area)),"gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],"err":e})
    return rec
def Xof(recs,fs): return np.array([[r[f] for f in fs] for r in recs])
def fit_selectors(cal):
    yc=np.array([r["err"] for r in cal])
    lin_ar=LinearRegression().fit(Xof(cal,["score","log_ar"]),yc)
    lin_sz=LinearRegression().fit(Xof(cal,["score","log_ar","log_sqrt_area"]),yc)
    gbr=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,FEATS),yc)
    return lin_ar,lin_sz,gbr
def scores_for(aud,lin_ar,lin_sz,gbr):
    return {"score_only":np.array([r["score"] for r in aud]),
            "score_ar_linear":-lin_ar.predict(Xof(aud,["score","log_ar"])),
            "score_ar_size_linear":-lin_sz.predict(Xof(aud,["score","log_ar","log_sqrt_area"])),
            "nonlinear":-gbr.predict(Xof(aud,FEATS))}
def metr(s,r):
    nr=nrc_auc(s,r); order=np.argsort(-s); k=max(1,int(0.7*len(s))); ret=r[order[:k]]
    return {"NRC":round(nr["nrc_auc"],4),"AURC":round(nr["aurc_model"],4),
            "Risk@70":round(risk_at_coverage(s,r,0.7),3),"Risk@90":round(risk_at_coverage(s,r,0.9),3),
            "p90_at70":round(float(np.percentile(ret,90)),2),"p99_at70":round(float(np.percentile(ret,99)),2)}
def paired_delta(s_base,s_nl,r,B=500):
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n)
        v=nrc_auc(s_base[i],r[i])["nrc_auc"]-nrc_auc(s_nl[i],r[i])["nrc_auc"]
        if math.isfinite(v): d.append(v)
    return round(float(np.median(d)),4),[round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
DATA={}
for ds,bid,det in CELLS:
    r=build(ds,bid)
    if r: DATA[(ds,bid,det)]=r; print(f"matched {ds}/{bid} n={len(r)}",flush=True)
rows=[]
for (ds,bid,det),rec in DATA.items():
    for armin,tag in ((1.6,"primary_ar1.6"),(1.3,"sens_ar1.3"),(2.0,"sens_ar2.0")):
        sub=[r for r in rec if r["ar"]>=armin]
        cal=[r for r in sub if assign_split(r["img"])=="D_cal"]; aud=[r for r in sub if assign_split(r["img"])=="D_audit"]
        if len(cal)<100 or len(aud)<100: continue
        # fixed size bins from D_cal tertiles
        cuts=np.quantile([r["log_sqrt_area"] for r in cal],[1/3,2/3])
        def binof(r): return 0 if r["log_sqrt_area"]<cuts[0] else (1 if r["log_sqrt_area"]<cuts[1] else 2)
        lin_ar,lin_sz,gbr=fit_selectors(cal)
        sc=scores_for(aud,lin_ar,lin_sz,gbr); ya=np.array([r["err"] for r in aud])
        for name,s in sc.items():
            mm=metr(s,ya); mm.update({"ar":tag,"dataset":ds,"baseline_id":bid,"detector":det,"scope":"overall","n_audit":len(aud),"selector":name}); rows.append(mm)
        md,ci=paired_delta(sc["score_ar_size_linear"],sc["nonlinear"],ya)
        rows.append({"ar":tag,"dataset":ds,"baseline_id":bid,"detector":det,"scope":"overall","selector":"DELTA_sizelin_minus_nl","NRC":md,"ci_lo":ci[0],"ci_hi":ci[1],"nl_better_sig":bool(ci[0]>0),"n_audit":len(aud)})
        # within size bins
        binr=np.array([binof(r) for r in aud])
        for b,bname in ((0,"small"),(1,"medium"),(2,"large")):
            idx=np.where(binr==b)[0]
            if len(idx)<60: continue
            yb=ya[idx]; sl=sc["score_ar_size_linear"][idx]; nl=sc["nonlinear"][idx]
            nrc_sl=nrc_auc(sl,yb)["nrc_auc"]; nrc_nl=nrc_auc(nl,yb)["nrc_auc"]
            md,ci=paired_delta(sl,nl,yb)
            rows.append({"ar":tag,"dataset":ds,"baseline_id":bid,"detector":det,"scope":f"sizebin_{bname}","selector":"DELTA_sizelin_minus_nl",
                         "NRC_sizelin":round(nrc_sl,4),"NRC_nl":round(nrc_nl,4),"NRC":md,"ci_lo":ci[0],"ci_hi":ci[1],"nl_better_sig":bool(ci[0]>0),"n_audit":len(idx)})
        # permutation importance overall primary only
        if tag=="primary_ar1.6":
            from sklearn.inspection import permutation_importance
            pi=permutation_importance(gbr,Xof(aud,FEATS),ya,n_repeats=5,random_state=0,scoring="neg_mean_absolute_error")
            rows.append({"ar":tag,"dataset":ds,"baseline_id":bid,"detector":det,"scope":"perm_importance","selector":"nonlinear",
                         "NRC":json.dumps({FEATS[j]:round(float(pi.importances_mean[j]),3) for j in range(len(FEATS))})})
    print(f"done {ds}/{bid}",flush=True)
cols=["ar","dataset","baseline_id","detector","scope","selector","n_audit","NRC","NRC_sizelin","NRC_nl","AURC","Risk@70","Risk@90","p90_at70","p99_at70","ci_lo","ci_hi","nl_better_sig"]
with open(f"{OUT}/g2_double_prime_results_039.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
json.dump(rows,open(f"{OUT}/g2_double_prime_results_039.json","w"),indent=2,default=str)
print("G2DP DONE",len(rows),flush=True)
