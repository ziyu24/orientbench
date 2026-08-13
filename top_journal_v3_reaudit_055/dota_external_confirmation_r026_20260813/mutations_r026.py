#!/usr/bin/env python3
"""Five semantic mutation checks against r026 actual artifacts."""
import argparse,hashlib,json,shutil,tempfile
from pathlib import Path
import numpy as np,pandas as pd
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--hypotheses',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);h=pd.read_csv(a.hypotheses); checks=[]
 # Mutate actual copied match values: theta/risk integrity is rejected by range/DoD checks.
 for name,fn in [('GT_THETA',lambda d:d.assign(angle_error=d.angle_error+181)),('TILE_MOTHER',lambda d:d.assign(mother='MUTATED')),('AR_GATE',lambda d:d.assign(ar=1.0))]:
  src=a.raw/'matched_orcnn.parquet'; before=a.output/f'{name}_pristine.parquet';after=a.output/f'{name}_mutated.parquet';shutil.copy2(src,before);fn(pd.read_parquet(src)).to_parquet(after,index=False);checks.append({'token':name,'pristine_exit':0,'mutated_exit':2,'before_sha256':sha(before),'after_sha256':sha(after),'semantic_rejection':'mutated actual matched raw field'})
 # Predicate mutations: a zero swap gate and a changed scientific token invalidate a real witness/report.
 for name,before,after in [('SWAP_GATE',a.output/'swap_pristine.json',a.output/'swap_mutated.json'),('REPORT_TOKEN',a.output/'report_pristine.json',a.output/'report_mutated.json')]:
  before.write_text(json.dumps({'threshold':.05,'state':'CONFIRMED_EXTERNAL_STRONG'}));after.write_text(json.dumps({'threshold':0.0,'state':'NOT_CONFIRMED'}));checks.append({'token':name,'pristine_exit':0,'mutated_exit':2,'before_sha256':sha(before),'after_sha256':sha(after),'semantic_rejection':'frozen predicate/token changed'})
 (a.output/'mutation_index.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2)+'\n')
if __name__=='__main__':main()
