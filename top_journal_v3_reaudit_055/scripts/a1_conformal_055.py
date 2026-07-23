"""A1 — P2 conformal risk control strengthening (055).
Real 052 matched tables; frozen masked protocol (ar>=1.6); frozen D_cal/D_audit
(field d_cal_daudit_split_flag). Split-conformal / CRC style:
  calibrate threshold on D_cal, audit empirical coverage/risk/violation on D_audit.
No training of detectors, no threshold/split change. GBR selector trains only on
D_cal features (source-supervised) -> allowed.
Outputs: p2_alpha_scan / p2_tail_conformal / p2_conformal_score_menu /
p2_mondrian_ar_conformal (055).
"""
import json, csv, sys, os, math
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from sklearn.ensemble import GradientBoostingRegressor
OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
TTA=f"{ROOT}/top_journal_v3/reports/tta_circular_variance_full_052.csv"
PM=f"{ROOT}/top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv"
AR_MASK=1.6; TAIL_DEG=5.0   # 5deg tail: base rate high enough that guarantees force abstention (not empty)
CELLS=[("DIOR-R","22","PSC","DIOR#22"),("FAIR1M-v1.0","24","PSC","FAIR1M#24"),
       ("SODA-A","23","PSC","SODA#23"),("DIOR-R","3","ORCNN","DIOR#3"),
       ("DIOR-R","61","RTMDet","DIOR#61"),("SODA-A","4","ORCNN","SODA#4")]

def load_cell(ds,bid):
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    d=dict(img=[r["image_id"] for r in recs], pid=[r["pred_id"] for r in recs],
           score=np.array([r["score"] for r in recs]),
           err=np.array([r["angle_error"] for r in recs]),
           ar=np.array([r["aspect_ratio"] for r in recs]),
           size=np.array([r["size"] for r in recs]),
           split=np.array([r["d_cal_daudit_split_flag"] for r in recs]))
    return d

WANT=set(f"{ds}/{bid}" for ds,bid,_,_ in CELLS)
def index_csv(path, valcol):
    """Single pass: {cell_id: {(img,pid): float(valcol)}} for wanted cells."""
    idx={}
    with open(path) as fh:
        r=csv.reader(fh); header=next(r)
        ci=header.index("cell_id"); ii=header.index("image_id"); pi=header.index("pred_id"); vi=header.index(valcol)
        for row in r:
            if row[ci] not in WANT: continue
            try: idx.setdefault(row[ci],{})[(row[ii],int(row[pi]))]=float(row[vi])
            except: pass
    return idx
print("indexing TTA...",flush=True); TTA_IDX=index_csv(TTA,"circular_variance")
print("indexing PM...",flush=True);  PM_IDX=index_csv(PM,"phase_mod")
def load_tta(ds,bid,keyset): return TTA_IDX.get(f"{ds}/{bid}",{})
def load_pm(cellid,keyset):  return PM_IDX.get(cellid,{})

def conformal_threshold(cal_score, cal_loss, alpha, slack=0.0):
    """Largest-coverage score threshold t s.t. mean(loss over cal kept by score>=t)+slack<=alpha.
    Returns (t, cal_cov, cal_risk). Sweep thresholds at sorted score values."""
    order=np.argsort(-cal_score, kind="stable")
    s=cal_score[order]; l=cal_loss[order]
    csum=np.cumsum(l); ks=np.arange(1,len(l)+1); running=csum/ks
    ok=running+slack<=alpha
    if not ok.any(): return None,0.0,float("nan")
    k=np.max(np.where(ok)[0])  # largest k (most coverage) satisfying
    return s[k], (k+1)/len(l), running[k]

def audit(aud_score, aud_loss, t):
    keep=aud_score>=t
    if keep.sum()==0: return 0.0,float("nan"),0
    return float(keep.mean()), float(aud_loss[keep].mean()), int(keep.sum())

