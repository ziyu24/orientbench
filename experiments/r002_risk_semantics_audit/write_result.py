#!/usr/bin/env python3
"""Write a path-free correction-only result receipt and artifact manifest."""
from __future__ import annotations
import hashlib,os
from pathlib import Path
E=Path(os.environ['R002_EVIDENCE_DIR']);ROOT=Path(os.environ['ORIENTBENCH_ROOT'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 paths=[]
 for base in (E,ROOT/'experiments/r002_risk_semantics_audit'):
  for p in sorted(base.rglob('*')):
   if p.is_file() and p.name != 'artifact_manifest.yaml':paths.append((p.relative_to(ROOT).as_posix(),p))
 lines=['schema_version: 1','decision: INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE','artifacts:']
 for name,p in paths:lines+=['  - path: '+name,'    bytes: '+str(p.stat().st_size),'    sha256: '+sha(p)]
 (E/'artifact_manifest.yaml').write_text('\n'.join(lines)+'\n')
 result=['schema_version: 1','status: COMPLETE','scientific_status: INCONCLUSIVE_R002_RISK_SEMANTICS','decision: INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE','repair_status: REPAIR_R002_RISK_PIPELINE','g2_started: false','r014_raw_assets: UNAVAILABLE','r002_bug: missing_long_side_canonicalization_before_le90','independent_verification: PASS','remote_publish: PENDING']
 (E/'R002_RISK_AUDIT_RESULT.yaml').write_text('\n'.join(result)+'\n')
if __name__=='__main__':main()
