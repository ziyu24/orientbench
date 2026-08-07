#!/usr/bin/env python3
"""Paired image-cluster AP bootstrap for the frozen 0/15 degree variants."""
import csv,pickle
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'outputs/persistent_artifacts/orientbench_r010'; REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
def ap(rows,field,mults):
 if not rows:return 0.
 by={}
 for r in rows: by.setdefault((r['image_id'],r['class_name']),[]).append(r)
 vals=[]
 for key,rs in by.items():
  rs.sort(key=lambda x:(-x['score'],x['image_id']))
  mult=np.asarray([mults.get(r['image_id'],0) for r in rs],dtype=np.int32)
  if mult.sum()==0: continue
  t=np.repeat(np.asarray([r[field] for r in rs],dtype=np.int8),mult); n=max(1,int(t.sum())); rec=np.cumsum(t)/n; prec=np.cumsum(t)/np.maximum(np.arange(len(t))+1,1)
  vals.append(sum((prec[rec>=x].max() if np.any(rec>=x) else 0)/11 for x in np.linspace(0,1,11)))
 return float(np.mean(vals)) if vals else 0.
def main():
 detail_files=sorted(OUT.glob('details_*.pkl')); reps=1000; seed=20260806; out=[]; summ=[]
 for fp in detail_files:
  with fp.open('rb') as f:d=pickle.load(f)
  cell=next((c for c in ['DIOR-R/22','DIOR-R/3','DIOR-R/61','FAIR1M-v1.0/24','SODA-A/23','SODA-A/4'] if fp.stem==('details_'+c.replace('/','_'))),fp.stem.replace('details_','',1)); base=d.get('P0',[]); imgs=sorted({r['image_id'] for r in base}); rng=np.random.default_rng(seed); series=[]
  variants={'P0':d.get('P0',[]),'D15':d.get('D15',[]),'P15':d.get('P15',[]),'plus15':d.get('plus15',[]),'minus15':d.get('minus15',[])}
  if not variants['plus15']: variants['plus15']=d.get('S15',[]); variants['minus15']=variants['plus15']
  for b in range(reps):
   draw=rng.choice(imgs,len(imgs),replace=True); mult={x:int(np.sum(draw==x)) for x in imgs}; a={k:(ap(v,'tp50',mult),ap(v,'tp75',mult)) for k,v in variants.items()}
   def t(k): return (a['P0'][1]-a[k][1])-(a['P0'][0]-a[k][0])
   row={'cell':cell,'replicate':b,'T_P':t('P15'),'T_D':t('D15'),'T_plus':t('plus15'),'T_minus':t('minus15'),'T_S':(t('plus15')+t('minus15'))/2}; out.append(row)
  arr={k:np.asarray([r[k] for r in out if r['cell']==cell]) for k in ['T_P','T_D','T_plus','T_minus','T_S']}
  ss={'cell':cell,'n_reps':reps,'seed':seed}
  for k,v in arr.items():
   ss[k+'_point']=float(v.mean()); ss[k+'_ci_low']=float(np.quantile(v,.025)); ss[k+'_ci_high']=float(np.quantile(v,.975)); ss[k+'_p_one_sided']=float((1+np.sum(v<=0))/(len(v)+1)); ss[k+'_support']=bool(ss[k+'_point']>0 and ss[k+'_ci_low']>0 and ss[k+'_p_one_sided']<.05)
  ss['D_support']=ss['T_D_support']; ss['S_support']=ss['T_S_support']; summ.append(ss)
 fields=list(out[0]) if out else ['cell'];
 with (REP/'a4_paired_ap_bootstrap_replicates_r010.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 with (REP/'a4_paired_ap_bootstrap_summary_r010.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(summ[0]) if summ else ['status']);w.writeheader();w.writerows(summ)
if __name__=='__main__':main()
