#!/usr/bin/env python3
"""Compute per-match risk outcomes for the frozen r009 dose tracks."""
import json, math, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'top_journal_v3_reaudit_055/scripts'))
sys.path.insert(0,str(ROOT/'scripts'))
from gpu_eval_r009 import CELLS, load, la, le90, ar
from recompute_table1_fullval_k1_065 import eval_cell
from m069_common import delta_theta_075

def run(cell,dose,track):
    pp,gp=CELLS[cell]; base=load(pp); gts=load(gp)
    _,_,_,_,base_matches=eval_cell(base,gts)
    def shifted(sign):
        return [dict(p,obb_theta=float(p['obb_theta'])+math.radians(sign*dose)) if ar(p)>=2.1 and dose else p for p in base]
    extra={}
    if track=='P': work=shifted(1)
    elif track=='D':
        matched={i:g for i,g in base_matches if ar(base[i])>=2.1}; work=[]
        for i,p in enumerate(base):
            if i not in matched or not dose: work.append(p); continue
            g=matched[i]; plus=le90(la(p)+math.radians(dose),la(g)); minus=le90(la(p)-math.radians(dose),la(g))
            work.append(dict(p,obb_theta=float(p['obb_theta'])+math.radians(dose if plus>=minus else -dose)))
        extra['matched_ar21']=len(matched)
    else:
        # Symmetric track uses the positive curve for match-level outcomes;
        # AP fields are supplied by the already aggregated symmetric report.
        work=shifted(1)
    ap50,ap75,fp,errs,matches,matches75=eval_cell(work,gts,return_tau_matches=True)
    outcomes=[]
    for i,g in matches:
        p=work[i]
        if ar(p)<2.1: continue
        e=math.degrees(le90(la(p),la(g)))
        gar=max(float(g['obb_w']),float(g['obb_h']))/max(min(float(g['obb_w']),float(g['obb_h'])),1e-6)
        th=delta_theta_075(gar)
        outcomes.append({'image_id':p['image_id'],'pred_index':i,'ar':gar,'angle_error_deg':e,'severe':int(e>th),'delta_theta_075_deg':th})
    tp75_ar21=sum(1 for i,_ in matches75 if ar(work[i])>=2.1)
    return {'cell':cell,'track':track,'dose_deg':dose,'AP50':float(ap50),'AP75':float(ap75),'fp50':int(fp),'matched_ar21':len(outcomes),'tp75_count':tp75_ar21,'outcomes':outcomes,**extra}

if __name__=='__main__':
    cell=sys.argv[1]; track=sys.argv[2]; doses=[int(x) for x in sys.argv[3:]]
    for d in doses: print(json.dumps(run(cell,d,track),ensure_ascii=False),flush=True)
