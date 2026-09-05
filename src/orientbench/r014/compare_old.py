"""Bind preserved r013 raw predictions to the r014 corrected reconstruction."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
def main():
 p=argparse.ArgumentParser();p.add_argument('--old',type=Path,required=True);p.add_argument('--new',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
 for k in ('resnet50','vit_b16'):
  for s in (1201,1202,1203):
   o=np.load(a.old/f'raw_{k}_{s}.npz');n=np.load(a.new/f'raw_{k}_{s}.npz')
   if not(np.array_equal(o['object_id'],n['object_id']) and np.array_equal(o['component'],n['component']) and np.array_equal(o['labels'],n['labels'])):raise RuntimeError('old/new row identity')
   d=np.max(np.abs(o['prob']-n['p_avg'][...,1]),axis=(0,2));aff=n['affected'].astype(bool);rows.append({'model':k,'seed':s,'changed_affected':int(np.count_nonzero(d[aff]>0)),'changed_unaffected':int(np.count_nonzero(d[~aff]>0)),'max_abs_affected':float(d[aff].max()),'max_abs_unaffected':float(d[~aff].max())})
 old_summary=json.load(open(a.old/'statistics/summary.json'));a.out.write_text(json.dumps({'old_summary_delta':old_summary['delta'],'old_summary_q':old_summary['q'],'comparison':rows},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
