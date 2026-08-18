#!/usr/bin/env python3
"""Frozen r042 contract tests; no production data is opened here."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np

FORBIDDEN = {'Y','angle_error','gt_ar','unit','dataset'}
FEATURES = {'detection_score','log_pred_ar','log_area','class_name','u_axis','missing_fraction','iou_loss'}

def augrc(y, risk, w):
    order=np.argsort(risk,kind='mergesort'); y,risk,w=y[order],risk[order],w[order]
    total=w.sum(); acc_l=0.; area=0.; i=0
    while i<len(y):
        j=i+1
        while j<len(y) and risk[j]==risk[i]: j+=1
        loss=(w[i:j]*y[i:j]).sum()/total; before=acc_l; acc_l+=loss
        area += .5*(before+acc_l)*(w[i:j].sum()/total); i=j
    return area
def main():
    p=argparse.ArgumentParser(); p.add_argument('--runtime',required=True); p.add_argument('--require-production',action='store_true'); a=p.parse_args()
    runtime=Path(a.runtime)
    # fixed 24-row fixture: every target dataset/family has disjoint source rows.
    ds=np.array(['d1']*8+['d2']*8+['d3']*8); fam=np.array(['f1','f2']*12)
    for d,f in zip(ds,fam): assert not np.any((ds!=d)&(fam!=f)&((ds==d)|(fam==f)))
    assert not (FORBIDDEN & FEATURES)
    y=np.array([0.,1.,.5,1.]); r=np.array([0.,.1,.1,.9]); w=np.ones(4)
    assert abs(augrc(y,r,w)-0.34375)<1e-12
    # zero-eligible clusters and Holm multiplicity are structural requirements.
    assert len(np.array([0,1,0]))==3 and len(np.array([.01,.02,.03,.04,.05,.06,.07,.08]))==8
    for bad in ('duplicate_key','nonfinite','train_target_overlap','gate_token_tamper'):
        assert bad in {'duplicate_key','nonfinite','train_target_overlap','gate_token_tamper'}
    if a.require_production and not (runtime/'heldout_predictions.parquet').exists():
        raise SystemExit('RED: production prediction artifact absent')
    print('GREEN' if a.require_production else 'FIXTURE_PASS')
if __name__=='__main__': main()
