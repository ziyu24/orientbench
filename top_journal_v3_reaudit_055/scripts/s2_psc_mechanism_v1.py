"""S2 — PSC mechanism free tests under frozen masked protocol (v1).
Test 1 (aliasing fingerprint): among high-phase_mod (high intrinsic confidence)
instances, is angle error concentrated near encoding-frequency-related angles?
Test 2 (confounding): does phase_mod NRC>1 survive stratification by class/size/ar?
phase_mod = mechanism CANDIDATE only. DOTA#20 excluded (invalid). No training.
"""
import csv, sys, os, math
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
OUTd=f"{ROOT}/top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1"
PM=f"{ROOT}/top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv"
AR=1.6; rng=np.random.RandomState(55)
CELLS={"DIOR-R/22":"DIOR#22","FAIR1M-v1.0/24":"FAIR1M#24","SODA-A/23":"SODA#23"}  # DOTA#20 excluded (invalid)
by={}
for r in csv.DictReader(open(PM)):
    if r["cell_id"] not in CELLS: continue
    try:
        if float(r["aspect_ratio"])<AR: continue
        by.setdefault(r["cell_id"],[]).append((float(r["phase_mod"]),float(r["angle_error"]),
                                                r["class"],float(r["size"]),float(r["aspect_ratio"])))
    except: pass

# Test 1: aliasing fingerprint — angle-error histogram for top-quartile phase_mod
alias=[]
for cid,name in CELLS.items():
    rr=by[cid]; ph=np.array([x[0] for x in rr]); er=np.array([x[1] for x in rr])
    hi=ph>=np.percentile(ph,75)  # high intrinsic confidence
    h,edges=np.histogram(er[hi],bins=[0,2,5,10,15,20,30,45,90])
    frac=h/max(h.sum(),1)
    for i in range(len(h)):
        alias.append(dict(cell=name,bin_lo=edges[i],bin_hi=edges[i+1],
                          count=int(h[i]),frac_high_phase_mod=round(float(frac[i]),4),
                          median_err_high=round(float(np.median(er[hi])),3),n_high=int(hi.sum())))
    # peakiness: is high-confidence error MORE concentrated at large angles than low-confidence?
    lo=ph<=np.percentile(ph,25)
    alias.append(dict(cell=name,bin_lo="SUMMARY",bin_hi="",count="",
                      frac_high_phase_mod=f"med_err hi={np.median(er[hi]):.2f} lo={np.median(er[lo]):.2f}",
                      median_err_high="reverse" if np.median(er[hi])>np.median(er[lo]) else "normal",n_high=int(hi.sum())))
with open(f"{OUTd}/s2_phase_mod_aliasing_masked_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","bin_lo","bin_hi","count","frac_high_phase_mod","median_err_high","n_high"]); w.writeheader(); w.writerows(alias)

# Test 2: confounding — phase_mod NRC within class / size-bin / ar-bin strata
def nrc(s,e):
    v=nrc_auc(s,e)["nrc_auc"]; return round(v,4) if v==v else float("nan")
conf=[]
for cid,name in CELLS.items():
    rr=by[cid]
    ph=np.array([x[0] for x in rr]); er=np.array([x[1] for x in rr])
    cls=np.array([x[2] for x in rr]); sz=np.array([x[3] for x in rr]); ar=np.array([x[4] for x in rr])
    conf.append(dict(cell=name,stratum="ALL",value="",n=len(rr),phase_mod_nrc=nrc(ph,er)))
    # by size tertiles
    for lab,lo,hi in [("size_low",0,33),("size_mid",33,66),("size_high",66,100)]:
        m=(sz>=np.percentile(sz,lo))&(sz<np.percentile(sz,hi) if hi<100 else sz<=sz.max())
        if m.sum()<200: continue
        conf.append(dict(cell=name,stratum="size",value=lab,n=int(m.sum()),phase_mod_nrc=nrc(ph[m],er[m])))
    # by ar tertiles (within masked)
    for lab,lo,hi in [("ar_low",0,33),("ar_mid",33,66),("ar_high",66,100)]:
        m=(ar>=np.percentile(ar,lo))&(ar<np.percentile(ar,hi) if hi<100 else ar<=ar.max())
        if m.sum()<200: continue
        conf.append(dict(cell=name,stratum="ar",value=lab,n=int(m.sum()),phase_mod_nrc=nrc(ph[m],er[m])))
    # top-3 classes by count
    uc,cnt=np.unique(cls,return_counts=True)
    for c in uc[np.argsort(-cnt)][:3]:
        m=cls==c
        if m.sum()<200: continue
        conf.append(dict(cell=name,stratum="class",value=str(c),n=int(m.sum()),phase_mod_nrc=nrc(ph[m],er[m])))
with open(f"{OUTd}/s2_phase_mod_confounding_masked_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["cell","stratum","value","n","phase_mod_nrc"]); w.writeheader(); w.writerows(conf)
# print quick verdict
for cid,name in CELLS.items():
    sub=[r for r in conf if r["cell"]==name and r["stratum"] in("size","ar","class")]
    persist=sum(1 for r in sub if r["phase_mod_nrc"]==r["phase_mod_nrc"] and r["phase_mod_nrc"]>1.0)
    print(f"{name}: strata with phase_mod NRC>1: {persist}/{len(sub)}",flush=True)
print("WROTE s2 aliasing + confounding")
