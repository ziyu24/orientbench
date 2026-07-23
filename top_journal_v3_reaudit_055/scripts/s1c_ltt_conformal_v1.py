"""S1c — guarantee-layer technical fixes (v1).
(1) LTT fixed-sequence testing (control FWER) instead of grid + pointwise Hoeffding UCB.
(2) Bounded-mean guarantee: angle error in [0,90], so mean loss is bounded ->
    Hoeffding valid with range B=90 (strict, not 'approximate').
(3) Image-level clustered bootstrap CI (split is image-level; risk is instance-level).
Calibrate on D_calib (sub-split of frozen D_cal), audit on D_audit (frozen). Masked ar>=1.6.
No detector training, no threshold/split-file change.
"""
import json, csv, sys, os, math, hashlib
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
AR=1.6; DELTA=0.1; B=90.0; rng=np.random.RandomState(55)
CELLS=[("DIOR-R","22","DIOR#22"),("FAIR1M-v1.0","24","FAIR1M#24"),("SODA-A","23","SODA#23"),
       ("DIOR-R","3","DIOR#3"),("DIOR-R","61","DIOR#61"),("SODA-A","4","SODA#4")]
def sub(i): return "D_fit" if int(hashlib.md5(str(i).encode()).hexdigest(),16)%2==0 else "D_calib"

from scipy.stats import binom
def pval(Remp,alpha,n,kind,rng_B):
    """Valid p-value for H0: R>=alpha.
    kind='indicator': exact binomial (tight). kind='mean': Hoeffding on [0,rng_B] (valid, conservative)."""
    if Remp>=alpha: return 1.0
    if kind=="indicator":
        V=int(round(Remp*n)); return float(binom.cdf(V,n,alpha))  # P(<=V | R=alpha)
    return math.exp(-2*n*((alpha-Remp)/rng_B)**2)

def ltt_select(score_cal,loss_cal,alpha,kind,rng_B):
    """Fixed-sequence LTT low->high coverage; keep while p<=DELTA; stop at first fail (FWER control)."""
    o=np.argsort(-score_cal,kind="stable"); s=score_cal[o]; l=loss_cal[o]
    n=len(l); run=np.cumsum(l)/np.arange(1,n+1)
    ks=np.unique(np.linspace(max(50,int(0.02*n)),n,80).astype(int))
    sel=None
    for k in ks:
        Remp=run[k-1]; p=pval(Remp,alpha,k,kind,rng_B)
        if p<=DELTA: sel=(s[k-1],k/n,Remp)
        else: break
    return sel

def img_bootstrap_ci(images, keep_mask, loss, Bn=300):
    """cluster (image) bootstrap of audit empirical risk over kept set."""
    uimg=np.array(images); uniq=np.unique(uimg)
    idx_by={u:np.where(uimg==u)[0] for u in uniq}
    vals=[]
    for _ in range(Bn):
        pick=uniq[rng.randint(0,len(uniq),len(uniq))]
        ii=np.concatenate([idx_by[u] for u in pick])
        km=keep_mask[ii]
        if km.sum()==0: continue
        vals.append(loss[ii][km].mean())
    if not vals: return ("","")
    return round(float(np.percentile(vals,2.5)),4), round(float(np.percentile(vals,97.5)),4)

rows=[]
for ds,bid,name in CELLS:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    recs=[r for r in recs if r["aspect_ratio"]>=AR]
    split=np.array([r["d_cal_daudit_split_flag"] for r in recs])
    img=np.array([r["image_id"] for r in recs]); err=np.array([r["angle_error"] for r in recs]); sc=np.array([r["score"] for r in recs])
    subf=np.array([sub(img[k]) if split[k]=="D_cal" else "D_audit" for k in range(len(recs))])
    cal=subf=="D_calib"; aud=subf=="D_audit"
    # --- (2) bounded MEAN-risk guarantee via LTT (loss = angle error, bounded [0,90]) ---
    for alpha in [1.5,2.0]:
        s=ltt_select(sc[cal],err[cal],alpha,'mean',B)
        if s is None:
            rows.append(dict(cell=name,mode="mean_deg",alpha=alpha,ltt="FAIL",coverage=0)); continue
        t,ccov,crisk=s; keep=sc[aud]>=t
        acov=float(keep.mean()); arisk=float(err[aud][keep].mean()) if keep.sum() else float("nan")
        lo,hi=img_bootstrap_ci(img[aud],keep,err[aud])
        rows.append(dict(cell=name,mode="mean_deg",alpha=alpha,ltt="PASS",
                         coverage=round(acov,4),emp_risk=round(arisk,3),violation=bool(arisk>alpha),
                         img_ci_lo=lo,img_ci_hi=hi,n_calib=int(cal.sum()),n_audit=int(aud.sum()),
                         bound="Hoeffding B=90 (bounded, strict)"))
    # --- (1) tail-risk guarantee P(err>5)<=alpha via LTT (bounded [0,1]) ---
    tl=(err>5.0).astype(float)
    for alpha in [0.03,0.05]:
        s=ltt_select(sc[cal],tl[cal],alpha,'indicator',1.0)
        if s is None:
            rows.append(dict(cell=name,mode="tail_gt5",alpha=alpha,ltt="FAIL",coverage=0)); continue
        t,ccov,crisk=s; keep=sc[aud]>=t
        acov=float(keep.mean()); arate=float(tl[aud][keep].mean()) if keep.sum() else float("nan")
        lo,hi=img_bootstrap_ci(img[aud],keep,tl[aud])
        rows.append(dict(cell=name,mode="tail_gt5",alpha=alpha,ltt="PASS",
                         coverage=round(acov,4),emp_risk=round(arate,4),violation=bool(arate>alpha),
                         img_ci_lo=lo,img_ci_hi=hi,n_calib=int(cal.sum()),n_audit=int(aud.sum()),
                         bound="Hoeffding B=1 (indicator)"))
    print(f"{name}: mean/tail LTT done (n_cal={int(cal.sum())}, n_aud={int(aud.sum())})",flush=True)
cols=["cell","mode","alpha","ltt","coverage","emp_risk","violation","img_ci_lo","img_ci_hi","n_calib","n_audit","bound"]
with open(f"{OUTd}/s1c_ltt_conformal_tables_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("WROTE s1c_ltt_conformal_tables_v1.csv")
