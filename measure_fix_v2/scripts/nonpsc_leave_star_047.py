import json,os,math,csv,sys,time
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
ART=f"{ROOT}/measure_fix_v2/artifacts/features_v2"; OUT=f"{ROOT}/measure_fix_v2/reports"; HB=f"{OUT}/heartbeat_047.json"
# non-PSC cells: (dataset, bid, family)
CELLS=[("DIOR-R","3","orcnn"),("SODA-A","4","orcnn"),("FAIR1M-v1.0","5","orcnn"),
       ("DIOR-R","10","lsknet"),("SODA-A","11","lsknet"),("FAIR1M-v1.0","12","lsknet"),
       ("DIOR-R","61","rtmdet")]
GEO=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]; RC=GEO+["local_angle_consistency"]
rng=np.random.RandomState(47)
def hb(m): json.dump({"task":"047_leave_star","msg":m,"t":time.strftime("%H:%M:%S")},open(HB,"w"))
DATA={}
for ds,bid,fam in CELLS:
    p=f"{ART}/{ds}_{bid}.jsonl"
    if os.path.isfile(p): DATA[(ds,bid,fam)]=[json.loads(l) for l in open(p)]
def Xof(rs,fs): return np.array([[r[k] for k in fs] for r in rs])
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def fitG(cal,fs): return GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,fs),np.array([r["err"] for r in cal]))
def ci_beats(base,cmp,r,B=200):  # base - cmp >0 => cmp better
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(base[i],r[i])-nrc(cmp[i],r[i])
        if math.isfinite(v): d.append(v)
    return [round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
def evaluate(mode,train_cells,target):
    cal=[r for c in train_cells for r in DATA[c] if r["split"]=="D_cal"]
    if len(cal)>120000:  # tractability: subsample GBR training source (eval unchanged on full D_audit)
        idx=np.random.RandomState(47).choice(len(cal),120000,replace=False); cal=[cal[i] for i in idx]
    taud=[r for r in DATA[target] if r["split"]=="D_audit"]
    if len(cal)<200 or len(taud)<100: return None
    ya=np.array([r["err"] for r in taud])
    s_score=np.array([r["score"] for r in taud])
    s_szlin=-LinearRegression().fit(Xof(cal,["score","log_ar","log_sqrt_area"]),np.array([r["err"] for r in cal])).predict(Xof(taud,["score","log_ar","log_sqrt_area"]))
    s_geo=-fitG(cal,GEO).predict(Xof(taud,GEO))
    s_proxy=-np.array([r["local_angle_consistency"] for r in taud])   # standalone GT-free proxy
    s_src=-fitG(cal,RC).predict(Xof(taud,RC))                          # source-supervised + target GT-free inference
    def M(s): nr=nrc_auc(s,ya); return (round(nr["nrc_auc"],4),round(nr["aurc_model"],4),round(risk_at_coverage(s,ya,0.7),3),round(risk_at_coverage(s,ya,0.9),3))
    out={"mode":mode,"target":f"{target[0]}/{target[1]}({target[2]})","n_audit":len(taud),"uses_target_GT":False}
    for nm,s in (("score_only",s_score),("score_ar_size_linear",s_szlin),("geometry_selector",s_geo),("standalone_tta_proxy",s_proxy),("source_supervised_targetGTfree",s_src)):
        nrcv,aurc,r70,r90=M(s); out[f"NRC_{nm}"]=nrcv; out[f"AURC_{nm}"]=aurc; out[f"R70_{nm}"]=r70
    out["src_beats_sizelin_ci"]=ci_beats(s_szlin,s_src,ya); out["src_beats_geo_ci"]=ci_beats(s_geo,s_src,ya)
    out["src_beats_sizelin"]=bool(out["src_beats_sizelin_ci"][0]>0); out["src_beats_geo"]=bool(out["src_beats_geo_ci"][0]>0)
    out["proxy_beats_score"]=bool(out["NRC_standalone_tta_proxy"]<out["NRC_score_only"]); out["proxy_below_random"]=bool(out["NRC_standalone_tta_proxy"]<1.0)
    return out
fams=set(c[2] for c in DATA); dss=set(c[0] for c in DATA)
rows=[]
# leave-detector: hold out each family
for held in fams:
    src=[c for c in DATA if c[2]!=held]
    for tgt in [c for c in DATA if c[2]==held]:
        m=evaluate("leave_detector",src,tgt)
        if m: rows.append(m); print(f"LDET hold {held} -> {m['target']}: src={m['NRC_source_supervised_targetGTfree']} szlin={m['NRC_score_ar_size_linear']} geo={m['NRC_geometry_selector']} proxy={m['NRC_standalone_tta_proxy']} beats_sz={m['src_beats_sizelin']}",flush=True)
    hb(f"leave_detector hold {held} done")
# leave-dataset: hold out each dataset
for held in dss:
    src=[c for c in DATA if c[0]!=held]
    for tgt in [c for c in DATA if c[0]==held]:
        m=evaluate("leave_dataset",src,tgt)
        if m: rows.append(m); print(f"LD hold {held} -> {m['target']}: src={m['NRC_source_supervised_targetGTfree']} szlin={m['NRC_score_ar_size_linear']} beats_sz={m['src_beats_sizelin']}",flush=True)
    hb(f"leave_dataset hold {held} done")
cols=["mode","target","n_audit","uses_target_GT","NRC_score_only","NRC_score_ar_size_linear","NRC_geometry_selector","NRC_standalone_tta_proxy","NRC_source_supervised_targetGTfree",
      "AURC_source_supervised_targetGTfree","R70_source_supervised_targetGTfree","src_beats_sizelin","src_beats_geo","src_beats_sizelin_ci","proxy_beats_score","proxy_below_random"]
with open(f"{OUT}/nonpsc_deployable_leave_star_047.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
# summary
ps=sum(1 for r in rows if r["src_beats_sizelin"]); n=len(rows)
fam_pass=set(r["target"].split("(")[-1].rstrip(")") for r in rows if r["src_beats_sizelin"])
ds_pass=set(r["target"].split("/")[0] for r in rows if r["src_beats_sizelin"])
summ={"n_evals":n,"src_beats_sizelin":ps,"frac":round(ps/n,3) if n else 0,"families_pass":sorted(fam_pass),"datasets_pass":sorted(ds_pass),
      "proxy_beats_score":sum(1 for r in rows if r["proxy_beats_score"]),"proxy_below_random":sum(1 for r in rows if r["proxy_below_random"]),
      "failures":[r["target"]+"/"+r["mode"] for r in rows if not r["src_beats_sizelin"]]}
json.dump(summ,open(f"{OUT}/nonpsc_leave_star_summary_047.json","w"),indent=2)
hb("ALL DONE"); print("LEAVESTAR DONE",json.dumps(summ),flush=True)
