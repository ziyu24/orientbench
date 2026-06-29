import json,os,math,csv,sys,hashlib
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import match_dataset
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.gv import gv_obliquity
from orientbench.data.splits import assign_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
SC="/dev/shm/cqc/orientbench/predictions"; ART=f"{ROOT}/measure_fix_v2/artifacts/features"; OUT=f"{ROOT}/measure_fix_v2/reports"
os.makedirs(ART,exist_ok=True)
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
rng=np.random.RandomState(11)
def build(ds,bid):
    cache=f"{ART}/{ds}_{bid}.jsonl"
    if os.path.isfile(cache): return [json.loads(l) for l in open(cache)]
    sch=fs(ds,bid); g=gtp(ds)
    if not(sch and g): return None
    preds=[json.loads(l) for l in open(sch)]; gts=[json.loads(l) for l in open(g)]
    gids={x["image_id"] for x in gts}; pset=[p for p in preds if p.get("score",1)>=0.30 and p["image_id"] in gids]
    m=match_dataset(pset,gts); rec=[]
    for pi,gj,_ in m["matched_pairs"]:
        p,gg=pset[pi],gts[gj]; c=angle_error_contract(p["obb_w"],p["obb_h"],p["obb_theta"],gg["obb_w"],gg["obb_h"],gg["obb_theta"])
        if c["near_square"]: continue
        e=c["angle_error_canonical_longside"]
        if not math.isfinite(e): continue
        w,h=gg["obb_w"],gg["obb_h"]; ar=max(w,h)/max(1e-6,min(w,h))
        if ar<1.6: continue  # deployable uses primary well-defined
        gv=gv_obliquity(p["obb_w"],p["obb_h"],p["obb_theta"]).get("gv_obb_needed",0.0)
        if not math.isfinite(gv): gv=0.0
        rec.append({"img":p["image_id"],"score":p["score"],"log_ar":math.log(ar),
                    "log_sqrt_area":math.log(math.sqrt(max(1.0,w*h))),"gv_obb_needed":gv,"w":p["obb_w"],"h":p["obb_h"],"err":e,
                    "split":assign_split(p["img"] if False else p["image_id"])})
    with open(cache,"w") as f:
        for r in rec: f.write(json.dumps(r)+"\n")
    return rec
DATA={c:build(*c[:2]) for c in CELLS}
DATA={k:v for k,v in DATA.items() if v}
for k,v in DATA.items(): print(f"feat {k[0]}/{k[1]} n={len(v)}",flush=True)
def Xof(recs,fs): return np.array([[r[f] for f in fs] for r in recs])
def fit(cal):
    yc=np.array([r["err"] for r in cal])
    lin=LinearRegression().fit(Xof(cal,["score","log_ar","log_sqrt_area"]),yc)
    gbr=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0).fit(Xof(cal,FEATS),yc)
    return lin,gbr
def nrc(s,r): return nrc_auc(s,r)["nrc_auc"]
def pdelta(sa,sb,r,B=400):  # sa - sb
    n=len(r); d=[]
    for _ in range(B):
        i=rng.randint(0,n,n); v=nrc(sa[i],r[i])-nrc(sb[i],r[i])
        if math.isfinite(v): d.append(v)
    return round(float(np.median(d)),4),[round(float(np.percentile(d,2.5)),4),round(float(np.percentile(d,97.5)),4)]
rows=[]
def evaluate(name,train_cells,target_cell):
    # train on ALL of train_cells (their full feature rows = source; no target GT used in training)
    cal=[r for c in train_cells for r in DATA[c]]
    tgt=DATA[target_cell]
    # within-target oracle (G2DP, for retained-fraction ref): train on target D_cal
    tcal=[r for r in tgt if r["split"]=="D_cal"]; taud=[r for r in tgt if r["split"]=="D_audit"]
    if len(cal)<200 or len(taud)<100: return
    lin_s,gbr_s=fit(cal)  # source-trained (deployable)
    ya=np.array([r["err"] for r in taud])
    s_score=np.array([r["score"] for r in taud])
    s_lin=-lin_s.predict(Xof(taud,["score","log_ar","log_sqrt_area"]))
    s_nl=-gbr_s.predict(Xof(taud,FEATS))
    nrc_score,nrc_lin,nrc_nl=nrc(s_score,ya),nrc(s_lin,ya),nrc(s_nl,ya)
    # oracle within-target
    orc=None
    if len(tcal)>=100:
        _,gbr_t=fit(tcal); orc=nrc(-gbr_t.predict(Xof(taud,FEATS)),ya)
    d_sl,ci_sl=pdelta(s_lin,s_nl,ya)      # size_linear - nl  (>0 => nl better)
    d_so,ci_so=pdelta(s_score,s_nl,ya)    # score_only - nl
    rows.append({"mode":name,"target":f"{target_cell[0]}/{target_cell[1]}({target_cell[2]})","n_audit":len(taud),
                 "uses_target_GT_in_train":False,"NRC_score_only":round(nrc_score,4),"NRC_size_linear":round(nrc_lin,4),
                 "NRC_nonlinear_deployed":round(nrc_nl,4),"NRC_oracle_within_target":round(orc,4) if orc else None,
                 "delta_sizelin_minus_nl":d_sl,"ci_sl":ci_sl,"nl_beats_sizelin":bool(ci_sl[0]>0),
                 "delta_scoreonly_minus_nl":d_so,"ci_so":ci_so,"nl_beats_scoreonly":bool(ci_so[0]>0)})
    print(f"{name} -> {target_cell[0]}/{target_cell[1]}: nl={nrc_nl:.3f} sizelin={nrc_lin:.3f} score={nrc_score:.3f} oracle={orc} nl>sizelin={ci_sl[0]>0} nl>score={ci_so[0]>0}",flush=True)
PSC=[c for c in DATA if c[2]=="psc"]; NONP=[c for c in DATA if c[2]!="psc"]
# leave-dataset (PSC): hold out each PSC dataset
for held in PSC:
    evaluate("leave_dataset",[c for c in PSC if c!=held],held)
# leave-detector: train PSC, test non-PSC; and train non-PSC, test PSC
for tgt in NONP:
    evaluate("leave_detector_psc2nonpsc",PSC,tgt)
for tgt in PSC:
    evaluate("leave_detector_nonpsc2psc",NONP,tgt)
cols=["mode","target","n_audit","uses_target_GT_in_train","NRC_score_only","NRC_size_linear","NRC_nonlinear_deployed","NRC_oracle_within_target","delta_sizelin_minus_nl","ci_sl","nl_beats_sizelin","delta_scoreonly_minus_nl","ci_so","nl_beats_scoreonly"]
with open(f"{OUT}/deployable_results_039.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
json.dump(rows,open(f"{OUT}/deployable_results_039.json","w"),indent=2,default=str)
# persist manifest
man=[{"cell":f"{k[0]}/{k[1]}","detector":k[2],"feature_table":f"{ART}/{k[0]}_{k[1]}.jsonl","n_rows":len(v),
      "sha256":hashlib.sha256(open(f"{ART}/{k[0]}_{k[1]}.jsonl","rb").read()).hexdigest()} for k,v in DATA.items()]
json.dump({"note":"v2 matched feature tables (ar>=1.6 well-defined); /dev/shm source non-persistent; these persisted to measure_fix_v2/artifacts (gitignored)","tables":man},
          open(f"{OUT}/v2_feature_persistence_manifest_039.json","w"),indent=2)
print("DEPLOY DONE",len(rows),flush=True)
