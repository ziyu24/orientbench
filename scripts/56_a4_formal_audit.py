#!/usr/bin/env python3
"""56_a4_formal_audit.py — A4 same-host source-attribution FORMAL gate on D_audit.

Applies the FROZEN A4 thresholds (read-only) to the D_audit attribution results;
never mutates them. PASS iff a non-GV source shows significant orientation-risk
dependence on D_audit (HSIC p <= hsic_p_min). Scope: same-host A4 source
attribution (NO cross-host causal claim).
"""
from __future__ import annotations

import json
import os
import sys

import yaml

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.reports import write_csv  # noqa: E402

DETAIL = os.path.join(PROOT, "outputs/probes/a4_source_attribution_real/a4_attribution_real_detail.json")
REP = os.path.join(PROOT, "outputs/bench_core/reports")
FDIR = os.path.join(PROOT, "outputs/probes/a4_source_attribution_formal")


def main():
    os.makedirs(FDIR, exist_ok=True)
    thr = yaml.safe_load(open(os.path.join(PROOT, "configs/thresholds.yaml")))
    a4 = thr["A_A4"]
    assert a4["status"] == "frozen" and a4["gate_name"] == "A4_source_attribution"
    hsic_p_min = a4["hsic_p_min_after_correction"]; pc_max = a4["partial_corr_max_abs"]
    bg_enabled = a4["background_source_enabled"]
    host = a4["host_sha256"]
    if not os.path.isfile(DETAIL):
        print("[blocked] no A4 attribution detail"); return
    d = json.load(open(DETAIL))
    if d.get("bg_unavailable_ratio", 1.0) > 0.5:
        verdict = "formal_blocked"; reason = "background_unavailable"
        srcs = {}
    else:
        srcs = (d.get("detail", {}).get("D_audit", {}) or {}).get("sources", {})
        non_gv = {k: v for k, v in srcs.items() if k != "gv"}
        sig = {k: v for k, v in non_gv.items()
               if v.get("hsic_p") is not None and v["hsic_p"] <= hsic_p_min}
        verdict = "formal_pass" if sig else "formal_fail"
        reason = (f"significant non-GV sources (HSIC p<={hsic_p_min}): {sorted(sig)}"
                  if sig else "no non-GV source significant on D_audit")
    n_used = (d.get("detail", {}).get("D_audit", {}) or {}).get("n_used")
    row = {"gate": "A4_source_attribution", "host": "O2-RTDETR", "host_sha256": host,
           "split": "D_audit", "background_source_enabled": bg_enabled,
           "bg_unavailable_ratio": d.get("bg_unavailable_ratio"), "n_used": n_used,
           "hsic_p_min_threshold": hsic_p_min, "partial_corr_max_abs": pc_max,
           "verdict": verdict, "reason": reason,
           "scope": "same_host_A4_source_attribution_NO_cross_host_causal_claim"}
    for k, v in srcs.items():
        row[f"{k}_partial_corr"] = v.get("partial_corr"); row[f"{k}_hsic_p"] = v.get("hsic_p")
    write_csv(os.path.join(REP, "a4_formal_audit.csv"), [row], list(row.keys()))
    json.dump({"row": row, "d_audit_sources": srcs}, open(os.path.join(FDIR, "a4_formal_detail.json"), "w"),
              indent=2, ensure_ascii=False)
    L = ["# A4 Formal Audit — D_audit (same-host source attribution)", "",
         f"> O2-RTDETR frozen sha256 {host}…; frozen thresholds applied (NOT mutated); D_audit holdout; "
         f"background_source_enabled={bg_enabled}.",
         f"> **scope: same-host A4 source attribution — NO cross-host causal claim.**", "",
         f"## VERDICT: **{verdict}** {'(within same-host A4 source-attribution scope; no cross-host causal claim)' if verdict=='formal_pass' else ''}",
         f"- {reason}", f"- n_used(D_audit)={n_used}; bg_unavailable_ratio={d.get('bg_unavailable_ratio')}", "",
         "| source | partial_corr (D_audit) | HSIC p | significant(<=%.2f) |" % hsic_p_min,
         "|---|---|---|---|"]
    for k, v in srcs.items():
        sigflag = (v.get("hsic_p") is not None and v["hsic_p"] <= hsic_p_min and k != "gv")
        L.append(f"| {k} | {v.get('partial_corr')} | {v.get('hsic_p')} | {sigflag} |")
    L += ["", "## 边界",
          "- formal_pass 仅 same-host A4 source-attribution scope；**不得**宣称跨 host 因果；DOTA partial；阈值未调；GV+class 已控；near-square masked。"]
    open(os.path.join(REP, "a4_formal_audit.md"), "w").write("\n".join(L) + "\n")
    print(f"[A4 formal] verdict={verdict}; {reason}")


if __name__ == "__main__":
    main()
