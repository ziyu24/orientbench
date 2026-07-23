#!/usr/bin/env python3
"""Validate B1-B3 outputs and write the frozen reproduction status."""
from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path

BROOT = Path(__file__).resolve().parents[1]
OUT = BROOT / "reports/b1_b3_reproduction_status.csv"


def csv_rows(rel, required, minimum=1):
    path = BROOT / rel
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = set(reader.fieldnames or []); rows = list(reader)
    missing = set(required) - fields
    if missing or len(rows) < minimum:
        raise RuntimeError(f"{rel}: missing={sorted(missing)} rows={len(rows)}")
    return rows


def main():
    checks=[]
    protocol=json.loads((BROOT/"reports/b1_protocol_frozen.json").read_text())
    checks.append(("frozen_hypotheses",protocol["hypotheses"]==["H1","H2","H3","H4"],"exact H1-H4"))
    checks.append(("endpoints_separated",set(protocol["endpoints"])=={"endpoint_continuous","endpoint_severe_event"},"two frozen endpoints"))
    registry=csv_rows("reports/b1_candidate_score_registry.csv",["candidate","formula","origin"],4)
    checks.append(("candidate_registry",len(registry)==4,"four historical candidates only"))
    toy=csv_rows("reports/b2_toy_model_sufficiency.csv",["decision","informative_rows","near_random_rows","reverse_rows"],1)[0]
    checks.append(("toy_three_regions",all(int(toy[k])>0 for k in ("informative_rows","near_random_rows","reverse_rows")),toy["decision"]))
    base=csv_rows("reports/b3_baseline_identity_manifest.csv",["dataset","seed","prediction_identity_hash","AP50","AP75"],9)
    checks.append(("nine_baselines",len(base)==9,"3 datasets x 3 seeds"))
    metrics=csv_rows("reports/b3_intervention_metrics.csv",["analysis","dataset","seed","endpoint","evidence_role"],100)
    analyses=set(r["analysis"] for r in metrics)
    need={"BASELINE_SCORE","RADIAL","TANGENTIAL_SYNC","PRIMARY_ONLY","SECONDARY_ONLY","FREQUENCY_CONFLICT","BOUNDARY_CROSS"}
    checks.append(("intervention_coverage",need<=analyses,";".join(sorted(analyses))))
    ident=csv_rows("reports/b3_intervention_identity_audit.csv",["prediction_identity_equal","box_equal","nms_membership_equal","evidence_role"],20)
    checks.append(("identity_roles_explicit",{"RANKING_ONLY","MECHANISM_ONLY_NOT_RANKING_ONLY"}<=set(r["evidence_role"] for r in ident),"both roles present"))
    conf=csv_rows("reports/b3_confounding_control.csv",["endpoint","analysis","factor","estimate"],100)
    checks.append(("confounding_endpoint_separation",set(r["endpoint"] for r in conf)=={"endpoint_continuous","endpoint_severe_event"},"both endpoints"))
    ev=csv_rows("reports/b3_hypothesis_evidence_matrix.csv",["hypothesis","status","real_intervention"],4)
    checks.append(("hypothesis_matrix",set(r["hypothesis"] for r in ev)=={"H1","H2","H3","H4"},"H1-H4"))
    final=csv_rows("reports/b1_b3_final_decision.csv",["condition","status","evidence"],5)
    decision=[r["status"] for r in final if r["condition"]=="final_decision"]
    checks.append(("decision_valid",decision and decision[0] in {"PROCEED_B4_EXTERNAL_VALIDATION","PROCEED_B4_WITH_WEAK_MECHANISM","STOP_B_MECHANISM"},str(decision)))
    for seed in range(3):
        manifest=json.loads((BROOT/f"artifacts/b3_fair1m/seed{seed}/manifest.json").read_text())
        checks.append((f"fair1m_seed{seed}_identity",manifest["status"]=="complete" and all(manifest["identity_checks"].values()),str(manifest["identity_checks"])))
    rows=[{"check":name,"status":"PASS" if ok else "FAIL","detail":detail} for name,ok,detail in checks]
    tmp=OUT.with_suffix(".csv.tmp")
    with tmp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    os.replace(tmp,OUT)
    if not all(ok for _,ok,_ in checks): raise SystemExit(1)


if __name__=="__main__": main()
