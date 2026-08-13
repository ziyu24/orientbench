#!/usr/bin/env python3
"""Fresh r028 raw-layer revalidation of the frozen r026 DOTA inputs.

This intentionally does not import or invoke r025/r026 analysis modules, and
does not read r026 hypotheses or gate unless ``--compare`` is explicitly
provided after computation.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
FIELDS=['delta_main','delta_ablation','dod','delta_main_ci_low','delta_main_ci_high','delta_ablation_ci_low','delta_ablation_ci_high','dod_ci_low','dod_ci_high','p_raw','epsilon_main','epsilon_ablation','swap_main_70','swap_ablation_70','p_holm','witness']

def q(x,p): return float(np.quantile(x,p,method='linear'))
def augrc(score,risk):
 o=np.argsort(-score,kind='stable');s=score[o];r=risk[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);c=np.diff(np.r_[st,n]);rr=np.add.reduceat(r,st);cr=np.cumsum(rr)
 return float(np.sum((np.r_[0.,cr[:-1]/n]+cr/n)*c/n/2))
def risk70(score,risk):
 o=np.argsort(-score,kind='stable');s=score[o];r=risk[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);c=np.diff(np.r_[st,n]);rr=np.add.reduceat(r,st);cc=np.cumsum(c);cr=np.cumsum(rr);j=np.searchsorted(cc,.7*n)
 return float(cr[j]/cc[j])
def accept(score,q=.7):
 o=np.argsort(-score,kind='stable');s=score[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];j=np.searchsorted(np.cumsum(np.diff(np.r_[st,len(s)])),q*len(s))
 return score>=s[st[j]]
def delta_tolerance(ar,source):
 d=json.loads(source.read_text()); xy=sorted((float(a),float(b))for a,b in zip(d['ar'],d['dtheta_075'])if b is not None);x=np.array([a for a,_ in xy]);y=np.array([b for _,b in xy]);c=min(a*b for a,b in xy if a>=max(8,x[-1]/2));z=np.interp(ar,x,y);z=np.asarray(z);z[ar<x[0]]=np.inf;m=ar>x[-1];z[m]=np.maximum(0,c/ar[m]-2*float(d['solve_tolerance_deg']));return z
def assert_match_integrity(frame,delta_source):
 # Individual detector match tables need not cover every mother scene; the
 # two-table union is checked by ``calculate`` below.
 if frame.mother.nunique()<1: raise ValueError('empty_mother_set')
 if not frame.ar.ge(1).all(): raise ValueError('ar_range')
 expected=np.minimum(frame.angle_error.to_numpy(float)/np.maximum(delta_tolerance(frame.ar.to_numpy(float),delta_source),1),3)/3
 if not np.allclose(expected,frame.risk.to_numpy(float),atol=3e-7,rtol=0): raise ValueError('angle_risk_relation')
def holm(rows):
 for level in ('unit','dataset'):
  family=sorted([r for r in rows if r['level']==level],key=lambda r:(r['p_raw'],r['key'],r['endpoint'])); prev=0.
  for i,r in enumerate(family): prev=max(prev,min(1.,(len(family)-i)*r['p_raw']));r['p_holm']=prev
def make_row(level,key,endpoint,main,all_,bm,ba,em,ea,swm,swa):
 d=bm-ba; dod=main-all_
 return {'level':level,'key':key,'endpoint':endpoint,'delta_main':main,'delta_ablation':all_,'dod':dod,
  'delta_main_ci_low':q(bm,.025),'delta_main_ci_high':q(bm,.975),'delta_ablation_ci_low':q(ba,.025),'delta_ablation_ci_high':q(ba,.975),'dod_ci_low':q(d,.025),'dod_ci_high':q(d,.975),'p_raw':float((1+np.count_nonzero(np.abs(d-dod)>=abs(dod)))/10001),'epsilon_main':em,'epsilon_ablation':ea,'swap_main_70':swm,'swap_ablation_70':swa}
def calculate(raw,delta_source,swap_threshold=.05,tile_map=None):
 boot=np.load(raw/'bootstrap.npy'); rows=[]
 if boot.shape!=(10000,16): raise ValueError('bootstrap_shape')
 for ui,unit in enumerate(('orcnn','rtmdet')):
  f=pd.read_parquet(raw/f'matched_{unit}.parquet');assert_match_integrity(f,delta_source)
  if tile_map is not None:
   expected=f.image_id.astype(str).map(tile_map)
   if expected.isna().any() or not (expected.to_numpy()==f.mother.astype(str).to_numpy()).all(): raise ValueError('tile_mother_relation')
  for ei,endpoint in enumerate(('AUGRC','Risk@70')):
   vals=[]; eps=[]; swaps=[]
   for ci,main in enumerate((True,False)):
    z=f[f.ar>=2.1] if main else f
    fn=augrc if endpoint=='AUGRC' else risk70
    raw_v,lin_v=fn(z.raw_confidence.to_numpy(),z.risk.to_numpy()),fn(z.linear_source_frozen.to_numpy(),z.risk.to_numpy())
    vals.append((lin_v-raw_v,boot[:,ui*8+ci*4+2+ei]-boot[:,ui*8+ci*4+ei]))
    eps.append(max(.0005 if endpoint=='AUGRC' else .001,.02*max(abs(raw_v),abs(lin_v))))
    a,b=accept(z.linear_source_frozen.to_numpy()),accept(z.raw_confidence.to_numpy());swaps.append(float(np.count_nonzero(a^b)/np.count_nonzero(a|b)))
   rows.append(make_row('unit',unit,endpoint,vals[0][0],vals[1][0],vals[0][1],vals[1][1],eps[0],eps[1],swaps[0],swaps[1]))
 for ei,endpoint in enumerate(('AUGRC','Risk@70')):
  source=[x for x in rows if x['endpoint']==endpoint]; bm=np.mean([boot[:,u*8+2+ei]-boot[:,u*8+ei] for u in range(2)],axis=0);ba=np.mean([boot[:,u*8+6+ei]-boot[:,u*8+4+ei] for u in range(2)],axis=0)
  rows.append(make_row('dataset','DOTA-v1.0',endpoint,float(np.mean([x['delta_main'] for x in source])),float(np.mean([x['delta_ablation'] for x in source])),bm,ba,float(np.mean([x['epsilon_main'] for x in source])),float(np.mean([x['epsilon_ablation'] for x in source])),float(np.mean([x['swap_main_70'] for x in source])),float(np.mean([x['swap_ablation_70'] for x in source]))))
 holm(rows)
 for r in rows:r['witness']=bool(r['delta_main_ci_low']>r['epsilon_main'] and r['delta_ablation_ci_high']<-r['epsilon_ablation'] and r['p_holm']<.05 and (r['dod_ci_low']>0 or r['dod_ci_high']<0) and abs(r['dod'])>=r['epsilon_main']+r['epsilon_ablation'] and (r['endpoint']=='AUGRC' or(min(r['swap_main_70'],r['swap_ablation_70'])>=swap_threshold)))
 out=pd.DataFrame(rows); ds=out[out.level.eq('dataset')]; state='CONFIRMED_EXTERNAL_STRONG' if ds.witness.all() and out[(out.level=='unit')&(out.endpoint=='AUGRC')].witness.any() else 'CONFIRMED_EXTERNAL' if bool(ds[ds.endpoint=='AUGRC'].witness.iloc[0]) and out[(out.level=='unit')&(out.endpoint=='AUGRC')].witness.any() else 'NOT_CONFIRMED' if not ds.witness.any() else 'INCONCLUSIVE_EXTERNAL'
 return out,{'candidate_scientific_state':state,'unit_witnesses':int(out[(out.level=='unit')&out.witness].shape[0]),'dataset_witnesses':int(ds.witness.sum())}
def compare(actual,frozen):
 checks=[]
 for _,r in actual.iterrows():
  f=frozen[(frozen.level.eq(r.level))&(frozen.key.eq(r.key))&(frozen.endpoint.eq(r.endpoint))].iloc[0]
  for field in FIELDS:
   av,bv=r[field],f[field];diff=float(abs(float(av)-float(bv))) if field!='witness' else float(bool(av)!=bool(bv));checks.append({'row':f'{r.level}|{r.key}|{r.endpoint}','field':field,'recomputed_value':bool(av) if field=='witness' else float(av),'r026_value':bool(bv) if field=='witness' else float(bv),'abs_diff':diff,'consistent':bool(diff<=1e-10)})
 return checks
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compare',type=Path);p.add_argument('--tile-map',type=Path);p.add_argument('--delta-source',type=Path,default=ROOT/'top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json');p.add_argument('--swap-threshold',type=float,default=.05);p.add_argument('--declared-state');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 tile_map=None if a.tile_map is None else dict(zip(pd.read_csv(a.tile_map).stem.astype(str),pd.read_csv(a.tile_map).mother.astype(str)))
 try: out,gate=calculate(a.raw,a.delta_source,a.swap_threshold,tile_map)
 except Exception as e: (a.output/'error.json').write_text(json.dumps({'status':'INVALID_RAW','error':str(e)})+'\n');raise SystemExit(2)
 out.to_csv(a.output/'recomputed_hypotheses.csv',index=False);(a.output/'recomputed_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
 if a.declared_state is not None and a.declared_state!=gate['candidate_scientific_state']:
  (a.output/'error.json').write_text(json.dumps({'status':'REPORT_TOKEN_MISMATCH','recomputed_state':gate['candidate_scientific_state'],'declared_state':a.declared_state})+'\n');raise SystemExit(3)
 if a.compare:
  checks=compare(out,pd.read_csv(a.compare));status='PASS' if all(x['consistent']for x in checks) else 'MISMATCH';(a.output/'revalidation.json').write_text(json.dumps({'status':status,'n_checks':len(checks),'n_consistent':sum(x['consistent']for x in checks),'checks':checks},indent=2)+'\n');
  if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
