import json,os,math,csv,sys
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
ART=f"{ROOT}/measure_fix_v2/artifacts/features_real_tta"; OUT=f"{ROOT}/measure_fix_v2/reports"
GEO=["score","log_ar","log_sqrt_area","gv_obb_needed","w","h"]
RTTA=GEO+["real_tta_consistency"]
rng=np.random.RandomState(42)
CELLS=[("DIOR-R","3","orcnn"),("DIOR-R","22","psc"),("DIOR-R","10","lsknet")]
DATA={c:[json.loads(l) for l in open(f"{ART}/{c[0]}_{c[1]}.jsonl")] for c in CELLS if os.path.isfile(f"{ART}/{c[0]}_{c[1]}.jsonl")}
def Xof(r,fs): return np.array([[x[f] for f in fs] for x in r])
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def fitL(cal,fs): return LinearRegression().fit(Xof(cal,fs),np.array([r["err"] for r in cal]))
def fitG(cal,fs): return GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,fs),np.array([r["err"] for r in cal]))
def pdelta(sa,sb,r,B=400):
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(sa[i],r[i])-nrc(sb[i],r[i])
        if math.isfinite(v): d.append(v)
    return round(float(np.median(d)),4),[round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
rows=[]
for tgt in list(DATA.keys()):
    src=[c for c in DATA if c!=tgt]
    cal=[r for c in src for r in DATA[c] if r["split"]=="D_cal"]
    taud=[r for r in DATA[tgt] if r["split"]=="D_audit"]; tcal=[r for r in DATA[tgt] if r["split"]=="D_cal"]
    if len(cal)<200 or len(taud)<100: print("skip",tgt,flush=True); continue
    ya=np.array([r["err"] for r in taud])
    s_score=np.array([r["score"] for r in taud])
    s_szlin=-fitL(cal,["score","log_ar","log_sqrt_area"]).predict(Xof(taud,["score","log_ar","log_sqrt_area"]))
    s_geo=-fitG(cal,GEO).predict(Xof(taud,GEO))
    s_rtta=-fitG(cal,RTTA).predict(Xof(taud,RTTA))
    orc=nrc(-fitG(tcal,RTTA).predict(Xof(taud,RTTA)),ya) if len(tcal)>=100 else None
    nrc_sc,nrc_sz,nrc_geo,nrc_rt=nrc(s_score,ya),nrc(s_szlin,ya),nrc(s_geo,ya),nrc(s_rtta,ya)
    d_sz,ci_sz=pdelta(s_szlin,s_rtta,ya); d_geo,ci_geo=pdelta(s_geo,s_rtta,ya)
    ret=((nrc_sc-nrc_rt)/(nrc_sc-orc)) if (orc and nrc_sc-orc>0.02) else None
    order=np.argsort(-s_rtta); k=max(1,int(0.7*len(s_rtta))); rete=ya[order[:k]]
    rows.append({"mode":"leave_detector_DIOR","target":f"{tgt[0]}/{tgt[1]}({tgt[2]})","n_audit":len(taud),
        "NRC_score":round(nrc_sc,4),"NRC_sizelin":round(nrc_sz,4),"NRC_geo":round(nrc_geo,4),"NRC_realTTA":round(nrc_rt,4),"NRC_oracle":round(orc,4) if orc else None,
        "AURC_realTTA":round(nrc_auc(s_rtta,ya)["aurc_model"],4),"Risk@70":round(risk_at_coverage(s_rtta,ya,0.7),3),"Risk@90":round(risk_at_coverage(s_rtta,ya,0.9),3),
        "p90":round(float(np.percentile(rete,90)),2),"p95":round(float(np.percentile(rete,95)),2),"p99":round(float(np.percentile(rete,99)),2),
        "delta_sizelin_minus_realTTA":d_sz,"ci_sz_lo":ci_sz[0],"realTTA_beats_sizelin":bool(ci_sz[0]>0),
        "delta_geo_minus_realTTA":d_geo,"ci_geo_lo":ci_geo[0],"realTTA_beats_geo":bool(ci_geo[0]>0),
        "oracle_gain_retained":round(ret,3) if ret else None,"uses_target_GT":False})
    print(f"{tgt[0]}/{tgt[1]}: realTTA={nrc_rt:.4f} sizelin={nrc_sz:.4f} geo={nrc_geo:.4f} beats_sz={ci_sz[0]>0} beats_geo={ci_geo[0]>0} ret={ret}",flush=True)
cols=list(rows[0].keys())
with open(f"{OUT}/real_tta_selector_results_042.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
ps=sum(1 for r in rows if r["realTTA_beats_sizelin"]); pg=sum(1 for r in rows if r["realTTA_beats_geo"])
rets=[r["oracle_gain_retained"] for r in rows if r["oracle_gain_retained"] is not None]
summ={"n":len(rows),"realTTA_beats_sizelin":ps,"realTTA_beats_geo":pg,"mean_retained":round(float(np.mean(rets)),3) if rets else None}
json.dump(summ,open(f"{OUT}/real_tta_summary_042.json","w"),indent=2)
print("RTTA_SEL DONE",json.dumps(summ),flush=True)
