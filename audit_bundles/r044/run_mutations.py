#!/usr/bin/env python3
"""Run pristine validation and three isolated semantic mutations."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "audit_bundles/r044"
VALIDATOR = HERE / "validate_claims.py"


def mutate_csv(src, dst, predicate, field, value=None, delete=False):
    with src.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f)); fields = list(rows[0])
    out = []
    changed = 0
    for r in rows:
        if predicate(r):
            changed += 1
            if delete: continue
            r[field] = value
        out.append(r)
    if changed != 1: raise RuntimeError(f"mutation expected one row, got {changed}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(out)


def invoke(name, override=None):
    out = HERE / "mutations" / f"{name}_claim_check.json"
    cmd=[sys.executable,str(VALIDATOR),"--output",str(out)]
    if override: cmd += ["--override", override]
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    return {"name":name,"exit_code":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip(),"result_path":str(out.relative_to(ROOT))}


def main():
    mroot=HERE/"mutations"; mroot.mkdir(parents=True,exist_ok=True)
    perturb_rel="top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1/s1a_full_pipeline_perturbation_v1.csv"
    human_rel="reports/m4_human_annotation_primary_summary_073.csv"
    nrc_rel="top_journal_v3_reaudit_055/reports/a0_masked_nrc_bootstrap_ci_055.csv"
    p1=mroot/"ap75_changed.csv"; mutate_csv(ROOT/perturb_rel,p1,lambda r:r["cell"]=="DIOR-R/3","pert_AP75","0.1897")
    p2=mroot/"human_mean_changed.csv"; mutate_csv(ROOT/human_rel,p2,lambda r:r["subset"]=="overall","mean_deg","9.9999")
    p3=mroot/"nrc_row_deleted.csv"; mutate_csv(ROOT/nrc_rel,p3,lambda r:r["cell"]=="DIOR-R/22" and r["selector"]=="detection_score","nrc",delete=True)
    results=[invoke("pristine"),invoke("mutate_ap75",f"{perturb_rel}={p1}"),invoke("mutate_human",f"{human_rel}={p2}"),invoke("mutate_delete_row",f"{nrc_rel}={p3}")]
    ok=results[0]["exit_code"]==0 and all(r["exit_code"]!=0 for r in results[1:])
    report={"schema_version":1,"status":"PASS" if ok else "FAIL","pristine_exit_zero":results[0]["exit_code"]==0,"all_mutations_nonzero":all(r["exit_code"]!=0 for r in results[1:]),"results":results}
    (HERE/"mutation_results.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report))
    return 0 if ok else 1


if __name__=="__main__": sys.exit(main())
