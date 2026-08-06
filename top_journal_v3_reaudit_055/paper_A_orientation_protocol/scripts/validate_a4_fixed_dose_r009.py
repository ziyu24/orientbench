#!/usr/bin/env python3
"""Read-only r009 validator."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
CORE={'DIOR-R/22','DIOR-R/3','DIOR-R/61','FAIR1M-v1.0/24','SODA-A/23','SODA-A/4'}
def main():
    errors=[]; p=json.loads((REP/'a4_fixed_dose_protocol_r009.json').read_text())
    if p.get('dose_grid_deg') != [0,2,5,10,15,20,25,30]: errors.append('dose grid mismatch')
    rows=list(csv.DictReader((REP/'a4_raw_prediction_inventory_r009.csv').open(encoding='utf-8')))
    if {r['unit'] for r in rows} != CORE: errors.append('Core inventory mismatch')
    if not any(r['status']=='INCONCLUSIVE_PROVENANCE_R009' for r in rows): errors.append('provenance stop absent')
    for n in ['a4_baseline_recompute_r009.csv','a4_fixed_dose_positive_r009.csv','a4_fixed_dose_gt_directed_r009.csv','a4_fixed_dose_symmetric_r009.csv']:
        if not (REP/n).exists(): errors.append('missing '+n)
    out={'status':'PASS_VALIDATOR_R009' if not errors else 'FAIL_VALIDATOR_R009','provenance_gate':'INCONCLUSIVE_PROVENANCE_R009','errors':errors,'read_only':True}
    print(json.dumps(out,ensure_ascii=False)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
