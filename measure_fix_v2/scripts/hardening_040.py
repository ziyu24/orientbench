import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
ART=f"{ROOT}/measure_fix_v2/artifacts/features"; OUT=f"{ROOT}/measure_fix_v2/reports"
FEATS=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]
rng=np.random.RandomState(23)
CELLS=[("DOTA-v1.0","20","psc"),("DIOR-R","22","psc"),("FAIR1M-v1.0","24","psc"),("SODA-A","23","psc"),
       ("SODA-A","4","orcnn"),("DIOR-R","3","orcnn"),("DIOR-R","10","lsknet")]
DATA={}
for ds,bid,det in CELLS:
    p=f"{ART}/{ds}_{bid}.jsonl"
    if os.path.isfile(p): DATA[(ds,bid,det)]=[json.loads(l) for l in open(p)]
def Xof(r,fs): return np.array([[x[f] for f in fs] for x in r])
def fit(cal):
    yc=np.array([r["err"] for r in cal])
    lin=LinearRegression().fit(Xof(cal,["score","log_ar","log_sqrt_area"]),yc)
    gbr=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,FEATS),yc)
    return lin,gbr
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def pdelta(sa,sb,r,B=400):
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(sa[i],r[i])-nrc(sb[i],r[i])
        if math.isfinite(v): d.append(v)
    return round(float(np.median(d)),4),[round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
def full_metrics(name,train_cells,target):
    cal=[r for c in train_cells for r in DATA[c] if r["split"]=="D_cal"]
    taud=[r for r in DATA[target] if r["split"]=="D_audit"]; tcal=[r for r in DATA[target] if r["split"]=="D_cal"]
    if len(cal)<200 or len(taud)<100: return None
    lin,gbr=fit(cal); ya=np.array([r["err"] for r in taud])
    s_score=np.array([r["score"] for r in taud]); s_lin=-lin.predict(Xof(taud,["score","log_ar","log_sqrt_area"])); s_nl=-gbr.predict(Xof(taud,FEATS))
    def aftersel(s):
        order=np.argsort(-s); k=max(1,int(0.7*len(s))); ret=ya[order[:k]]
        return [round(float(np.percentile(ret,q)),2) for q in (90,95,99)]
    nrc_sc,nrc_li,nrc_nl=nrc(s_score,ya),nrc(s_lin,ya),nrc(s_nl,ya)
    orc=None
    if len(tcal)>=100: _,g=fit(tcal); orc=nrc(-g.predict(Xof(taud,FEATS)),ya)
    d_sl,ci_sl=pdelta(s_lin,s_nl,ya); d_so,ci_so=pdelta(s_score,s_nl,ya)
    ret_frac=((nrc_sc-nrc_nl)/(nrc_sc-orc)) if (orc and nrc_sc-orc>0.02) else None
    p=aftersel(s_nl)
    return {"mode":name,"target":f"{target[0]}/{target[1]}({target[2]})","n_audit":len(taud),
            "NRC_score":round(nrc_sc,4),"NRC_size_linear":round(nrc_li,4),"NRC_deployed_nl":round(nrc_nl,4),"NRC_oracle":round(orc,4) if orc else None,
            "AURC_nl":round(nrc_auc(s_nl,ya)["aurc_model"],4),"Risk@70":round(risk_at_coverage(s_nl,ya,0.7),3),"Risk@90":round(risk_at_coverage(s_nl,ya,0.9),3),
            "p90_sel":p[0],"p95_sel":p[1],"p99_sel":p[2],"delta_sizelin_minus_nl":d_sl,"ci_sl_lo":ci_sl[0],"ci_sl_hi":ci_sl[1],"nl_beats_sizelin":bool(ci_sl[0]>0),
            "delta_score_minus_nl":d_so,"ci_so_lo":ci_so[0],"nl_beats_score":bool(ci_so[0]>0),"oracle_gain_retained":round(ret_frac,3) if ret_frac else None,"uses_target_GT":False}
PSC=[c for c in DATA if c[2]=="psc"]; NONP=[c for c in DATA if c[2]!="psc"]
DS={}
for c in DATA: DS.setdefault(c[0],[]).append(c)
# leave-dataset (all cells of held-out dataset as targets; train on other datasets' PSC)
ld=[]
for held_ds in DS:
    src=[c for c in PSC if c[0]!=held_ds]
    if not src: continue
    for tgt in DS[held_ds]:
        m=full_metrics("leave_dataset",src,tgt)
        if m: ld.append(m); print(f"LD {tgt[0]}/{tgt[1]}: nl={m['NRC_deployed_nl']} sizelin={m['NRC_size_linear']} beats_sizelin={m['nl_beats_sizelin']} ret={m['oracle_gain_retained']}",flush=True)
# leave-detector
lde=[]
for tgt in NONP:
    m=full_metrics("leave_detector_psc2nonpsc",PSC,tgt)
    if m: lde.append(m); print(f"LDET psc->{tgt[2]} {tgt[0]}/{tgt[1]}: nl={m['NRC_deployed_nl']} beats_sizelin={m['nl_beats_sizelin']} ret={m['oracle_gain_retained']}",flush=True)
for tgt in PSC:
    m=full_metrics("leave_detector_nonpsc2psc",NONP,tgt)
    if m: lde.append(m); print(f"LDET nonpsc->{tgt[0]}/{tgt[1]}: nl={m['NRC_deployed_nl']} beats_sizelin={m['nl_beats_sizelin']} ret={m['oracle_gain_retained']}",flush=True)
cols=list(ld[0].keys())
for fn,rows in (("leave_dataset_hardening_040",ld),("leave_detector_hardening_040",lde)):
    with open(f"{OUT}/{fn}.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
# DOTA #20 failure analysis: compare distributions
da=[]
allc=PSC
for c in allc:
    r=DATA[c]; aud=[x for x in r if x["split"]=="D_audit"]; cal=[x for x in r if x["split"]=="D_cal"]
    errs=np.array([x["err"] for x in aud]); ar=np.array([math.exp(x["log_ar"]) for x in aud]); sz=np.array([x["log_sqrt_area"] for x in aud]); sc=np.array([x["score"] for x in aud])
    # within-target oracle gain
    orc=None
    if len(cal)>=100:
        _,g=fit(cal); orc=nrc(-g.predict(Xof(aud,FEATS)),errs)
    nrc_sc=nrc(sc,errs)
    from scipy.stats import spearmanr
    da.append({"cell":f"{c[0]}/{c[1]}","n_audit":len(aud),"n_cal":len(cal),"median_err":round(float(np.median(errs)),3),
               "ar_median":round(float(np.median(ar)),2),"log_sqrtarea_median":round(float(np.median(sz)),2),
               "NRC_score":round(nrc_sc,4),"oracle_within_nl":round(orc,4) if orc else None,
               "oracle_gain":round(nrc_sc-orc,4) if orc else None,"spearman_score_err":round(float(spearmanr(sc,errs)[0]),4)})
    print(f"DOTAanalysis {c[0]}/{c[1]}: n={len(aud)} oracle_gain={round(nrc_sc-(orc or nrc_sc),4)} spearman_score_err={round(float(spearmanr(sc,errs)[0]),4)} ar_med={round(float(np.median(ar)),2)}",flush=True)
with open(f"{OUT}/dota20_failure_analysis_040.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(da[0].keys())); w.writeheader(); w.writerows(da)
# summary
all_unseen=ld+lde
ps=sum(1 for m in all_unseen if m["nl_beats_sizelin"]); n=len(all_unseen)
rets=[m["oracle_gain_retained"] for m in all_unseen if m["oracle_gain_retained"] is not None]
summ={"n_unseen":n,"nl_beats_sizelin":ps,"frac":round(ps/n,3),"mean_retained":round(float(np.mean(rets)),3),"median_retained":round(float(np.median(rets)),3),
      "leave_dataset_pass":sum(1 for m in ld if m["nl_beats_sizelin"]),"leave_dataset_n":len(ld),
      "leave_detector_pass":sum(1 for m in lde if m["nl_beats_sizelin"]),"leave_detector_n":len(lde),
      "failures":[m["target"]+"/"+m["mode"] for m in all_unseen if not m["nl_beats_sizelin"]]}
json.dump(summ,open(f"{OUT}/hardening_summary_040.json","w"),indent=2)
print("HARDEN DONE",json.dumps(summ),flush=True)
