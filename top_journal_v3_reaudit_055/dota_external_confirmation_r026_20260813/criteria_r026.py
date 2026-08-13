#!/usr/bin/env python3
"""r026 frozen witness layer over a raw DOTA bootstrap bundle."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd

def q(x,p): return float(np.quantile(x,p,method='linear'))
def acc(s,t=.7):
 o=np.argsort(-s,kind='stable');z=s[o];st=np.r_[0,np.flatnonzero(z[1:]!=z[:-1])+1];j=int(np.searchsorted(np.cumsum(np.diff(np.r_[st,len(s)])),t*len(s)));return s>=z[st[j]]
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True);b=np.load(a.raw/'bootstrap.npy');pt=pd.read_csv(a.raw/'point_metrics.csv'); rows=[]
 for ui,u in enumerate(('orcnn','rtmdet')):
  f=pd.read_parquet(a.raw/f'matched_{u}.parquet')
  for ei,e in enumerate(('AUGRC','Risk@70')):
   dm=[]
   for ci,co in enumerate(('MAIN','NORMALIZED_ALL_AR')):
    dm.append(b[:,ui*8+ci*4+2+ei]-b[:,ui*8+ci*4+ei])
   x,y=dm; d=x-y
   get=lambda co,pr:float(pt[(pt.unit==u)&(pt.cohort==co)&(pt.probe==pr)][e].iloc[0])
   main=get('MAIN','linear_source_frozen')-get('MAIN','raw_confidence'); ab=get('NORMALIZED_ALL_AR','linear_source_frozen')-get('NORMALIZED_ALL_AR','raw_confidence')
   eps=lambda co:max(.0005 if e=='AUGRC' else .001,.02*max(abs(get(co,'linear_source_frozen')),abs(get(co,'raw_confidence'))))
   zmain=f[f.ar>=2.1]; zab=f
   swm=np.count_nonzero(acc(zmain.linear_source_frozen.to_numpy())^acc(zmain.raw_confidence.to_numpy()))/np.count_nonzero(acc(zmain.linear_source_frozen.to_numpy())|acc(zmain.raw_confidence.to_numpy()))
   swa=np.count_nonzero(acc(zab.linear_source_frozen.to_numpy())^acc(zab.raw_confidence.to_numpy()))/np.count_nonzero(acc(zab.linear_source_frozen.to_numpy())|acc(zab.raw_confidence.to_numpy()))
   rows.append(dict(level='unit',key=u,endpoint=e,delta_main=main,delta_ablation=ab,dod=main-ab,delta_main_ci_low=q(x,.025),delta_main_ci_high=q(x,.975),delta_ablation_ci_low=q(y,.025),delta_ablation_ci_high=q(y,.975),dod_ci_low=q(d,.025),dod_ci_high=q(d,.975),p_raw=(1+np.count_nonzero(np.abs(d-(main-ab))>=abs(main-ab)))/10001,epsilon_main=eps('MAIN'),epsilon_ablation=eps('NORMALIZED_ALL_AR'),swap_main_70=swm,swap_ablation_70=swa))
 for ei,e in enumerate(('AUGRC','Risk@70')):
  x=np.mean([b[:,ui*8+2+ei]-b[:,ui*8+ei] for ui in range(2)],axis=0);y=np.mean([b[:,ui*8+6+ei]-b[:,ui*8+4+ei] for ui in range(2)],axis=0);d=x-y;sub=[z for z in rows if z['endpoint']==e];hat=float(np.mean([z['delta_main']-z['delta_ablation']for z in sub]));rows.append(dict(level='dataset',key='DOTA-v1.0',endpoint=e,delta_main=float(np.mean([z['delta_main']for z in sub])),delta_ablation=float(np.mean([z['delta_ablation']for z in sub])),dod=hat,delta_main_ci_low=q(x,.025),delta_main_ci_high=q(x,.975),delta_ablation_ci_low=q(y,.025),delta_ablation_ci_high=q(y,.975),dod_ci_low=q(d,.025),dod_ci_high=q(d,.975),p_raw=(1+np.count_nonzero(np.abs(d-hat)>=abs(hat)))/10001,epsilon_main=float(np.mean([z['epsilon_main']for z in sub])),epsilon_ablation=float(np.mean([z['epsilon_ablation']for z in sub])),swap_main_70=float(np.mean([z['swap_main_70']for z in sub])),swap_ablation_70=float(np.mean([z['swap_ablation_70']for z in sub]))))
 for lev in ('unit','dataset'):
  z=sorted([r for r in rows if r['level']==lev],key=lambda r:r['p_raw']);run=0
  for i,r in enumerate(z):run=max(run,min(1,(len(z)-i)*r['p_raw']));r['p_holm']=run
 for r in rows:r['witness']=bool(r['delta_main_ci_low']>r['epsilon_main'] and r['delta_ablation_ci_high']<-r['epsilon_ablation'] and r['p_holm']<.05 and (r['dod_ci_low']>0 or r['dod_ci_high']<0) and abs(r['dod'])>=r['epsilon_main']+r['epsilon_ablation'] and (r['endpoint']=='AUGRC' or(r['swap_main_70']>=.05 and r['swap_ablation_70']>=.05)))
 out=pd.DataFrame(rows);out.to_csv(a.output/'hypotheses.csv',index=False);ds=out[out.level=='dataset'];state='CONFIRMED_EXTERNAL_STRONG' if ds.witness.all() and out[(out.level=='unit')&(out.endpoint=='AUGRC')].witness.any() else 'CONFIRMED_EXTERNAL' if bool(ds[ds.endpoint=='AUGRC'].witness.iloc[0]) and out[(out.level=='unit')&(out.endpoint=='AUGRC')].witness.any() else 'NOT_CONFIRMED' if not ds.witness.any() else 'INCONCLUSIVE_EXTERNAL';json.dump({'candidate_scientific_state':state,'unit_witnesses':int(out[(out.level=='unit')&out.witness].shape[0]),'dataset_witnesses':int(ds.witness.sum())},open(a.output/'gate.json','w'),indent=2)
if __name__=='__main__':main()
