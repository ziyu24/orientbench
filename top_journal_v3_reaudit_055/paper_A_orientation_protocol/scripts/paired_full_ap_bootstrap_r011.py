#!/usr/bin/env python3
"""Paired image-cluster AP bootstrap for the frozen 0/15 degree variants.

The first implementation re-sorted and repeated Python records for every
replicate.  SODA-A made that needlessly serial.  This version keeps the
frozen estimand but vectorizes score order and image multiplicities, and runs
one independent cell per CPU worker.
"""
import csv,pickle,os,json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'outputs/persistent_artifacts/orientbench_r011'; REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
CELL_META={
 'DIOR-R_22':('A','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'DIOR-R_3':('B','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'DIOR-R_61':('C','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'FAIR1M-v1.0_24':('D','outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl'),
 'SODA-A_23':('E','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
 'SODA-A_4':('F','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl')}
def _prepared(rows, image_index):
 by={}
 for r in rows:
  by.setdefault(r['class_name'],[]).append((float(r['score']),image_index[r['image_id']],int(r['tp50']),int(r['tp75'])))
 out={}
 for cls,rs in by.items():
  rs.sort(key=lambda x:(-x[0],x[1])); out[cls]=(np.asarray([x[1] for x in rs],np.int32),np.asarray([x[2] for x in rs],np.int8),np.asarray([x[3] for x in rs],np.int8))
 return out
def _ap_matrix(prepared,mults,gt_counts):
 vals50=np.zeros(mults.shape[0],np.float64); vals75=np.zeros(mults.shape[0],np.float64)
 classes=sorted(gt_counts)
 for cls in classes:
  item=prepared.get(cls)
  if item is None: continue
  img,tp50,tp75=item; w=mults[:,img].astype(np.float64); n=np.maximum(mults@gt_counts[cls],1.0); den=np.maximum(np.cumsum(w,1),1.0)
  for endpoint,tp in enumerate((tp50,tp75)):
   c=np.cumsum(w*tp,1); rec=c/n[:,None]; prec=c/den; a=np.zeros(mults.shape[0])
   for q in np.linspace(0,1,11): a+=np.where(rec>=q,prec,0).max(1)/11.0
   if endpoint==0: vals50 += a
   else: vals75 += a
 return vals50/max(len(classes),1), vals75/max(len(classes),1)
def compute_shard(task,seed=20260806):
 fp,start,reps=task; fp=Path(fp)
 with fp.open('rb') as f:d=pickle.load(f)
 cell=fp.stem.replace('details_','',1); variants={'P0':d.get('P0',[]),'D15':d.get('D15',[]),'P15':d.get('P15',[]),'plus15':d.get('plus15',[]),'minus15':d.get('minus15',[])}
 if not variants['plus15']: variants['plus15']=d.get('S15',[]); variants['minus15']=variants['plus15']
 key=cell; role,gt_rel=CELL_META[key]; universe=ROOT/f'outputs/persistent_artifacts/m069_fullval_reliability/{role}/image_universe.csv'
 with universe.open() as f: imgs=sorted({r['image_id'] for r in csv.DictReader(f)})
 image_index={x:i for i,x in enumerate(imgs)}; series=[]
 prepared={k:_prepared(v,image_index) for k,v in variants.items()}
 gt_counts={}
 with (ROOT/gt_rel).open() as f:
  for line in f:
   row=json.loads(line); cls=row['class_name']; gt_counts.setdefault(cls,np.zeros(len(imgs),np.int32))[image_index[str(row['image_id'])]]+=1
 point_mult=np.ones((1,len(imgs)),np.int16); point_ap={k:_ap_matrix(v,point_mult,gt_counts) for k,v in prepared.items()}
 def point_t(k): return float((point_ap['P0'][1]-point_ap[k][1])-(point_ap['P0'][0]-point_ap[k][0]))
 # Process bootstrap draws in small chunks to cap peak memory on SODA-A.
 for chunk_start in range(start,start+reps,25):
  nr=min(25,start+reps-chunk_start)
  # A replicate-indexed SeedSequence makes shards bitwise reproducible while
  # allowing the 1000 paired image multiplicity vectors to run concurrently.
  draws=np.stack([np.random.default_rng(np.random.SeedSequence([seed,rep])).integers(0,len(imgs),size=len(imgs),dtype=np.int32) for rep in range(chunk_start,chunk_start+nr)])
  mult=np.zeros((nr,len(imgs)),np.int16)
  for i in range(nr): mult[i]=np.bincount(draws[i],minlength=len(imgs))
  a={k:_ap_matrix(v,mult,gt_counts) for k,v in prepared.items()}
  def t(k): return (a['P0'][1]-a[k][1])-(a['P0'][0]-a[k][0])
  for j in range(nr): series.append({'cell':cell,'replicate':chunk_start+j,'T_P':float(t('P15')[j]),'T_D':float(t('D15')[j]),'T_plus':float(t('plus15')[j]),'T_minus':float(t('minus15')[j]),'T_S':float((t('plus15')[j]+t('minus15')[j])/2)})
 points={'T_P':point_t('P15'),'T_D':point_t('D15'),'T_plus':point_t('plus15'),'T_minus':point_t('minus15')}; points['T_S']=(points['T_plus']+points['T_minus'])/2
 return series,points
def main():
 detail_files=sorted(OUT.glob('details_*.pkl')); reps=1000; out=[]; summ=[]
 workers=max(1,int(os.environ.get('R010_BOOT_WORKERS','38'))); shards=min(8,max(1,workers//len(detail_files)))
 tasks=[]
 for fp in detail_files:
  bounds=np.linspace(0,reps,shards+1,dtype=int)
  tasks.extend((str(fp),int(bounds[i]),int(bounds[i+1]-bounds[i])) for i in range(shards))
 grouped=defaultdict(list); points={}
 with ProcessPoolExecutor(max_workers=workers) as ex:
  for series,point in ex.map(compute_shard,tasks):
   grouped[series[0]['cell']].extend(series); points[series[0]['cell']]=point
 for cell,series in sorted(grouped.items()):
  series.sort(key=lambda r:int(r['replicate'])); out.extend(series); ss={'cell':cell,'n_reps':reps,'seed':20260806,'rng':'SeedSequence([seed,replicate])'}
  for k in ['T_P','T_D','T_plus','T_minus','T_S']:
   v=np.asarray([r[k] for r in series]); point=points[cell][k]; centered=v-v.mean(); ss[k+'_point']=point; ss[k+'_bootstrap_mean']=float(v.mean()); ss[k+'_bias']=float(v.mean()-point); ss[k+'_ci_low']=float(np.quantile(v,.025)); ss[k+'_ci_high']=float(np.quantile(v,.975)); ss[k+'_p_one_sided']=float((1+np.sum(centered<=-point))/(len(v)+1)); ss[k+'_support_unadjusted']=bool(point>0 and ss[k+'_ci_low']>0 and ss[k+'_p_one_sided']<.05)
  summ.append(ss)
 fields=list(out[0]) if out else ['cell'];
 # Holm adjustment is separate for the six D and six S tests.
 for endpoint in ('D','S'):
  ordered=sorted(range(len(summ)),key=lambda i:summ[i][f'T_{endpoint}_p_one_sided'])
  running=0.0
  for rank,index in enumerate(ordered):
   adjusted=min(1.0,(len(ordered)-rank)*summ[index][f'T_{endpoint}_p_one_sided']); running=max(running,adjusted)
   summ[index][f'T_{endpoint}_p_holm']=running
   summ[index][f'{endpoint}_support']=bool(summ[index][f'T_{endpoint}_point']>0 and summ[index][f'T_{endpoint}_ci_low']>0 and running<.05)
 with (REP/'paired_ap_bootstrap_replicates_r011.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(out)
 with (REP/'paired_ap_bootstrap_summary_r011.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(summ[0]) if summ else ['status'],lineterminator='\n');w.writeheader();w.writerows(summ)
if __name__=='__main__':main()
