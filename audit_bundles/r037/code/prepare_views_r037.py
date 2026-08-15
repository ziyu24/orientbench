#!/usr/bin/env python3
"""Create phase-separated r037 views from the locked r036 row cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

CONFIGS = [
    ("HOdet_A_to_B", "A", "B"),
    ("HOdet_A_to_C", "A", "C"),
    ("HOdet_BC_to_A", "BC", "A"),
    ("HOdata_ABC_to_D", "ABC", "D"),
    ("HOdata_ABC_to_E", "ABC", "E"),
    ("HOdata_ABC_to_F", "ABC", "F"),
    ("HOdata_ABC_to_G", "ABC", "G"),
    ("HOdata_ABC_to_H", "ABC", "H"),
]
LABELS = ["angle_error", "signed_residual_deg"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def emit(frame: pd.DataFrame, path: Path) -> dict:
    frame.to_parquet(path, index=False, compression="zstd")
    return {"path": str(path), "rows": len(frame), "bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = pd.read_parquet(args.input)
    if len(rows) != 616184 or set(rows.unit) != set("ABCDEFGH") or rows.row_id.duplicated().any():
        raise RuntimeError("locked cohort identity failed")
    manifest = {"schema_version": 1, "input": {"path": str(args.input), "rows": len(rows), "bytes": args.input.stat().st_size, "sha256": sha(args.input)}, "views": []}
    for source_key in ("A", "BC", "ABC"):
        source = rows.loc[rows.unit.isin(list(source_key))].copy().sort_values("row_id")
        manifest["views"].append(emit(source, args.output / f"source_labeled_{source_key}.parquet"))
    covariate_columns = [c for c in rows.columns if c not in LABELS]
    for config, _, target_unit in CONFIGS:
        target = rows.loc[rows.unit.eq(target_unit)].copy().sort_values("row_id")
        manifest["views"].append(emit(target[covariate_columns], args.output / f"target_covariates_{config}.parquet"))
        manifest["views"].append(emit(target[["row_id", "unit", "dataset", "detector", "cluster", *LABELS]], args.output / f"target_evaluation_labels_{config}.parquet"))
    (args.output / "view_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    guard = {
        "schema_version": 1,
        "phase_boundary": "fit processes may open source_labeled and target_covariates only; evaluation labels are opened only after prediction seals exist",
        "target_label_rows_in_fit": 0,
        "clean_endpoint_access_count": 0,
        "inventory_not_authorization": True,
    }
    (args.output / "phase_guard.json").write_text(json.dumps(guard, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
