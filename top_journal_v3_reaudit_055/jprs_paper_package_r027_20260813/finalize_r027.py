#!/usr/bin/env python3
"""Refresh the r027 ledger hashes and write a reproducible package manifest."""
from pathlib import Path
import hashlib, json
import pandas as pd

R=Path(__file__).resolve().parents[2]
O=R/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def main():
 ledger=O/'evidence_ledger.csv'; d=pd.read_csv(ledger)
 for i,row in d.iterrows():
  p=R/row.artifact_path
  if not p.exists(): raise FileNotFoundError(p)
  d.at[i,'sha256']=digest(p)
 d.to_csv(ledger,index=False)
 files=[]
 for p in sorted(O.iterdir()):
  if p.is_file(): files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':digest(p)})
 (O/'package_manifest.json').write_text(json.dumps({'schema_version':1,'status':'COMPLETE_DESCRIPTIVE_PACKAGE','files':files},indent=2)+'\n')
if __name__=='__main__':main()
