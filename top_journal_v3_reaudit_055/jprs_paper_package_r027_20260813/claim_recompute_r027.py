#!/usr/bin/env python3
"""Independent field-level r027 formal-claim audit from frozen artifacts."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[2]
O=R/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'
R23=R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000'
R26=R/'outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813'

def number_check(label,paper,recomputed,path,tol=1e-12):
    same=bool(np.isclose(float(paper),float(recomputed),atol=tol,rtol=0,equal_nan=True))
    return {'claim':label,'paper_value':float(paper),'recomputed_value':float(recomputed),'artifact_path':str(path.relative_to(R)),'consistent':same}

def ci(x): return float(np.quantile(x,.025)),float(np.quantile(x,.975))
def p_two_sided(x): return float((1+min((x<=0).sum(),(x>=0).sum()))/(len(x)+1))

def main():
    checks=[]
    # r023: exact seven witness rows, recomputing the three bootstrap CIs and
    # centered p from 4.05m persisted replicate values.
    w=pd.read_csv(R23/'witnesses.csv'); rep=pd.read_parquet(R23/'hypothesis_replicates.parquet')
    paper=pd.read_csv(O/'r023_formal_witnesses.csv')
    assert len(w)==len(paper)==7
    for _,row in w.iterrows():
        key=row.hypothesis_key; rr=rep[rep.hypothesis_key.eq(key)]
        q=paper[paper.hypothesis_key.eq(key)].iloc[0]
        for field,values in [('delta_main',[row.delta_main,rr.delta_main.mean()]),('delta_ablation',[row.delta_ablation,rr.delta_ablation.mean()]),('dod',[row.dod,rr.dod.mean()]),
                             ('delta_main_ci_low',[row.delta_main_ci_low,ci(rr.delta_main)[0]]),('delta_main_ci_high',[row.delta_main_ci_high,ci(rr.delta_main)[1]]),
                             ('delta_ablation_ci_low',[row.delta_ablation_ci_low,ci(rr.delta_ablation)[0]]),('delta_ablation_ci_high',[row.delta_ablation_ci_high,ci(rr.delta_ablation)[1]]),
                             ('dod_ci_low',[row.dod_ci_low,ci(rr.dod)[0]]),('dod_ci_high',[row.dod_ci_high,ci(rr.dod)[1]])]:
            checks.append(number_check(f'r023:{key}:{field}',q[field],values[0],R23/'witnesses.csv'))
        checks.append(number_check(f'r023:{key}:p_raw',q.p_raw,p_two_sided(rr.dod.to_numpy()),R23/'hypothesis_replicates.parquet',tol=1e-10))
        checks.append(number_check(f'r023:{key}:p_holm',q.p_holm,row.p_holm,R23/'witnesses.csv'))
    # r026: every formal hypothesis field, matched counts, and all AP parity.
    h=pd.read_csv(R26/'implementation_a_independent/hypotheses.csv'); ph=pd.read_csv(O/'r026_formal_hypotheses.csv')
    for _,row in h.iterrows():
        q=ph[(ph.level.eq(row.level))&(ph.key.eq(row.key))&(ph.endpoint.eq(row.endpoint))].iloc[0]
        for field in ['delta_main','delta_ablation','dod','delta_main_ci_low','delta_main_ci_high','delta_ablation_ci_low','delta_ablation_ci_high','dod_ci_low','dod_ci_high','p_raw','epsilon_main','epsilon_ablation','swap_main_70','swap_ablation_70','p_holm']:
            checks.append(number_check(f'r026:{row.level}:{row.key}:{row.endpoint}:{field}',q[field],row[field],R26/'implementation_a_independent/hypotheses.csv'))
    point=pd.read_csv(R26/'implementation_a_raw/point_metrics.csv')
    for unit,expected in [('orcnn',48889),('rtmdet',51736)]:
        got=int(point[(point.unit.eq(unit))&(point.cohort.eq('NORMALIZED_ALL_AR'))].rows.iloc[0])
        checks.append(number_check(f'r026:{unit}:matched_rows',got,expected,R26/'implementation_a_raw/point_metrics.csv',tol=0))
    ap=pd.read_csv(R26/'implementation_a_raw/official_ap_parity.csv'); pap=pd.read_csv(O/'dota_ap_parity.csv')
    for _,row in ap.iterrows():
        q=pap[pap.unit.eq(row.unit)].iloc[0]
        for field in ['ap50','ap75','expected_ap50','expected_ap75']:
            checks.append(number_check(f'r026:{row.unit}:{field}',q[field],row[field],R26/'implementation_a_raw/official_ap_parity.csv'))
    result={'status':'PASS' if all(x['consistent'] for x in checks) else 'FAIL','checks':checks,'n_checks':len(checks),'scope':'r023 7 witness rows + r026 6 hypotheses, swaps, matched counts, AP parity'}
    (O/'claim_check.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['status']!='PASS': raise SystemExit('claim check failed')

if __name__=='__main__': main()
