#!/usr/bin/env python3
"""Build a non-self-referential manifest for all r044 artifacts and canonical inputs."""
from __future__ import annotations
import csv, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"audit_bundles/r044/manifest.csv"
roots=[ROOT/"docs/paper_jprs_r044",ROOT/"audit_bundles/r044",ROOT/"outputs/persistent_artifacts/orientbench_jprs_manuscript_r044_20260818",ROOT/"dis/server_reports/orientbench-b-r044-jprs-measurement-manuscript-20260818"]
canonical=[
"top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1/s1a_full_pipeline_perturbation_v1.csv",
"top_journal_v3_reaudit_055/reports/r3_reverse_perturbation.csv",
"top_journal_v3_reaudit_055/reports/m4_delta_theta_tau_curve.csv",
"top_journal_v3_reaudit_055/reports/m4_geometry_normalized_risk.csv",
"top_journal_v3_reaudit_055/reports/a0_masked_nrc_bootstrap_ci_055.csv",
"top_journal_v3_reaudit_055/reports/m3_image_level_ltt.csv",
"top_journal_v3_reaudit_055/reports/m3_instance_vs_image_comparison.csv",
"reports/m4_human_annotation_primary_summary_073.csv",
"reports/m4_human_annotation_analysis_audit.json",
]
rows=[]
def add(p,kind,recompute):
    if p==OUT or not p.is_file(): return
    b=p.read_bytes(); rows.append({"artifact_type":kind,"path":str(p.relative_to(ROOT)),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"can_recompute":recompute})
for root in roots:
    if root.exists():
        for p in sorted(root.rglob("*")): add(p,"r044_artifact","yes" if p.suffix in {".csv",".json",".svg",".png"} or p.name.endswith(".py") else "authored_or_report")
for rel in canonical: add(ROOT/rel,"canonical_input","existing_frozen_pipeline")
add(ROOT/"claude_code_and_supervisor.md","execution_log","authored_append_only")
with OUT.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["artifact_type","path","bytes","sha256","can_recompute"],lineterminator="\n"); w.writeheader(); w.writerows(sorted(rows,key=lambda r:(r["artifact_type"],r["path"])))
print(f"manifest_rows={len(rows)}")
