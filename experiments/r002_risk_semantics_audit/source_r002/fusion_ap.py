#!/usr/bin/env python3
"""Independent complete-prediction AP evaluator for frozen GR-EQS scores.

This deliberately does not import the GR-EQS fitting or ranking implementation.
It joins sealed scores to the frozen identity prediction dump and recomputes
AP50/AP75/mAP from boxes, score order and annotations only.
"""
from __future__ import annotations
import argparse, json, pickle
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import qbox2rbox

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
UNITS={
 'A':('dior22',Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test')),
 'B':('dior3',Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test')),
 'C':('dior61',Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test')),
 'D':('fair24',Path('${RUNTIME_DATA_ROOT}/fair1m-v1.0/val_annfiles_r002')),
 'E':('soda23',Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles')),
 'F':('soda4',Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles')),
}
AB=('airplane','airport','baseballfield','basketballcourt','bridge','chimney','dam','Expressway-Service-area','Expressway-toll-station','golffield','groundtrackfield','harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill')
C=('airplane','airport','baseballfield','basketballcourt','bridge','chimney','Expressway-Service-area','Expressway-toll-station','dam','golffield','groundtrackfield','harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill')
SODA=('airplane','helicopter','small-vehicle','large-vehicle','ship','container','storage-tank','swimming-pool','windmill')
FAIR=('Passenger Ship','Liquid Cargo Ship','Dry Cargo Ship','Motorboat','Fishing Boat','Warship','Engineering Ship','other-ship','Tugboat','Small Car','Cargo Truck','Van','Trailer','other-vehicle','Dump Truck','Bus','Tractor','Excavator','Truck Tractor','Boeing737','Boeing747','Boeing777','Boeing787','other-airplane','C919','A220','A321','A330','A350','ARJ21','Tennis Court','Football Field','Basketball Court','Baseball Field','Intersection','Bridge','Roundabout')
def names(u): return FAIR if u=='D' else SODA if u in 'EF' else C if u=='C' else AB
def parse(path):
 out=[]
 for line in path.read_text(errors='ignore').splitlines():
  x=line.split()
  if len(x)<10 or x[-1]!='0':continue
  try: box=[float(v) for v in x[:8]]
  except ValueError:continue
  out.append((' '.join(x[8:-1]),qbox2rbox(torch.tensor([box],dtype=torch.float32))[0].tolist()))
 return out
def ap(tp,score,n):
 if not n:return float('nan')
 order=np.argsort(-np.asarray(score),kind='stable');tp=np.asarray(tp)[order]
 rec=np.cumsum(tp)/n;prec=np.cumsum(tp)/np.arange(1,len(tp)+1)
 return float(sum((prec[rec>=t].max() if np.any(rec>=t) else 0)/11 for t in np.linspace(0,1,11)))
def _class_matches(entries,by_image):
 """Cache each image's rotated IoU matrix once.

 The former implementation called the CUDA/C++ rotated-IoU kernel once per
 prediction *and* once per IoU threshold.  That is mathematically correct but
 makes the SODA audit needlessly quadratic in kernel-launch overhead.  The
 frozen predictions and greedy matching rule remain identical here.
 """
 best_iou=np.full(len(entries),-np.inf,dtype=np.float32)
 best_gt=np.full(len(entries),-1,dtype=np.int64)
 by_pred=defaultdict(list)
 for i,(_,_,image,_) in enumerate(entries): by_pred[image].append(i)
 for image,indices in by_pred.items():
  boxes=by_image.get(image,[])
  if not boxes: continue
  pboxes=torch.stack([entries[i][3] for i in indices]).float()
  gboxes=torch.tensor(boxes,dtype=torch.float32)
  mat=box_iou_rotated(pboxes,gboxes).cpu().numpy()
  best_iou[indices]=mat.max(axis=1)
  best_gt[indices]=mat.argmax(axis=1)
 return best_iou,best_gt

def evaluate(pred,gt):
 """Return raw/fusion AP at all required thresholds from frozen records."""
 thresholds=np.arange(.50,.951,.05)
 values={name:[] for name in ('raw','fusion')}
 for cls,by_image in gt.items():
  entries=pred[cls]; n=sum(map(len,by_image.values()))
  best_iou,best_gt=_class_matches(entries,by_image)
  for name,score_col in (('raw',0),('fusion',1)):
   scores=np.asarray([x[score_col] for x in entries],dtype=np.float64)
   order=np.argsort(-scores,kind='stable')
   ordered_scores=scores[order]
   per_tau=[]
   for tau in thresholds:
    used=set(); tp=[]
    for idx in order:
     image=entries[idx][2]; j=int(best_gt[idx])
     good=j>=0 and best_iou[idx]>=tau and (image,j) not in used
     tp.append(int(good))
     if good: used.add((image,j))
    per_tau.append(ap(tp,ordered_scores,n))
   values[name].append(per_tau)
 return {name:np.nanmean(np.asarray(rows),axis=0) for name,rows in values.items()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--unit',required=True,choices=UNITS);p.add_argument('--heldout',required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args()
 slug,ann=UNITS[a.unit];score_path=RUNTIME/'g1'/f'sealed_scores_{a.heldout.replace("/","_")}_{a.unit}_seed{a.seed}.parquet';scores=pd.read_parquet(score_path)
 lookup={(str(x.image_id),int(x.pred_id),int(x.class_id)):float(x.fusion_score) for x in scores.itertuples(index=False)}
 with (RUNTIME/'raw'/slug/'identity.pkl').open('rb') as f:records=pickle.load(f)
 gt=defaultdict(lambda:defaultdict(list));pred=defaultdict(list);classes=names(a.unit)
 for path in ann.glob('*.txt'):
  for cls,box in parse(path):gt[cls][path.stem].append(box)
 for rec in records:
  image=str(rec['img_id']);inst=rec['pred_instances'];boxes=inst['bboxes'].tensor if hasattr(inst['bboxes'],'tensor') else inst['bboxes']
  for idx,(box,score,label) in enumerate(zip(boxes.detach().cpu(),inst['scores'].detach().cpu(),inst['labels'].detach().cpu())):
   label=int(label)
   if label>=len(classes):continue
   key=(image,idx,label)
   if key not in lookup:raise RuntimeError(f'missing sealed score: {key}')
   pred[classes[label]].append((float(score),lookup[key],image,box.float()))
 curves=evaluate(pred,gt)
 result={'raw_AP50':float(curves['raw'][0]),'fusion_AP50':float(curves['fusion'][0]),
         'raw_AP75':float(curves['raw'][5]),'fusion_AP75':float(curves['fusion'][5]),
         'raw_mAP':float(np.mean(curves['raw'])),'fusion_mAP':float(np.mean(curves['fusion']))}
 result.update(unit=a.unit,heldout_dataset=a.heldout,seed=a.seed,score_sha256=__import__('hashlib').sha256(score_path.read_bytes()).hexdigest(),images=len(records))
 out=RUNTIME/'g1'/'fusion_ap';out.mkdir(parents=True,exist_ok=True);(out/f'{a.heldout.replace("/","_")}_{a.unit}_seed{a.seed}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
