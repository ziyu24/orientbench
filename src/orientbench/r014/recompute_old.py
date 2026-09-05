"""Adapt preserved r013 averaged binary probabilities for an independent r014 old-summary rebuild."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
def main():
 p=argparse.ArgumentParser();p.add_argument('--old',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 for k in ('resnet50','vit_b16'):
  for s in (1201,1202,1203):
   x=np.load(a.old/f'raw_{k}_{s}.npz');pos=x['prob'];avg=np.stack((1-pos,pos),-1);np.savez_compressed(a.out/f'raw_{k}_{s}.npz',p_avg=avg,object_id=x['object_id'],component=x['component'],labels=x['labels'])
if __name__=='__main__':main()
