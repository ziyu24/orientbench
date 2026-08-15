#!/usr/bin/env python3
"""Fieldwise A/B comparator for r037."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

TABLES=["source_oof_predictions.parquet","target_predictions_common_support.parquet","bootstrap_replicates.parquet","t2_evidence_increment.csv","t3_interval_validity.csv","t3_set_gain.csv","interval_predictions.parquet"]

def frame(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix==".parquet" else pd.read_csv(path)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--a",type=Path,required=True); ap.add_argument("--b",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    out=[]; total=0; maximum=0.
    for name in TABLES:
        x,y=frame(a.a/name),frame(a.b/name)
        if list(x.columns)!=list(y.columns) or len(x)!=len(y): raise RuntimeError(f"schema mismatch {name}")
        for col in x.columns:
            total+=len(x)
            if pd.api.types.is_numeric_dtype(x[col]):
                xa,ya=x[col].to_numpy(float),y[col].to_numpy(float); diff=np.abs(xa-ya); same=np.all((diff<=1e-10)|(np.isnan(xa)&np.isnan(ya)))
                maximum=max(maximum,float(np.nanmax(diff)) if len(diff) and not np.isnan(diff).all() else 0.)
            else: same=x[col].fillna("<NA>").astype(str).equals(y[col].fillna("<NA>").astype(str))
            if not same: raise RuntimeError(f"field mismatch {name}:{col}")
        out.append({"object":name,"rows":len(x),"columns":len(x.columns),"status":"PASS"})
    for name in [p.name for p in sorted((a.a/"multiplicities").glob("*.npz"))]:
        xa=np.load(a.a/"multiplicities"/name,allow_pickle=False); xb=np.load(a.b/"multiplicities"/name,allow_pickle=False)
        if not np.array_equal(xa["multiplicities"],xb["multiplicities"]) or not np.array_equal(xa["clusters"],xb["clusters"]): raise RuntimeError(f"multiplicity mismatch {name}")
        out.append({"object":f"multiplicities/{name}","rows":len(xa["multiplicities"]),"columns":xa["multiplicities"].shape[1],"status":"PASS"})
    ja=json.loads((a.a/"judgment_final.json").read_text()); jb=json.loads((a.b/"judgment_final.json").read_text()); ja.pop("implementation"); jb.pop("implementation")
    if ja!=jb: raise RuntimeError("judgment mismatch")
    result={"schema_version":1,"status":"PASS","atol":1e-10,"rtol":0,"compared_fields":total,"max_abs_diff":maximum,"objects":out,"final_judgment":ja}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
