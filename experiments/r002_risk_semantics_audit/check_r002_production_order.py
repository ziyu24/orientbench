#!/usr/bin/env python3
"""Test whether archived feature-table order restores r002 metric tie behavior."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage


KEYS = ["image_id", "pred_id", "class_id"]


def metric(frame: pd.DataFrame, score: str) -> dict[str, float]:
    scores = frame[score].to_numpy()
    risks = frame.geometry_risk.to_numpy()
    return {
        "NRC": float(nrc_auc(scores, risks)["nrc_auc"]),
        "AUGRC": float(aurc(scores, risks)),
        "Risk70": float(risk_at_coverage(scores, risks, 0.7)),
        "Risk90": float(risk_at_coverage(scores, risks, 0.9)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    parser.add_argument("--write-universe", action="store_true")
    args = parser.parse_args()
    risk = pd.read_parquet(args.evidence / "risk_rows.parquet")
    scores = pd.read_parquet(args.evidence / "compact_scores.parquet")
    reported = pd.read_csv(args.evidence / "corrected_g1_unit_metrics.csv")
    old_universe = pd.read_csv(args.evidence / "universe_identity.csv", low_memory=False)
    report: list[dict[str, object]] = []
    ordered_universe: list[pd.DataFrame] = []
    for row in reported.itertuples(index=False):
        unit = str(row.unit)
        features = pd.read_parquet(args.runtime / "features" / f"{unit}.parquet")[KEYS]
        current = risk[(risk.unit == unit) & (risk.role == "D_audit")]
        ordered = features.merge(current, on=KEYS, how="inner", validate="one_to_one")
        sealed = scores[(scores.unit == unit) & (scores.seed == row.seed)]
        ordered = ordered.merge(sealed, on=["unit", *KEYS, "role"], validate="one_to_one")
        baseline = metric(ordered, "standalone_score")
        ordered["selector_score"] = -ordered.predicted_risk
        gr_eqs = metric(ordered, "selector_score")
        expected = {
            "standalone_NRC": row.standalone_NRC,
            "standalone_AUGRC": row.standalone_AUGRC,
            "standalone_Risk70": row.standalone_Risk70,
            "standalone_Risk90": row.standalone_Risk90,
            "gr_eqs_NRC": row.gr_eqs_NRC,
            "gr_eqs_AUGRC": row.gr_eqs_AUGRC,
            "gr_eqs_Risk70": row.gr_eqs_Risk70,
            "gr_eqs_Risk90": row.gr_eqs_Risk90,
        }
        observed = {**{f"standalone_{key}": value for key, value in baseline.items()},
                    **{f"gr_eqs_{key}": value for key, value in gr_eqs.items()}}
        maximum = max(abs(float(observed[key]) - float(expected[key])) for key in expected)
        report.append({"unit": unit, "seed": int(row.seed), "rows": len(ordered),
                       "max_abs_error": maximum, "matches": maximum <= args.tolerance})
    if args.write_universe:
        for unit in "ABCDEF":
            features = pd.read_parquet(args.runtime / "features" / f"{unit}.parquet")[KEYS]
            current = risk[risk.unit == unit]
            ordered = features.merge(current, on=KEYS, how="inner", validate="one_to_one")
            status = old_universe[old_universe.unit == unit][KEYS + ["r014_key_status"]]
            ordered_universe.append(ordered.merge(status, on=KEYS, validate="one_to_one"))
        universe = pd.concat(ordered_universe, ignore_index=True)
        expected = ["unit", "image_id", "pred_id", "gt_id", "class_id", "cluster", "role", "r014_key_status"]
        if len(universe) != len(old_universe) or universe.duplicated(["unit", *KEYS]).any():
            raise RuntimeError("production-order universe key cardinality mismatch")
        universe[expected].to_csv(args.evidence / "universe_identity.csv", index=False)
    payload = {"ok": all(bool(item["matches"]) for item in report), "cells": report}
    print(json.dumps(payload, sort_keys=True))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
