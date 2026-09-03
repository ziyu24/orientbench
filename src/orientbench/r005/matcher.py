"""Frozen theta-free matcher shared by r005 trainval and test audits."""
from __future__ import annotations
import math
import numpy as np

def global_match(gt: np.ndarray, pred: np.ndarray) -> list[tuple[int,int]]:
    """All eligible pairs, global `(cost, gt_index, pred_index)` greedy order."""
    candidates=[]
    for gi,g in enumerate(gt):
        for pi,p in enumerate(pred):
            dc=math.hypot(float(g[0]-p[0]),float(g[1]-p[1]))/max(math.sqrt(max(float(g[2]*g[3]),1.)),1.)
            ar=float(p[2]*p[3])/max(float(g[2]*g[3]),1e-9)
            se=sum(abs(math.log(max(float(x),1e-9)/max(float(y),1e-9))) for x,y in zip(sorted(g[2:4]),sorted(p[2:4])))
            if dc<=.5 and .25<=ar<=4 and se<=math.log(4): candidates.append((dc+se,gi,pi))
    used_g=set();used_p=set(); out=[]
    for _,gi,pi in sorted(candidates):
        if gi not in used_g and pi not in used_p:
            used_g.add(gi);used_p.add(pi);out.append((gi,pi))
    return out

def counterexample() -> bool:
    # p0 is valid for both GTs; p1 is valid only for g0.  A GT-order matcher
    # takes p0 for g0 (its local minimum) and leaves g1 unmatched, whereas the
    # global order takes p0->g1 first and preserves both GTs.
    gt=np.array([[0.,0.,10.,2.,0.],[4.,0.,10.,2.,0.]])
    pred=np.array([[2.2,0.,10.,2.,0.],[-2.21,0.,10.,2.,0.]])
    global_pairs=set(global_match(gt,pred))
    sequential=[]; used=set()
    for gi,g in enumerate(gt):
        options=[]
        for pi,p in enumerate(pred):
            dc=math.hypot(float(g[0]-p[0]),float(g[1]-p[1]))/math.sqrt(float(g[2]*g[3]))
            ar=float(p[2]*p[3])/float(g[2]*g[3])
            if dc<=.5 and .25<=ar<=4: options.append((dc,pi))
        if options:
            _,pi=min(options)
            if pi not in used: used.add(pi); sequential.append((gi,pi))
    return global_pairs=={(0,1),(1,0)} and sequential==[(0,0)]
