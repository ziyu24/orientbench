import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
ART=f"{ROOT}/measure_fix_v2/artifacts/features_v2"; OUT=f"{ROOT}/measure_fix_v2/reports"
GEO=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]
ROUTEC=GEO+["local_angle_consistency"]
rng=np.random.RandomState(41)
CELLS=[("FAIR1M-v1.0","24","psc"),("SODA-A","23","psc"),("DIOR-R","22","psc"),
       ("DIOR-R","3","orcnn"),("DIOR-R","10","lsknet"),("DOTA-v1.0","20","psc")]
DATA={c:[json.loads(l) for l in open(f"{ART}/{c[0]}_{c[1]}.jsonl")] for c in CELLS if os.path.isfile(f"{ART}/{c[0]}_{c[1]}.jsonl")}
def Xof(r,fs): return np.array([[x[f] for f in fs] for x in r])
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def fit_lin(cal,fs): 
    return LinearRegression().fit(Xof(cal,fs),np.array([r["err"] for r in cal]))
def fit_gbr(cal,fs):
    return GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,fs),np.array([r["err"] for r in cal]))
def pdelta(sa,sb,r,B=400):
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(sa[i],r[i])-nrc(sb[i],r[i])
        if math.isfinite(v): d.append(v)
    return round(float(np.median(d)),4),[round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
def evalcell(mode,train_cells,target):
    cal=[r for c in train_cells for r in DATA[c] if r["split"]=="D_cal"]
    taud=[r for r in DATA[target] if r["split"]=="D_audit"]; tcal=[r for r in DATA[target] if r["split"]=="D_cal"]
    if len(cal)<200 or len(taud)<100: return None
    ya=np.array([r["err"] for r in taud])
    s_score=np.array([r["score"] for r in taud])
    s_szlin=-fit_lin(cal,["score","log_ar","log_sqrt_area"]).predict(Xof(taud,["score","log_ar","log_sqrt_area"]))
    s_geo=-fit_gbr(cal,GEO).predict(Xof(taud,GEO))
    s_rc=-fit_gbr(cal,ROUTEC).predict(Xof(taud,ROUTEC))
    orc=None
    if len(tcal)>=100: orc=nrc(-fit_gbr(tcal,ROUTEC).predict(Xof(taud,ROUTEC)),ya)
    nrc_sc,nrc_sz,nrc_geo,nrc_rc=nrc(s_score,ya),nrc(s_szlin,ya),nrc(s_geo,ya),nrc(s_rc,ya)
    d_sz,ci_sz=pdelta(s_szlin,s_rc,ya)       # sizelin - routeC (>0 routeC better)
    d_geo,ci_geo=pdelta(s_geo,s_rc,ya)       # geo - routeC (>0 routeC better than geo-only)
    ret=((nrc_sc-nrc_rc)/(nrc_sc-orc)) if (orc and nrc_sc-orc>0.02) else None
    order=np.argsort(-s_rc); k=max(1,int(0.7*len(s_rc))); ret_e=ya[order[:k]]
    return {"mode":mode,"target":f"{target[0]}/{target[1]}({target[2]})","n_audit":len(taud),
            "NRC_score":round(nrc_sc,4),"NRC_sizelin":round(nrc_sz,4),"NRC_geo_selector":round(nrc_geo,4),"NRC_routeC":round(nrc_rc,4),"NRC_oracle":round(orc,4) if orc else None,
            "AURC_rc":round(nrc_auc(s_rc,ya)["aurc_model"],4),"Risk@70":round(risk_at_coverage(s_rc,ya,0.7),3),"Risk@90":round(risk_at_coverage(s_rc,ya,0.9),3),
            "p90":round(float(np.percentile(ret_e,90)),2),"p95":round(float(np.percentile(ret_e,95)),2),"p99":round(float(np.percentile(ret_e,99)),2),
            "delta_sizelin_minus_routeC":d_sz,"ci_sz_lo":ci_sz[0],"routeC_beats_sizelin":bool(ci_sz[0]>0),
            "delta_geo_minus_routeC":d_geo,"ci_geo_lo":ci_geo[0],"routeC_beats_geo":bool(ci_geo[0]>0),
            "oracle_gain_retained":round(ret,3) if ret else None,"uses_target_GT":False,"is_dota_negctrl":target[0]=="DOTA-v1.0"}
PSC=[c for c in DATA if c[2]=="psc"]; NONP=[c for c in DATA if c[2]!="psc"]
DS={}
for c in DATA: DS.setdefault(c[0],[]).append(c)
rows=[]
for held in DS:
    src=[c for c in PSC if c[0]!=held]
    if src:
        for tgt in DS[held]:
            m=evalcell("leave_dataset",src,tgt)
            if m: rows.append(m); print(f"LD {m['target']}: routeC={m['NRC_routeC']} sizelin={m['NRC_sizelin']} geo={m['NRC_geo_selector']} beats_sz={m['routeC_beats_sizelin']} beats_geo={m['routeC_beats_geo']} ret={m['oracle_gain_retained']}",flush=True)
for tgt in NONP:
    m=evalcell("leave_detector_psc2nonpsc",PSC,tgt)
    if m: rows.append(m); print(f"LDET {m['target']}: routeC={m['NRC_routeC']} beats_sz={m['routeC_beats_sizelin']} beats_geo={m['routeC_beats_geo']} ret={m['oracle_gain_retained']}",flush=True)
for tgt in PSC:
    m=evalcell("leave_detector_nonpsc2psc",NONP,tgt)
    if m: rows.append(m); print(f"LDET2 {m['target']}: routeC={m['NRC_routeC']} beats_sz={m['routeC_beats_sizelin']} ret={m['oracle_gain_retained']}",flush=True)
cols=list(rows[0].keys())
with open(f"{OUT}/route_c_tta_proxy_results_041.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
# also write feature table summary (tta_proxy_features)
with open(f"{OUT}/tta_proxy_features_041.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["cell","n","mean_local_angle_consistency_rad","feature_set"])
    for c in CELLS:
        if c in DATA:
            lac=np.mean([r["local_angle_consistency"] for r in DATA[c]])
            w.writerow([f"{c[0]}/{c[1]}",len(DATA[c]),round(float(lac),4),"score+geometry+local_angle_consistency(GT-free)"])
nd=[m for m in rows if not m["is_dota_negctrl"]]
ps_sz=sum(1 for m in nd if m["routeC_beats_sizelin"]); ps_geo=sum(1 for m in nd if m["routeC_beats_geo"])
rets=[m["oracle_gain_retained"] for m in nd if m["oracle_gain_retained"] is not None]
summ={"n_nondota":len(nd),"routeC_beats_sizelin_nondota":ps_sz,"routeC_beats_geo_nondota":ps_geo,
      "mean_retained_nondota":round(float(np.mean(rets)),3),"median_retained_nondota":round(float(np.median(rets)),3),
      "dota_negctrl":[{"target":m["target"],"mode":m["mode"],"routeC_beats_sizelin":m["routeC_beats_sizelin"],"NRC_routeC":m["NRC_routeC"],"oracle":m["NRC_oracle"]} for m in rows if m["is_dota_negctrl"]]}
json.dump(summ,open(f"{OUT}/route_c_summary_041.json","w"),indent=2)
print("ROUTEC DONE",json.dumps(summ),flush=True)
