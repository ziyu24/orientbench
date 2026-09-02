"""Run only the trainval-frozen r004 test conditions for one detector."""
from __future__ import annotations
import argparse, subprocess
from pathlib import Path
from .prepare_inference import MODELS

def main():
 p=argparse.ArgumentParser(); p.add_argument('--run-root',type=Path,required=True);p.add_argument('--pth-root',type=Path,required=True);p.add_argument('--tool',type=Path,required=True);p.add_argument('--python',required=True);p.add_argument('--model',choices=MODELS,required=True);a=p.parse_args()
 for label in ('clean','blur_1.5','blur_1.25','downsample_2','downsample_1.75'):
  root=a.run_root/'inference'/'test'/a.model/label; out=root/'predictions.pkl'
  if not out.exists(): subprocess.run([a.python,str(a.tool),str(root/'runtime_config.py'),str(a.pth_root/MODELS[a.model]['checkpoint']),'--out',str(out)],check=True)
if __name__=='__main__': main()
