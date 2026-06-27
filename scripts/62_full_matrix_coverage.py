#!/usr/bin/env python3
"""62_full_matrix_coverage.py — probe summary + coverage + status refresh (019)."""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from collections import Counter

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(P, "outputs", "bench_core", "reports")


def rd(name):
    p = os.path.join(REP, name)
    return list(csv.DictReader(open(p))) if os.path.isfile(p) else []


def main():
    plan = rd("full_matrix_execution_plan.csv")
    met = rd("full_matrix_metrics_summary.csv")
    val = rd("full_matrix_schema_validation.csv")
    TS = time.strftime("%Y-%m-%d %H:%M:%S %Z")

    # ---- probe summary ----
    prob = []
    for m in met:
        ds = m["dataset"]; arch = m["archetype"]
        d2 = "formal_compatible" if ds in ("DOTA-v1.0", "DOTA-v1.5") else "exploratory"
        c1 = ("formal_frozen" if arch == "rotated_detr_rhino" and ds == "DOTA-v1.0"
              else "not_applicable_or_exploratory")
        a4 = ("formal_frozen" if arch == "hybrid_encoder_oriented_detr_a4" and ds == "DOTA-v1.5"
              else "not_applicable_or_exploratory")
        prob.append({"archetype": arch, "dataset": ds, "baseline_id": m["baseline_id"],
                     "D2_orientation_reliability": d2, "D2_NRC_AUC": m["NRC_AUC"], "D2_Risk@90": m["Risk@90"],
                     "C1_augmentation_view": c1, "A4_source_attribution": a4})
    with open(os.path.join(REP, "full_matrix_probe_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prob[0].keys())); w.writeheader(); w.writerows(prob)
    L = ["# Full-Matrix Probe Summary", "", f"> {TS}",
         "> D2 = orientation reliability(NRC/Risk)。C1/A4 仅 locked host formal_frozen，其余 not_applicable/exploratory。",
         "> 本轮不冻结新阈值，不扩大 C1/A4 formal claim。", "",
         "| archetype | dataset | baseline | D2 | D2 NRC | D2 Risk@90 | C1 | A4 |",
         "|---|---|---|---|---|---|---|---|"]
    for r in prob:
        L.append(f"| {r['archetype']} | {r['dataset']} | {r['baseline_id']} | {r['D2_orientation_reliability']} | "
                 f"{r['D2_NRC_AUC']} | {r['D2_Risk@90']} | {r['C1_augmentation_view']} | {r['A4_source_attribution']} |")
    open(os.path.join(REP, "full_matrix_probe_summary.md"), "w").write("\n".join(L) + "\n")

    # ---- coverage report ----
    sc = Counter(r["status"] for r in plan)
    detectors = {r["archetype"] for r in plan if r["archetype"] != "all"}
    det_covered = {m["archetype"] for m in met}
    ds_present = {r["dataset"] for r in plan if r["status"] != "blocked_missing_dataset"}
    ds_covered = {m["dataset"] for m in met}
    formal_cells = [m for m in met if m["dataset"] in ("DOTA-v1.0", "DOTA-v1.5")]
    expl_cells = [m for m in met if m["dataset"] not in ("DOTA-v1.0", "DOTA-v1.5")]
    cov = {
        "generated": TS, "detector_archetypes_total": len(detectors),
        "detector_archetypes_covered": sorted(det_covered), "n_detector_covered": len(det_covered),
        "datasets_present": sorted(ds_present), "datasets_covered": sorted(ds_covered),
        "successful_cells": len(met), "schema_cells": len(val),
        "blocked_cells": {k: v for k, v in sc.items() if "blocked" in k or "weak" in k},
        "formal_compatible_cells": len(formal_cells), "exploratory_cells": len(expl_cells),
        "missing_datasets": ["SODA-A", "ICDAR-MLT"],
        "dependency_blockers": "LSKNet(pcp-obb-soda)/ARS-DETR(ars)/strip/point2rbox/h2rbox(unknown) envs not installed",
        "format_blockers": "none observed in run cells",
        "angle_blockers": "HRSC angle uncertain (not run this batch)",
        "weak_pseudo_nonformal": "h2rbox/point2rbox -> weak_nonformal",
        "oom_blockers": "none (all 4-GPU cells healthy, no OOM)",
        "config_mismatch_blockers": "none in run cells",
        "next_minimum_actions": [
            "install/register LSKNet/ARS-DETR/Strip/point2rbox/h2rbox envs (needs approval; this round forbidden)",
            "run DIOR-R/HRSC/FAIR1M exploratory cells for available-env detectors",
            "resolve HRSC angle convention before any HRSC angle gate",
            "acquire SODA-A/ICDAR-MLT datasets (out of scope)",
        ],
        "dota_scoped_milestone": "pass", "full_project_complete": False,
        "full_matrix_status": "partial", "training_needed_now": False,
    }
    json.dump(cov, open(os.path.join(REP, "full_project_coverage_report.json"), "w"), indent=2, ensure_ascii=False)
    with open(os.path.join(REP, "full_project_coverage_report.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["metric", "value"])
        for k, v in cov.items():
            w.writerow([k, v if not isinstance(v, (list, dict)) else json.dumps(v, ensure_ascii=False)])
    L = ["# Full Project Coverage Report", "", f"> {TS}", "",
         f"- detector archetypes covered (real metrics): **{len(det_covered)}** ({', '.join(sorted(det_covered))})",
         f"- datasets covered: **{sorted(ds_covered)}** / present {sorted(ds_present)}",
         f"- successful cells: **{len(met)}**; schema cells: {len(val)}",
         f"- formal-compatible cells (DOTA): {len(formal_cells)}; exploratory cells: {len(expl_cells)}",
         f"- plan status counts: {dict(sc)}", "",
         "## blockers",
         f"- dependency: {cov['dependency_blockers']}",
         f"- missing datasets: {cov['missing_datasets']}",
         f"- angle: {cov['angle_blockers']}; weak/pseudo: {cov['weak_pseudo_nonformal']}",
         f"- OOM: {cov['oom_blockers']}; config mismatch: {cov['config_mismatch_blockers']}", "",
         "## 口径",
         "- DOTA scoped milestone = **pass**；full project complete = **false**；full matrix status = **partial**；training_needed_now = **false**。",
         "## next minimum actions"]
    L += [f"- {a}" for a in cov["next_minimum_actions"]]
    open(os.path.join(REP, "full_project_coverage_report.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] coverage: {len(det_covered)} archetypes, {len(met)} cells, status={dict(sc)}")


if __name__ == "__main__":
    main()