rows_alpha=[]; rows_tail=[]; rows_menu=[]; rows_mond=[]; rows_shift=[]; CACHE={}
for ds,bid,fam,name in CELLS:
    d=load_cell(ds,bid)
    m=d["ar"]>=AR_MASK
    sc=d["score"][m]; er=d["err"][m]; ar=d["ar"][m]; sz=d["size"][m]; sp=d["split"][m]
    imgs=[d["img"][i] for i in range(len(d["img"])) if m[i]]
    pids=[d["pid"][i] for i in range(len(d["pid"])) if m[i]]
    cal=sp=="D_cal"; aud=sp=="D_audit"
    n_cal=int(cal.sum()); n_aud=int(aud.sum())
    base_risk=float(er[aud].mean())
    base_tail=float((er[aud]>TAIL_DEG).mean())
    # ---- A1-1 mean-risk alpha scan (detection score); alpha spans BELOW base to force abstention ----
    for alpha in [1.0,1.5,2.0,2.5,3.0]:
        t,ccov,crisk=conformal_threshold(sc[cal], er[cal], alpha)
        if t is None:
            rows_alpha.append(dict(cell=name,alpha_deg=alpha,achievable=False,coverage=0,emp_risk="",
                                   abstention=1.0,violation="",n_cal=n_cal,n_audit=n_aud,base_risk=round(base_risk,3)))
            continue
        acov,arisk,_=audit(sc[aud], er[aud], t)
        rows_alpha.append(dict(cell=name,alpha_deg=alpha,achievable=True,coverage=round(acov,4),
                               emp_risk=round(arisk,3),abstention=round(1-acov,4),
                               violation=bool(arisk>alpha),n_cal=n_cal,n_audit=n_aud,base_risk=round(base_risk,3)))
    # ---- A1-2 tail conformal: control P(err>5deg)<=alpha; alpha below base_tail => real abstention ----
    tail_loss=(er>TAIL_DEG).astype(float)
    for alpha in [0.02,0.03,0.05,0.08,0.10]:
        hoeff=math.sqrt(math.log(1/0.1)/(2*max(n_cal,1)))
        t,ccov,crisk=conformal_threshold(sc[cal], tail_loss[cal], alpha, slack=hoeff)
        if t is None:
            rows_tail.append(dict(cell=name,alpha=alpha,achievable=False,coverage=0,emp_tail_rate="",
                                  violation="",hoeffding=round(hoeff,4),n_cal=n_cal,n_audit=n_aud))
            continue
        acov,arisk,_=audit(sc[aud], tail_loss[aud], t)
        rows_tail.append(dict(cell=name,tail_deg=TAIL_DEG,base_tail=round(base_tail,4),alpha=alpha,achievable=True,
                              coverage=round(acov,4),abstention=round(1-acov,4),
                              emp_tail_rate=round(arisk,4),violation=bool(arisk>alpha),
                              hoeffding=round(hoeff,4),n_cal=n_cal,n_audit=n_aud))
    # ---- A1-3 score menu: STRICT guarantee P(err>5)<=0.03 (< base_tail) => coverage differentiates scores ----
    MENU_ALPHA=0.03
    keyset=set(zip(imgs,pids))
    scores_menu={"detection_score":sc}
    # geometry selector: GBR err ~ [score,log_ar,log_size] on D_cal
    X=np.column_stack([sc,np.log(ar),np.log(np.sqrt(sz)+1e-9)])
    gbr=GradientBoostingRegressor(n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.8,random_state=0)
    gbr.fit(X[cal], er[cal]); scores_menu["geometry_selector"]=-gbr.predict(X)
    # TTA circular variance (lower=better -> score=-cv)
    tta=load_tta(ds,bid,keyset)
    if len(tta)>0.5*len(imgs):
        cv=np.array([tta.get((imgs[i],pids[i]),np.nan) for i in range(len(imgs))])
        scores_menu["tta_neg_circular_var"]=-cv
    # phase_mod (PSC only)
    if fam=="PSC":
        pm=load_pm(f"{ds}/{bid}",keyset)
        if len(pm)>0.5*len(imgs):
            scores_menu["intrinsic_phase_mod"]=np.array([pm.get((imgs[i],pids[i]),np.nan) for i in range(len(imgs))])
    alpha=MENU_ALPHA; hoeff=math.sqrt(math.log(1/0.1)/(2*max(n_cal,1)))
    for sname,sv in scores_menu.items():
        valid=np.isfinite(sv)
        c2=cal&valid; a2=aud&valid
        if c2.sum()<200 or a2.sum()<100:
            rows_menu.append(dict(cell=name,score=sname,alpha=alpha,base_tail=round(base_tail,4),coverage="",emp_tail_rate="",note="insufficient_join")); continue
        t,_,_=conformal_threshold(sv[c2], tail_loss[c2], alpha, slack=hoeff)
        if t is None:
            rows_menu.append(dict(cell=name,score=sname,alpha=alpha,base_tail=round(base_tail,4),coverage=0,emp_tail_rate="",note="guarantee_infeasible")); continue
        acov,arisk,_=audit(sv[a2], tail_loss[a2], t)
        rows_menu.append(dict(cell=name,score=sname,alpha=alpha,base_tail=round(base_tail,4),coverage=round(acov,4),
                              emp_tail_rate=round(arisk,4),violation=bool(arisk>alpha),note=f"n_join={int(valid.sum())}"))
    # ---- A1-4 Mondrian by ar-bin (tail err>5 alpha=0.05), global-threshold vs ar-stratified threshold ----
    MOND_ALPHA=0.05
    bins=[(1.6,2.0),(2.0,3.0),(3.0,1e9)]
    tg,_,_=conformal_threshold(sc[cal], tail_loss[cal], MOND_ALPHA, slack=hoeff)  # one global thr from pooled D_cal
    for lo,hi in bins:
        bm=(ar>=lo)&(ar<hi)
        cb=cal&bm; ab=aud&bm
        if cb.sum()<100 or ab.sum()<50: continue
        ts,_,_=conformal_threshold(sc[cb], tail_loss[cb], MOND_ALPHA, slack=math.sqrt(math.log(1/0.1)/(2*cb.sum())))
        g_cov,g_rate,_=audit(sc[ab], tail_loss[ab], tg) if tg is not None else (0,float("nan"),0)
        s_cov,s_rate,_=audit(sc[ab], tail_loss[ab], ts) if ts is not None else (0,float("nan"),0)
        rows_mond.append(dict(cell=name,ar_bin=f"[{lo},{hi if hi<1e9 else 'inf'})",alpha=MOND_ALPHA,n_audit_bin=int(ab.sum()),
                              global_cov=round(g_cov,4),global_tail=round(g_rate,4) if g_rate==g_rate else "",
                              global_violation=bool(g_rate>MOND_ALPHA) if g_rate==g_rate else "",
                              strat_cov=round(s_cov,4),strat_tail=round(s_rate,4) if s_rate==s_rate else "",
                              strat_violation=bool(s_rate>MOND_ALPHA) if s_rate==s_rate else ""))
    # stash per-cell arrays for shift audit
    CACHE[name]=dict(sc_cal=sc[cal],tl_cal=tail_loss[cal],ar_cal=ar[cal],
                     sc_aud=sc[aud],tl_aud=tail_loss[aud],ar_aud=ar[aud],ds=ds)
    print(f"{name}: base_risk={base_risk:.2f} base_tail(>{TAIL_DEG:.0f})={base_tail:.3f} n_cal={n_cal} n_aud={n_aud} menu={list(scores_menu)}",flush=True)

