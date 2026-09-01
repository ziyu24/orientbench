#!/usr/bin/env python3
"""Independent AP50/AP75 parity check for a frozen Core-6 identity dump."""
from __future__ import annotations

import argparse
import json
import math
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import qbox2rbox

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
UNITS = {
 'D': ('fair24', Path('${RUNTIME_DATA_ROOT}/fair1m-v1.0/val_annfiles_r002'),
       ('Passenger Ship','Liquid Cargo Ship','Dry Cargo Ship','Motorboat','Fishing Boat','Warship','Engineering Ship','other-ship','Tugboat','Small Car','Cargo Truck','Van','Trailer','other-vehicle','Dump Truck','Bus','Tractor','Excavator','Truck Tractor','Boeing737','Boeing747','Boeing777','Boeing787','other-airplane','C919','A220','A321','A330','A350','ARJ21','Tennis Court','Football Field','Basketball Court','Baseball Field','Intersection','Bridge','Roundabout'), .3462),
 'A': ('dior22', Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'), (), .5368),
 'B': ('dior3', Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'), (), None),
 # The checkpoint filename and old table report dota/mAP=0.5489.  The frozen
 # identity AP50 log is 0.6460; parity uses AP50 and must not compare metrics.
 'C': ('dior61', Path('${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'), (), .6460),
 'E': ('soda23', Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles'), (), .5991),
 'F': ('soda4', Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles'), (), .7295),
}
DIOR_AB = ('airplane','airport','baseballfield','basketballcourt','bridge',
           'chimney','dam','Expressway-Service-area','Expressway-toll-station',
           'golffield','groundtrackfield','harbor','overpass','ship','stadium',
           'storagetank','tenniscourt','trainstation','vehicle','windmill')
DIOR_C = ('airplane','airport','baseballfield','basketballcourt','bridge',
          'chimney','Expressway-Service-area','Expressway-toll-station','dam',
          'golffield','groundtrackfield','harbor','overpass','ship','stadium',
          'storagetank','tenniscourt','trainstation','vehicle','windmill')
SODA = ('airplane','helicopter','small-vehicle','large-vehicle','ship','container','storage-tank','swimming-pool','windmill')

def classes(u): return UNITS[u][2] or (DIOR_C if u == 'C' else DIOR_AB if u in 'AB' else SODA)
def parse(path):
    r=[]
    for l in path.read_text(errors='ignore').splitlines():
        x=l.split()
        if len(x)<10 or x[-1]!='0': continue
        try: b=[float(a) for a in x[:8]]
        except ValueError: continue
        r.append((' '.join(x[8:-1]), qbox2rbox(torch.tensor([b], dtype=torch.float32))[0].tolist()))
    return r
def ap(tp, sc, n):
    if not n:return float('nan')
    o=np.argsort(-np.asarray(sc),kind='stable'); tp=np.asarray(tp)[o]
    rec=np.cumsum(tp)/n; pre=np.cumsum(tp)/np.maximum(np.arange(1,len(tp)+1),1)
    return float(sum((pre[rec>=t].max() if np.any(rec>=t) else 0)/11 for t in np.linspace(0,1,11)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--unit',choices=UNITS,required=True);a=p.parse_args(); slug,ann_dir,_,expected=UNITS[a.unit]; names=classes(a.unit)
 with (RUNTIME/'raw'/slug/'identity.pkl').open('rb') as f: recs=pickle.load(f)
 gt=defaultdict(lambda:defaultdict(list)); pred=defaultdict(list)
 for path in ann_dir.glob('*.txt'):
  for name,b in parse(path): gt[name][path.stem].append(b)
 for r in recs:
  i=str(r['img_id']); q=r['pred_instances']; b=q['bboxes'].tensor if hasattr(q['bboxes'],'tensor') else q['bboxes']
  for box,s,l in zip(b.detach().cpu(),q['scores'].detach().cpu(),q['labels'].detach().cpu()):
   if int(l)<len(names): pred[names[int(l)]].append((float(s),i,box.float()))
 out={}
 for tau in (.5,.75):
  aps=[]
  for name,byimg in gt.items():
   ds=sorted(pred[name],key=lambda z:-z[0]); used=set();tp=[];sc=[]
   for score,img,box in ds:
    sc.append(score); boxes=byimg.get(img,[])
    if not boxes:tp.append(0);continue
    vals=box_iou_rotated(box[None],torch.tensor(boxes,dtype=torch.float32)).squeeze(0).numpy(); j=int(vals.argmax())
    good=vals[j]>=tau and (img,j) not in used;tp.append(int(good));
    if good:used.add((img,j))
   aps.append(ap(tp,sc,sum(map(len,byimg.values()))))
  out[f'AP{int(tau*100)}']=float(np.nanmean(aps))
 out['expected_AP50']=expected;out['delta_AP50']=None if expected is None else out['AP50']-expected;out['unit']=a.unit;out['images']=len(recs);out['gt_classes']=len(gt)
 d=RUNTIME/'parity';d.mkdir(exist_ok=True);(d/f'{a.unit}.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
