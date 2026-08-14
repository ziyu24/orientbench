#!/usr/bin/env python3
"""Write non-self-referential manifests for completed r034 artifacts."""
import hashlib,json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814'
HERE=Path(__file__).resolve().parent
BUNDLE=ROOT/'audit_bundles/r034'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def manifest(base,dest):
 rows=[]
 for p in sorted(x for x in base.rglob('*') if x.is_file() and x.resolve()!=dest.resolve()):rows.append({'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 pd.DataFrame(rows).to_csv(dest,index=False)
 return rows
def main():
 out=manifest(OUT,OUT/'artifact_manifest.csv')
 code=manifest(HERE,HERE/'artifact_manifest.csv')
 bundle=pd.read_csv(BUNDLE/'bundle_manifest.csv')
 identity={'schema':'r034_manifest_identity_v1','persistent_manifest':{'path':str((OUT/'artifact_manifest.csv').relative_to(ROOT)),'bytes':(OUT/'artifact_manifest.csv').stat().st_size,'sha256':sha(OUT/'artifact_manifest.csv'),'entries':len(out)},'execution_manifest_path':str((HERE/'artifact_manifest.csv').relative_to(ROOT)),'execution_manifest_note':'non-self-referential; excludes itself and includes this identity record','bundle_manifest':{'path':str((BUNDLE/'bundle_manifest.csv').relative_to(ROOT)),'bytes':(BUNDLE/'bundle_manifest.csv').stat().st_size,'sha256':sha(BUNDLE/'bundle_manifest.csv'),'entries':len(bundle)},'bundle_total_bytes':int(bundle.bytes.sum())}
 (HERE/'manifest_identity.json').write_text(json.dumps(identity,indent=2,sort_keys=True)+'\n')
 # Refresh the execution manifest once to include manifest_identity itself;
 # the manifest deliberately excludes only itself.
 manifest(HERE,HERE/'artifact_manifest.csv')
 print(json.dumps(identity,sort_keys=True))
if __name__=='__main__':main()
