#!/usr/bin/env python3
"""Build the r045 non-equivalence table and integrity manifest."""
import csv, hashlib, json, math
from pathlib import Path

ROOT=Path('/home/rspip/cqc/pro/study/orientbench')
BUNDLE=ROOT/'audit_bundles/r045'

frozen=json.loads((ROOT/'reports/m4_delta_theta_075_frozen.json').read_text())
with (BUNDLE/'axis_drift_vs_iou_tolerance.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['aspect_ratio','axis_drift_q025_deg','axis_drift_q050_deg','axis_drift_q100_deg','delta_0.75_deg'])
    for ar,delta in zip(frozen['ar'],frozen['dtheta_075']):
        if ar>=2.1:
            angles=[math.degrees(math.asin(min(1.,2*q/ar))) for q in (.25,.5,1.)]
            w.writerow([ar,*angles,delta])

access={
  'schema_version':2,
  'dispatch_id':'orientbench-b-r045-prospective-axis-drift-decision-20260818',
  'operative_policy_seal':{'commit':'e8f757bf38d620e078763cf5f626351ef1b24980','pushed_before_target_score_access':True},
  'target_threshold_seal':{'commit':'e9326ccf4a6d8ab86e06bd01ccb9922ef66aaa5e','commit_time':'2026-08-18T20:24:19-07:00','pushed_before_target_audit_gt_access':True},
  'target_threshold_metadata_amendment':{'commit':'4b4309607c4fd316c8449872498914bde00ee426','commit_time':'2026-08-18T20:26:48-07:00','pushed_before_target_audit_gt_access':True},
  'first_hrsc_audit_gt_access':{'operation':'implementation A XML parse and class-aware matching','earliest_persisted_result_time':'2026-08-18T20:30:02-07:00'},
  'pre_policy_hrsc_daudit_gt_or_outcome_opened':False,
  'pre_threshold_hrsc_dcal_columns':['image_id','prediction_id','score'],
  'pre_threshold_forbidden_columns_opened':[],
  'hrsc_daudit_inference_was_image_only':True,
  'split_modified':False,
  'post_outcome_rescue':False,
  'forbidden_endpoints':{'DOTA-v2.0_val':False,'SODA-A_official_test':False}
}
(BUNDLE/'target_access_audit.json').write_text(json.dumps(access,indent=2,sort_keys=True)+'\n')

roots=[ROOT/'experiments/r045_axis_drift',ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818',ROOT/'audit_bundles/r045',ROOT/'docs/paper_jprs_r045']
manifest=BUNDLE/'manifest.csv'; rows=[]
for root in roots:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.is_symlink() or p==manifest or '__pycache__' in p.parts: continue
        rel=p.relative_to(ROOT); data=p.read_bytes()
        rows.append([str(rel),len(data),hashlib.sha256(data).hexdigest(),'2' if p.suffix in ('.json','.csv','.md','.py') else 'native',str(p.suffix not in ('.pth',)).lower()])
with manifest.open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['path','bytes','sha256','schema_or_format','can_recompute']); w.writerows(rows)
print(json.dumps({'manifest_rows':len(rows),'access_audit':str((BUNDLE/'target_access_audit.json').relative_to(ROOT))}))
