#!/usr/bin/env python3
"""GPU full-evaluator kernel for r009 (no Shapely).

Uses the K1-validated mmrotate RBboxOverlaps2D implementation and rematches
the complete prediction/GT universe at each dose. This is intentionally a
small kernel used by the r009 driver; it does not alter NMS or prediction IDs.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'top_journal_v3_reaudit_055/scripts'))
from recompute_table1_fullval_k1_065 import eval_cell

CELLS = {
    'DIOR-R/22': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'DIOR-R/3': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'DIOR-R/61': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/schema/pred_b61_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'FAIR1M-v1.0/24': ('outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl'),
    'SODA-A/23': ('outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
    'SODA-A/4': ('outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
}

def load(rel):
    with (ROOT / rel).open() as f: return [json.loads(x) for x in f]

def la(p):
    return float(p['obb_theta']) + (math.pi/2 if float(p['obb_w']) < float(p['obb_h']) else 0.0)
def le90(a,b):
    d=abs(a-b)%math.pi
    return min(d,math.pi-d)
def ar(p): return max(float(p['obb_w']),float(p['obb_h']))/max(min(float(p['obb_w']),float(p['obb_h'])),1e-6)

def run(cell, dose, track='P'):
    pp, gp = CELLS[cell]; preds, gts = load(pp), load(gp)
    base=preds
    _,_,_,_,matches=eval_cell(base,gts)
    def shifted(sign):
        out=[]
        for p in base:
            if ar(p)<2.1 or not dose: out.append(p); continue
            out.append(dict(p,obb_theta=float(p['obb_theta'])+math.radians(sign*dose)))
        return out
    if track=='P': work=shifted(1); ap50,ap75,fp,errs,_=eval_cell(work,gts); extra={}
    elif track=='D':
        matched={i:g for i,g in matches if ar(base[i])>=2.1}
        work=[]
        for i,p in enumerate(base):
            if i not in matched or not dose: work.append(p); continue
            g=matched[i]; a0,b=la(p),la(g); plus=le90(a0+math.radians(dose),b); minus=le90(a0-math.radians(dose),b)
            work.append(dict(p,obb_theta=float(p['obb_theta'])+math.radians(dose if plus>=minus else -dose)))
        ap50,ap75,fp,errs,_=eval_cell(work,gts); extra={'matched_ar21':len(matched)}
    else:
        plus=shifted(1); minus=shifted(-1)
        p50,p75,pfp,pe,_=eval_cell(plus,gts); m50,m75,mfp,me,_=eval_cell(minus,gts)
        ap50,ap75,fp,errs=(p50+m50)/2,(p75+m75)/2,(pfp+mfp)/2,np.asarray([float(np.mean(pe)),float(np.mean(me))]); extra={'plus_AP50':float(p50),'minus_AP50':float(m50),'plus_AP75':float(p75),'minus_AP75':float(m75)}
    return {'cell': cell, 'track':track, 'dose_deg': dose, 'AP50': float(ap50), 'AP75': float(ap75), 'fp50': int(fp), 'angle_error_mean': float(np.mean(errs)) if len(errs) else None, 'n_pred': len(base), 'n_gt': len(gts), 'evaluator': 'GPU_RBboxOverlaps2D_K1', **extra}

if __name__ == '__main__':
    cell = sys.argv[1]; track='P'
    if '--track' in sys.argv:
        j=sys.argv.index('--track'); track=sys.argv[j+1]; argv=sys.argv[2:j]+sys.argv[j+2:]
    else: argv=sys.argv[2:]
    doses = [int(x) for x in (argv or ['0'])]
    for d in doses:
        print(json.dumps(run(cell, d, track), ensure_ascii=False), flush=True)
