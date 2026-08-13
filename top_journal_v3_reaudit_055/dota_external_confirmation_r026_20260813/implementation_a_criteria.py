#!/usr/bin/env python3
"""Independent r026 predicate calculation from A's frozen raw bundle."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

def percentile(v):
 s=np.sort(v); return float(s[(len(s)-1)*25//1000] + (((len(s)-1)*.025)%1)*(s[(len(s)-1)*25//1000+1]-s[(len(s)-1)*25//1000]))
def interval(v): return float(np.quantile(v,.025,method='linear')),float(np.quantile(v,.975,method='linear'))
def whole_tie(values):
 ranked=np.sort(values)[::-1]; cuts=np.r_[0,np.where(ranked[:-1]!=ranked[1:])[0]+1]; cut=cuts[np.searchsorted(np.cumsum(np.diff(np.r_[cuts,len(ranked)])),.7*len(values))];return values>=ranked[cut]
def row(level,key,endpoint,dm,da,dbm,dba,em,ea,sm,sa):
 dd=dbm-dba; dod=dm-da; lo1,hi1=interval(dbm);lo2,hi2=interval(dba);lod,hid=interval(dd)
 return {'level':level,'key':key,'endpoint':endpoint,'delta_main':dm,'delta_ablation':da,'dod':dod,'delta_main_ci_low':lo1,'delta_main_ci_high':hi1,'delta_ablation_ci_low':lo2,'delta_ablation_ci_high':hi2,'dod_ci_low':lod,'dod_ci_high':hid,'p_raw':float((1+(np.abs(dd-dod)>=abs(dod)).sum())/10001),'epsilon_main':em,'epsilon_ablation':ea,'swap_main_70':sm,'swap_ablation_70':sa}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('raw',type=Path);ap.add_argument('out',type=Path);z=ap.parse_args();z.out.mkdir(parents=True);boot=np.load(z.raw/'bootstrap.npy');points=pd.read_csv(z.raw/'point_metrics.csv'); out=[]
 for ui,name in enumerate(('orcnn','rtmdet')):
  data=pd.read_parquet(z.raw/f'matched_{name}.parquet')
  for ei,label in enumerate(('AUGRC','Risk@70')):
   values=[]; eps=[];sw=[]
   for ci,cohort in enumerate(('MAIN','NORMALIZED_ALL_AR')):
    bx=boot[:,ui*8+ci*4+2+ei]-boot[:,ui*8+ci*4+ei];values.append(bx)
    a=points.query('unit==@name and cohort==@cohort and probe=="linear_source_frozen"')[label].iloc[0]; b=points.query('unit==@name and cohort==@cohort and probe=="raw_confidence"')[label].iloc[0]; eps.append(max(.0005 if label=='AUGRC' else .001,.02*max(abs(a),abs(b))))
    s=data[data.ar>=2.1] if cohort=='MAIN' else data; x=whole_tie(s.linear_source_frozen.to_numpy());y=whole_tie(s.raw_confidence.to_numpy());sw.append(float((x^y).sum()/(x|y).sum()))
   dm=float(points.query('unit==@name and cohort=="MAIN" and probe=="linear_source_frozen"')[label].iloc[0]-points.query('unit==@name and cohort=="MAIN" and probe=="raw_confidence"')[label].iloc[0]);da=float(points.query('unit==@name and cohort=="NORMALIZED_ALL_AR" and probe=="linear_source_frozen"')[label].iloc[0]-points.query('unit==@name and cohort=="NORMALIZED_ALL_AR" and probe=="raw_confidence"')[label].iloc[0]);out.append(row('unit',name,label,dm,da,values[0],values[1],eps[0],eps[1],sw[0],sw[1]))
 for ei,label in enumerate(('AUGRC','Risk@70')):
  dbm=np.mean([boot[:,i*8+2+ei]-boot[:,i*8+ei] for i in range(2)],axis=0);dba=np.mean([boot[:,i*8+6+ei]-boot[:,i*8+4+ei] for i in range(2)],axis=0);sub=[x for x in out if x['endpoint']==label];out.append(row('dataset','DOTA-v1.0',label,float(np.mean([x['delta_main']for x in sub])),float(np.mean([x['delta_ablation']for x in sub])),dbm,dba,float(np.mean([x['epsilon_main']for x in sub])),float(np.mean([x['epsilon_ablation']for x in sub])),float(np.mean([x['swap_main_70']for x in sub])),float(np.mean([x['swap_ablation_70']for x in sub]))))
 for level in ('unit','dataset'):
  family=sorted([x for x in out if x['level']==level],key=lambda x:(x['p_raw'],x['key'],x['endpoint'])); prior=0
  for n,x in enumerate(family):prior=max(prior,min(1,(len(family)-n)*x['p_raw']));x['p_holm']=prior
 for x in out:x['witness']=bool(x['delta_main_ci_low']>x['epsilon_main'] and x['delta_ablation_ci_high']<-x['epsilon_ablation'] and x['p_holm']<.05 and (x['dod_ci_low']>0 or x['dod_ci_high']<0) and abs(x['dod'])>=x['epsilon_main']+x['epsilon_ablation'] and (x['endpoint']=='AUGRC' or min(x['swap_main_70'],x['swap_ablation_70'])>=.05))
 df=pd.DataFrame(out);df.to_csv(z.out/'hypotheses.csv',index=False);ds=df[df.level=='dataset'];state='CONFIRMED_EXTERNAL_STRONG' if ds.witness.all() and df[(df.level=='unit')&(df.endpoint=='AUGRC')].witness.any() else 'CONFIRMED_EXTERNAL' if ds[ds.endpoint=='AUGRC'].witness.iloc[0] and df[(df.level=='unit')&(df.endpoint=='AUGRC')].witness.any() else 'NOT_CONFIRMED' if not ds.witness.any() else 'INCONCLUSIVE_EXTERNAL';(z.out/'gate.json').write_text(json.dumps({'candidate_scientific_state':state,'unit_witnesses':int(df[(df.level=='unit')&df.witness].shape[0]),'dataset_witnesses':int(ds.witness.sum())},indent=2)+'\n')
if __name__=='__main__':main()
