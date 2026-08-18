#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
def main():
 p=argparse.ArgumentParser();p.add_argument('--pred',required=True);p.add_argument('--metrics',required=True);p.add_argument('--out',required=True);p.add_argument('--meta');a=p.parse_args()
 d=pd.read_parquet(a.pred);m=pd.read_csv(a.metrics);e=[]
 if len(m)!=8 or set(m.unit)!=set('ABCDEFGH'):e.append('unit_registry')
 if d.row_id.duplicated().any() or not np.isfinite(d.select_dtypes('number').to_numpy()).all():e.append('rows')
 if not (m.delta<0).all():e.append('gate_not_reject')
 if a.meta:
  q=json.loads(Path(a.meta).read_text())
  if q.get('fit_leakage') or set(q.get('features',[])) & {'Y','angle_error','gt_ar','unit','dataset'} or q.get('bootstrap_tampered') or q.get('gate_token')!='REJECT_OER_METHOD': e.append('metadata')
 Path(a.out).write_text(json.dumps({'pass':not e,'errors':e,'scientific_token':'REJECT_OER_METHOD' if not e else 'NOT_ADJUDICATED'},indent=2)+'\n')
 raise SystemExit(bool(e))
if __name__=='__main__':main()
