#!/usr/bin/env python3
"""Run r028 semantic mutations through the independent r026 validator."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
import numpy as np, tempfile
import pandas as pd

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def run(script,raw,out,tile_map,delta_source,frozen,extra=()):
 cmd=[sys.executable,str(script),'--raw',str(raw),'--output',str(out),'--tile-map',str(tile_map),'--delta-source',str(delta_source),'--compare',str(frozen),*extra]
 z=subprocess.run(cmd,capture_output=True,text=True)
 (out/'stdout.txt').write_text(z.stdout);(out/'stderr.txt').write_text(z.stderr)
 return z.returncode,sha(out/'stdout.txt'),sha(out/'stderr.txt')
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--validator',type=Path,required=True);p.add_argument('--tile-map',type=Path,required=True);p.add_argument('--delta-source',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);checks=[]
 mutations={
  'GT_THETA':lambda d:d.assign(angle_error=d.angle_error+1.),
  'TILE_MOTHER':lambda d:d.assign(mother='MUTATED_MOTHER'),
  'AR_GATE':lambda d:d.assign(ar=1.0),
  'BOOTSTRAP_CELL':None,
 }
 for name,fn in mutations.items():
  root=a.output/name
  with tempfile.TemporaryDirectory(prefix='r028_mutation_') as td:
   pr=Path(td)/'pristine';mu=Path(td)/'mutated';shutil.copytree(a.raw,pr);shutil.copytree(a.raw,mu)
   if fn:
    for u in ('orcnn','rtmdet'):
     f=mu/f'matched_{u}.parquet';fn(pd.read_parquet(f)).to_parquet(f,index=False)
   else:
    b=np.load(mu/'bootstrap.npy');b[0,0]+=0.123;np.save(mu/'bootstrap.npy',b)
   pe,po,ps=run(a.validator,pr,root/'pristine_run',a.tile_map,a.delta_source,a.frozen);me,mo,ms=run(a.validator,mu,root/'mutated_run',a.tile_map,a.delta_source,a.frozen)
  checks.append({'token':name,'pristine_exit':pe,'mutated_exit':me,'pristine_stdout_sha256':po,'pristine_stderr_sha256':ps,'mutated_stdout_sha256':mo,'mutated_stderr_sha256':ms})
 # Predicate and report-token mutations are passed as genuine command options.
 for name,extra in [('SWAP_GATE',['--swap-threshold','1.0']),('REPORT_TOKEN',['--declared-state','NOT_CONFIRMED'])]:
  root=a.output/name
  with tempfile.TemporaryDirectory(prefix='r028_mutation_') as td:
   pr=Path(td)/'pristine';shutil.copytree(a.raw,pr)
   pe,po,ps=run(a.validator,pr,root/'pristine_run',a.tile_map,a.delta_source,a.frozen);me,mo,ms=run(a.validator,pr,root/'mutated_run',a.tile_map,a.delta_source,a.frozen,extra)
  checks.append({'token':name,'pristine_exit':pe,'mutated_exit':me,'pristine_stdout_sha256':po,'pristine_stderr_sha256':ps,'mutated_stdout_sha256':mo,'mutated_stderr_sha256':ms})
 status='PASS' if all(x['pristine_exit']==0 and x['mutated_exit']!=0 for x in checks) else 'FAIL'
 (a.output/'mutation_index.json').write_text(json.dumps({'status':status,'checks':checks},indent=2)+'\n')
 if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
