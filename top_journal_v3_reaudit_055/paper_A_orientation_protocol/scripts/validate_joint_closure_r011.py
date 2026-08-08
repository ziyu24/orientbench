#!/usr/bin/env python3
"""Read-only independent validator for the r011 closure."""
import csv, hashlib, json, subprocess
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol'
REP=WORK/'reports'
CELLS={'DIOR-R/22','DIOR-R/3','DIOR-R/61','FAIR1M-v1.0/24','SODA-A/23','SODA-A/4'}
DOSES={0,2,5,10,15,20,25,30}

def rows(name):
 with (REP/name).open(newline='') as f:return list(csv.DictReader(f))
def close(a,b,tol=1e-12):return abs(float(a)-float(b))<=tol
def check(condition,label,checks):
 checks[label]=bool(condition)
 if not condition: raise AssertionError(label)
def holm(values):
 out=[0.]*len(values); running=0.
 for rank,index in enumerate(sorted(range(len(values)),key=lambda i:values[i])):
  running=max(running,min(1.,(len(values)-rank)*values[index]));out[index]=running
 return out

def main():
 checks={}
 protocol=json.loads((REP/'joint_protocol_r011.json').read_text())
 check(protocol['dose_grid_deg']==sorted(DOSES),'protocol_dose_grid',checks)
 check(protocol['bootstrap_seed']==20260806 and protocol['bootstrap_reps']==1000,'protocol_bootstrap',checks)
 check(set(protocol['core_units'])==CELLS,'protocol_core6',checks)
 golden=rows('evaluator_golden_r011.csv')
 check(len(golden)>=40 and sum(r['case'].startswith('bootstrap_optimizer_synthetic_') for r in golden)>=20 and all(r['status']=='PASS' and float(r['max_abs_diff'])<=1e-12 for r in golden),'executable_golden',checks)
 parity=rows('evaluator_parity_r011.csv')
 check(len(parity)==6 and {r['cell'] for r in parity}==CELLS,'parity_universe',checks)
 check(all(r['status']=='PASS' and max(float(r['AP50_abs_diff']),float(r['AP75_abs_diff']))<=.002 and max(float(r['authority_AP50_abs_diff']),float(r['authority_AP75_abs_diff']))<=.002 for r in parity),'official_clean_authority_parity',checks)
 tracks=rows('fixed_dose_tracks_r011.csv'); comps=rows('symmetric_components_r011.csv')
 check(len(tracks)==144 and {(r['cell'],r['track'],int(r['dose_deg'])) for r in tracks}=={(c,t,d) for c in CELLS for t in 'PDS' for d in DOSES},'fixed_grid_144',checks)
 check(len(comps)==96 and {(r['cell'],r['component'],int(r['dose_deg'])) for r in comps}=={(c,s,d) for c in CELLS for s in '+-' for d in DOSES},'symmetric_grid_96',checks)
 lookup={(r['cell'],r['component'],int(r['dose_deg'])):r for r in comps}
 check(all(close(r['AP50'],(float(lookup[(r['cell'],'+',int(r['dose_deg']))]['AP50'])+float(lookup[(r['cell'],'-',int(r['dose_deg']))]['AP50']))/2,1e-10) and close(r['AP75'],(float(lookup[(r['cell'],'+',int(r['dose_deg']))]['AP75'])+float(lookup[(r['cell'],'-',int(r['dose_deg']))]['AP75']))/2,1e-10) for r in tracks if r['track']=='S'),'symmetric_actual_mean',checks)
 risk=rows('risk_event_r011.csv'); baseline=rows('baseline_metrics_r011.csv')
 check(len(risk)==960 and {(r['cell'],r['track'],int(r['dose_deg']),r['stratum']) for r in risk}=={(c,t,d,b) for c in CELLS for t in ('P','D','+','-','S') for d in DOSES for b in ('all','[2.1,3)','[3,5)','[5,+inf)')},'risk_schema_960',checks)
 check(len(baseline)==6 and {r['cell'] for r in baseline}==CELLS and all(r['AURC'] and r['NRC'] and r['Risk70'] and r['Risk90'] and r['denominator_row_key'] for r in baseline),'baseline_metric_closure',checks)
 repl=rows('paired_ap_bootstrap_replicates_r011.csv'); summ=rows('paired_ap_bootstrap_summary_r011.csv')
 check(len(repl)==6000 and len(summ)==6,'bootstrap_row_counts',checks)
 check(all(v==1000 for v in Counter(r['cell'] for r in repl).values()),'bootstrap_1000_per_cell',checks)
 by=defaultdict(list)
 for r in repl:by[r['cell']].append(r)
 for endpoint in ('P','D','plus','minus','S'):
  for s in summ:
   values=np.asarray([float(r['T_'+endpoint]) for r in by[s['cell']]])
   check(close(values.mean(),s['T_'+endpoint+'_bootstrap_mean'],1e-12),f'bootstrap_mean_{endpoint}_{s["cell"]}',checks)
   check(close(np.quantile(values,.025),s['T_'+endpoint+'_ci_low'],1e-12) and close(np.quantile(values,.975),s['T_'+endpoint+'_ci_high'],1e-12),f'bootstrap_ci_{endpoint}_{s["cell"]}',checks)
 for endpoint in ('D','S'):
  adjusted=holm([float(s[f'T_{endpoint}_p_one_sided']) for s in summ])
  check(all(close(a,s[f'T_{endpoint}_p_holm']) for a,s in zip(adjusted,summ)),f'holm_{endpoint}',checks)
  check(all((s[f'{endpoint}_support']=='True')==(float(s[f'T_{endpoint}_point'])>0 and float(s[f'T_{endpoint}_ci_low'])>0 and float(s[f'T_{endpoint}_p_holm'])<.05) for s in summ),f'support_rule_{endpoint}',checks)
 survival=rows('baseline_tp_survival_r011.csv'); surv_boot=rows('baseline_tp_survival_bootstrap_r011.csv')
 bins={'[2.1,3)','[3,5)','[5,+inf)'}
 check(len(survival)==90 and {(r['cell'],r['track'],r['ar_bin']) for r in survival}=={(c,t,b) for c in CELLS for t in ('P','D','+','-','S') for b in bins},'survival_fixed_cohort_90',checks)
 check(len(surv_boot)==90 and all(int(r['reps'])==1000 for r in surv_boot),'survival_bootstrap',checks)
 p3=rows('p3_cross_domain_results_r011.csv'); gate3=json.loads((REP/'p3_gate_r011.json').read_text())
 computed=[r for r in p3 if r['status']=='COMPUTED_R011']; supported=[r for r in computed if r['supported']=='True']
 check(len(p3)==12 and len(computed)==11 and all(r['leakage_check']=='PASS_SOURCE_DCAL_FIT_ONLY' and r['target_gt_use']=='D_audit_evaluation_only' for r in computed),'p3_folds_and_leakage',checks)
 check(gate3['eligible_folds']==len(computed) and gate3['supported_folds']==len(supported) and close(gate3['supported_ratio'],len(supported)/len(computed)),'p3_gate_recomputed',checks)
 gate1=json.loads((REP/'p1_gate_r011.json').read_text()); joint=json.loads((REP/'joint_gate_r011.json').read_text())
 check(gate1['bootstrap_reps_per_unit']==1000 and gate1['evaluator_pass'] and gate1['provenance_pass'],'p1_gate_inputs',checks)
 check(joint['p1']==gate1['status'] and joint['p3']==gate3['status'],'joint_gate_links',checks)
 manifest=json.loads((REP/'evidence_manifest_r011.json').read_text())
 scripts={'run_joint_closure_r011.py','official_evaluator_adapter_r011.py','cleanroom_evaluator_r011.py','paired_full_ap_bootstrap_r011.py','fixed_cohort_mechanism_r011.py','p3_cross_domain_r011.py','validate_joint_closure_r011.py'}
 reports={'joint_protocol_r011.json','resource_telemetry_r011.csv','provenance_r011.csv','evaluator_golden_r011.csv','evaluator_parity_r011.csv','fixed_dose_tracks_r011.csv','symmetric_components_r011.csv','baseline_metrics_r011.csv','risk_event_r011.csv','paired_ap_bootstrap_replicates_r011.csv','paired_ap_bootstrap_summary_r011.csv','baseline_tp_survival_r011.csv','baseline_tp_survival_bootstrap_r011.csv','p3_cross_domain_results_r011.csv','p3_cross_domain_bootstrap_r011.csv','p1_gate_r011.json','p3_gate_r011.json','joint_gate_r011.json','claim_ledger_r011.csv','evidence_manifest_r011.json'}
 docs={'joint_evidence_r011.md','fixed_dose_curves_r011.svg','p3_cross_domain_r011.svg','orientation_reliability_measure_diagnose_fix_r011.md'}
 allowed={'claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r011-20260807.md'}|{str(WORK.relative_to(ROOT)/'scripts'/x) for x in scripts}|{str(WORK.relative_to(ROOT)/'reports'/x) for x in reports}|{str(WORK.relative_to(ROOT)/'docs'/x) for x in docs}
 check(set(manifest['authorized_changes'])==allowed and len(allowed)==33,'authorized_33_exact',checks)
 for item in manifest['inputs']+manifest['outputs']:
  path=ROOT/item['path']; digest=hashlib.sha256(path.read_bytes()).hexdigest()
  check(path.stat().st_size==item['bytes'] and digest==item['sha256'],f'identity_{item["path"]}',checks)
 check(manifest['self_identity']=='N/A_SELF_REFERENCE','manifest_self_identity',checks)
 check(subprocess.check_output(['git','rev-parse','HEAD:dis/B.md'],cwd=ROOT,text=True).strip()=='1a6093cf3b1f396dbee30803ae616643353ea0aa','dis_B_unchanged',checks)
 manuscript=(WORK/'docs/orientation_reliability_measure_diagnose_fix_r011.md').read_text()
 check('固定剂量与跨域选择器复核' in manuscript and manuscript.find('固定剂量与跨域选择器复核')<manuscript.find('## 参考文献'),'manuscript_integration_before_references',checks)
 ledger=rows('claim_ledger_r011.csv')
 check(len(ledger)>=8 and all(r['row_keys'] and r['generator'] and r['input_manifest'] and r['manuscript_anchor'] for r in ledger),'claim_ledger_scope',checks)
 check(all(hashlib.sha256(r['claim'].encode()).hexdigest()==r['text_sha256'] for r in ledger),'claim_text_hashes',checks)
 result={'status':'PASS','checks':len(checks),'p1':gate1['status'],'p3':gate3['status'],'joint':joint['status'],'read_only':True}
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
