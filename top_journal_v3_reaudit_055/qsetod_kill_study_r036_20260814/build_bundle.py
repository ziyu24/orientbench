#!/usr/bin/env python3
"""Build the portable r036 replay bundle without duplicating the frozen r034 bundle."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PERSIST=ROOT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
BUNDLE=ROOT/"audit_bundles/r036"


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8<<20),b""): h.update(block)
    return h.hexdigest()


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,destination)


def main():
    BUNDLE.mkdir(parents=True,exist_ok=True)
    for relative in ["inputs","endpoint_audit","implementation_a","implementation_b","comparator"]:
        for source in sorted((PERSIST/relative).rglob("*")):
            if source.is_file(): copy(source,BUNDLE/relative/source.relative_to(PERSIST/relative))
    for name in ["judgment.json","fit_target_label_guard.csv","artifact_manifest.csv"]: copy(PERSIST/name,BUNDLE/name)
    for name in ["audit_protocol.json","DECISIVE_REPORT.md","deviation_ledger.csv","resource_usage.json","execution_summary.json","execution_ledger.csv","artifact_manifest.csv"]: copy(HERE/name,BUNDLE/"execution"/name)
    for relative in ["validation/validation.json","mutations/mutation_results.json"]: copy(HERE/relative,BUNDLE/"execution"/relative)
    for name in ["prepare_inputs.py","audit_endpoints.py","implementation_a.py","implementation_b.py","multimodality_a.py","multimodality_b.py","compare_ab.py","finalize_results.py","validate_r036.py","run_mutations.py","verify_bundle_manifest.py"]:
        source=HERE/name
        if source.exists(): copy(source,BUNDLE/"code"/name)
    reference={"schema":"r036_external_reference_v1","r034_bundle_path":"audit_bundles/r034","r034_bundle_manifest_sha256":sha(ROOT/"audit_bundles/r034/bundle_manifest.csv"),"relationship":"r036 prepared input is derived from r034 rows plus immutable frozen feature/matched-geometry assets; r034 bundle itself is not duplicated","can_recompute":True}
    (BUNDLE/"external_reference_r034.json").write_text(json.dumps(reference,indent=2,sort_keys=True)+"\n")
    records=[]
    for path in sorted(BUNDLE.rglob("*")):
        if path.is_file() and path.name!="bundle_manifest.csv": records.append({"path":str(path.relative_to(BUNDLE)),"bytes":path.stat().st_size,"sha256":sha(path)})
    if any(row["bytes"]>80*1024*1024 for row in records): raise RuntimeError("bundle object exceeds 80 MiB")
    pd.DataFrame(records).to_csv(BUNDLE/"bundle_manifest.csv",index=False)
    print(json.dumps({"files":len(records),"bytes":sum(x["bytes"] for x in records),"largest":max(x["bytes"] for x in records)},sort_keys=True))


if __name__=="__main__": main()
