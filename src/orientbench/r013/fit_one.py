"""Run exactly one pre-registered fresh r013 fit; no retry or resume support."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r013.train_six import FITS,fit,rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--canvases',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--kind',required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args()
 if (a.kind,a.seed) not in FITS or a.out.exists():raise RuntimeError('unregistered or duplicate r013 fit')
 pf=json.load(open(a.preflight))
 if any(not x['finite'] or x['optimizer_steps']!=0 for x in pf['architectures'].values()):raise RuntimeError('invalid preflight')
 a.out.parent.mkdir(parents=True,exist_ok=True);fit(a.kind,a.seed,rows(a.root,a.g0,a.canvases),a.out)
if __name__=='__main__':main()
