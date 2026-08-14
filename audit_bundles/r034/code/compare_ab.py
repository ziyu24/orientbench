#!/usr/bin/env python3
"""Exact-key, atol=1e-10 comparator for independent r034 implementations."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


NUMERIC = ["delta_ar21", "delta_all", "dod", "delta_ar21_ci_low", "delta_ar21_ci_high", "delta_all_ci_low", "delta_all_ci_high", "dod_ci_low", "dod_ci_high", "p_raw", "p_holm", "epsilon_ar21", "epsilon_all", "swap_ar21_70", "swap_all_70"]
EXACT = ["level", "key", "dataset", "risk", "estimand", "contrast", "left_ranker", "right_ranker", "endpoint", "primary", "witness"]


def main():
    p = argparse.ArgumentParser(); p.add_argument("--a", type=Path, required=True); p.add_argument("--b", type=Path, required=True); p.add_argument("--output", type=Path, required=True); z = p.parse_args(); z.output.mkdir(parents=True, exist_ok=True)
    ha = pd.read_csv(z.a / "hypotheses.csv").set_index("hypothesis_key", verify_integrity=True).sort_index()
    hb = pd.read_csv(z.b / "hypotheses.csv").set_index("hypothesis_key", verify_integrity=True).sort_index()
    checks = []
    if list(ha.index) != list(hb.index): raise RuntimeError("hypothesis key identity mismatch")
    for key in ha.index:
        for field in EXACT:
            av, bv = ha.at[key, field], hb.at[key, field]; ok = str(av) == str(bv)
            checks.append({"key": key, "field": field, "a": av, "b": bv, "abs_diff": 0.0 if ok else 1.0, "consistent": ok})
        for field in NUMERIC:
            av, bv = float(ha.at[key, field]), float(hb.at[key, field]); diff = 0.0 if np.isnan(av) and np.isnan(bv) else abs(av - bv)
            checks.append({"key": key, "field": field, "a": av, "b": bv, "abs_diff": diff, "consistent": diff <= 1e-10})
    array_checks = []
    for name in ("unit", "dataset"):
        aa = np.load(z.a / "bootstrap_metrics.npz")[name]; bb = np.load(z.b / "bootstrap_metrics.npz")[name]
        if aa.shape != bb.shape: raise RuntimeError(f"bootstrap shape mismatch {name}")
        diff = float(np.nanmax(np.abs(aa - bb))); array_checks.append({"array": name, "shape": list(aa.shape), "max_abs_diff": diff, "consistent": diff <= 1e-10})
    ma, mb = np.load(z.a / "multiplicities.npz"), np.load(z.b / "multiplicities.npz")
    for name in sorted(ma.files):
        ok = name in mb.files and np.array_equal(ma[name], mb[name]); array_checks.append({"array": f"multiplicity:{name}", "shape": list(ma[name].shape), "max_abs_diff": 0.0 if ok else 1.0, "consistent": ok})
    ja, jb = json.loads((z.a / "judgment.json").read_text()), json.loads((z.b / "judgment.json").read_text())
    judgment_fields = ["candidate_state", "K1", "K2", "survival", "primary_count", "primary_witnesses", "residual_Rnorm_witness", "replicates", "seed"]
    judgment_checks = [{"field": f, "a": ja[f], "b": jb[f], "consistent": ja[f] == jb[f]} for f in judgment_fields]
    pd.DataFrame(checks).to_csv(z.output / "field_comparison.csv", index=False)
    status = "PASS" if all(x["consistent"] for x in checks + array_checks + judgment_checks) else "MISMATCH"
    result = {"status": status, "hypotheses": len(ha), "field_checks": len(checks), "atol": 1e-10, "array_checks": array_checks, "judgment_checks": judgment_checks}
    (z.output / "comparator.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if status != "PASS": raise SystemExit(1)


if __name__ == "__main__": main()
