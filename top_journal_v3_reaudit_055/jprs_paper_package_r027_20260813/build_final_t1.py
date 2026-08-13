#!/usr/bin/env python3
"""Assemble r027's remaining descriptive T1 tables from frozen inputs."""
from pathlib import Path
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
O = R / 'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'

def aug(score, risk):
    o=np.argsort(-score,kind='stable'); score,risk=score[o],risk[o]
    st=np.r_[0,np.flatnonzero(score[1:]!=score[:-1])+1]; n=len(score)
    count=np.diff(np.r_[st,n]); total=np.add.reduceat(risk,st)
    c=np.cumsum(total)
    return float(np.sum((np.r_[0.,c[:-1]/n]+c/n)*count/n/2))

def risk_at(score, risk, q):
    o=np.argsort(-score,kind='stable'); score,risk=score[o],risk[o]
    st=np.r_[0,np.flatnonzero(score[1:]!=score[:-1])+1]; n=len(score)
    count=np.diff(np.r_[st,n]); total=np.add.reduceat(risk,st)
    ccount, crisk=np.cumsum(count),np.cumsum(total); i=np.searchsorted(ccount,q*n)
    return float(crisk[i]/ccount[i])

def main():
    scan=pd.read_csv(O/'all_ar_scans_with_cluster_ci_descriptive.csv')
    # T1.3: clean two-domain Risk@90 table for each detector and both declared
    # DOTA aggregates. (The scan is the source of its cluster CIs.)
    d90=scan[(scan.dataset.eq('DOTA-v1.0')) & scan.endpoint.eq('Risk@90') & scan.cutoff.isin([1.0,2.1])].copy()
    d90['cohort']=np.where(d90.cutoff.eq(2.1),'MAIN_AR_GE_2.1','ALL_AR')
    d90.to_csv(O/'dota_risk90_two_domain_cluster_ci_descriptive.csv',index=False)

    # T1.5: all eight requested units, four probes, all endpoints and domains.
    core=pd.read_parquet(R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/rows.parquet')
    d=R/'outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw'
    feature=R/'outputs/persistent_artifacts/orientbench_r019/prelabel/target_features'
    frames=[]
    for unit,z in core.groupby('unit'):
        frames.append((z.dataset.iloc[0],unit,z,['raw_confidence','linear_source_frozen','tta_angle','tta_localization']))
    for unit in ('orcnn','rtmdet'):
        z=pd.read_parquet(d/f'matched_{unit}.parquet')
        f=pd.read_parquet(feature/f'{unit}.parquet',columns=['image_id','pred_id','u_axis','missing_fraction','iou_loss'])
        z=z.merge(f,on=['image_id','pred_id'],validate='one_to_one')
        # Frozen r023 definitions of the two TTA proxy probes.
        z['tta_angle']=1-z.u_axis
        z['tta_localization']=1-z.iou_loss.clip(0,1)
        frames.append(('DOTA-v1.0',unit,z,['raw_confidence','linear_source_frozen','tta_angle','tta_localization']))
    out=[]
    for dataset,unit,z,probes in frames:
        risk_col='risk_main' if 'risk_main' in z else 'risk'
        for cohort,sub in [('MAIN_AR_GE_2.1',z[z.ar>=2.1]),('ALL_AR',z)]:
            r=sub[risk_col].to_numpy(float)
            for probe in probes:
                s=sub[probe].to_numpy(float)
                out.append({'dataset':dataset,'unit':unit,'cohort':cohort,'probe':probe,'rows':len(sub),
                            'AUGRC':aug(s,r),'Risk@70':risk_at(s,r,.7),'Risk@90':risk_at(s,r,.9),'status':'DESCRIPTIVE'})
    pd.DataFrame(out).to_csv(O/'all_units_descriptive_point_table.csv',index=False)

    # T1.6: dataset-level disclosure with explicit equal-unit aggregates.
    frozen=R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000'
    bb=np.load(frozen/'bootstrap_metrics.npz')['unit']
    mapping={'DIOR-R':[0,1,2],'FAIR1M':[3],'SODA-A':[4,5]}
    units=['A','B','C','D','E','F']; rows=[]
    for dataset,idx in mapping.items():
        z=core[core.dataset.eq(dataset)]
        for endpoint_i, endpoint in enumerate(['AUGRC','Risk@70','Risk@90']):
            rep=(bb[:,idx,0,1,endpoint_i]-bb[:,idx,0,0,endpoint_i]).mean(axis=1)
            se=float(rep.std(ddof=1))
            rows.append({'dataset':dataset,'unit_aggregation':'equal_unit','clusters':int(z.cluster.nunique()),
                         'eligible_clusters_main':int(z[z.ar>=2.1].cluster.nunique()),'endpoint':endpoint,
                         'bootstrap_se':se,'mde80_normal_approx':2.80*se,'bootstrap_replicates':len(rep),'status':'DESCRIPTIVE'})
    dota_scan=scan[(scan.dataset.eq('DOTA-v1.0')) & scan.unit.eq('equal_unit') & scan.cutoff.eq(2.1)]
    for _,x in dota_scan.iterrows():
        # CI-derived SE is an explicit descriptive approximation where r026's
        # frozen bootstrap has no Risk@90 slot.
        se=(x.ci_high-x.ci_low)/(2*1.96)
        rows.append({'dataset':'DOTA-v1.0','unit_aggregation':'equal_unit','clusters':458,
                     'eligible_clusters_main':458,'endpoint':x.endpoint,'bootstrap_se':se,
                     'mde80_normal_approx':2.80*se,'bootstrap_replicates':int(x.bootstrap_replicates),'status':'DESCRIPTIVE_CI_DERIVED'})
    pd.DataFrame(rows).to_csv(O/'dataset_uncertainty_mde80_descriptive.csv',index=False)

if __name__=='__main__': main()
