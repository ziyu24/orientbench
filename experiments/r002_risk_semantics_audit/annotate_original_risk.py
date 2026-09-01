#!/usr/bin/env python3
"""Attach the preserved original r002 risk without recalculating it."""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
E=Path(os.environ['R002_EVIDENCE_DIR']);R=Path(os.environ['R002_ORIGINAL_RUNTIME'])
def main():
 x=pd.read_parquet(E/'risk_rows.parquet');parts=[]
 for u in 'ABCDEF':
  y=pd.read_parquet(R/'labels'/f'{u}.parquet')[['image_id','pred_id','class_id','risk']].rename(columns={'risk':'r002_original_risk'})
  parts.append(x[x.unit==u].merge(y,on=['image_id','pred_id','class_id'],validate='one_to_one'))
 pd.concat(parts,ignore_index=True).to_parquet(E/'risk_rows.parquet',compression='zstd',index=False)
if __name__=='__main__':main()