def dump(path,rows):
    if not rows: return
    keys=list({k for r in rows for k in r})
    order=["cell","alpha_deg","alpha","score","ar_bin","achievable","coverage","emp_risk","emp_tail_rate",
           "abstention","violation","strat_violation","global_cov","global_tail","strat_cov","strat_tail",
           "hoeffding","n_cal","n_audit","n_audit_bin","base_risk","note"]
    cols=[k for k in order if k in keys]+[k for k in keys if k not in order]
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print("WROTE",path)
# ---- A1-4 shift audit: calibrate on source cell, audit on different-DATASET target cell.
# Compare (a) one global threshold vs (b) ar-stratified thresholds; report tail violation & coverage.
SHIFT_ALPHA=0.05
PAIRS=[("DIOR#22","SODA#23"),("DIOR#3","SODA#4"),("DIOR#22","FAIR1M#24"),("SODA#4","DIOR#3")]
bins=[(1.6,2.0),(2.0,3.0),(3.0,1e9)]
for src,tgt in PAIRS:
    if src not in CACHE or tgt not in CACHE: continue
    S=CACHE[src]; T=CACHE[tgt]
    hs=math.sqrt(math.log(1/0.1)/(2*len(S["sc_cal"])))
    tg,_,_=conformal_threshold(S["sc_cal"],S["tl_cal"],SHIFT_ALPHA,slack=hs)
    if tg is None: continue
    gcov,grate,_=audit(T["sc_aud"],T["tl_aud"],tg)
    # stratified: per-bin threshold from source bin
    strat_keep=np.zeros(len(T["sc_aud"]),bool)
    for lo,hi in bins:
        cbm=(S["ar_cal"]>=lo)&(S["ar_cal"]<hi); tbm=(T["ar_aud"]>=lo)&(T["ar_aud"]<hi)
        if cbm.sum()<100: continue
        ts,_,_=conformal_threshold(S["sc_cal"][cbm],S["tl_cal"][cbm],SHIFT_ALPHA,slack=math.sqrt(math.log(1/0.1)/(2*cbm.sum())))
        if ts is None: continue
        strat_keep|=(tbm&(T["sc_aud"]>=ts))
    scov=float(strat_keep.mean()); srate=float(T["tl_aud"][strat_keep].mean()) if strat_keep.sum() else float("nan")
    rows_shift.append(dict(source=src,target=tgt,alpha=SHIFT_ALPHA,
        global_cov=round(gcov,4),global_tail=round(grate,4),global_violation=bool(grate>SHIFT_ALPHA),
        strat_cov=round(scov,4),strat_tail=round(srate,4) if srate==srate else "",
        strat_violation=bool(srate>SHIFT_ALPHA) if srate==srate else "",
        strat_reduces_violation=bool((grate>SHIFT_ALPHA) and (srate==srate and srate<=grate))))
dump(f"{OUT}/p2_shift_audit_055.csv",rows_shift)
dump(f"{OUT}/p2_alpha_scan_055.csv",rows_alpha)
dump(f"{OUT}/p2_tail_conformal_055.csv",rows_tail)
dump(f"{OUT}/p2_conformal_score_menu_055.csv",rows_menu)
dump(f"{OUT}/p2_mondrian_ar_conformal_055.csv",rows_mond)
