"""Standalone orientation-reliability metrics. Higher scores mean more reliable."""
from __future__ import annotations
import math
import numpy as np
from scipy.stats import binom, beta
from shapely import affinity
from shapely.geometry import Polygon

def circular_distance_le90(a,b):
    d=np.abs(np.asarray(a,float)-np.asarray(b,float))%180.0
    return np.minimum(d,180.0-d)

def canonical_angle_error(pred_angle,gt_angle,pred_w=None,pred_h=None,gt_w=None,gt_h=None):
    p=np.asarray(pred_angle,float); g=np.asarray(gt_angle,float)
    if pred_w is not None: p=p+90.0*(np.asarray(pred_w)<np.asarray(pred_h))
    if gt_w is not None: g=g+90.0*(np.asarray(gt_w)<np.asarray(gt_h))
    return circular_distance_le90(p,g)

def _centered_iou(ar,degree):
    p=Polygon([(-ar/2,-.5),(ar/2,-.5),(ar/2,.5),(-ar/2,.5)])
    q=affinity.rotate(p,float(degree),origin=(0,0))
    i=p.intersection(q).area
    return i/(2*ar-i)

def delta_tau(aspect_ratio,tau,tol_deg=.001):
    ar=float(aspect_ratio); tau=float(tau)
    if ar<1 or not 0<tau<1: raise ValueError("requires ar>=1 and 0<tau<1")
    lo,hi=0.,90.
    if _centered_iou(ar,hi)>=tau: return 90.
    while hi-lo>tol_deg:
        mid=(lo+hi)/2
        if _centered_iou(ar,mid)>=tau: lo=mid
        else: hi=mid
    return hi

def geometry_severe(angle_error,aspect_ratio,tau=.75):
    e=np.asarray(angle_error,float); ar=np.asarray(aspect_ratio,float)
    cut=np.array([delta_tau(x,tau) for x in ar])
    return e>cut

def risk_coverage(scores,risks):
    s=np.asarray(scores,float); r=np.asarray(risks,float); m=np.isfinite(s)&np.isfinite(r);s=s[m];r=r[m]
    o=np.argsort(-s,kind="stable"); y=np.cumsum(r[o])/np.arange(1,len(r)+1)
    return np.arange(1,len(r)+1)/len(r),y

def aurc(scores,risks):
    _,r=risk_coverage(scores,risks); return float(r.mean()) if len(r) else math.nan

def nrc(scores,risks):
    r=np.asarray(risks,float);r=r[np.isfinite(r)]; model=aurc(scores,risks)
    oracle=float(np.mean(np.cumsum(np.sort(r,kind="stable"))/np.arange(1,len(r)+1))); random=float(r.mean()); den=random-oracle
    return math.nan if abs(den)<1e-12 else (model-oracle)/den

def fixed_angle_events(angle_error):
    e=np.asarray(angle_error,float); return {f"gt_{d}deg":e>d for d in (5,10,15)}

def eligible_scene_universe(scene_ids): return np.unique(np.asarray(scene_ids,object))

def conditional_scene_risk(scene_ids,severe,selected,universe=None):
    ids=np.asarray(scene_ids,object); bad=np.asarray(severe,bool); keep=np.asarray(selected,bool)
    universe=eligible_scene_universe(ids) if universe is None else np.asarray(universe,object)
    losses=[];events=[]; selected_n=0
    for scene in universe:
        m=(ids==scene)&keep
        if not np.any(m): continue
        losses.append(float(np.mean(bad[m])));events.append(int(np.any(bad[m])));selected_n+=int(m.sum())
    return {"losses":np.asarray(losses),"events":np.asarray(events),"eligible_scenes":len(universe),"nonempty_scenes":len(losses),
            "nonempty_scene_rate":len(losses)/len(universe) if len(universe) else 0.,"selected_count":selected_n,
            "selected_instance_coverage":selected_n/len(ids) if len(ids) else 0.}

def _kl(a,b):
    a=min(max(a,1e-12),1-1e-12);b=min(max(b,1e-12),1-1e-12)
    return a*math.log(a/b)+(1-a)*math.log((1-a)/(1-b))

def hb_pvalue(rhat,alpha,n):
    if n<=0 or rhat>=alpha:return 1.
    return min(1.,math.exp(-n*_kl(rhat,alpha)),math.e*binom.cdf(math.ceil(n*rhat),n,alpha))

def hb_ucb(rhat,n,delta=.1):
    if n<=0:return math.nan
    lo,hi=float(rhat),1.
    for _ in range(60):
        mid=(lo+hi)/2
        if hb_pvalue(rhat,mid,n)<=delta:hi=mid
        else:lo=mid
    return hi

def scene_event_ucb(events,delta=.1):
    x=np.asarray(events,int);k=int(x.sum());n=len(x)
    return math.nan if not n else (1. if k==n else float(beta.ppf(1-delta,k+1,n-k)))

def cluster_bootstrap(values,clusters,reps=1000,seed=0):
    v=np.asarray(values,float);c=np.asarray(clusters,object);u=np.unique(c);by={x:np.where(c==x)[0] for x in u};rng=np.random.RandomState(seed);out=[]
    for _ in range(reps):
        pick=rng.choice(u,len(u),replace=True);idx=np.concatenate([by[x] for x in pick]);out.append(float(np.mean(v[idx])))
    return np.percentile(out,[2.5,97.5])

def certify_alpha_frontier(scores,severe,scene_ids,alphas=(.001,.0025,.005,.01),coverage_grid=(.01,.025,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.),delta=.1):
    s=np.asarray(scores,float);bad=np.asarray(severe,bool);ids=np.asarray(scene_ids,object);u=eligible_scene_universe(ids);rows=[]
    for alpha in alphas:
        chosen=None;open_sequence=True
        for cov in coverage_grid:
            t=float(np.quantile(s,1-cov));q=conditional_scene_risk(ids,bad,s>=t,u);loss=q["losses"]
            ucb=hb_ucb(float(loss.mean()),len(loss),delta) if len(loss) else math.nan;passed=bool(len(loss) and ucb<=alpha)
            if open_sequence and passed:chosen=(cov,t,q,ucb)
            else:open_sequence=False
        if chosen is None:rows.append({"alpha":alpha,"status":"INFEASIBLE","coverage":0.,"nonempty_scene_rate":0.,"selected_count":0})
        else:
            cov,t,q,ucb=chosen;rows.append({"alpha":alpha,"status":"CERTIFIED","coverage":q["selected_instance_coverage"],"nonempty_scene_rate":q["nonempty_scene_rate"],"selected_count":q["selected_count"],"threshold":t,"risk":float(q["losses"].mean()),"risk_ucb":ucb,"scene_event":float(q["events"].mean()),"scene_event_ucb":scene_event_ucb(q["events"],delta)})
    return rows
