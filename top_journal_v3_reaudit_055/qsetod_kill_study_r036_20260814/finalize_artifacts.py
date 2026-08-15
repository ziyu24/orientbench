#!/usr/bin/env python3
"""Close r036 execution ledgers and non-self-referential artifact manifests."""

from __future__ import annotations
import csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PERSIST=ROOT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
BUNDLE=ROOT/"audit_bundles/r036"

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''): h.update(block)
 return h.hexdigest()

def manifest(root,path,excluded):
 rows=[]
 for item in sorted(root.rglob('*')):
  if item.is_file() and item.resolve() not in excluded and '__pycache__' not in item.parts: rows.append({'path':str(item.relative_to(root)),'bytes':item.stat().st_size,'sha256':sha(item)})
 with path.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256'],lineterminator='\n');writer.writeheader();writer.writerows(rows)
 return rows

def main():
 ledger=[
  ['T1','endpoint consumption audit','PASS','2 clean present endpoints; inventory only'],
  ['T2','evidence increment','PASS','5/8 witnesses; KILL-E=false'],
  ['T3','multimodality','PASS_WITH_DISCLOSED_APPROXIMATION','row-weighted 0.144760; PRUNE-M=false'],
  ['T4','source-only calibration','SCIENTIFIC_KILL_C','coverage-transfer tolerance violated'],
  ['T5','registered decision','COMPLETE','QSETOD_EVIDENCE_ONLY_KEEP_M candidate'],
  ['T6','dual implementation and audit','PASS','A/B comparator, raw validator, 6 mutations, bundle replay'],
  ['T7','reporting and persistence','PASS','report, manifests, reproduction entry point'],
 ]
 with (HERE/'execution_ledger.csv').open('w',newline='') as f:
  writer=csv.writer(f,lineterminator='\n');writer.writerow(['stage','task','status','detail']);writer.writerows(ledger)
 persistent=manifest(PERSIST,PERSIST/'artifact_manifest.csv',{(PERSIST/'artifact_manifest.csv').resolve()})
 top=manifest(HERE,HERE/'artifact_manifest.csv',{(HERE/'artifact_manifest.csv').resolve(),(HERE/'manifest_identity.json').resolve()})
 identity={'schema':'r036_manifest_identity_v1','persistent_manifest':{'path':str((PERSIST/'artifact_manifest.csv').relative_to(ROOT)),'entries':len(persistent),'bytes':(PERSIST/'artifact_manifest.csv').stat().st_size,'sha256':sha(PERSIST/'artifact_manifest.csv')},'execution_manifest':{'path':str((HERE/'artifact_manifest.csv').relative_to(ROOT)),'entries':len(top),'bytes':(HERE/'artifact_manifest.csv').stat().st_size,'sha256':sha(HERE/'artifact_manifest.csv')},'bundle_manifest':None if not (BUNDLE/'bundle_manifest.csv').exists() else {'path':'audit_bundles/r036/bundle_manifest.csv','bytes':(BUNDLE/'bundle_manifest.csv').stat().st_size,'sha256':sha(BUNDLE/'bundle_manifest.csv')}}
 (HERE/'manifest_identity.json').write_text(json.dumps(identity,indent=2,sort_keys=True)+'\n');print(json.dumps(identity,sort_keys=True))
if __name__=='__main__':main()
