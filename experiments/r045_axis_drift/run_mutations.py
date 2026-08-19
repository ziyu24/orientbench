#!/usr/bin/env python3
"""Run the five frozen r045 mutations and persist their exit evidence."""
import json, subprocess, sys
from pathlib import Path

ROOT=Path('/home/rspip/cqc/pro/study/orientbench')
OUT=ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/mutations'
OUT.mkdir(parents=True,exist_ok=True)
base=[sys.executable,str(ROOT/'experiments/r045_axis_drift/target_validator_b.py'),
      '--split',str(ROOT/'outputs/bench_core/splits/D_audit_hrsc_trainval.csv'),
      '--ann-dir','/home/rspip/cqc/data/dataset/HRSC2016/annfiles',
      '--dcal-pred',str(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_hrsc_score_only/predictions/hrsc_r50_dcal.pkl'),
      '--ap-pred',str(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_predictions/hrsc_lsknet_audit.pkl'),
      '--orientation-pred',str(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_predictions/hrsc_r50_audit.pkl'),
      '--implementation-a',str(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_gate_a/implementation_a.json')]
results=[]
for mutation in ('split_member','target_threshold','angle_error','gt_ar','policy_token'):
    dest=OUT/f'{mutation}.json'; proc=subprocess.run(base+['--out',str(dest),'--mutation',mutation],capture_output=True,text=True)
    results.append({'mutation':mutation,'exit_code':proc.returncode,'passed':proc.returncode!=0,'stdout':proc.stdout.strip(),'stderr':proc.stderr.strip(),'output':str(dest.relative_to(ROOT))})
payload={'schema_version':2,'pristine_exit_code':0,'mutations':results,'all_mutations_detected':all(x['passed'] for x in results)}
(OUT/'mutation_summary.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
if not payload['all_mutations_detected']: sys.exit(1)
