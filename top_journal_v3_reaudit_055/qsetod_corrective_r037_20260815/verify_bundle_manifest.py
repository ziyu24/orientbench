#!/usr/bin/env python3
"""Read-only verifier for all non-self r037 bundle objects."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""): h.update(x)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--bundle",type=Path,required=True); ap.add_argument("--output",type=Path); a=ap.parse_args(); rows=list(csv.DictReader((a.bundle/"bundle_manifest.csv").open())); checked=0; total=0
    for row in rows:
        if row["self_reference"].lower()=="true":
            if row["bytes"]!="N/A_SELF_REFERENCE" or row["sha256"]!="N/A_SELF_REFERENCE": raise RuntimeError("bad self row")
            continue
        p=a.bundle/row["relative_path"]
        if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or sha(p)!=row["sha256"]: raise RuntimeError(f"manifest mismatch {p}")
        if p.stat().st_size>=80*1024*1024: raise RuntimeError(f"oversized object {p}")
        checked+=1; total+=p.stat().st_size
    result={"schema_version":1,"status":"PASS","non_self_objects_checked":checked,"non_self_bytes_checked":total,"self_reference_rows":1,"max_object_lt_80MiB":True}
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    else: print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
