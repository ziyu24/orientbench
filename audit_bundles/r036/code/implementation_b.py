#!/usr/bin/env python3
"""Independent implementation B for the r036 source-only paper-kill experiment."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import time
from pathlib import Path

import numpy
import pandas
from scipy.stats import rankdata, spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score


PROJECT = Path(__file__).resolve().parents[2]
TABLE = PROJECT / "outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/inputs/qsetod_rows.parquet"
RANDOM_SEED = 20260814
TRIALS = [
    ("HOdet_A_to_B", "A", "B"), ("HOdet_A_to_C", "A", "C"),
    ("HOdet_BC_to_A", "BC", "A"), ("HOdata_ABC_to_D", "ABC", "D"),
    ("HOdata_ABC_to_E", "ABC", "E"), ("HOdata_ABC_to_F", "ABC", "F"),
    ("HOdata_ABC_to_G", "ABC", "G"), ("HOdata_ABC_to_H", "ABC", "H"),
]
BOOT_DATA = None


def make_matrix(frame, categories, augmented):
    names = ["log_pred_ar", "log_area"] + (["u_axis", "missing_fraction", "iou_loss", "detection_score"] if augmented else [])
    numerical = frame[names].to_numpy(dtype=numpy.float64)
    categorical = numpy.zeros((len(frame), len(categories)), numpy.float64)
    lookup = {value: number for number, value in enumerate(categories)}
    for row_number, value in enumerate(frame.class_name.astype(str)):
        if value in lookup:
            categorical[row_number, lookup[value]] = 1
    return numpy.concatenate((numerical, categorical), axis=1)


def new_regressor(kind):
    options = {"max_iter": 200, "max_leaf_nodes": 15, "learning_rate": .05, "random_state": RANDOM_SEED, "early_stopping": False}
    if kind == "q75": options.update(loss="quantile", quantile=.75)
    else: options.update(loss="squared_error")
    return HistGradientBoostingRegressor(**options)


def train_models(source):
    categories = sorted(source.class_name.astype(str).unique())
    predictions = source[["row_id", "fold"]].copy()
    columns = [(False, "geom_mean", "mean"), (True, "evidence_mean", "mean"), (False, "geom_q75", "q75"), (True, "evidence_q75", "q75")]
    for _, column, _ in columns: predictions[column] = numpy.nan
    for held_fold in range(5):
        training = source[source.fold != held_fold]; held = source[source.fold == held_fold]
        for augmented, column, kind in columns:
            estimator = new_regressor(kind)
            estimator.fit(make_matrix(training, categories, augmented), training.angle_error.to_numpy(float))
            predictions.loc[held.index, column] = estimator.predict(make_matrix(held, categories, augmented))
    if predictions.isna().any().any(): raise ValueError("incomplete independent OOF")
    fitted = {}
    for augmented, column, kind in columns:
        fitted[column] = new_regressor(kind).fit(make_matrix(source, categories, augmented), source.angle_error.to_numpy(float))
    return categories, fitted, predictions


def quintile_limits(values):
    boundary = numpy.unique(numpy.quantile(values, numpy.linspace(0, 1, 6), method="linear"))
    if len(boundary) < 2: boundary = numpy.array([-numpy.inf, numpy.inf])
    boundary[0], boundary[-1] = -numpy.inf, numpy.inf
    return boundary


def bin_number(values, limits): return numpy.searchsorted(limits[1:-1], values, side="right").astype(numpy.int16)


def restrict_common(source, target):
    ar, size = quintile_limits(source.log_pred_ar.to_numpy(float)), quintile_limits(source.log_area.to_numpy(float))
    common_classes = sorted(set(source.class_name).intersection(target.class_name))
    a = source[source.class_name.isin(common_classes)].copy(); b = target[target.class_name.isin(common_classes)].copy()
    for frame in (a, b):
        frame["ar_bin"] = bin_number(frame.log_pred_ar.to_numpy(float), ar); frame["size_bin"] = bin_number(frame.log_area.to_numpy(float), size)
        frame["support_cell"] = frame.class_name.astype(str)+"|"+frame.ar_bin.astype(str)+"|"+frame.size_bin.astype(str)
    allowed = set(a.support_cell).intersection(b.support_cell); b = b[b.support_cell.isin(allowed)].copy()
    if b.empty: raise ValueError("independent common support empty")
    return b


def check_loss(actual, estimate):
    difference = actual-estimate
    return numpy.maximum(.75*difference, -.25*difference)


def area_under_generalized_risk(actual, estimated, weight=None):
    permutation = numpy.argsort(estimated, kind="stable"); losses = numpy.clip(actual[permutation]/90, 0, 1)
    weights = numpy.ones(len(actual), float) if weight is None else weight[permutation].astype(float)
    total = weights.sum(); cumulative = numpy.cumsum(weights*losses)
    return float(numpy.sum((numpy.r_[0., cumulative[:-1]/total]+cumulative/total)*weights/total/2))


def summarize(frame):
    y=frame.angle_error.to_numpy(float); gm=frame.geom_mean.to_numpy(float); em=frame.evidence_mean.to_numpy(float); gq=frame.geom_q75.to_numpy(float); eq=frame.evidence_q75.to_numpy(float)
    rg=float(spearmanr(gm,y).statistic); re=float(spearmanr(em,y).statistic)
    lg=float(check_loss(y,gq).mean()); le=float(check_loss(y,eq).mean())
    ag=area_under_generalized_risk(y,gm); ae=area_under_generalized_risk(y,em)
    return {"spearman_geom":rg,"spearman_evidence":re,"spearman_gain":re-rg,"q75_loss_geom":lg,"q75_loss_evidence":le,"q75_loss_gain":lg-le,"AUGRC_geom":ag,"AUGRC_evidence":ae,"AUGRC_gain":ag-ae,"epsilon_AUGRC":max(.0005,.02*max(abs(ag),abs(ae)))}


def bootstrap_package(frame, multiplicity):
    cluster_names=sorted(frame.cluster.astype(str).unique()); positions={v:i for i,v in enumerate(cluster_names)}; ci=frame.cluster.astype(str).map(positions).to_numpy(numpy.int32)
    y=frame.angle_error.to_numpy(float); gm=frame.geom_mean.to_numpy(float); em=frame.evidence_mean.to_numpy(float)
    ranks_y=rankdata(y,method="average"); stats=[]
    for prediction in (gm,em):
        ranks_x=rankdata(prediction,method="average"); per=[]
        for cluster in range(len(cluster_names)):
            use=ci==cluster; x=ranks_x[use]; z=ranks_y[use]
            per.append([x.sum(),z.sum(),numpy.square(x).sum(),numpy.square(z).sum(),(x*z).sum(),use.sum()])
        stats.append(numpy.asarray(per,float))
    difference=check_loss(y,frame.geom_q75.to_numpy(float))-check_loss(y,frame.evidence_q75.to_numpy(float))
    return {"cluster":ci,"actual":y,"geom":gm,"evidence":em,"stats":stats,"loss_sum":numpy.bincount(ci,weights=difference,minlength=len(cluster_names)),"count":numpy.bincount(ci,minlength=len(cluster_names)).astype(float),"multiplicity":multiplicity}


def correlation(stats, weights):
    sx,sy,sxx,syy,sxy,n=weights@stats
    return float((sxy-sx*sy/n)/math.sqrt(max((sxx-sx*sx/n)*(syy-sy*sy/n),1e-30)))


def start_worker(package):
    global BOOT_DATA
    BOOT_DATA=package


def calculate_replicates(bounds):
    begin,end=bounds; answer=numpy.empty((end-begin,3),float)
    for offset,replicate in enumerate(range(begin,end)):
        multiplicity=BOOT_DATA["multiplicity"][replicate].astype(float); row_weight=multiplicity[BOOT_DATA["cluster"]]
        gain_rho=correlation(BOOT_DATA["stats"][1],multiplicity)-correlation(BOOT_DATA["stats"][0],multiplicity)
        gain_loss=float((multiplicity@BOOT_DATA["loss_sum"])/(multiplicity@BOOT_DATA["count"]))
        gain_area=area_under_generalized_risk(BOOT_DATA["actual"],BOOT_DATA["geom"],row_weight)-area_under_generalized_risk(BOOT_DATA["actual"],BOOT_DATA["evidence"],row_weight)
        answer[offset]=gain_rho,gain_loss,gain_area
    return begin,answer


def source_calibration(source,target,trial):
    limit=quintile_limits(source.log_pred_ar.to_numpy(float)); source=source.copy(); target=target.copy()
    source["ar_bin"]=bin_number(source.log_pred_ar.to_numpy(float),limit); target["ar_bin"]=bin_number(target.log_pred_ar.to_numpy(float),limit)
    source["bucket"]=source.class_name.astype(str)+"|"+source.ar_bin.astype(str); target["bucket"]=target.class_name.astype(str)+"|"+target.ar_bin.astype(str)
    source["nc"]=source.angle_error.to_numpy(float)/numpy.maximum(source.geom_q75.to_numpy(float),1)
    groups={key:part.nc.to_numpy(float) for key,part in source.groupby("bucket") if len(part)>=50}; answer=[]
    for alpha in (.1,.2):
        def threshold(values):
            probability=min(1.,math.ceil((len(values)+1)*(1-alpha))/len(values)); return float(numpy.quantile(values,probability,method="higher"))
        global_value=threshold(source.nc.to_numpy(float)); local={key:threshold(value) for key,value in groups.items()}
        q=target.bucket.map(local).fillna(global_value).to_numpy(float); half=q*numpy.maximum(target.geom_q75.to_numpy(float),1); width=numpy.minimum(2*half,180); covered=target.angle_error.to_numpy(float)<=half
        group_coverage=pandas.DataFrame({"bucket":target.bucket,"covered":covered}).groupby("bucket").covered.mean()
        answer.append({"config":trial,"target_unit":str(target.unit.iloc[0]),"alpha":alpha,"nominal_coverage":1-alpha,"rows":len(target),"source_rows":len(source),"mondrian_non_sparse_buckets":len(groups),"global_threshold":global_value,"overall_coverage":float(covered.mean()),"coverage_deviation":float(covered.mean()-(1-alpha)),"worst_bucket_coverage":float(group_coverage.min()),"median_width_deg":float(numpy.median(width)),"normalized_median_width":float(numpy.median(width)/180),"near_full_gt150_rate":float(numpy.mean(width>150)),"fallback_rate":float(numpy.mean(~target.bucket.isin(groups))),"kill":bool(abs(covered.mean()-(1-alpha))>.05 or numpy.median(width)>120)})
    return answer


def probe(source,key):
    x=source[["u_axis","missing_fraction","iou_loss"]].to_numpy(float); classes=sorted(source.class_name.unique()); onehot=make_matrix(source,classes,False)[:,2:]
    outputs=[]
    for name,target in (("log_pred_ar",source.log_pred_ar.to_numpy(float)),("log_area",source.log_area.to_numpy(float)),("class_onehot",onehot)):
        prediction=numpy.empty_like(target)
        for fold in range(5):
            training=source.fold.ne(fold).to_numpy(); held=~training
            prediction[held]=Ridge(alpha=1.).fit(x[training],target[training]).predict(x[held])
        outputs.append({"source_units":key,"target_z":name,"rows":len(source),"cross_fitted_R2":float(r2_score(target,prediction,multioutput="variance_weighted"))})
    return outputs


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); parser.add_argument("--replicates",type=int,default=10000); parser.add_argument("--workers",type=int,default=96); args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True); started=time.time()
    table=pandas.read_parquet(TABLE); fitted_sources={}; leak=[]
    for key in ("A","BC","ABC"):
        source=table[table.unit.isin(list(key))].copy().reset_index(drop=True); categories,estimators,oof=train_models(source); fitted_sources[key]=(source,categories,estimators,oof); leak.extend(probe(source,key))
    pandas.DataFrame(leak).to_csv(args.output/"leakage_linear_probe.csv",index=False)
    result=[]; calibration=[]; multiplicities={}; replicates=[]
    for trial_number,(trial,key,target_unit) in enumerate(TRIALS):
        source,categories,estimators,oof=fitted_sources[key]; target=table[table.unit==target_unit].copy().reset_index(drop=True)
        for augmented,column in ((False,"geom_mean"),(True,"evidence_mean"),(False,"geom_q75"),(True,"evidence_q75")):
            target[column]=estimators[column].predict(make_matrix(target,categories,augmented))
        selected=restrict_common(source,target); point=summarize(selected); clusters=sorted(selected.cluster.astype(str).unique()); random=numpy.random.RandomState(RANDOM_SEED+trial_number)
        count=numpy.empty((args.replicates,len(clusters)),numpy.int16)
        for replicate in range(args.replicates): count[replicate]=numpy.bincount(random.randint(0,len(clusters),len(clusters)),minlength=len(clusters))
        multiplicities[trial]=count; package=bootstrap_package(selected,count); distribution=numpy.empty((args.replicates,3),float); width=math.ceil(args.replicates/args.workers); jobs=[(x,min(x+width,args.replicates)) for x in range(0,args.replicates,width)]
        with multiprocessing.get_context("fork").Pool(args.workers,initializer=start_worker,initargs=(package,)) as pool:
            for first,block in pool.imap_unordered(calculate_replicates,jobs): distribution[first:first+len(block)]=block
        ci={}; names=["spearman_gain","q75_loss_gain","AUGRC_gain"]
        for j,name in enumerate(names): ci[name+"_ci_low"]=float(numpy.quantile(distribution[:,j],.025)); ci[name+"_ci_high"]=float(numpy.quantile(distribution[:,j],.975))
        all_positive=all(ci[x+"_ci_low"]>0 for x in names); below=point["spearman_gain"]<.03 and point["AUGRC_gain"]<point["epsilon_AUGRC"]
        result.append({"config":trial,"source_units":key,"target_unit":target_unit,"target_dataset":str(target.dataset.iloc[0]),"common_support_rows":len(selected),**point,**ci,"all_increment_ci_positive":all_positive,"below_both_preregistered_floors":below,"evidence_witness":bool(all_positive and not below)})
        replicates.append(pandas.DataFrame({"config":trial,"replicate":numpy.arange(args.replicates),"spearman_gain":distribution[:,0],"q75_loss_gain":distribution[:,1],"AUGRC_gain":distribution[:,2]}))
        source_oof=source.merge(oof[["row_id","geom_q75"]],on="row_id",validate="one_to_one"); calibration.extend(source_calibration(source_oof,target,trial))
    numpy.savez_compressed(args.output/"bootstrap_multiplicities.npz",**multiplicities); pandas.concat(replicates,ignore_index=True).to_parquet(args.output/"bootstrap_replicates.parquet",index=False,compression="zstd")
    outcomes=pandas.DataFrame(result); outcomes.to_csv(args.output/"t2_evidence_increment.csv",index=False); coverage=pandas.DataFrame(calibration); coverage.to_csv(args.output/"t4_source_only_calibration.csv",index=False)
    kill_e=bool((~outcomes.evidence_witness).all()); kill_c=bool(coverage.kill.any()); state="QSETOD_KILLED_ON_PAPER" if kill_e else "QSETOD_EVIDENCE_ONLY" if kill_c else "QSETOD_PROCEED_CANDIDATE"
    judgment={"schema":"r036_judgment_partial_v1","KILL_E":kill_e,"KILL_C":kill_c,"evidence_witnesses":int(outcomes.evidence_witness.sum()),"heldout_configurations":len(outcomes),"candidate_state_before_PRUNE_M":state,"replicates":args.replicates,"seed":RANDOM_SEED,"elapsed_seconds":time.time()-started}
    (args.output/"judgment_partial.json").write_text(json.dumps(judgment,indent=2,sort_keys=True)+"\n"); print(json.dumps(judgment,sort_keys=True))


if __name__=="__main__": main()
