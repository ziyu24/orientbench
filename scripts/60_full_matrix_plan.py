#!/usr/bin/env python3
"""60_full_matrix_plan.py — full-matrix execution plan from existing assets (019).

Maps a 9-archetype detector taxonomy x present datasets to representative valid
baselines, assigns each cell a status (already_available / ready_to_run /
blocked_dependency / blocked_missing_dataset / weak_nonformal / ...), and writes
the plan + a machine-readable cell registry. Read-only (no inference here).
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(P, "outputs", "bench_core", "reports")
INSTALLED_ENVS = {"ai4rs_train", "geostructdota", "mr", "mr_dev1x", "p2_foundation"}
DATASETS_PRESENT = ["DOTA-v1.0", "DOTA-v1.5", "DIOR-R", "HRSC2016", "FAIR1M-v1.0"]
DATASETS_MISSING = ["SODA-A", "ICDAR-MLT"]

# 9-archetype taxonomy -> representative family + env hint + formal capability
ARCHETYPES = [
    ("two_stage_oriented_rcnn", "oriented_rcnn", {"mr_dev1x"}, "formal_capable"),
    ("angle_coder_psc", "rotated_retinanet_psc", {"mr_dev1x"}, "formal_capable"),
    ("one_stage_rtmdet", "rotated_rtmdet", {"mr_dev1x"}, "formal_capable"),
    ("rotated_detr_rhino", "RHINO_host", {"ai4rs_train"}, "formal_capable_locked_host"),
    ("hybrid_encoder_oriented_detr_a4", "O2RTDETR_host", {"ai4rs_train"}, "formal_capable_locked_host"),
    ("lsknet_backbone", "oriented_rcnn_lsknet_s_fpn", {"ai4rs_train"}, "formal_capable"),
    ("strip_rcnn", "strip_rcnn_s_fpn", {"ai4rs_train"}, "formal_capable"),
    ("weakly_supervised_h2rbox", "h2rbox_v2", {"ai4rs_train"}, "weak_or_pseudo_nonformal"),
    ("pseudo_point2rbox", "point2rbox_v2", {"unknown"}, "weak_or_pseudo_nonformal_blocked_network_init"),
    ("rotated_detr_arsdetr_distinct", "arsdetr", {"ars"}, "formal_capable_NOT_rhino_substitute"),
]


def _existing_schema(dataset, baseline_id):
    base = os.path.join(P, "outputs/predictions", dataset, baseline_id, "schema")
    if os.path.isdir(base) and any(f.endswith(".jsonl") for f in os.listdir(base)):
        return True
    return False


def main():
    recs = json.load(open(os.path.join(REP.replace("reports", ""), "baseline_inventory.json")))["records"]
    # index valid inference-ready baselines by (family,dataset)
    idx = {}
    for r in recs:
        fam = r["model_id"].split("_r50")[0].split("_r101")[0].split("_le")[0].split("_1x")[0]
        if r.get("valid") and r.get("pth_exists") and r.get("config_exists"):
            idx.setdefault((fam, r["dataset"]), r)

    # existing already-available cells (predictions on disk)
    available = {
        ("two_stage_oriented_rcnn", "DOTA-v1.0"): "1",
        ("angle_coder_psc", "DOTA-v1.0"): "20",
        ("one_stage_rtmdet", "DOTA-v1.0"): "32",
        ("rotated_detr_rhino", "DOTA-v1.0"): "rhino",
        ("hybrid_encoder_oriented_detr_a4", "DOTA-v1.5"): "a4_host",
        ("lsknet_backbone", "DOTA-v1.0"): "7",
        ("strip_rcnn", "DOTA-v1.0"): "35",
        ("weakly_supervised_h2rbox", "DOTA-v1.0"): "70",
    }

    rows = []
    cells = []
    for arch, famrep, envs, formalcap in ARCHETYPES:
        for ds in DATASETS_PRESENT:
            baseline = idx.get((famrep, ds)) or idx.get((famrep.lower(), ds))
            avail_id = available.get((arch, ds))
            env_ok = bool(envs & INSTALLED_ENVS)
            if avail_id:
                status = "already_available"
                bid = avail_id
            elif "weak" in formalcap and not env_ok:
                status = "weak_nonformal_blocked_dependency"
                bid = baseline["id"] if baseline else None
            elif not env_ok:
                status = "blocked_dependency_not_installed"
                bid = baseline["id"] if baseline else None
            elif baseline:
                status = "ready_to_run"
                bid = baseline["id"]
            else:
                status = "not_applicable"
                bid = None
            formal = ("formal_compatible" if (ds in ("DOTA-v1.0", "DOTA-v1.5") and "formal_capable" in formalcap)
                      else "cross_dataset_exploratory" if ds not in ("DOTA-v1.0", "DOTA-v1.5")
                      else "nonformal")
            rows.append({"archetype": arch, "detector_family": famrep, "dataset": ds,
                         "representative_baseline_id": bid, "required_env": ";".join(envs),
                         "env_installed": env_ok, "status": status, "formal_capability": formalcap,
                         "formal_scope": formal})
            if status == "already_available":
                cells.append({"archetype": arch, "dataset": ds, "baseline_id": bid, "formal_scope": formal})
    # missing datasets (record only)
    for ds in DATASETS_MISSING:
        rows.append({"archetype": "all", "detector_family": "all", "dataset": ds,
                     "representative_baseline_id": None, "required_env": "-", "env_installed": False,
                     "status": "blocked_missing_dataset", "formal_capability": "-",
                     "formal_scope": "out_of_scope_current"})

    cols = ["archetype", "detector_family", "dataset", "representative_baseline_id", "required_env",
            "env_installed", "status", "formal_capability", "formal_scope"]
    with open(os.path.join(REP, "full_matrix_execution_plan_020.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump(cells, open(os.path.join(REP, "full_matrix_available_cells.json"), "w"), indent=2)

    from collections import Counter
    sc = Counter(r["status"] for r in rows)
    L = ["# Full-Matrix Execution Plan (existing assets)", "", f"> {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
         "> 9-archetype x present datasets. existing-assets only; no download/train.", "",
         f"## status counts: {dict(sc)}", "",
         "| archetype | family | dataset | baseline | env | env_installed | status | formal_scope |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['archetype']} | {r['detector_family']} | {r['dataset']} | {r['representative_baseline_id']} | "
                 f"{r['required_env']} | {r['env_installed']} | **{r['status']}** | {r['formal_scope']} |")
    L += ["", "## 说明",
          "- already_available: 已有真实 prediction schema（5 archetype on DOTA）。",
          "- blocked_dependency_not_installed: 需 pcp-obb-soda/ars/unknown env，未安装（不下载/不安装）。",
          "- weak_nonformal: h2rbox/point2rbox 弱/伪监督，不入 formal angle gate（可 schema smoke）。",
          "- blocked_missing_dataset: SODA-A / ICDAR-MLT 不在 present datasets（仅记录）。",
          "- RHINO 用 locked RHINO host；ARS-DETR 为独立 archetype，**不**替代 RHINO。",
          "- DOTA-v1.0/v1.5 = formal_compatible（不改阈值）；DIOR-R/HRSC/FAIR1M = cross_dataset_exploratory。"]
    open(os.path.join(REP, "full_matrix_execution_plan_020.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] matrix plan: {dict(sc)}; available cells={len(cells)}")


if __name__ == "__main__":
    main()
