#!/usr/bin/env python3
"""Strict r036 A/B comparator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ATOL=1e-10


def compare_csv(a: Path,b: Path,key:list[str],name:str):
    left=pd.read_csv(a).sort_values(key).reset_index(drop=True); right=pd.read_csv(b).sort_values(key).reset_index(drop=True)
    if list(left.columns)!=list(right.columns) or len(left)!=len(right): raise RuntimeError(f"{name} shape/schema")
    if not left[key].astype(str).equals(right[key].astype(str)): raise RuntimeError(f"{name} keys")
    checks=0; maximum=0.
    for column in left.columns:
        if column in key: continue
        if pd.api.types.is_numeric_dtype(left[column]):
            x=left[column].to_numpy(float); y=right[column].to_numpy(float); finite=np.isfinite(x)|np.isfinite(y)
            if not np.array_equal(np.isnan(x),np.isnan(y)): raise RuntimeError(f"{name} nan {column}")
            difference=float(np.max(np.abs(x[finite]-y[finite]))) if finite.any() else 0.; maximum=max(maximum,difference); checks+=int(finite.sum())
            if difference>ATOL: raise RuntimeError(f"{name} {column} max={difference}")
        else:
            if not left[column].astype(str).equals(right[column].astype(str)): raise RuntimeError(f"{name} token {column}")
            checks+=len(left)
    return {"table":name,"rows":len(left),"field_checks":checks,"max_abs_difference":maximum}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--a",type=Path,required=True); parser.add_argument("--b",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    tables=[]
    tables.append(compare_csv(args.a/"t2_evidence_increment.csv",args.b/"t2_evidence_increment.csv",["config"],"t2"))
    tables.append(compare_csv(args.a/"t4_source_only_calibration.csv",args.b/"t4_source_only_calibration.csv",["config","alpha"],"t4"))
    tables.append(compare_csv(args.a/"leakage_linear_probe.csv",args.b/"leakage_linear_probe.csv",["source_units","target_z"],"leakage"))
    tables.append(compare_csv(args.a/"t3_multimodality_strata.csv",args.b/"t3_multimodality_strata.csv",["unit","class_name","ar_bin"],"t3"))
    ar=pd.read_parquet(args.a/"bootstrap_replicates.parquet").sort_values(["config","replicate"]).reset_index(drop=True); br=pd.read_parquet(args.b/"bootstrap_replicates.parquet").sort_values(["config","replicate"]).reset_index(drop=True)
    if not ar[["config","replicate"]].equals(br[["config","replicate"]]): raise RuntimeError("bootstrap keys")
    diff=float(np.max(np.abs(ar[["spearman_gain","q75_loss_gain","AUGRC_gain"]].to_numpy()-br[["spearman_gain","q75_loss_gain","AUGRC_gain"]].to_numpy())))
    if diff>ATOL: raise RuntimeError(f"bootstrap max={diff}")
    tables.append({"table":"bootstrap_replicates","rows":len(ar),"field_checks":len(ar)*3,"max_abs_difference":diff})
    am=np.load(args.a/"bootstrap_multiplicities.npz"); bm=np.load(args.b/"bootstrap_multiplicities.npz")
    if set(am.files)!=set(bm.files): raise RuntimeError("multiplicity keys")
    for key in am.files:
        if not np.array_equal(am[key],bm[key]): raise RuntimeError(f"multiplicity {key}")
    ja=json.loads((args.a/"judgment_partial.json").read_text()); jb=json.loads((args.b/"judgment_partial.json").read_text())
    for key in ["KILL_E","KILL_C","evidence_witnesses","heldout_configurations","candidate_state_before_PRUNE_M","replicates","seed"]:
        if ja[key]!=jb[key]: raise RuntimeError(f"judgment {key}")
    ma=json.loads((args.a/"t3_multimodality_summary.json").read_text()); mb=json.loads((args.b/"t3_multimodality_summary.json").read_text())
    for key in ["strata","rows","multimodal_strata","multimodal_row_weighted_fraction","PRUNE_M"]:
        if isinstance(ma[key],float):
            if abs(ma[key]-mb[key])>ATOL: raise RuntimeError(f"multimodality {key}")
        elif ma[key]!=mb[key]: raise RuntimeError(f"multimodality {key}")
    report={"schema":"r036_ab_comparator_v1","status":"PASS","atol":ATOL,"tables":tables,"multiplicity_arrays_equal":True,"judgment_equal":True,"multimodality_summary_equal":True,"total_field_checks":int(sum(x["field_checks"] for x in tables)),"max_abs_difference":float(max(x["max_abs_difference"] for x in tables))}
    (args.output/"comparator.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); pd.DataFrame(tables).to_csv(args.output/"table_comparison.csv",index=False); print(json.dumps(report,sort_keys=True))


if __name__=="__main__": main()
