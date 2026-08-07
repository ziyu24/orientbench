#!/usr/bin/env python3
import csv,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; W=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs'; R=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
rows=[]
for p in sorted(W.glob('*.jsonl')):
    if p.name.startswith('surv_'): continue
    for line in p.read_text().splitlines():
        try:
            d=json.loads(line)
            if 'outcomes' in d: rows.append(d)
        except Exception: pass
summary=[]; boot=[]; survival=[]
for d in rows:
    o=d['outcomes']; n=len(o); severe=np.array([x['severe'] for x in o],dtype=float) if o else np.array([])
    survival.append({'cell':d['cell'],'track':d['track'],'dose_deg':d['dose_deg'],'tp50_ar21_count':n,'tp75_total_count':d.get('tp75_count',''),'tp75_over_tp50_ar21':float(d['tp75_count']/n) if n else None,'AP50':d['AP50'],'AP75':d['AP75'],'status':'exact_tau75_evaluator_survival'})
    for label,mask in [('all',np.ones(n,dtype=bool)),('ar21_3',np.array([2.1<=x['ar']<3 for x in o])),('ar3_5',np.array([3<=x['ar']<5 for x in o])),('ar5_plus',np.array([x['ar']>=5 for x in o]))]:
        z=severe[mask]; summary.append({'cell':d['cell'],'track':d['track'],'dose_deg':d['dose_deg'],'stratum':label,'matched_count':int(len(z)),'severe_count':int(z.sum()) if len(z) else 0,'severe_rate':float(z.mean()) if len(z) else None,'AP50':d['AP50'],'AP75':d['AP75'],'fp50':d['fp50']})
    # image-cluster bootstrap for the primary all-stratum event rate
    by={}
    for x in o: by.setdefault(x['image_id'],[]).append(x['severe'])
    vals=np.array([np.mean(v) for v in by.values()],dtype=float)
    if len(vals):
        rng=np.random.default_rng(9000+int(d['dose_deg']))
        means=np.array([rng.choice(vals,len(vals),replace=True).mean() for _ in range(500)])
        boot.append({'cell':d['cell'],'track':d['track'],'dose_deg':d['dose_deg'],'cluster_count':len(vals),'mean_severe_rate':float(vals.mean()),'bootstrap_ci95_low':float(np.quantile(means,.025)),'bootstrap_ci95_high':float(np.quantile(means,.975))})
surv_rows=[]
for p in sorted(W.glob('surv_*.jsonl')):
    for line in p.read_text().splitlines():
        try:
            d=json.loads(line); n=sum(1 for x in d['outcomes']); surv_rows.append({'cell':d['cell'],'track':d['track'],'dose_deg':d['dose_deg'],'tp50_ar21_count':n,'tp75_total_count':d.get('tp75_count',''),'tp75_over_tp50_ar21':float(d['tp75_count']/n) if n else None,'AP50':d['AP50'],'AP75':d['AP75'],'status':'exact_tau75_evaluator_survival'})
        except Exception: pass
for fn, data in [('a4_risk_event_r009.csv',summary),('a4_cluster_bootstrap_r009.csv',boot),('a4_geometry_survival_r009.csv',surv_rows)]:
    if data:
        with (R/fn).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
print('risk_rows',len(summary),'bootstrap_rows',len(boot))
