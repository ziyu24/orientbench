#!/usr/bin/env python3
"""Independent implementation B of the r036 axial-residual multimodality audit."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy
import pandas
from scipy.special import i0e, logsumexp


PROJECT=Path(__file__).resolve().parents[2]
SOURCE=PROJECT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/inputs/qsetod_rows.parquet"


def increasing_projection(sequence):
    blocks=[]
    for number in sequence.astype(float):
        blocks.append([number,1,1])
        while len(blocks)>1 and blocks[-2][0]>blocks[-1][0]:
            left,right=blocks[-2],blocks[-1]; mass=left[1]+right[1]
            blocks[-2]=[(left[0]*left[1]+right[0]*right[1])/mass,mass,left[2]+right[2]]; blocks.pop()
    answer=[]
    for mean,_,length in blocks: answer.extend([mean]*length)
    return numpy.asarray(answer,float)


def dip_projection(sample):
    count=len(sample)
    if count<5 or numpy.ptp(sample)<=1e-12: return 0.,1.
    number_bins=min(128,max(8,int(numpy.ceil(numpy.sqrt(count))))); histogram,_=numpy.histogram(sample,bins=number_bins,range=(float(sample.min()),float(sample.max())))
    empirical=numpy.cumsum(histogram)/count; distance=1.
    for peak_position in range(number_bins):
        rise=increasing_projection(histogram[:peak_position+1]); fall=increasing_projection(histogram[peak_position:][::-1])[::-1]; peak=max(rise[-1],fall[0])
        fitted_mass=numpy.concatenate((numpy.minimum(rise[:-1],peak),[peak],numpy.minimum(fall[1:],peak))); fitted=numpy.cumsum(fitted_mass/fitted_mass.sum())
        distance=min(distance,float(numpy.max(numpy.abs(empirical-fitted))))
    return distance,min(1.,2*math.exp(-2*count*distance*distance))


def estimate_kappa(resultant):
    r=float(numpy.clip(resultant,0,.999999))
    if r<.53: k=2*r+r**3+5*r**5/6
    elif r<.85: k=-.4+1.39*r+.43/(1-r)
    else: k=1/(r**3-4*r*r+3*r)
    return float(numpy.clip(k,1e-8,500))


def normalization(k): return math.log(2*math.pi)+math.log(float(i0e(k)))+abs(k)


def log_likelihoods(angles):
    resultant=numpy.exp(1j*angles).mean(); mean=float(numpy.angle(resultant)); k=estimate_kappa(abs(resultant)); one=float(numpy.sum(k*numpy.cos(angles-mean)-normalization(k)))
    two=-numpy.inf
    for first,second in ((float(numpy.quantile(angles,.25)),float(numpy.quantile(angles,.75))),(-math.pi/2,math.pi/2),(0.,math.pi)):
        proportion=.5; k_first=k_second=1.
        for _ in range(80):
            a=numpy.log(max(proportion,1e-8))+k_first*numpy.cos(angles-first)-normalization(k_first); b=numpy.log(max(1-proportion,1e-8))+k_second*numpy.cos(angles-second)-normalization(k_second)
            denominator=logsumexp(numpy.vstack((a,b)),axis=0); membership=numpy.exp(a-denominator); n_first=float(membership.sum()); n_second=len(angles)-n_first
            if min(n_first,n_second)<1e-6: break
            z_first=numpy.sum(membership*numpy.exp(1j*angles))/n_first; z_second=numpy.sum((1-membership)*numpy.exp(1j*angles))/n_second
            updated=(n_first/len(angles),float(numpy.angle(z_first)),float(numpy.angle(z_second)),estimate_kappa(abs(z_first)),estimate_kappa(abs(z_second)))
            movement=max(abs(updated[0]-proportion),abs(updated[1]-first),abs(updated[2]-second),abs(updated[3]-k_first),abs(updated[4]-k_second)); proportion,first,second,k_first,k_second=updated
            if movement<1e-8: break
        value=float(numpy.sum(logsumexp(numpy.vstack((numpy.log(max(proportion,1e-8))+k_first*numpy.cos(angles-first)-normalization(k_first),numpy.log(max(1-proportion,1e-8))+k_second*numpy.cos(angles-second)-normalization(k_second))),axis=0)))
        two=max(two,value)
    return one,two


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); options=parser.parse_args(); options.output.mkdir(parents=True,exist_ok=True)
    data=pandas.read_parquet(SOURCE); records=[]
    for unit,unit_data in data.groupby("unit",sort=True):
        limits=numpy.unique(numpy.quantile(unit_data.log_pred_ar,numpy.linspace(0,1,6))); limits[0],limits[-1]=-numpy.inf,numpy.inf; unit_data=unit_data.copy(); unit_data["ar_bin"]=numpy.searchsorted(limits[1:-1],unit_data.log_pred_ar,side="right")
        for (category,ar_group),stratum in unit_data.groupby(["class_name","ar_bin"],sort=True):
            residual=stratum.signed_residual_deg.to_numpy(float); doubled=numpy.deg2rad(2*residual); center=math.degrees(float(numpy.angle(numpy.exp(1j*doubled).mean()))/2); recentered=(residual-center+90)%180-90; dip,pvalue=dip_projection(recentered)
            if len(stratum)>=20 and numpy.ptp(doubled)>1e-12:
                one,two=log_likelihoods(doubled); change=2*(two-one)-3*math.log(len(stratum))
            else: one=two=change=float("nan")
            records.append({"unit":unit,"dataset":str(stratum.dataset.iloc[0]),"class_name":category,"ar_bin":int(ar_group),"rows":len(stratum),"dip":dip,"dip_p_asymptotic":pvalue,"delta_BIC_two_vs_one":change,"single_loglik":one,"mixture_loglik":two,"multimodal":bool(pvalue<.01 and numpy.isfinite(change) and change>10),"insufficient_n_lt20":len(stratum)<20})
    result=pandas.DataFrame(records); result.to_csv(options.output/"t3_multimodality_strata.csv",index=False); ratio=float(result.loc[result.multimodal,"rows"].sum()/result.rows.sum())
    summary={"schema":"r036_multimodality_v1","strata":len(result),"rows":int(result.rows.sum()),"multimodal_strata":int(result.multimodal.sum()),"multimodal_row_weighted_fraction":ratio,"PRUNE_M":bool(ratio<.10),"dip_backend":"deterministic 128-bin maximum binned Hartigan-style dip projection; asymptotic uniform-null upper p=2exp(-2nD^2)","implementation_deviation":"diptest package absent in frozen conda environment; disclosed deterministic approximation, no dependency download permitted"}
    (options.output/"t3_multimodality_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n"); print(json.dumps(summary,sort_keys=True))


if __name__=="__main__": main()
