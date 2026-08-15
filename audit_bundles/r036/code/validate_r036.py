#!/usr/bin/env python3
"""Raw-layer validator for r036; derives the registered state without expected-result forcing."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor


SEED=20260814; ATOL=1e-10
CONFIGS=[("HOdet_A_to_B","A","B"),("HOdet_A_to_C","A","C"),("HOdet_BC_to_A","BC","A"),("HOdata_ABC_to_D","ABC","D"),("HOdata_ABC_to_E","ABC","E"),("HOdata_ABC_to_F","ABC","F"),("HOdata_ABC_to_G","ABC","G"),("HOdata_ABC_to_H","ABC","H")]


def fail(message): raise SystemExit("VALIDATION_FAIL: "+message)
def close(a,b,tol=ATOL): return bool(np.isclose(float(a),float(b),atol=tol,rtol=0))


def fold(dataset,cluster): return int.from_bytes(hashlib.sha256(f"{SEED}|{dataset}|{cluster}".encode()).digest()[:8],"little")%5


def design(frame,classes):
    numeric=frame[["log_pred_ar","log_area"]].to_numpy(float); onehot=np.zeros((len(frame),len(classes)),float); lookup={v:i for i,v in enumerate(classes)}
    for row,value in enumerate(frame.class_name.astype(str)):
        if value in lookup: onehot[row,lookup[value]]=1
    return np.column_stack([numeric,onehot])


def quantile_model(): return HistGradientBoostingRegressor(max_iter=200,max_leaf_nodes=15,learning_rate=.05,random_state=SEED,early_stopping=False,loss="quantile",quantile=.75)


def pinball(y,q):
    d=y-q; return np.maximum(.75*d,-.25*d)


def augrc(y,pred,w=None):
    order=np.argsort(pred,kind="stable"); risk=np.clip(y[order]/90,0,1); weight=np.ones(len(y),float) if w is None else w[order].astype(float); total=weight.sum(); cumulative=np.cumsum(weight*risk)
    return float(np.sum((np.r_[0.,cumulative[:-1]/total]+cumulative/total)*weight/total/2))


def point(frame):
    y=frame.angle_error.to_numpy(float); g=frame.geom_mean.to_numpy(float); e=frame.evidence_mean.to_numpy(float); gq=frame.geom_q75.to_numpy(float); eq=frame.evidence_q75.to_numpy(float)
    rg=float(spearmanr(g,y).statistic); re=float(spearmanr(e,y).statistic); lg=float(pinball(y,gq).mean()); le=float(pinball(y,eq).mean()); ag=augrc(y,g); ae=augrc(y,e)
    return {"spearman_geom":rg,"spearman_evidence":re,"spearman_gain":re-rg,"q75_loss_geom":lg,"q75_loss_evidence":le,"q75_loss_gain":lg-le,"AUGRC_geom":ag,"AUGRC_evidence":ae,"AUGRC_gain":ag-ae,"epsilon_AUGRC":max(.0005,.02*max(abs(ag),abs(ae)))}


def spot_boot(frame,multiplicity):
    clusters=sorted(frame.cluster.astype(str).unique()); lookup={v:i for i,v in enumerate(clusters)}; ci=frame.cluster.astype(str).map(lookup).to_numpy(np.int32); mult=multiplicity.astype(float); row_w=mult[ci]
    y=frame.angle_error.to_numpy(float); g=frame.geom_mean.to_numpy(float); e=frame.evidence_mean.to_numpy(float); ry=rankdata(y); rg=rankdata(g); re=rankdata(e)
    def weighted_corr(x,z):
        sw=row_w.sum(); mx=np.sum(row_w*x)/sw; mz=np.sum(row_w*z)/sw
        return float(np.sum(row_w*(x-mx)*(z-mz))/math.sqrt(np.sum(row_w*(x-mx)**2)*np.sum(row_w*(z-mz)**2)))
    qgain=float(np.sum(row_w*(pinball(y,frame.geom_q75.to_numpy(float))-pinball(y,frame.evidence_q75.to_numpy(float))))/row_w.sum())
    return weighted_corr(re,ry)-weighted_corr(rg,ry),qgain,augrc(y,g,row_w)-augrc(y,e,row_w)


def qedges(values):
    result=np.unique(np.quantile(values,np.linspace(0,1,6))); result[0]=-np.inf; result[-1]=np.inf; return result


def conformal_recompute(rows,oof,t2,reported):
    output=[]
    for config,source_key,target_unit in CONFIGS:
        source=rows[rows.unit.isin(list(source_key))].copy().reset_index(drop=True); target=rows[rows.unit.eq(target_unit)].copy().reset_index(drop=True); classes=sorted(source.class_name.unique())
        target["geom_q75"]=quantile_model().fit(design(source,classes),source.angle_error.to_numpy(float)).predict(design(target,classes))
        source_oof=oof[oof.source_units.eq(source_key)][["row_id","geom_q75"]]; source=source.merge(source_oof,on="row_id",validate="one_to_one")
        limits=qedges(source.log_pred_ar.to_numpy(float)); source["ar_bin"]=np.searchsorted(limits[1:-1],source.log_pred_ar,side="right"); target["ar_bin"]=np.searchsorted(limits[1:-1],target.log_pred_ar,side="right")
        source["bucket"]=source.class_name.astype(str)+"|"+source.ar_bin.astype(str); target["bucket"]=target.class_name.astype(str)+"|"+target.ar_bin.astype(str); source["nc"]=source.angle_error/np.maximum(source.geom_q75,1)
        groups={k:p.nc.to_numpy(float) for k,p in source.groupby("bucket") if len(p)>=50}
        for alpha in (.1,.2):
            def threshold(values): return float(np.quantile(values,min(1.,math.ceil((len(values)+1)*(1-alpha))/len(values)),method="higher"))
            global_q=threshold(source.nc.to_numpy(float)); local={k:threshold(v) for k,v in groups.items()}; q=target.bucket.map(local).fillna(global_q).to_numpy(float); half=q*np.maximum(target.geom_q75.to_numpy(float),1); width=np.minimum(2*half,180); covered=target.angle_error.to_numpy(float)<=half; bucket_cov=pd.DataFrame({"bucket":target.bucket,"covered":covered}).groupby("bucket").covered.mean()
            output.append({"config":config,"alpha":alpha,"nominal_coverage":1-alpha,"overall_coverage":float(covered.mean()),"coverage_deviation":float(covered.mean()-(1-alpha)),"worst_bucket_coverage":float(bucket_cov.min()),"median_width_deg":float(np.median(width)),"near_full_gt150_rate":float(np.mean(width>150)),"fallback_rate":float(np.mean(~target.bucket.isin(groups))),"kill":bool(abs(covered.mean()-(1-alpha))>.05 or np.median(width)>120)})
    calc=pd.DataFrame(output).sort_values(["config","alpha"]); rep=reported.sort_values(["config","alpha"])
    for column in ["nominal_coverage","overall_coverage","coverage_deviation","worst_bucket_coverage","median_width_deg","near_full_gt150_rate","fallback_rate"]:
        if np.max(np.abs(calc[column].to_numpy(float)-rep[column].to_numpy(float)))>ATOL: fail("T4 raw recompute "+column)
    if not np.array_equal(calc.kill.to_numpy(bool),rep.kill.to_numpy(bool)): fail("T4 kill recompute")
    return bool(calc.kill.any())


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--project",type=Path,required=True); parser.add_argument("--persistent",type=Path); parser.add_argument("--execution",type=Path); parser.add_argument("--protocol",type=Path); parser.add_argument("--t2",type=Path); parser.add_argument("--t4",type=Path); parser.add_argument("--judgment",type=Path); parser.add_argument("--fit-guard",type=Path); parser.add_argument("--output",type=Path); args=parser.parse_args()
    persistent=args.persistent or args.project/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"; execution=args.execution or args.project/"top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814"; a=persistent/"implementation_a"; b=persistent/"implementation_b"
    protocol=json.loads((args.protocol or execution/"audit_protocol.json").read_text())
    expected={"seed":SEED,"bootstrap_replicates":10000,"cross_folds":5,"KILL_E_spearman_floor":.03,"conformal_coverage_tolerance":.05,"conformal_median_width_kill_deg":120.,"dip_p_threshold":.01,"delta_BIC_threshold":10.,"PRUNE_M_row_fraction_threshold":.10,"validator_output_forcing":False,"target_labels_in_fit":False}
    for key,value in expected.items():
        if protocol.get(key)!=value: fail("protocol mutation "+key)
    if "source AR quintiles" not in protocol.get("common_support_definition",""): fail("common-support mutation")
    rows=pd.read_parquet(persistent/"inputs/qsetod_rows.parquet")
    if len(rows)!=616184 or rows.row_id.duplicated().any() or set(rows.unit)!=set("ABCDEFGH"): fail("prepared rows identity")
    if np.max(np.abs(np.abs(rows.signed_residual_deg)-rows.angle_error))>2e-5: fail("angle residual identity")
    actual_fold=np.asarray([fold(str(d),str(c)) for d,c in zip(rows.dataset,rows.cluster)])
    if not np.array_equal(actual_fold,rows.fold.to_numpy()): fail("fold mutation")
    guard=pd.read_csv(args.fit_guard or persistent/"fit_target_label_guard.csv")
    if len(guard)!=8 or guard.target_angle_label_rows_in_fit.sum()!=0 or not guard.status.eq("PASS").all(): fail("target label fit guard")
    comp=json.loads((persistent/"comparator/comparator.json").read_text())
    if comp.get("status")!="PASS" or comp.get("atol")!=ATOL: fail("A/B comparator")
    t2=pd.read_csv(args.t2 or a/"t2_evidence_increment.csv"); predictions=pd.read_parquet(a/"target_predictions_common_support.parquet"); reps=pd.read_parquet(a/"bootstrap_replicates.parquet"); mult_a=np.load(a/"bootstrap_multiplicities.npz"); mult_b=np.load(b/"bootstrap_multiplicities.npz")
    if len(t2)!=8 or set(t2.config)!=set(x[0] for x in CONFIGS): fail("T2 config family")
    for config_number,(config,_,_) in enumerate(CONFIGS):
        frame=predictions[predictions.config.eq(config)]; report=t2[t2.config.eq(config)].iloc[0]; metrics=point(frame)
        for key,value in metrics.items():
            if not close(value,report[key]): fail(f"T2 point {config} {key}")
        distribution=reps[reps.config.eq(config)].sort_values("replicate")
        for name in ["spearman_gain","q75_loss_gain","AUGRC_gain"]:
            if not close(np.quantile(distribution[name],.025),report[name+"_ci_low"]) or not close(np.quantile(distribution[name],.975),report[name+"_ci_high"]): fail(f"T2 CI {config} {name}")
        clusters=sorted(frame.cluster.astype(str).unique()); rng=np.random.RandomState(SEED+config_number); generated=np.empty_like(mult_a[config])
        for replicate in range(10000): generated[replicate]=np.bincount(rng.randint(0,len(clusters),len(clusters)),minlength=len(clusters))
        if not np.array_equal(generated,mult_a[config]) or not np.array_equal(generated,mult_b[config]): fail("multiplicity "+config)
        for replicate in (0,4999,9999):
            got=np.asarray(spot_boot(frame,generated[replicate])); wanted=distribution.loc[distribution.replicate.eq(replicate),["spearman_gain","q75_loss_gain","AUGRC_gain"]].to_numpy(float)[0]
            if np.max(np.abs(got-wanted))>ATOL: fail(f"bootstrap spot {config} {replicate}")
        positive=bool(report.spearman_gain_ci_low>0 and report.q75_loss_gain_ci_low>0 and report.AUGRC_gain_ci_low>0); below=bool(report.spearman_gain<.03 and report.AUGRC_gain<report.epsilon_AUGRC); witness=positive and not below
        if witness!=bool(report.evidence_witness): fail("evidence witness "+config)
    kill_e=bool((~t2.evidence_witness.astype(bool)).all())
    t4=pd.read_csv(args.t4 or a/"t4_source_only_calibration.csv")
    if len(t4)!=16 or not np.allclose(t4.nominal_coverage,1-t4.alpha,atol=0,rtol=0): fail("T4 nominal mutation")
    oof=pd.read_parquet(a/"source_oof_predictions.parquet"); kill_c=conformal_recompute(rows,oof,t2,t4)
    t3=pd.read_csv(a/"t3_multimodality_strata.csv"); fraction=float(t3.loc[(t3.dip_p_asymptotic<.01)&(t3.delta_BIC_two_vs_one>10),"rows"].sum()/t3.rows.sum()); prune=bool(fraction<.10)
    summary=json.loads((a/"t3_multimodality_summary.json").read_text())
    if not close(fraction,summary["multimodal_row_weighted_fraction"]) or prune!=summary["PRUNE_M"]: fail("T3 decision")
    endpoint=json.loads((persistent/"endpoint_audit/summary.json").read_text()); final=json.loads((args.judgment or persistent/"judgment.json").read_text()); state="QSETOD_KILLED_ON_PAPER" if kill_e else "QSETOD_EVIDENCE_ONLY" if kill_c else "QSETOD_PROCEED_CANDIDATE"
    derived={"KILL_E":kill_e,"KILL_C":kill_c,"PRUNE_M":prune,"candidate_state":state,"evidence_witnesses":int(t2.evidence_witness.sum()),"multimodal_row_weighted_fraction":fraction,"clean_endpoint_count":endpoint["clean_present_count"]}
    for key,value in derived.items():
        if isinstance(value,float):
            if not close(value,final.get(key)): fail("judgment "+key)
        elif final.get(key)!=value: fail("judgment "+key)
    result={"schema":"r036_raw_validation_v1","status":"PASS","rows":len(rows),"T2_configurations":8,"bootstrap_replicates":10000,"bootstrap_spot_recomputations":24,"T4_rows":16,"T3_strata":len(t3),"derived":derived,"validator_output_forcing":False}
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__": main()
