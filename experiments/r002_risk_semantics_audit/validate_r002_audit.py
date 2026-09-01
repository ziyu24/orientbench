#!/usr/bin/env python3
"""Read-only independent validator for the r002 correction evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage

KEYS = ["unit", "image_id", "pred_id", "class_id"]
UNITS = tuple("ABCDEF")
EPS = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def le90(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    delta = np.abs(a - b) % math.pi
    return np.minimum(delta, math.pi - delta)


def metrics(score: np.ndarray, risk: np.ndarray) -> dict[str, float]:
    return {
        "NRC": float(nrc_auc(score, risk)["nrc_auc"]),
        "AUGRC": float(aurc(score, risk)),
        "Risk70": float(risk_at_coverage(score, risk, .7)),
        "Risk90": float(risk_at_coverage(score, risk, .9)),
    }


def close(left: float, right: float, *, atol: float = 1e-7) -> bool:
    return bool(np.isclose(left, right, atol=atol, rtol=0.0))


def audit(result: Path, manifest: Path) -> dict[str, object]:
    evidence = result.parent
    errors: list[str] = []
    manifest_checks: list[dict[str, object]] = []
    try:
        entries: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("- path: "):
                if current:
                    entries.append(current)
                current = {"path": stripped.removeprefix("- path: ")}
            elif current and ": " in stripped:
                key, value = stripped.split(": ", 1)
                current[key] = value
        if current:
            entries.append(current)
        root = evidence.parents[3]
        for entry in entries:
            path = root / entry["path"]
            ok = path.is_file() and str(path.stat().st_size) == entry.get("bytes") and sha256(path) == entry.get("sha256")
            manifest_checks.append({"path": entry["path"], "ok": ok})
            if not ok:
                errors.append(f"manifest mismatch: {entry['path']}")
        if not entries:
            errors.append("artifact manifest contains no entries")
    except Exception as exc:
        errors.append(f"manifest unreadable: {type(exc).__name__}: {exc}")

    risk = pd.read_parquet(evidence / "risk_rows.parquet")
    scores = pd.read_parquet(evidence / "compact_scores.parquet")
    boots = pd.read_parquet(evidence / "bootstrap_replicates.parquet")
    reported = pd.read_csv(evidence / "corrected_g1_unit_metrics.csv")
    universe = pd.read_csv(evidence / "universe_identity.csv", low_memory=False,
                           dtype={"unit": str, "image_id": str, "pred_id": int,
                                  "class_id": int, "role": str})
    risk["image_id"] = risk.image_id.astype(str)
    scores["image_id"] = scores.image_id.astype(str)
    need = {"unit", "image_id", "pred_id", "gt_id", "class_id", "cluster", "role", "pred_angle_rad", "pred_angle_deg", "gt_angle_rad", "gt_angle_deg", "pred_long_axis_rad", "gt_long_axis_rad", "le90_error_rad", "le90_error_deg", "gt_width", "gt_height", "gt_ar", "delta_075_deg", "geometry_risk", "standalone_score", "detection_score", "u_axis", "missing_fraction", "iou_loss"}
    missing = sorted(need - set(risk.columns))
    if missing:
        errors.append("risk schema missing: " + ",".join(missing))
    if risk.duplicated(KEYS).any() or risk[KEYS].isna().any().any():
        errors.append("risk row identity is not unique and non-null")
    expected_error = le90(risk.pred_long_axis_rad.to_numpy(), risk.gt_long_axis_rad.to_numpy())
    expected_risk = np.minimum(risk.le90_error_deg.to_numpy() / np.maximum(risk.delta_075_deg.to_numpy(), 1.0), 3.0)
    geometry_ok = bool(np.allclose(risk.pred_angle_deg, np.degrees(risk.pred_angle_rad), atol=EPS, rtol=0) and np.allclose(risk.gt_angle_deg, np.degrees(risk.gt_angle_rad), atol=EPS, rtol=0) and np.allclose(risk.le90_error_rad, expected_error, atol=EPS, rtol=0) and np.allclose(risk.le90_error_deg, np.degrees(expected_error), atol=EPS, rtol=0) and np.allclose(risk.geometry_risk, expected_risk, atol=EPS, rtol=0) and bool(((risk.geometry_risk >= 0) & (risk.geometry_risk <= 3)).all()))
    if not geometry_ok:
        errors.append("row-level canonical le90/risk recomputation mismatch")

    audit_rows = risk[risk.role == "D_audit"].copy()
    if scores[KEYS + ["seed"]].duplicated().any() or len(scores) != len(audit_rows) * 3:
        errors.append("compact score cardinality/key mismatch")
    if set(scores.unit.unique()) != set(UNITS) or set(reported.unit.unique()) != set(UNITS):
        errors.append("not all six frozen units are represented")
    fusion_identity = bool((scores.lambda_ == 0).all() and np.array_equal(scores.fusion_score.to_numpy(), scores.logit_score.to_numpy()))
    if not fusion_identity:
        errors.append("lambda=0 fusion/raw score identity failed")

    recomputed: list[dict[str, object]] = []
    for row in reported.itertuples(index=False):
        ordered = universe[(universe.unit == row.unit) & (universe.role == "D_audit")][KEYS + ["role"]]
        unit_rows = audit_rows[audit_rows.unit == row.unit]
        if len(ordered) != len(unit_rows) or ordered.duplicated(KEYS + ["role"]).any():
            errors.append(f"ordered audit universe mismatch {row.unit}")
            continue
        q = ordered.merge(unit_rows, on=KEYS + ["role"], validate="one_to_one").merge(scores[(scores.unit == row.unit) & (scores.seed == row.seed)], on=KEYS + ["role"], validate="one_to_one", suffixes=("", "_score"))
        if len(q) != row.n:
            errors.append(f"metric row count mismatch {row.unit}/{row.seed}")
            continue
        baseline = metrics(q.standalone_score.to_numpy(), q.geometry_risk.to_numpy())
        gr_eqs = metrics(-q.predicted_risk.to_numpy(), q.geometry_risk.to_numpy())
        checks = {"standalone_NRC": baseline["NRC"], "standalone_AUGRC": baseline["AUGRC"], "standalone_Risk70": baseline["Risk70"], "standalone_Risk90": baseline["Risk90"], "gr_eqs_NRC": gr_eqs["NRC"], "gr_eqs_AUGRC": gr_eqs["AUGRC"], "gr_eqs_Risk70": gr_eqs["Risk70"], "gr_eqs_Risk90": gr_eqs["Risk90"], "delta_NRC": baseline["NRC"] - gr_eqs["NRC"]}
        if any(not close(value, float(getattr(row, field))) for field, value in checks.items()):
            errors.append(f"18-cell metric mismatch {row.unit}/{row.seed}")
        b = boots[(boots.unit == row.unit) & (boots.seed == row.seed)]
        if len(b) != 10000 or b.replicate.nunique() != 10000 or b.draw_seed.nunique() != 10000:
            errors.append(f"bootstrap identity mismatch {row.unit}/{row.seed}")
        else:
            ci = b[["delta_NRC", "delta_Risk70", "delta_Risk90"]].quantile([.025, .975])
            for field, value in {"ci_low": ci.loc[.025, "delta_NRC"], "ci_high": ci.loc[.975, "delta_NRC"], "risk70_ci_low": ci.loc[.025, "delta_Risk70"], "risk90_ci_low": ci.loc[.025, "delta_Risk90"]}.items():
                if not close(float(value), float(getattr(row, field))):
                    errors.append(f"bootstrap CI mismatch {row.unit}/{row.seed}/{field}")
        recomputed.append({"unit": row.unit, "seed": int(row.seed), **checks})
    if len(boots) != 180000 or boots.groupby(["unit", "seed"]).ngroups != 18:
        errors.append("bootstrap evidence is not exactly 18 synchronized x 10000")

    original_d = evidence.parents[3] / "outputs/persistent_artifacts/orientbench_r002_execution_archive/original_runtime/labels/D.parquet"
    d_audit = audit_rows[audit_rows.unit == "D"]
    d_universe: dict[str, object] = {"original_available": original_d.is_file(), "corrected_rows": int(len(d_audit)), "corrected_clusters": int(d_audit.cluster.nunique())}
    if original_d.is_file():
        old = pd.read_parquet(original_d)
        old = old[old.role == "D_audit"]
        d_universe.update({"original_rows": int(len(old)), "original_clusters": int(old.cluster.nunique())})
        if len(old) != len(d_audit) or old.cluster.nunique() != d_audit.cluster.nunique():
            errors.append("FAIR1M-D cohort drift: original r002 universe was not restored")
    else:
        errors.append("original FAIR1M-D cohort evidence unavailable")

    gate = []
    for dataset, frame in reported.groupby("heldout_dataset"):
        gate.append({"dataset": dataset, "delta_nrc_all": bool(((frame.delta_NRC >= .02) & (frame.ci_low > 0)).all()), "risk_noninferior": bool(((frame.risk70_ci_low >= 0) & (frame.risk90_ci_low >= 0)).all()), "no_significant_reverse": bool((frame.ci_high >= 0).all()), "seed_direction_consistent": bool(frame.groupby("unit").delta_NRC.apply(lambda x: (x > 0).all() or (x < 0).all()).all())})
    return {"ok": not errors, "validator": "independent_read_only_r002_closeout_v1", "manifest_entries": len(manifest_checks), "manifest_all_match": all(bool(x["ok"]) for x in manifest_checks), "risk_rows": int(len(risk)), "compact_score_rows": int(len(scores)), "bootstrap_rows": int(len(boots)), "geometry_recomputed": geometry_ok, "fusion_raw_identity": fusion_identity, "g1_cells_recomputed": len(recomputed), "gate": gate, "fair1m_d_universe": d_universe, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.result, args.manifest)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
