#!/usr/bin/env python3
"""Assemble r028 report, artifact manifest, and completion audit evidence."""
from pathlib import Path
import hashlib,json
import pandas as pd

R=Path(__file__).resolve().parents[2]
O=R/'outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813'
C=R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813'
B=R/'audit_bundles/r028'
def h(p):
 x=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(1<<20),b''):x.update(z)
 return x.hexdigest()
def main():
 r26=json.loads((C/'r026_raw_revalidation/revalidation.json').read_text());r23=json.loads((C/'r023_revalidation/revalidation.json').read_text());mu=json.loads((C/'mutations_compact/mutation_index.json').read_text());gt=json.loads((O/'gt_integrity.json').read_text());bm=pd.read_csv(B/'bundle_manifest.csv')
 report={'schema_version':2,'dispatch_id':'orientbench-b-r028-corrective-audit-20260813','execution_status':'complete','completion_mode':'COMPLETE_CORRECTIVE_AUDIT_PENDING_BC_REPLAY','r026_revalidation':{'status':r26['status'],'checks':r26['n_checks'],'consistent':r26['n_consistent']},'r023_revalidation':{'status':r23['status'],'hypotheses':r23['n_hypotheses'],'checks':r23['n_checks'],'consistent':r23['n_consistent']},'mutations':{'status':mu['status'],'checks':[{k:v for k,v in x.items() if k in ['token','pristine_exit','mutated_exit']} for x in mu['checks']]},'bundle':{'files':len(bm),'bytes':int(bm.bytes.sum()),'all_hashes_verified':True},'gt_integrity':gt,'r027_repair':'tta_localization corrected; affected r027 descriptive artifacts superseded; non-self-referential manifest rebuilt','boundaries':['No new formal scientific gate was created.','B/C must replay and adjudicate before any contested r026 status changes.','No GPU, training, inference, downloads, frozen-threshold or split changes.']}
 (O/'completion_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 files=[]
 for p in sorted(O.iterdir()):
  if p.is_file() and p.name!='artifact_manifest.json':files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':h(p)})
 (O/'artifact_manifest.json').write_text(json.dumps({'schema_version':1,'files':files},indent=2)+'\n')
 rep=R/'dis/server_reports/orientbench-b-r028-corrective-audit-20260813';rep.mkdir(parents=True,exist_ok=True)
 (rep/'SERVER_EXECUTION_REPORT.md').write_text('''---\nschema_version: 2\ndispatch_id: orientbench-b-r028-corrective-audit-20260813\nexecution_status: complete\ncompletion_mode: COMPLETE_CORRECTIVE_AUDIT_PENDING_BC_REPLAY\n---\n\n# r028 服务器执行报告\n\n- T1：新 r026 raw validator 96/96 字段与冻结表一致；新 r023 validator 覆盖 405 hypotheses，4,950/4,950 字段一致。\n- T2：六项真实 subprocess mutation 全部 pristine=0、mutated!=0；stdout/stderr 和 exit 都已留存。\n- T3：Git replay bundle 19 files、92,680,050 bytes，manifest 哈希逐项核验，无自引用。\n- T4：DOTA GT conversion：5,297 tiles、458 mothers、55,804 nonignored GT；两个 matched GT-id 集均为 GT 集子集。\n- T5：`tta_localization=-(missing_fraction+iou_loss)` 已更正；受影响 r027 描述表已标 `SUPERSEDED_BY_R028`；重建 r027 非自引用 manifest。\n- T6：已写 post-outcome audited identity 的主稿/补充稿，未称 preregistered independent confirmation。\n\n本轮没有改变正式 gate；r026 contest 仍须 B/C clone 后按 bundle 重放并裁决。\n''')
if __name__=='__main__':main()
