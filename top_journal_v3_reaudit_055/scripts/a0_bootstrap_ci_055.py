"""A0 bootstrap CIs for masked NRC (detection-score & intrinsic phase_mod), PSC cells.
Tests whether masked NRC is significantly !=1 (reverse-calibrated) under the
frozen ar>=1.6 protocol. Read-only; real 052 artifacts."""
import json, csv, sys, os
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
rng=np.random.RandomState(55)

def nrc(s,e):
    v=nrc_auc(s,e)["nrc_auc"]; return v
def boot_ci(s,e,B=400):
    n=len(s); vals=[]
    for _ in range(B):
        idx=rng.randint(0,n,n); v=nrc(s[idx],e[idx])
        if np.isfinite(v): vals.append(v)
    return round(float(np.percentile(vals,2.5)),4), round(float(np.percentile(vals,97.5)),4)

pm=list(csv.DictReader(open("top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv")))
by={}
for r in pm: by.setdefault(r["cell_id"],[]).append(r)
rows=[]
for cell,rr in by.items():
    ph=np.array([float(r["phase_mod"]) for r in rr]); er=np.array([float(r["angle_error"]) for r in rr])
    sc=np.array([float(r["score"]) for r in rr]); arr=np.array([float(r["aspect_ratio"]) for r in rr])
    m=arr>=1.6
    for sel,s in (("detection_score",sc),("intrinsic_phase_mod",ph)):
        sm,em=s[m],er[m]
        pt=round(nrc(sm,em),4); lo,hi=boot_ci(sm,em)
        rows.append(dict(cell=cell,selector=sel,protocol="masked_ar1.6",n=int(m.sum()),
                         nrc=pt,ci_lo=lo,ci_hi=hi,
                         reverse_calibrated_sig=bool(lo>1.0),calibrated_sig=bool(hi<1.0)))
        print(f"{cell:14s} {sel:20s} n={int(m.sum()):7d} NRC={pt:.3f} CI[{lo:.3f},{hi:.3f}] "
              f"{'REVERSE-CAL(sig)' if lo>1 else 'calibrated(sig)' if hi<1 else 'inconclusive~1'}")
with open(f"{OUT}/a0_masked_nrc_bootstrap_ci_055.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("WROTE",f"{OUT}/a0_masked_nrc_bootstrap_ci_055.csv")
