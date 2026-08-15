#!/usr/bin/env python3
"""Execute real temporary-copy mutations against the same r037 raw validator."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
import pandas as pd

def write_frame(path: Path, frame: pd.DataFrame):
    path.unlink()
    (frame.to_parquet(path,index=False,compression="zstd") if path.suffix==".parquet" else frame.to_csv(path,index=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--validator",type=Path,required=True); ap.add_argument("--views",type=Path,required=True); ap.add_argument("--raw",type=Path,required=True); ap.add_argument("--reference",type=Path,required=True); ap.add_argument("--work",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    if a.work.exists(): shutil.rmtree(a.work)
    a.work.mkdir(parents=True)
    mutations=[]
    def mutate(name,fn):
        root=a.work/name; shutil.copytree(a.reference,root,copy_function=os.link)
        fn(root)
        cmd=[sys.executable,str(a.validator),"--phase","validate","--views",str(a.views),"--output",str(a.raw),"--reference",str(root),"--validation-out",str(root/"should_not_pass.json")]
        p=subprocess.run(cmd,text=True,capture_output=True)
        mutations.append({"mutation":name,"command":cmd,"exit_code":p.returncode,"rejected":p.returncode!=0,"stdout":p.stdout[-1000:],"stderr":p.stderr[-2000:]})
    def numeric(root,file,col):
        p=root/file; d=pd.read_parquet(p) if p.suffix==".parquet" else pd.read_csv(p); d.loc[0,col]=float(d.loc[0,col])+.123456; write_frame(p,d)
    mutate("registered_increment_GCT_minus_G",lambda r:numeric(r,"t2_evidence_increment.csv","Delta_rho"))
    mutate("detection_score_removed_from_GC",lambda r:numeric(r,"target_predictions_common_support.parquet","GC_mean"))
    mutate("fixed_observed_ranks",lambda r:numeric(r,"bootstrap_replicates.parquet","Delta_rho"))
    def absolute_coverage(root):
        p=root/"t3_interval_validity.csv"; d=pd.read_csv(p); d.loc[0,"overall_validity_pass"]=not bool(d.loc[0,"overall_validity_pass"]); write_frame(p,d)
    mutate("absolute_coverage_deviation",absolute_coverage)
    mutate("class_by_ar_primary_bucket",lambda r:numeric(r,"t3_interval_validity.csv","supported_buckets"))
    mutate("interval_score_penalty",lambda r:numeric(r,"interval_predictions.parquet","IS_GCT"))
    def final_token(root):
        p=root/"judgment_final.json"; d=json.loads(p.read_text()); d["candidate"]="TAMPERED_PROCEED"; p.unlink(); p.write_text(json.dumps(d,indent=2)+"\n")
    mutate("final_token",final_token)
    def fit_ledger(root):
        p=root/"fit_ledger.jsonl"; rows=p.read_text().splitlines(); d=json.loads(rows[0]); d["target_label_rows_in_fit"]=1; rows[0]=json.dumps(d,sort_keys=True); p.unlink(); p.write_text("\n".join(rows)+"\n")
    mutate("target_label_fit_ledger",fit_ledger)
    if not all(x["rejected"] for x in mutations): raise RuntimeError("one or more mutations escaped")
    result={"schema_version":1,"status":"PASS","validator":str(a.validator),"mutation_count":len(mutations),"all_rejected":True,"mutations":mutations}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    shutil.rmtree(a.work)
if __name__=="__main__": main()
