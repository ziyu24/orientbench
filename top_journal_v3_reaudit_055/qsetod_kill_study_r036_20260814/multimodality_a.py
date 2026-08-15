#!/usr/bin/env python3
"""Implementation A of the r036 residual multimodality audit."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import i0e, logsumexp


ROOT=Path(__file__).resolve().parents[2]
INPUT=ROOT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/inputs/qsetod_rows.parquet"


def pava(values: np.ndarray) -> np.ndarray:
    means=[]; weights=[]; lengths=[]
    for value in values.astype(float):
        means.append(value); weights.append(1.); lengths.append(1)
        while len(means)>=2 and means[-2]>means[-1]:
            w=weights[-2]+weights[-1]; means[-2]=(means[-2]*weights[-2]+means[-1]*weights[-1])/w; weights[-2]=w; lengths[-2]+=lengths[-1]
            means.pop(); weights.pop(); lengths.pop()
    return np.concatenate([np.repeat(mean,length) for mean,length in zip(means,lengths)])


def binned_dip(values: np.ndarray) -> tuple[float,float]:
    n=len(values)
    if n<5 or np.ptp(values)<=1e-12: return 0.,1.
    bins=min(128,max(8,int(np.ceil(np.sqrt(n)))))
    count,_=np.histogram(values,bins=bins,range=(float(values.min()),float(values.max())))
    empirical=np.cumsum(count)/n; best=1.
    for mode in range(bins):
        left=pava(count[:mode+1]); right=pava(count[mode:][::-1])[::-1]
        peak=max(left[-1],right[0]); density=np.r_[np.minimum(left[:-1],peak),peak,np.minimum(right[1:],peak)]
        density=np.maximum(density,0); fitted=np.cumsum(density/density.sum())
        best=min(best,float(np.max(np.abs(empirical-fitted))))
    p=min(1.,2*math.exp(-2*n*best*best))
    return best,p


def kappa_from_r(r):
    r=float(np.clip(r,0,0.999999))
    if r<.53: value=2*r+r**3+5*r**5/6
    elif r<.85: value=-.4+1.39*r+.43/(1-r)
    else: value=1/(r**3-4*r*r+3*r)
    return float(np.clip(value,1e-8,500))


def log_norm(kappa): return math.log(2*math.pi)+math.log(float(i0e(kappa)))+abs(kappa)


def single_loglik(phi):
    z=np.exp(1j*phi).mean(); mu=float(np.angle(z)); k=kappa_from_r(abs(z))
    return float(np.sum(k*np.cos(phi-mu)-log_norm(k)))


def mixture_loglik(phi):
    best=-np.inf
    starts=[(float(np.quantile(phi,.25)),float(np.quantile(phi,.75))),(-math.pi/2,math.pi/2),(0.,math.pi)]
    for mu1,mu2 in starts:
        weight=.5; k1=k2=1.
        for _ in range(80):
            loga=np.log(max(weight,1e-8))+k1*np.cos(phi-mu1)-log_norm(k1)
            logb=np.log(max(1-weight,1e-8))+k2*np.cos(phi-mu2)-log_norm(k2)
            normal=logsumexp(np.vstack([loga,logb]),axis=0); responsibility=np.exp(loga-normal)
            mass1=float(responsibility.sum()); mass2=len(phi)-mass1
            if min(mass1,mass2)<1e-6: break
            z1=np.sum(responsibility*np.exp(1j*phi))/mass1; z2=np.sum((1-responsibility)*np.exp(1j*phi))/mass2
            new=(mass1/len(phi),float(np.angle(z1)),float(np.angle(z2)),kappa_from_r(abs(z1)),kappa_from_r(abs(z2)))
            change=max(abs(new[0]-weight),abs(new[1]-mu1),abs(new[2]-mu2),abs(new[3]-k1),abs(new[4]-k2))
            weight,mu1,mu2,k1,k2=new
            if change<1e-8: break
        ll=float(np.sum(logsumexp(np.vstack([np.log(max(weight,1e-8))+k1*np.cos(phi-mu1)-log_norm(k1),np.log(max(1-weight,1e-8))+k2*np.cos(phi-mu2)-log_norm(k2)]),axis=0)))
        best=max(best,ll)
    return best


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    rows=pd.read_parquet(INPUT); output=[]
    for unit,unit_frame in rows.groupby("unit",sort=True):
        boundaries=np.unique(np.quantile(unit_frame.log_pred_ar,np.linspace(0,1,6))); boundaries[0]=-np.inf; boundaries[-1]=np.inf
        unit_frame=unit_frame.copy(); unit_frame["ar_bin"]=np.searchsorted(boundaries[1:-1],unit_frame.log_pred_ar,side="right")
        for (class_name,ar_bin),part in unit_frame.groupby(["class_name","ar_bin"],sort=True):
            residual=part.signed_residual_deg.to_numpy(float); phi=np.deg2rad(2*residual); mean_axial=math.degrees(float(np.angle(np.exp(1j*phi).mean()))/2)
            centered=(residual-mean_axial+90)%180-90; dip,p=binned_dip(centered)
            if len(part)>=20 and np.ptp(phi)>1e-12:
                ll1=single_loglik(phi); ll2=mixture_loglik(phi); delta_bic=2*(ll2-ll1)-3*math.log(len(part))
            else: ll1=ll2=delta_bic=float("nan")
            multi=bool(p<.01 and np.isfinite(delta_bic) and delta_bic>10)
            output.append({"unit":unit,"dataset":str(part.dataset.iloc[0]),"class_name":class_name,"ar_bin":int(ar_bin),"rows":len(part),"dip":dip,"dip_p_asymptotic":p,"delta_BIC_two_vs_one":delta_bic,"single_loglik":ll1,"mixture_loglik":ll2,"multimodal":multi,"insufficient_n_lt20":len(part)<20})
    table=pd.DataFrame(output); table.to_csv(args.output/"t3_multimodality_strata.csv",index=False)
    fraction=float(table.loc[table.multimodal,"rows"].sum()/table.rows.sum()); summary={"schema":"r036_multimodality_v1","strata":len(table),"rows":int(table.rows.sum()),"multimodal_strata":int(table.multimodal.sum()),"multimodal_row_weighted_fraction":fraction,"PRUNE_M":bool(fraction<.10),"dip_backend":"deterministic 128-bin maximum binned Hartigan-style dip projection; asymptotic uniform-null upper p=2exp(-2nD^2)","implementation_deviation":"diptest package absent in frozen conda environment; disclosed deterministic approximation, no dependency download permitted"}
    (args.output/"t3_multimodality_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n"); print(json.dumps(summary,sort_keys=True))


if __name__=="__main__": main()
