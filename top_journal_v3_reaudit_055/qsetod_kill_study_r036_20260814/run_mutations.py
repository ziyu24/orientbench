#!/usr/bin/env python3
"""Execute real subprocess fault injections against the r036 raw validator."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PERSIST=ROOT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
CASES=HERE/"mutations/cases"


def invoke(extra):
    command=[sys.executable,str(HERE/"validate_r036.py"),"--project",str(ROOT)]+extra
    run=subprocess.run(command,text=True,capture_output=True)
    return run.returncode,run.stdout,run.stderr,command


def write_json(source,destination,change):
    value=json.loads(source.read_text()); change(value); destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")


def main():
    CASES.mkdir(parents=True,exist_ok=True); records=[]
    pristine=invoke([])
    if pristine[0]!=0: raise RuntimeError("pristine validator failed: "+pristine[1]+pristine[2])
    mutations=[]
    path=CASES/"m01_kill_e_floor/protocol.json"; write_json(HERE/"audit_protocol.json",path,lambda x:x.__setitem__("KILL_E_spearman_floor",0.0)); mutations.append(("KILL-E Spearman floor 0.03->0",["--protocol",str(path)]))
    path=CASES/"m02_common_support/protocol.json"; write_json(HERE/"audit_protocol.json",path,lambda x:x.__setitem__("common_support_definition","all target rows without source support")); mutations.append(("common-support definition tamper",["--protocol",str(path)]))
    path=CASES/"m03_nominal_coverage/t4.csv"; path.parent.mkdir(parents=True,exist_ok=True); table=pd.read_csv(PERSIST/"implementation_a/t4_source_only_calibration.csv"); table.loc[0,"nominal_coverage"]=.8; table.to_csv(path,index=False); mutations.append(("coverage nominal value tamper",["--t4",str(path)]))
    path=CASES/"m04_dip_threshold/protocol.json"; write_json(HERE/"audit_protocol.json",path,lambda x:x.__setitem__("dip_p_threshold",0.0)); mutations.append(("dip threshold 0.01->0",["--protocol",str(path)]))
    path=CASES/"m05_judgment/judgment.json"; write_json(PERSIST/"judgment.json",path,lambda x:x.__setitem__("candidate_state","QSETOD_PROCEED_CANDIDATE")); mutations.append(("judgment token tamper",["--judgment",str(path)]))
    path=CASES/"m06_target_label_guard/fit_guard.csv"; path.parent.mkdir(parents=True,exist_ok=True); table=pd.read_csv(PERSIST/"fit_target_label_guard.csv"); table.loc[0,"target_angle_label_rows_in_fit"]=1; table.to_csv(path,index=False); mutations.append(("target-label fit guard tamper",["--fit-guard",str(path)]))
    for name,extra in mutations:
        code,stdout,stderr,command=invoke(extra); records.append({"mutation":name,"command":" ".join(command),"exit_code":code,"rejected":code!=0,"stdout":stdout.strip(),"stderr":stderr.strip()})
    if not all(row["rejected"] for row in records): raise RuntimeError("one or more mutations survived")
    output={"schema":"r036_mutation_results_v1","status":"PASS","pristine_exit_code":pristine[0],"mutations":records,"real_subprocess_mutations":len(records),"all_rejected":True}
    (HERE/"mutations/mutation_results.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":"PASS","mutations":len(records),"all_rejected":True},sort_keys=True))


if __name__=="__main__": main()
