#!/usr/bin/env python3
"""74_final_matrix_summary.py — consolidate all completed cells into final matrix (029)."""
from __future__ import annotations

import csv
import json
import os
import time

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(P, "outputs", "bench_core", "reports")
TS = time.strftime("%Y-%m-%d %H:%M:%S %Z")


def rd(name):
    p = os.path.join(REP, name)
    return list(csv.DictReader(open(p))) if os.path.isfile(p) else []


def main():
    cells = {}  # (dataset, baseline_id) -> row

    def add(ds, bid, det, nrc, mederr, scope, source):
        if not ds or ds in ("none", ""):
            return
        if (nrc in (None, "", "None")) and not scope:
            return  # skip blocked/missing cells (no metrics)
        key = (ds, str(bid))
        if key not in cells or (cells[key]["NRC_AUC"] in (None, "", "None") and nrc not in (None, "", "None")):
            cells[key] = {"dataset": ds, "baseline_id": str(bid), "detector": det, "NRC_AUC": nrc,
                          "median_orient_err_deg": mederr, "scope": scope, "source": source}

    # DOTA 9-archetype (full_matrix_metrics_summary)
    for r in rd("full_matrix_metrics_summary.csv"):
        add(r.get("dataset"), r.get("baseline_id"), r.get("detector") or r.get("archetype"),
            r.get("NRC_AUC"), r.get("median_orient_err_deg"), r.get("formal_scope", "formal_compatible"), "dota_9archetype")
    # cross-dataset rounds
    for fn, src in (("metrics_024.csv", "fullval_024"), ("metrics_025.csv", "fullval_025"),
                    ("cross_dataset_metrics_022.csv", "xds_022"), ("arsdetr_xds_metrics_028.csv", "arsdetr_028")):
        for r in rd(fn):
            add(r.get("dataset"), r.get("baseline_id"), r.get("detector"),
                r.get("NRC_AUC"), r.get("median_orient_err_deg"), r.get("formal_scope", "cross_dataset_exploratory"), src)
    # HRSC from 021
    for r in rd("cross_dataset_metrics_021.csv"):
        if r.get("dataset") == "HRSC2016":
            add("HRSC2016", r.get("baseline_id"), r.get("detector"), r.get("NRC_AUC"),
                r.get("median_orient_err_deg"), "cross_dataset_exploratory_angle_uncertain", "hrsc_021")

    rows = sorted(cells.values(), key=lambda x: (x["dataset"], x["detector"]))
    # detector x dataset coverage
    from collections import defaultdict
    cov = defaultdict(set)
    for r in rows:
        cov[r["dataset"]].add(r["detector"])
    with open(os.path.join(REP, "final_matrix_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "baseline_id", "detector", "NRC_AUC", "median_orient_err_deg", "scope", "source"])
        w.writeheader(); w.writerows(rows)
    L = ["# Final Matrix Summary (029)", "", f"> {TS}",
         "> 全 detector×dataset 真实完成 cell 汇总。DOTA=formal-compatible(阈值未改)；非 DOTA=exploratory。", "",
         "## detector coverage per dataset",
         "| dataset | #detectors | detectors |", "|---|---|---|"]
    for ds in sorted(cov):
        L.append(f"| {ds} | {len(cov[ds])} | {', '.join(sorted(cov[ds]))} |")
    L += ["", f"## completed cells: **{len(rows)}**", "",
          "| dataset | baseline | detector | NRC-AUC | med_err° | scope |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['dataset']} | {r['baseline_id']} | {r['detector']} | {r['NRC_AUC']} | "
                 f"{r['median_orient_err_deg']} | {r['scope']} |")
    L += ["", "## 口径",
          "- DOTA scoped milestone=pass；DOTA 9-archetype=pass。cross_dataset_matrix=**partial/exploratory（多 detector，多 dataset）**。",
          "- full_project_complete=**false**。formal claims only frozen DOTA scope。non-DOTA all exploratory。ARS-DETR≠RHINO。"]
    open(os.path.join(REP, "final_matrix_summary.md"), "w").write("\n".join(L) + "\n")

    # remaining blockers
    bl = [
        {"item": "ARS-DETR FAIR1M", "status": "blocked_class_mapping_with_evidence", "reason": "FAIR1M class names contain spaces; DOTA-txt space-delimited + ARS-DETR fixed CLASSES KeyError"},
        {"item": "point2rbox", "status": "blocked_upstream_artifact_unavailable", "reason": "ted.pth empty/404/401 on modelscope/github/hf; weak_nonformal"},
        {"item": "ARS-DETR SODA/HRSC", "status": "partial/attempted", "reason": "annfile-population + class-map pattern available; budget-bounded"},
        {"item": "Strip cross-dataset FAIR1M/SODA/HRSC", "status": "pattern_available", "reason": "empty-annfile + DumpDetResults evaluator template verified on DIOR"},
        {"item": "genuine physical multi-view C1 / cross-host A4", "status": "out_of_scope", "reason": "needs new data / P2-P3 machinery"},
    ]
    with open(os.path.join(REP, "remaining_blockers.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "status", "reason"]); w.writeheader(); w.writerows(bl)
    open(os.path.join(REP, "remaining_blockers.md"), "w").write(
        f"# Remaining Blockers (029)\n\n> {TS}\n\n" + "\n".join(f"- **{b['item']}**: {b['status']} — {b['reason']}" for b in bl) + "\n")

    # coverage update
    covj = json.load(open(os.path.join(REP, "full_project_coverage_report.json")))
    covj["final_matrix"] = {"completed_cells": len(rows), "detector_coverage": {k: sorted(v) for k, v in cov.items()},
                            "cross_dataset_matrix": "partial_exploratory_multidetector", "full_project_complete": False}
    json.dump(covj, open(os.path.join(REP, "full_project_coverage_report.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[ok] final matrix: {len(rows)} cells; coverage {dict((k, len(v)) for k, v in cov.items())}")


if __name__ == "__main__":
    main()
