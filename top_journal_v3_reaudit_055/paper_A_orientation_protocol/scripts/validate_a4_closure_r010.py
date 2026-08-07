#!/usr/bin/env python3
"""Read-only r010 validator.  It never creates or edits a report."""
import argparse,csv,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; WORK=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol'; REP=WORK/'reports'; ALLOWED={
'claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r010-20260806.md','top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a4_closure_r010.py','top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/paired_ap_bootstrap_r010.py','top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/baseline_cohort_survival_r010.py','top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_a4_closure_r010.py','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_protocol_r010.json','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_provenance_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evaluator_golden_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evaluator_parity_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_tracks_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_symmetric_components_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_metrics_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_risk_event_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_paired_ap_bootstrap_replicates_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_paired_ap_bootstrap_summary_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_tp_survival_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_tp_survival_bootstrap_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_mechanism_gate_r010.json','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_claim_ledger_r010.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_manifest_r010.json','top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_statistical_mechanism_r010.md','top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_fixed_dose_curves_r010.svg','top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md'}
def main():
 errors=[]
 try:
  p=json.loads((REP/'a4_protocol_r010.json').read_text()); assert p['dose_grid_deg']==[0,2,5,10,15,20,25,30] and p['bootstrap_seed']==20260806 and p['bootstrap_reps']==1000
 except Exception as e: errors.append('protocol')
 try:
  rows=list(csv.DictReader((REP/'a4_fixed_dose_tracks_r010.csv').open())); assert len(rows)==144 and len({(r['cell'],r['track'],r['dose_deg']) for r in rows})==144
 except Exception: errors.append('track_row_set')
 try:
  rows=list(csv.DictReader((REP/'a4_symmetric_components_r010.csv').open())); assert len(rows)==96
 except Exception: errors.append('symmetric_components')
 try:
  rows=list(csv.DictReader((REP/'a4_evaluator_parity_r010.csv').open())); good=[r for r in rows if r.get('status')=='PASS']; missing=[r for r in rows if r.get('status')=='NOT_RUN_EVALUATOR_R010']; assert len(rows)==6 and ((len(good)==6 and len(missing)==0) or (len(good)==4 and len(missing)==2)) and all(float(r['AP50_diff'])<=.002 and float(r['AP75_diff'])<=.002 for r in good)
 except Exception: errors.append('parity')
 try:
  g=json.loads((REP/'a4_mechanism_gate_r010.json').read_text()); assert g['r009_protocol']=='FAIL_PROTOCOL_R009'
 except Exception: errors.append('gate')
 for f in ['a4_protocol_r010.json','a4_provenance_r010.csv','a4_evaluator_golden_r010.csv','a4_evaluator_parity_r010.csv','a4_fixed_dose_tracks_r010.csv','a4_symmetric_components_r010.csv','a4_baseline_metrics_r010.csv','a4_risk_event_r010.csv','a4_paired_ap_bootstrap_replicates_r010.csv','a4_paired_ap_bootstrap_summary_r010.csv','a4_baseline_tp_survival_r010.csv','a4_baseline_tp_survival_bootstrap_r010.csv','a4_mechanism_gate_r010.json','a4_claim_ledger_r010.csv','a4_evidence_manifest_r010.json','a4_statistical_mechanism_r010.md','a4_fixed_dose_curves_r010.svg','orientation_reliability_paper_A_zh_v080.md']:
  if not (REP/f).exists() and not (WORK/'docs'/f).exists(): errors.append('missing:'+f)
 out={'status':'PASS_VALIDATOR_R010' if not errors and not any(r.get('status')=='NOT_RUN_EVALUATOR_R010' for r in rows) else ('PASS_VALIDATOR_R010_QUARANTINE' if not errors else 'FAIL_VALIDATOR_R010'),'errors':errors,'read_only':True,'evaluator_gate':'PASS_EVALUATOR_R010' if not errors and not any(r.get('status')=='NOT_RUN_EVALUATOR_R010' for r in rows) else 'FAIL_EVALUATOR_R010'}; print(json.dumps(out,ensure_ascii=False)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
