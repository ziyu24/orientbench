#!/usr/bin/env python3
"""Build the portable r034 replay bundle from completed outputs."""
import hashlib, shutil
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814'
HERE=Path(__file__).resolve().parent
BUNDLE=ROOT/'audit_bundles/r034'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def copy_file(source,dest):dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
def main():
 BUNDLE.mkdir(parents=True,exist_ok=True)
 # Bundle construction is rerunnable only while the destination has no stale
 # objects; fail closed rather than deleting an older audit bundle.
 existing=[p for p in BUNDLE.rglob('*') if p.is_file()]
 if existing:raise RuntimeError('r034 bundle destination is not empty')
 for directory in ('inputs','implementation_a','implementation_b','comparator'):
  for source in sorted((SRC/directory).rglob('*')):
   if source.is_file():copy_file(source,BUNDLE/source.relative_to(SRC))
 for name in ('lineage_status.csv','mechanism_diagnostics.csv','nms_config_inventory.csv','class_composition.csv','matching_diagnostics.csv'):
  copy_file(SRC/name,BUNDLE/name)
 for name in ('prepare_inputs.py','implementation_a.py','implementation_b.py','compare_ab.py','validate_r034.py','run_mutations.py','verify_bundle_manifest.py'):
  copy_file(HERE/name,BUNDLE/'code'/name)
 copy_file(HERE/'validation/validation.json',BUNDLE/'validation/validation.json')
 copy_file(HERE/'mutations/mutation_results.json',BUNDLE/'mutations/mutation_results.json')
 rows=[]
 for path in sorted(p for p in BUNDLE.rglob('*') if p.is_file()):
  if path.stat().st_size>80*1024*1024:raise RuntimeError('file must be split before bundle: '+str(path))
  rows.append({'path':path.relative_to(BUNDLE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
 pd.DataFrame(rows).to_csv(BUNDLE/'bundle_manifest.csv',index=False)
 print(f'BUNDLE_READY files={len(rows)} bytes={sum(x["bytes"] for x in rows)}')
if __name__=='__main__':main()
