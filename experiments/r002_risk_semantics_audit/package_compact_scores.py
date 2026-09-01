#!/usr/bin/env python3
"""Package all repaired G1 audit scores without importing the G1 generator."""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

R=Path(os.environ['R002_REPAIRED_RUNTIME']);E=Path(os.environ['R002_EVIDENCE_DIR'])
def main():
 keys=pd.read_parquet(E/'risk_rows.parquet')[['unit','image_id','pred_id','class_id','role']]
 parts=[]
 for p in sorted((R/'g1').glob('sealed_scores_*_seed*.parquet')):
  z=pd.read_parquet(p); seed=int(z.seed.iloc[0]); held=str(z.heldout_dataset.iloc[0]); unit=p.name.split('_')[-2]
  q=keys[(keys.unit==unit)&(keys.role=='D_audit')].merge(z,on=['image_id','pred_id','class_id'],validate='one_to_one')
  q['seed']=seed;q['heldout_dataset']=held;parts.append(q)
 out=pd.concat(parts,ignore_index=True);out.to_parquet(E/'compact_scores.parquet',compression='zstd',index=False)
if __name__=='__main__':main()
