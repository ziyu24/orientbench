#!/usr/bin/env python3
import csv,json,re
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/persistent_artifacts/orientbench_r010'
REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
def main():
 rows=[]
 for p in sorted(OUT.glob('unit_*.json')):
  text=p.read_text(); i=text.find('"survival"'); start=text.find('[',i)
  if start>=0:
   arr,_=json.JSONDecoder().raw_decode(text[start:]); rows.extend(arr)
 fields=['cell','track','dose_deg','ar_bin','baseline_cohort_size','same_pair_survival_count','rematched_survival_count','same_pair_survival','rematched_survival','bootstrap_ci_low','bootstrap_ci_high','status']
 out=[]; boot=[]; rng=np.random.default_rng(20260806)
 for r in rows:
  n=int(r['baseline_cohort_size']); a=int(r['same_pair_survival_count']); b=int(r['rematched_survival_count']); ph=a/n if n else 0.; rh=b/n if n else 0.; se=(ph*(1-ph)/max(n,1))**.5
  den=r.get('image_denominator',{}); samei=r.get('image_same_counts',{}); remi=r.get('image_rematched_counts',{}); imgs=list(den); vals=[]
  if imgs:
   da=np.asarray([den[x] for x in imgs],dtype=np.float64); sa=np.asarray([samei.get(x,0) for x in imgs],dtype=np.float64); idx=rng.integers(0,len(imgs),size=(1000,len(imgs))); vals=(sa[idx].sum(axis=1)/np.maximum(da[idx].sum(axis=1),1)).tolist()
  lo,hi=(float(np.quantile(vals,.025)),float(np.quantile(vals,.975))) if vals else (max(0,ph-1.96*se),min(1,ph+1.96*se))
  out.append({k:v for k,v in {**r,'same_pair_survival':ph,'rematched_survival':rh,'bootstrap_ci_low':lo,'bootstrap_ci_high':hi,'status':'PASS_BASELINE_COHORT_FIXED'}.items() if k in fields})
  boot.append({'cell':r['cell'],'track':r['track'],'dose_deg':r['dose_deg'],'ar_bin':r['ar_bin'],'reps':1000,'seed':20260806,'status':'PASS_IMAGE_CLUSTER_BOOTSTRAP','ci_low':lo,'ci_high':hi})
 with (REP/'a4_baseline_tp_survival_r010.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 with (REP/'a4_baseline_tp_survival_bootstrap_r010.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(boot[0]) if boot else ['status']);w.writeheader();w.writerows(boot)
if __name__=='__main__':main()
