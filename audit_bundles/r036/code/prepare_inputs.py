#!/usr/bin/env python3
"""Build the immutable r036 modeling table from frozen r034 rows and feature assets."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
R034 = ROOT / "audit_bundles/r034"
R032_INV = ROOT / "reports/r032_circularity_asset_preflight/source_inventory.csv"
SEED = 20260814
UNITS = tuple("ABCDEFGH")
DOTA_NAMES = [
    "plane", "baseball-diamond", "bridge", "ground-track-field", "small-vehicle",
    "large-vehicle", "ship", "tennis-court", "basketball-court", "storage-tank",
    "soccer-ball-field", "roundabout", "harbor", "swimming-pool", "helicopter",
]
ALIASES = {
    "airplane": "plane", "baseballfield": "baseball-diamond",
    "baseball-field": "baseball-diamond", "basketballcourt": "basketball-court",
    "groundtrackfield": "ground-track-field", "storagetank": "storage-tank",
    "tenniscourt": "tennis-court", "fishing-boat": "ship", "fishing boat": "ship",
    "passenger-ship": "ship", "cargo-ship": "ship", "dry-cargo-ship": "ship",
    "liquid-cargo-ship": "ship", "engineering-ship": "ship", "motorboat": "ship",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def normalize_class(value, unit: str) -> str:
    text = str(value).strip()
    if unit in "GH" and text.lstrip("-").isdigit():
        idx = int(text)
        if not 0 <= idx < len(DOTA_NAMES):
            raise RuntimeError(f"DOTA class index outside 0..14: {text}")
        text = DOTA_NAMES[idx]
    text = text.lower().replace("_", "-").replace(" ", "-")
    while "--" in text:
        text = text.replace("--", "-")
    return ALIASES.get(text, text)


def long_axis_angle(obb: dict) -> float:
    theta = float(obb["obb_theta"])
    if float(obb["obb_w"]) < float(obb["obb_h"]):
        theta += math.pi / 2
    return theta % math.pi


def signed_axial_residual(record: dict) -> float:
    diff = long_axis_angle(record["pred_obb"]) - long_axis_angle(record["gt_obb"])
    return math.degrees((diff + math.pi / 2) % math.pi - math.pi / 2)


def fold_for(dataset: str, cluster: str) -> int:
    token = f"{SEED}|{dataset}|{cluster}".encode()
    return int.from_bytes(hashlib.sha256(token).digest()[:8], "little") % 5


def main() -> None:
    (OUT / "inputs").mkdir(parents=True, exist_ok=True)
    base = pd.read_parquet(R034 / "inputs/matched_rows_enriched.parquet")
    base["image_id"] = base.image_id.astype(str)
    base["pred_id"] = base.pred_id.astype(np.int64)
    inv = pd.read_csv(R032_INV)
    all_parts, join_rows, sources = [], [], []

    for unit in UNITS:
        frame = base.loc[base.unit.eq(unit)].copy()
        if frame.empty:
            raise RuntimeError(f"missing unit {unit}")
        feature_path = Path(inv.loc[(inv.unit.eq(unit)) & inv.semantic_role.eq("features"), "absolute_path"].iloc[0])
        geometry_path = Path(inv.loc[(inv.unit.eq(unit)) & inv.semantic_role.eq("matched_geometry"), "absolute_path"].iloc[0])
        for role, path in (("features", feature_path), ("matched_geometry", geometry_path)):
            if not path.is_file():
                raise RuntimeError(f"missing {unit} {role}: {path}")
            sources.append({"unit": unit, "role": role, "absolute_path": str(path), "bytes": path.stat().st_size, "sha256": sha(path), "read_only": True})

        cols = ["image_id", "pred_id", "half_log_pred_area", "u_axis", "missing_fraction", "iou_loss", "detection_score"]
        features = pd.read_parquet(feature_path, columns=cols)
        features["image_id"] = features.image_id.astype(str); features["pred_id"] = features.pred_id.astype(np.int64)
        if features.duplicated(["image_id", "pred_id"]).any():
            raise RuntimeError(f"duplicate feature key {unit}")
        before = len(frame)
        frame = frame.merge(features, on=["image_id", "pred_id"], how="left", validate="one_to_one", suffixes=("", "_feature"))
        feature_missing = int(frame.half_log_pred_area.isna().sum())
        if feature_missing:
            raise RuntimeError(f"feature join missing {unit}: {feature_missing}")

        wanted = set(zip(frame.image_id, frame.pred_id.astype(int)))
        geometry = {}
        with geometry_path.open() as handle:
            for line in handle:
                record = json.loads(line)
                key = (str(record["image_id"]), int(record["pred_id"]))
                if key not in wanted:
                    continue
                if key in geometry:
                    raise RuntimeError(f"duplicate matched geometry {unit} {key}")
                residual = signed_axial_residual(record)
                geometry[key] = (normalize_class(record["class"], unit), residual)
        missing_geometry = wanted.difference(geometry)
        if missing_geometry:
            raise RuntimeError(f"matched geometry join missing {unit}: {len(missing_geometry)}")
        frame["class_name"] = [geometry[(i, int(p))][0] for i, p in zip(frame.image_id, frame.pred_id)]
        frame["signed_residual_deg"] = [geometry[(i, int(p))][1] for i, p in zip(frame.image_id, frame.pred_id)]
        max_error_difference = float(np.max(np.abs(np.abs(frame.signed_residual_deg.to_numpy()) - frame.e_can.to_numpy(float))))
        if max_error_difference > 2e-5:
            raise RuntimeError(f"canonical error mismatch {unit}: {max_error_difference}")

        frame["log_area"] = 2.0 * frame.half_log_pred_area.astype(float)
        frame["angle_error"] = frame.e_can.astype(float)
        frame["detection_score"] = frame.conf.astype(float)
        frame["fold"] = [fold_for(str(d), str(c)) for d, c in zip(frame.dataset, frame.cluster)]
        frame["row_id"] = [f"{unit}|{i}|{int(p)}" for i, p in zip(frame.image_id, frame.pred_id)]
        keep = ["row_id", "unit", "dataset", "detector", "image_id", "pred_id", "cluster", "fold", "class_id", "class_name", "gt_ar", "log_pred_ar", "log_area", "angle_error", "signed_residual_deg", "u_axis", "missing_fraction", "iou_loss", "detection_score"]
        frame = frame[keep]
        if not np.isfinite(frame.select_dtypes(include=[np.number])).all().all():
            raise RuntimeError(f"nonfinite prepared fields {unit}")
        join_rows.append({"unit": unit, "input_rows": before, "output_rows": len(frame), "feature_missing": feature_missing, "geometry_missing": len(missing_geometry), "max_abs_error_identity_difference_deg": max_error_difference, "status": "PASS"})
        all_parts.append(frame)

    rows = pd.concat(all_parts, ignore_index=True)
    if rows.row_id.duplicated().any():
        raise RuntimeError("duplicate row_id")
    rows.to_parquet(OUT / "inputs/qsetod_rows.parquet", index=False, compression="zstd")
    pd.DataFrame(join_rows).to_csv(OUT / "inputs/join_audit.csv", index=False)
    pd.DataFrame(sources).to_csv(OUT / "inputs/source_inventory.csv", index=False)
    cluster_rows = rows[["dataset", "cluster"]].drop_duplicates().sort_values(["dataset", "cluster"])
    cluster_rows["cluster_index"] = cluster_rows.groupby("dataset").cumcount()
    cluster_rows.to_csv(OUT / "inputs/cluster_universe.csv", index=False)
    result = {"schema": "r036_prepared_input_v1", "rows": len(rows), "units": rows.unit.value_counts().sort_index().to_dict(), "datasets": rows.dataset.value_counts().sort_index().to_dict(), "clusters": cluster_rows.groupby("dataset").size().to_dict(), "target_label_columns": ["angle_error", "signed_residual_deg"], "target_label_fit_guard": "enforced in implementations by train_unit membership", "seed": SEED}
    (OUT / "inputs/preparation_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
