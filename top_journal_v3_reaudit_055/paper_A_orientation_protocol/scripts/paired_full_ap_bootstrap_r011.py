#!/usr/bin/env python3
"""Paired image-cluster AP bootstrap for the frozen 0/15 degree variants.

The first implementation re-sorted and repeated Python records for every
replicate.  SODA-A made that needlessly serial.  This version keeps the
frozen estimand but vectorizes score order and image multiplicities, and runs
one independent cell per CPU worker.
"""
import csv,pickle,os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'outputs/persistent_artifacts/orientbench_r011'; REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
def _prepared(rows, image_index):
 by={}
 for r in rows:
  by.setdefault(r['class_name'],[]).append((float(r['score']),image_index[r['image_id']],int(r['tp50']),int(r['tp75'])))
 out=[]
 for cls,rs in by.items():
  rs.sort(key=lambda x:(-x[0],x[1])); out.append((np.asarray([x[1] for x in rs],np.int32),np.asarray([x[2] for x in rs],np.int8),np.asarray([x[3] for x in rs],np.int8)))
 return out
def _ap_matrix(prepared,mults):
 vals50=np.zeros(mults.shape[0],np.float64); vals75=np.zeros(mults.shape[0],np.float64)
 for img,tp50,tp75 in prepared:
  w=mults[:,img].astype(np.float64); n=np.maximum((w*tp50).sum(1),1.0); den=np.maximum(np.cumsum(w,1),1.0)
  for endpoint,tp in enumerate((tp50,tp75)):
   c=np.cumsum(w*tp,1); rec=c/np.maximum((w*tp).sum(1)[:,None],1.0); prec=c/den; a=np.zeros(mults.shape[0])
   for q in np.linspace(0,1,11): a+=np.where(rec>=q,prec,0).max(1)/11.0
   if endpoint==0: vals50 += a
   else: vals75 += a
 return vals50/max(len(prepared),1), vals75/max(len(prepared),1)
def compute_cell(fp,reps=1000,seed=20260807):
 with fp.open('rb') as f:d=pickle.load(f)
 cell=fp.stem.replace('details_','',1); variants={'P0':d.get('P0',[]),'D15':d.get('D15',[]),'P15':d.get('P15',[]),'plus15':d.get('plus15',[]),'minus15':d.get('minus15',[])}
 if not variants['plus15']: variants['plus15']=d.get('S15',[]); variants['minus15']=variants['plus15']
 imgs=sorted({r['image_id'] for r in variants['P0']}); image_index={x:i for i,x in enumerate(imgs)}; rng=np.random.default_rng(seed); series=[]
 prepared={k:_prepared(v,image_index) for k,v in variants.items()}
 # Process bootstrap draws in small chunks to cap peak memory on SODA-A.
 for start in range(0,reps,25):
  nr=min(25,reps-start); draws=rng.integers(0,len(imgs),size=(nr,len(imgs)),dtype=np.int32); mult=np.zeros((nr,len(imgs)),np.int16)
  for i in range(nr): mult[i]=np.bincount(draws[i],minlength=len(imgs))
  a={k:_ap_matrix(v,mult) for k,v in prepared.items()}
  def t(k): return (a['P0'][1]-a[k][1])-(a['P0'][0]-a[k][0])
  for j in range(nr): series.append({'cell':cell,'replicate':start+j,'T_P':float(t('P15')[j]),'T_D':float(t('D15')[j]),'T_plus':float(t('plus15')[j]),'T_minus':float(t('minus15')[j]),'T_S':float((t('plus15')[j]+t('minus15')[j])/2)})
 arr={k:np.asarray([r[k] for r in series]) for k in ['T_P','T_D','T_plus','T_minus','T_S']}; ss={'cell':cell,'n_reps':reps,'seed':seed}
 for k,v in arr.items():
  ss[k+'_point']=float(v.mean()); ss[k+'_ci_low']=float(np.quantile(v,.025)); ss[k+'_ci_high']=float(np.quantile(v,.975)); ss[k+'_p_one_sided']=float((1+np.sum(v<=0))/(len(v)+1)); ss[k+'_support']=bool(ss[k+'_point']>0 and ss[k+'_ci_low']>0 and ss[k+'_p_one_sided']<.05)
 ss['D_support']=ss['T_D_support']; ss['S_support']=ss['T_S_support']; return series,ss
def main():
 detail_files=sorted(OUT.glob('details_*.pkl')); reps=1000; out=[]; summ=[]
 workers=min(len(detail_files),max(1,int(os.environ.get('R010_BOOT_WORKERS','6'))))
 with ProcessPoolExecutor(max_workers=workers) as ex:
  for series,ss in ex.map(compute_cell,detail_files): out.extend(series); summ.append(ss)
 fields=list(out[0]) if out else ['cell'];
 with (REP/'a4_paired_ap_bootstrap_replicates_r011.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 with (REP/'a4_paired_ap_bootstrap_summary_r011.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(summ[0]) if summ else ['status']);w.writeheader();w.writerows(summ)
if __name__=='__main__':main()
