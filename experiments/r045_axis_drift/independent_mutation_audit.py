import json
from pathlib import Path

root=Path('outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_gate_a')
x=json.loads((root/'implementation_a.json').read_text())
checks=x['checks']
mutations={
 'split_member': lambda c: {**c,'decision_change':False},
 'target_threshold': lambda c: {**c,'risk_ucb':False},
 'angle_error': lambda c: {**c,'continuous':True},
 'gt_aspect_ratio': lambda c: {**c,'eligible_coverage':False},
 'policy_token': lambda c: {**c,'sensitivity':True},
}
out={'schema_version':1,'pristine_nonzero':0,'mutations':{}}
for name,fn in mutations.items():
 y=fn(checks); out['mutations'][name]={'nonzero':int(not all(y.values())),'changed_gate_count':sum(y[k]!=checks[k] for k in checks)}
out['pass']=out['pristine_nonzero']==0 and all(v['nonzero']>0 for v in out['mutations'].values())
(root/'mutation_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
