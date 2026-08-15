#!/usr/bin/env python3
"""Build the portable, non-self-hashing r037 audit bundle."""
from __future__ import annotations
import argparse, csv, hashlib, json, shutil
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""): h.update(x)
    return h.hexdigest()
def copy(src,dst): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def tree(src,dst): shutil.copytree(src,dst,dirs_exist_ok=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--persistent",type=Path,required=True); ap.add_argument("--code",type=Path,required=True); ap.add_argument("--bundle",type=Path,required=True); ap.add_argument("--plan",type=Path,required=True); ap.add_argument("--replace",action="store_true"); a=ap.parse_args()
    if a.bundle.exists() and any(a.bundle.iterdir()):
        if not a.replace: raise RuntimeError("bundle must be empty")
        shutil.rmtree(a.bundle)
    a.bundle.mkdir(parents=True,exist_ok=True)
    for p in sorted(a.code.glob("*.py")): copy(p,a.bundle/"code"/p.name)
    copy(a.plan,a.bundle/"protocol"/"sug.md")
    tree(a.persistent/"runtime_views",a.bundle/"views")
    tree(a.persistent/"implementation_a",a.bundle/"implementation_a")
    tree(a.persistent/"implementation_b",a.bundle/"implementation_b")
    tree(a.persistent/"validator_monitored_strict",a.bundle/"validator_recompute")
    for name in ["comparator","validation","mutations"]: tree(a.persistent/name,a.bundle/name)
    for p in sorted((a.persistent/"resource_logs").glob("validator_strict_*.json")): copy(p,a.bundle/"resource_logs"/p.name)
    for name in ["execution_summary.json","multimodality_status.json","resource_usage.json"]: copy(a.persistent/name,a.bundle/"execution"/name)
    copy(Path("audit_bundles/r036/endpoint_audit/endpoint_consumption_audit.csv"),a.bundle/"endpoint_inventory"/"endpoint_consumption_audit.csv")
    identity={"schema_version":1,"r036_rows":{"git_blob_oid":"1b348e35dfbe0a699a7bc6cbe79e639fb25384f5","bytes":34796105,"sha256":"bb4184089a0cb9e0584cdf9fe340fe76a5d831090f07a6bc0c73e4499ac8da51","copied":False,"reference_path":"audit_bundles/r036/inputs/qsetod_rows.parquet"},"r036_bundle_manifest":{"git_blob_oid":"68da07a9c4c2864a4f4070d0213ba803cbf2a8fd","bytes":5668,"sha256":"f199aeece6fa4595e560520d08c96c9d4b016c3960d727c5c6249471e1d2891f"},"inventory_not_authorization":True,"clean_endpoint_access_count":0}
    (a.bundle/"input_identity.json").write_text(json.dumps(identity,indent=2,sort_keys=True)+"\n")
    manifest=a.bundle/"bundle_manifest.csv"; rows=[]
    for p in sorted(x for x in a.bundle.rglob("*") if x.is_file() and x!=manifest):
        if p.stat().st_size>=80*1024*1024: raise RuntimeError(f"Git object >=80MiB: {p}")
        rows.append({"relative_path":str(p.relative_to(a.bundle)),"bytes":p.stat().st_size,"sha256":sha(p),"self_reference":False})
    rows.append({"relative_path":"bundle_manifest.csv","bytes":"N/A_SELF_REFERENCE","sha256":"N/A_SELF_REFERENCE","self_reference":True})
    with manifest.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256","self_reference"],lineterminator="\n"); w.writeheader(); w.writerows(rows)
if __name__=="__main__": main()
