#!/usr/bin/env python3
"""Fixed baseline-IoU75 cohort survival with GT-AR bins and any-TP rematching."""
import argparse, csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch

import run_joint_closure_r011 as R

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/persistent_artifacts/orientbench_r011'
REP=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports'
BINS=(('[2.1,3)',2.1,3.0),('[3,5)',3.0,5.0),('[5,+inf)',5.0,float('inf')))

def indicators(cohort, transformed, gts, rematched):
    same=np.zeros(len(cohort),np.float64); any_tp=np.zeros(len(cohort),np.float64)
    for start in range(0,len(cohort),4096):
        chunk=cohort[start:start+4096]
        if not chunk: continue
        a=torch.tensor([R.rb(transformed[p]) for p,g in chunk],dtype=torch.float32,device=R.DEV)
        b=torch.tensor([R.rb(gts[g]) for p,g in chunk],dtype=torch.float32,device=R.DEV)
        same[start:start+len(chunk)]=(R.IOU(a,b).diag().detach().cpu().numpy()>=.75)
    for k,(p,_) in enumerate(cohort): any_tp[k]=float(p in rematched)
    return same,any_tp

def bootstrap(images, values, seed):
    unique=np.unique(images); groups={x:np.where(images==x)[0] for x in unique}; rng=np.random.default_rng(seed)
    vals=[]
    for _ in range(1000):
        pick=rng.choice(unique,len(unique),replace=True); idx=np.concatenate([groups[x] for x in pick]); vals.append(float(values[idx].mean()) if len(idx) else 0.0)
    return float(np.quantile(vals,.025)),float(np.quantile(vals,.975))

def run_unit(cell):
    ds,det,pp,gp=R.CELLS[cell]; preds,gts=R.load(ROOT/pp),R.load(ROOT/gp); base=R.evaluate_native(preds,gts,details=False)
    base_m={row['pred_index']:gts[row['gt_index']] for row in base['m50']}
    cohort=[(row['pred_index'],row['gt_index']) for row in base['m75'] if R.ar(gts[row['gt_index']])>=2.1]
    conditions={}
    for name,track,dose in (('P','P',15),('D','D',15),('+','P',15),('-','P',-15)):
        transformed=R.transform(preds,dose,track,base_m); evaluated=R.evaluate_native(transformed,gts,details=False)
        rematched={row['pred_index'] for row in evaluated['m75']}; conditions[name]=indicators(cohort,transformed,gts,rematched)
    rows=[]; boots=[]
    for bin_name,low,high in BINS:
        idx=np.asarray([k for k,(_,g) in enumerate(cohort) if low<=R.ar(gts[g])<high],dtype=int)
        images=np.asarray([str(gts[cohort[k][1]]['image_id']) for k in idx],dtype=object)
        for name in ('P','D','+','-','S'):
            if name=='S': same=(conditions['+'][0][idx]+conditions['-'][0][idx])/2; rem=(conditions['+'][1][idx]+conditions['-'][1][idx])/2
            else: same=conditions[name][0][idx]; rem=conditions[name][1][idx]
            same_rate=float(same.mean()) if len(idx) else 0.; rem_rate=float(rem.mean()) if len(idx) else 0.
            slo,shi=bootstrap(images,same,20260806+len(rows)) if len(idx) else (0.,0.); rlo,rhi=bootstrap(images,rem,20260806+100+len(rows)) if len(idx) else (0.,0.)
            rows.append({'cell':cell,'dataset':ds,'detector':det,'track':name,'dose_deg':15,'ar_bin':bin_name,
                         'baseline_cohort_size':len(idx),'same_pair_survival':same_rate,'rematched_any_tp_survival':rem_rate,
                         'same_pair_ci_low':slo,'same_pair_ci_high':shi,'rematched_ci_low':rlo,'rematched_ci_high':rhi,
                         'status':'PASS_FIXED_BASELINE_COHORT_R011'})
            boots.append({'cell':cell,'track':name,'dose_deg':15,'ar_bin':bin_name,'reps':1000,'seed':'20260806+row_index',
                          'same_pair_ci_low':slo,'same_pair_ci_high':shi,'rematched_ci_low':rlo,'rematched_ci_high':rhi})
    payload={'rows':rows,'bootstrap':boots}; (OUT/f"survival_unit_{cell.replace('/','_')}.json").write_text(json.dumps(payload)+'\n')

def aggregate():
    rows=[];boots=[]
    for path in sorted(OUT.glob('survival_unit_*.json')):
        value=json.loads(path.read_text());rows.extend(value['rows']);boots.extend(value['bootstrap'])
    for name,data in (('baseline_tp_survival_r011.csv',rows),('baseline_tp_survival_bootstrap_r011.csv',boots)):
        with (REP/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]) if data else ['status'],lineterminator='\n');writer.writeheader();writer.writerows(data)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--unit',choices=R.CELLS);parser.add_argument('--aggregate',action='store_true');args=parser.parse_args()
    if args.unit: run_unit(args.unit)
    if args.aggregate: aggregate()
