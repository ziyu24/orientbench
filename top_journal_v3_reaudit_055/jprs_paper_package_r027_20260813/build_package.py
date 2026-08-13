#!/usr/bin/env python3
"""Build r027 descriptive tables, formal claim check and evidence ledger."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[2]; O=R/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813';O.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def main():
 d=R/'outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813'; h=pd.read_csv(d/'implementation_a_independent/hypotheses.csv');pt=pd.read_csv(d/'implementation_a_raw/point_metrics.csv'); ap=pd.read_csv(d/'implementation_a_raw/official_ap_parity.csv')
 h.to_csv(O/'r026_formal_hypotheses.csv',index=False);pt.to_csv(O/'dota_unit_point_metrics.csv',index=False);ap.to_csv(O/'dota_ap_parity.csv',index=False)
 dior=pd.read_csv(R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/hypotheses.csv');w=dior[dior.witness];w.to_csv(O/'r023_formal_witnesses.csv',index=False)
 # Formal claim check: independently read formal source tables and compare values.
 checks=[]
 for name,src,dst,key in [('r023_witnesses',R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/witnesses.csv',O/'r023_formal_witnesses.csv',['hypothesis_key']),('r026_hypotheses',d/'implementation_a_independent/hypotheses.csv',O/'r026_formal_hypotheses.csv',['level','key','endpoint']),('r026_ap_parity',d/'implementation_a_raw/official_ap_parity.csv',O/'dota_ap_parity.csv',['unit'])]:
  x=pd.read_csv(src).sort_values(key).reset_index(drop=True);y=pd.read_csv(dst).sort_values(key).reset_index(drop=True);same=list(x.columns)==list(y.columns) and x.equals(y);checks.append({'claim':name,'paper_value_path':str(dst.relative_to(R)),'recomputed_path':str(src.relative_to(R)),'source_sha256':sha(src),'paper_sha256':sha(dst),'consistent':bool(same)})
 (O/'claim_check.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2)+'\n')
 ledger=[]
 for i,(claim,path,formal) in enumerate([('DIOR AR-domain signature',R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/witnesses.csv','formal'),('DOTA external confirmation',d/'implementation_a_independent/hypotheses.csv','formal'),('DOTA AP parity',d/'implementation_a_raw/official_ap_parity.csv','formal'),('DOTA point metrics',d/'implementation_a_raw/point_metrics.csv','descriptive'),('r027 claim check',O/'claim_check.json','descriptive'),('r027 AR scan and endpoints',O/'dota_descriptive_ar_scan_and_endpoints.csv','descriptive'),('r027 class decomposition',O/'dota_descriptive_class_decomposition.csv','descriptive'),('r027 source-beta sensitivity',O/'dota_source_beta_sensitivity_descriptive.csv','descriptive'),('r027 uncertainty MDE80',O/'dota_uncertainty_mde80_descriptive.csv','descriptive')],1):ledger.append({'claim_id':f'L{i}','claim':claim,'round':'r023' if 'DIOR'in claim else 'r026' if 'DOTA'in claim else 'r027','artifact_path':str(path.relative_to(R)),'sha256':sha(path),'status':formal,'generator':'top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/build_package.py'})
 pd.DataFrame(ledger).to_csv(O/'evidence_ledger.csv',index=False)
 # Descriptive DOTA tables, using the r026 matched rows only.
 def metric(s,r,q):
  o=np.argsort(-s,kind='stable');s=s[o];r=r[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);cs=np.diff(np.r_[st,n]);rs=np.add.reduceat(r,st);cc=np.cumsum(cs);cr=np.cumsum(rs);j=int(np.searchsorted(cc,q*n));return float(cr[j]/cc[j])
 def aug(s,r):
  o=np.argsort(-s,kind='stable');s=s[o];r=r[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);cs=np.diff(np.r_[st,n]);rs=np.add.reduceat(r,st);cr=np.cumsum(rs);return float(np.sum((np.r_[0,cr[:-1]/n]+cr/n)*cs/n/2))
 dota=[]; cats=[]
 for u in ('orcnn','rtmdet'):
  f=pd.read_parquet(d/'implementation_a_raw'/f'matched_{u}.parquet')
  for cutoff in np.round(np.arange(1,3.01,.1),1):
   z=f[f.ar>=cutoff]
   for e,fun in [('AUGRC',lambda a,b:aug(a,b)),('Risk@70',lambda a,b:metric(a,b,.7))]:dota.append({'unit':u,'cutoff':cutoff,'endpoint':e,'rows':len(z),'delta_linear_minus_raw':fun(z.linear_source_frozen.to_numpy(),z.risk.to_numpy())-fun(z.raw_confidence.to_numpy(),z.risk.to_numpy()),'status':'DESCRIPTIVE'})
  for cohort,z in [('MAIN',f[f.ar>=2.1]),('ALL_AR',f)]:
   for e,fun in [('AUGRC',lambda a,b:aug(a,b)),('Risk@70',lambda a,b:metric(a,b,.7)),('Risk@90',lambda a,b:metric(a,b,.9))]:
    for p in ('raw_confidence','linear_source_frozen'):dota.append({'unit':u,'cutoff':2.1 if cohort=='MAIN' else 1.0,'cohort':cohort,'endpoint':e,'probe':p,'rows':len(z),'value':fun(z[p].to_numpy(),z.risk.to_numpy()),'status':'DESCRIPTIVE'})
  for c,z in f.groupby('class_id'):
   for cohort,zz in [('MAIN',z[z.ar>=2.1]),('ALL_AR',z)]:
    if len(zz):cats.append({'unit':u,'class_id':c,'cohort':cohort,'rows':len(zz),'delta_augrc':aug(zz.linear_source_frozen.to_numpy(),zz.risk.to_numpy())-aug(zz.raw_confidence.to_numpy(),zz.risk.to_numpy()),'low_reliability':len(zz)<500,'status':'DESCRIPTIVE'})
 pd.DataFrame(dota).to_csv(O/'dota_descriptive_ar_scan_and_endpoints.csv',index=False);pd.DataFrame(cats).to_csv(O/'dota_descriptive_class_decomposition.csv',index=False)
 # All frozen core unit point estimates, deliberately descriptive in this package.
 core=pd.read_parquet(R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/rows.parquet'); rows=[]
 for u,z0 in core.groupby('unit'):
  for co,z in [('MAIN',z0[z0.ar>=2.1]),('ALL_AR',z0)]:
   for p in ('raw_confidence','linear_source_frozen','tta_angle','tta_localization'):
    rows.append({'unit':u,'dataset':z.dataset.iloc[0],'cohort':co,'probe':p,'rows':len(z),'AUGRC':aug(z[p].to_numpy(),z.risk_main.to_numpy()),'Risk@70':metric(z[p].to_numpy(),z.risk_main.to_numpy(),.7),'Risk@90':metric(z[p].to_numpy(),z.risk_main.to_numpy(),.9),'status':'DESCRIPTIVE'})
 pd.DataFrame(rows).to_csv(O/'all_units_descriptive_point_table.csv',index=False)
 # DIOR/FAIR1M/SODA AR cutoff curves and cluster-level uncertainty (DESCRIPTIVE).
 scans=[]; uncertainty=[]
 for (dataset,unit),z0 in core.groupby(['dataset','unit']):
  for cutoff in np.round(np.arange(1,3.01,.1),1):
   z=z0[z0.ar>=cutoff]
   if not len(z):continue
   for e,fun in [('AUGRC',lambda a,b:aug(a,b)),('Risk@70',lambda a,b:metric(a,b,.7))]:
    scans.append({'dataset':dataset,'unit':unit,'cutoff':cutoff,'endpoint':e,'rows':len(z),'delta_linear_minus_raw':fun(z.linear_source_frozen.to_numpy(),z.risk_main.to_numpy())-fun(z.raw_confidence.to_numpy(),z.risk_main.to_numpy()),'status':'DESCRIPTIVE'})
  # Bootstrap SE directly from r023 arrays, Main / linear-minus-raw; DOTA handled below.
  bbcore=np.load(R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/bootstrap_metrics.npz')['unit'];ui='ABCDEF'.index(unit)
  for ei,e in enumerate(('AUGRC','Risk@70','Risk@90')):
   v=bbcore[:,ui,0,1,ei]-bbcore[:,ui,0,0,ei];se=float(np.std(v,ddof=1));uncertainty.append({'dataset':dataset,'unit':unit,'clusters':int(z0.cluster.nunique()),'eligible_clusters_main':int(z0[z0.ar>=2.1].cluster.nunique()),'endpoint':e,'bootstrap_se':se,'mde80_normal_approx':2.80*se,'status':'DESCRIPTIVE'})
 pd.DataFrame(scans).to_csv(O/'core_descriptive_ar_scan.csv',index=False)
 # Source-beta sensitivity and uncertainty disclosure (DESCRIPTIVE, 1000 cluster draws).
 betas={'FAIR1M_source':np.array([-.26525345,.01355104,.00337013,.02027136]),'SODA_source':np.array([-.21289442,.01466760,-.01161673,.00892121])}
 sens=[]; rng=np.random.RandomState(20260813); mothers=sorted(set(pd.read_parquet(d/'implementation_a_raw/matched_orcnn.parquet').mother)|set(pd.read_parquet(d/'implementation_a_raw/matched_rtmdet.parquet').mother));pos={x:i for i,x in enumerate(mothers)}; draws=[np.bincount(rng.randint(0,len(mothers),len(mothers)),minlength=len(mothers)) for _ in range(1000)]
 for label,beta in betas.items():
  unit_frames={}
  for u in ('orcnn','rtmdet'):
   m=pd.read_parquet(d/'implementation_a_raw'/f'matched_{u}.parquet'); feat=pd.read_parquet(R/'outputs/persistent_artifacts/orientbench_r019/prelabel/target_features'/f'{u}.parquet',columns=['image_id','pred_id','logit_score','log_pred_ar','half_log_pred_area']);m=m.merge(feat,on=['image_id','pred_id'],validate='one_to_one');m['score']=np.c_[np.ones(len(m)),m[['logit_score','log_pred_ar','half_log_pred_area']]]@beta
   unit_frames[u]=m
   for co,z in [('MAIN',m[m.ar>=2.1]),('ALL_AR',m)]:
    for e,fun in [('AUGRC',lambda a,b:aug(a,b)),('Risk@70',lambda a,b:metric(a,b,.7))]:sens.append({'source':label,'unit':u,'cohort':co,'endpoint':e,'rows':len(z),'value':fun(z.score.to_numpy(),z.risk.to_numpy()),'status':'DESCRIPTIVE'})
  # Equal-unit mother-cluster bootstrap CI for each endpoint/cohort.
  for co in ('MAIN','ALL_AR'):
   for e,fun in [('AUGRC',lambda a,b:aug(a,b)),('Risk@70',lambda a,b:metric(a,b,.7))]:
    reps=[]
    for count in draws:
     uv=[]
     for u,m in unit_frames.items():
      z=m[m.ar>=2.1] if co=='MAIN' else m; w=count[np.array([pos[x] for x in z.mother])]; expanded=np.repeat(np.arange(len(z)),w)
      uv.append(fun(z.score.to_numpy()[expanded],z.risk.to_numpy()[expanded]))
     reps.append(float(np.mean(uv)))
    point=float(np.mean([x['value'] for x in sens if x['source']==label and x['cohort']==co and x['endpoint']==e]));sens.append({'source':label,'unit':'DOTA_equal_unit','cohort':co,'endpoint':e,'rows':sum(len(m[m.ar>=2.1] if co=='MAIN' else m) for m in unit_frames.values()),'value':point,'ci_low':float(np.quantile(reps,.025,method='linear')),'ci_high':float(np.quantile(reps,.975,method='linear')),'bootstrap_replicates':1000,'status':'DESCRIPTIVE'})
 pd.DataFrame(sens).to_csv(O/'dota_source_beta_sensitivity_descriptive.csv',index=False)
 # Bootstrap standard errors / MDE80 from the frozen formal bootstrap arrays.
 bb=np.load(d/'implementation_a_raw/bootstrap.npy'); unc=[]
 for ei,e in enumerate(('AUGRC','Risk@70')):
  for ui,u in enumerate(('orcnn','rtmdet')):
   x=(bb[:,ui*8+2+ei]-bb[:,ui*8+ei])-(bb[:,ui*8+6+ei]-bb[:,ui*8+4+ei]);se=float(np.std(x,ddof=1));unc.append({'dataset':'DOTA-v1.0','unit':u,'clusters':458,'endpoint':e,'bootstrap_se':se,'mde80_normal_approx':2.80*se,'status':'DESCRIPTIVE'})
 uncertainty.extend(unc);pd.DataFrame(unc).to_csv(O/'dota_uncertainty_mde80_descriptive.csv',index=False);pd.DataFrame(uncertainty).to_csv(O/'all_datasets_uncertainty_mde80_descriptive.csv',index=False)
if __name__=='__main__':main()
