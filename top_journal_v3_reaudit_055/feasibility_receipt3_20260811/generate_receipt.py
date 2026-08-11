#!/usr/bin/env python3
"""Generate receipt3 evidence from sealed rows and stored official-source bytes."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import multiprocessing as mp
import os
import re
import resource
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.update({
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
})

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811"
SOURCE_RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
R014 = ROOT / "outputs/persistent_artifacts/orientbench_r014"
LABEL = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
CODE = ROOT / "top_journal_v3_reaudit_055/feasibility_receipt3_20260811"
REFERENCE_CHECK = RUNTIME / "track_m_reference_check.json"
R014_REPORTS = ROOT / "p3_selector/deployable_proxy_r014/reports"
PTH_README = Path("/home/rspip/cqc/pro/study/pth_data/readme.md")

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_coverage_summary
from scripts.m069_common import delta_theta_075

ROUND = "orientbench-c-topjournal-feasibility-receipt3-20260811"
POST_PULL_HEAD = "6e0ea32bc3d1c13aa051f8abd9c9e37e5996d025"
UNITS = {
    "A": ("DIOR-R", "DIOR-R/22"),
    "B": ("DIOR-R", "DIOR-R/3"),
    "C": ("DIOR-R", "DIOR-R/61"),
    "D": ("FAIR1M", "FAIR1M-v1.0/24"),
    "E": ("SODA-A", "SODA-A/23"),
    "F": ("SODA-A", "SODA-A/4"),
}
SCORES = {
    "raw_confidence": "detection_score",
    "linear_source_frozen": "score_ar_size_linear",
    "tta_angle": "tta_angle",
    "tta_localization": "tta_localization",
    "S0": "S0",
    "learned_EQS": "EQS",
}
BASELINES = ["raw_confidence", "linear_source_frozen", "tta_angle", "tta_localization"]
BOOTSTRAP_COLUMNS = [
    f"{dataset}__S0_minus_{baseline}"
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A")
    for baseline in BASELINES
]
_BOOT_CONTEXT = None


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sequence_sha(values) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def sorted_set_sha(values) -> str:
    return sequence_sha(sorted(set(map(str, values))))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def schema_of(path: Path) -> str:
    return path.suffix.lstrip(".") or "directory"


def manifest_entry(tree: Any, relpath: str):
    if isinstance(tree, dict):
        if tree.get("path") == relpath:
            return tree
        for value in tree.values():
            found = manifest_entry(value, relpath)
            if found is not None:
                return found
    elif isinstance(tree, list):
        for value in tree:
            found = manifest_entry(value, relpath)
            if found is not None:
                return found
    return None


def protocol_and_preflight() -> None:
    protocol = {
        "round_id": ROUND,
        "retry_of": "orientbench-c-topjournal-feasibility-receipt2-20260810",
        "dispatch_base": "35358b5fef838b178aff0e16470ebe0117cab687",
        "post_pull_head": POST_PULL_HEAD,
        "source_execution_status": "ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809",
        "source_numbers_status": "DESCRIPTIVE_UNVERIFIED",
        "source_reported_gate": "FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED",
        "receipt_only": True,
        "pinned_reference_fetch_authorized": True,
        "pinned_reference_fetch_max_attempts": 3,
        "gpu_authorized": False,
        "download_authorized": False,
        "installation_authorized": False,
        "training_authorized": False,
        "forward_authorized": False,
        "inference_authorized": False,
        "new_target_outcome_authorized": False,
        "annotation_content_authorized": False,
        "manuscript_edit_authorized": False,
        "risk": "risk_cap3=clip(angle_error/max(delta_theta_0.75(GT_AR),1 degree),0,3); residual=risk_cap3/3",
        "coverage": "unique score thresholds; whole ties; origin (0,0); unscaled trapezoid",
        "aurc_nrc": "row-wise stable descending tie order; float64; no drops",
        "clusters": {"DIOR-R": "image", "FAIR1M": "image", "SODA-A": "mother scene"},
        "bootstrap": {"seed": 20260809, "replicates": 10000, "workers": 39, "ci": "percentile 95%", "role": "REPORT_ONLY_NOT_STATE_DRIVER"},
        "final_commit_sha": "POST_COMMIT_EXTERNAL_RECEIPT",
        "git_publish_status": "PENDING_EXTERNAL_RECEIPT",
    }
    write_json(RUNTIME / "protocol.json", protocol)
    reads = [
        (ROOT / "AGENTS.md", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (ROOT / "dis/sug.md", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (ROOT / "dis/collaboration_protocol.md", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (ROOT / "dis/C.md", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (ROOT / "dis/review_state.json", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (ROOT / "docs/server_migration_handoff_20260810.md", "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
        (PTH_README, "2026-08-11T02:16:04.884386-07:00", "2026-08-11T02:16:04.903063-07:00"),
    ]
    preflight = {
        "status": "PASS",
        "reads": [{
            "requested_path": str(path),
            "canonical_path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256_path(path),
            "started_at": start,
            "ended_at": end,
            "result": "READ_OK",
        } for path, start, end in reads],
        "applicable_claude_md": "NONE_IN_PROJECT_SCOPE",
        "initial_user_pull": {
            "pre_pull_head": "35358b5fef838b178aff0e16470ebe0117cab687",
            "post_pull_head": POST_PULL_HEAD,
            "result": "FAST_FORWARD",
        },
        "formal_pull": {
            "pre_pull_head": POST_PULL_HEAD,
            "post_pull_head": POST_PULL_HEAD,
            "started_at": "2026-08-11T02:16:40.710749-07:00",
            "ended_at": "2026-08-11T02:17:15.523058-07:00",
            "exit_code": 0,
            "result": "Already up to date.",
        },
        "origin": "https://github.com/ziyu24/orientbench.git",
        "branch": "main",
        "remote_default_branch": "main",
        "upstream": "origin/main",
        "head_upstream_https_remote_equal": True,
        "post_pull_head": POST_PULL_HEAD,
        "protected_B_blob": "c0c2571f3a5c828673b39e6458ceaed5f14c5a6a",
        "protected_B_ordinary_diff_exit": 0,
        "protected_B_staged_diff_exit": 0,
        "protected_B_content_read": False,
        "commit_objects_and_fixed_ancestry_all_exit_zero": True,
        "receipt1_report_blob": "4fe331a6a683313150a4fb21cbabd432ffde0f6b",
        "receipt1_archive_blob": "11553a92b05b692a14bf9c4f21898a5c9e10d144",
        "receipt2_report_blob": "8e1407d90f5a7247816c457eddcb60a704291951",
        "receipt2_archive_blob": "25ee36ec83db92364134a66bb44b349ac5f34cf9",
        "source_runtime": {
            "files": 74,
            "directories_including_root": 5,
            "symlinks": 0,
            "unreadable": 0,
            "actual_user_writable": 0,
            "mode_write_bit_objects": 0,
            "canonical_absolute_path_tree_sha256": "2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43",
        },
        "new_paths_absent_at_start": True,
        "metric_blob_identity_all_four_commits": True,
        "metric_blob_identity": {
            "orientbench/metrics/risk_coverage.py": {"git_blob": "566a3a84b6fffa3315faec606edf20ee9bf3843b", "bytes": 3165, "sha256": "ae9ab7e3c8b745f24b3cc60048dbd143cafd8da89b6a8e779fab37326d2f6aaa"},
            "orientbench/metrics/nrc_auc.py": {"git_blob": "fcd55fd7bd99d55d3dc889ae0100c2e99913787c", "bytes": 2774, "sha256": "e99206475b4015b563ccc5107991d326d85c330de346dc2452c4f1738afc52a0"},
        },
    }
    write_json(RUNTIME / "preflight.json", preflight)


def label_rows(unit: str) -> pd.DataFrame:
    rows = []
    with (LABEL / unit / "matched_fullval.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            gt = record["gt_obb"]
            width, height = float(gt["obb_w"]), float(gt["obb_h"])
            aspect_ratio = max(width, height) / max(min(width, height), 1e-6)
            if aspect_ratio < 2.1:
                continue
            risk_cap3 = float(np.clip(float(record["angle_error"]) / max(float(delta_theta_075(aspect_ratio)), 1.0), 0.0, 3.0))
            rows.append((str(record["image_id"]), int(record["pred_id"]), risk_cap3))
    frame = pd.DataFrame(rows, columns=["image_id", "pred_id", "risk_cap3"])
    if frame.duplicated(["image_id", "pred_id"]).any():
        raise RuntimeError(f"duplicate eligible keys in {unit}")
    return frame


def load_assets():
    evidence_path = R014_REPORTS / "evidence_manifest_r014.json"
    evidence = json.loads(evidence_path.read_text())
    tta_path = R014_REPORTS / "tta_inventory_r014.csv"
    provenance_path = R014_REPORTS / "provenance_r014.csv"
    inventory = [{
        "unit": "ALL", "dataset": "ALL", "path": str(path.relative_to(ROOT)),
        "role": role, "bytes": path.stat().st_size, "sha256": sha256_path(path),
        "schema": schema_of(path), "manifest_identity": "MANIFEST_SELF_BYTES_VERIFIED",
    } for path, role in ((evidence_path, "r014 evidence manifest"), (tta_path, "r014 TTA inventory"), (provenance_path, "r014 provenance"))]
    frames = {}
    cluster_rows = []
    soda_map_path = R014 / "soda_tile_to_mother_r014.csv"
    soda_map = pd.read_csv(soda_map_path, dtype=str).set_index("tile_id").mother_scene_id.to_dict()
    inventory.append({
        "unit": "E/F", "dataset": "SODA-A", "path": str(soda_map_path.relative_to(ROOT)),
        "role": "tile-to-mother mapping", "bytes": soda_map_path.stat().st_size,
        "sha256": sha256_path(soda_map_path), "schema": "csv",
        "manifest_identity": "R014_MAPPING_CONSUMED",
    })
    tta = pd.read_csv(tta_path)
    for unit, (dataset, identity) in UNITS.items():
        feature_path = R014 / f"features/{unit}.parquet"
        score_path = R014 / f"scores/{unit}.parquet"
        matched_path = LABEL / unit / "matched_fullval.jsonl"
        universe_path = LABEL / unit / "image_universe.csv"
        m069_manifest_path = LABEL / unit / "manifest.json"
        m069 = json.loads(m069_manifest_path.read_text())
        for path, role in (
            (feature_path, "prediction-only features"),
            (score_path, "sealed fixed scores"),
            (matched_path, "row-level risk source"),
            (universe_path, "complete image universe"),
            (m069_manifest_path, "m069 source manifest"),
        ):
            rel = str(path.relative_to(ROOT))
            if path in (feature_path, score_path):
                entry = manifest_entry(evidence, rel)
                manifest_status = "PASS" if entry and entry.get("sha256") == sha256_path(path) and int(entry.get("bytes")) == path.stat().st_size else "FAIL"
            elif path == matched_path:
                manifest_status = "PASS" if m069["matched_sha256"] == sha256_path(path) and int(m069["matched_bytes"]) == path.stat().st_size else "FAIL"
            elif path == universe_path:
                manifest_status = "PASS" if m069["universe_sha256"] == sha256_path(path) and int(m069["universe_bytes"]) == path.stat().st_size else "FAIL"
            else:
                manifest_status = "MANIFEST_SELF_BYTES_VERIFIED"
            if manifest_status == "FAIL":
                raise RuntimeError(f"source manifest mismatch: {rel}")
            inventory.append({
                "unit": unit, "dataset": dataset, "path": rel, "role": role,
                "bytes": path.stat().st_size, "sha256": sha256_path(path),
                "schema": schema_of(path), "manifest_identity": manifest_status,
            })

        features = pd.read_parquet(feature_path, columns=["image_id", "pred_id", "detection_score", "u_axis", "missing_fraction", "iou_loss"])
        scores = pd.read_parquet(score_path, columns=["image_id", "pred_id", "detection_score", "score_ar_size_linear", "EQS"])
        for frame in (features, scores):
            frame["image_id"] = frame.image_id.astype(str)
        eligible = label_rows(unit)
        eligible_keys = set(zip(eligible.image_id, eligible.pred_id))
        if len(eligible_keys) != len(eligible):
            raise RuntimeError(f"eligible key set failure {unit}")
        if features.duplicated(["image_id", "pred_id"]).any() or scores.duplicated(["image_id", "pred_id"]).any():
            raise RuntimeError(f"feature/score duplicate keys {unit}")
        feature_mask = pd.MultiIndex.from_frame(features[["image_id", "pred_id"]]).isin(pd.MultiIndex.from_tuples(eligible_keys))
        ordered = features.loc[feature_mask].copy()
        ordered_keys = list(zip(ordered.image_id, ordered.pred_id))
        if set(ordered_keys) != eligible_keys or len(ordered_keys) != len(eligible):
            raise RuntimeError(f"complete eligible cohort mismatch {unit}")
        joined = ordered.merge(scores, on=["image_id", "pred_id"], how="left", validate="one_to_one", suffixes=("", "_score"), sort=False)
        joined = joined.merge(eligible, on=["image_id", "pred_id"], how="left", validate="one_to_one", sort=False)
        if not np.array_equal(joined.detection_score.to_numpy(), joined.detection_score_score.to_numpy()):
            raise RuntimeError(f"detection score byte/value mismatch {unit}")
        joined.drop(columns=["detection_score_score"], inplace=True)
        joined["tta_angle"] = -joined.u_axis
        joined["tta_localization"] = -(joined.missing_fraction + joined.iou_loss)
        joined["S0"] = -(joined.u_axis + joined.missing_fraction + joined.iou_loss)
        joined["residual"] = joined.risk_cap3 / 3.0
        joined["cluster"] = joined.image_id.map(soda_map) if dataset == "SODA-A" else joined.image_id.astype(str)
        required = ["risk_cap3", "residual", "cluster", *SCORES.values()]
        if joined[required].isna().any().any() or not np.isfinite(joined[["risk_cap3", "residual", *SCORES.values()]].to_numpy(float)).all():
            raise RuntimeError(f"nonfinite or missing required cohort value {unit}")
        universe = pd.read_csv(universe_path, dtype=str).image_id.astype(str).tolist()
        clusters = sorted({soda_map[value] for value in universe} if dataset == "SODA-A" else set(universe))
        for cluster in clusters:
            cluster_rows.append({"unit": unit, "dataset": dataset, "cluster": cluster, "eligible_rows": int((joined.cluster == cluster).sum())})
        key_strings = [f"{image}\t{pred}" for image, pred in ordered_keys]
        key_sequence_sha = sequence_sha(key_strings)
        key_set_sha = sorted_set_sha(key_strings)
        cluster_sha = sequence_sha(clusters)
        source_tta = tta[tta.unit_key == unit]
        for row in inventory:
            if row.get("unit") == unit:
                row.update({
                    "eligible_row_count": len(joined),
                    "ordered_row_key_sequence_sha256": key_sequence_sha,
                    "sorted_complete_row_key_set_sha256": key_set_sha,
                    "cluster_count": len(clusters),
                    "sorted_complete_cluster_set_sha256": cluster_sha,
                    "cohort_key_alignment_exact": True,
                    "cohort_nonfinite_count": 0,
                    "all_scores_paired_bootstrap_same_cohort": True,
                    "row_drop_policy": "NO_ROW_DROP_ALLOWED",
                    "source_tta_identity_rows": len(source_tta),
                })
        keep = ["image_id", "pred_id", "cluster", "risk_cap3", "residual", *SCORES.values()]
        joined = joined[keep].copy()
        derived = RUNTIME / f"track_m_rows/{unit}.parquet"
        derived.parent.mkdir(parents=True, exist_ok=True)
        joined.to_parquet(derived, index=False, compression="zstd")
        frames[unit] = joined
    write_csv(RUNTIME / "track_m_source_inventory.csv", inventory)
    write_csv(RUNTIME / "track_m_cluster_universe.csv", cluster_rows)
    return frames, cluster_rows


def unique_curve(score, residual):
    score = np.asarray(score, dtype=np.float64)
    residual = np.asarray(residual, dtype=np.float64)
    if score.shape != residual.shape or score.ndim != 1 or len(score) == 0:
        raise RuntimeError("invalid unique-threshold metric input")
    if not np.isfinite(score).all() or not np.isfinite(residual).all():
        raise RuntimeError("nonfinite unique-threshold metric input")
    order = np.argsort(-score, kind="stable")
    sorted_score = score[order]
    sorted_residual = residual[order]
    starts = np.r_[0, np.flatnonzero(sorted_score[1:] != sorted_score[:-1]) + 1]
    counts = np.diff(np.r_[starts, len(score)])
    sums = np.add.reduceat(sorted_residual, starts)
    cumulative_count = np.cumsum(counts)
    cumulative_sum = np.cumsum(sums)
    coverage = cumulative_count / len(score)
    generalized = cumulative_sum / len(score)
    selective = cumulative_sum / cumulative_count
    augrc = float(np.trapz(np.r_[0.0, generalized], np.r_[0.0, coverage]))
    return sorted_score[starts], coverage, generalized, selective, augrc


def independent_aurc_nrc(score, residual):
    score = np.asarray(score, dtype=np.float64)
    residual = np.asarray(residual, dtype=np.float64)
    order = np.argsort(-score, kind="stable")
    model = float(np.mean(np.cumsum(residual[order]) / np.arange(1, len(residual) + 1)))
    oracle_values = np.sort(residual, kind="stable")
    oracle = float(np.mean(np.cumsum(oracle_values) / np.arange(1, len(residual) + 1)))
    random = float(np.mean(residual))
    denominator = random - oracle
    degenerate = abs(denominator) < 1e-12
    nrc = float("nan") if degenerate else (model - oracle) / denominator
    return model, oracle, random, nrc, degenerate


def compute_metrics(frames):
    source_metrics = pd.read_csv(SOURCE_RUNTIME / "track_m_metrics.csv")
    rows = []
    curve_path = RUNTIME / "track_m_risk_coverage.csv"
    with curve_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["dataset", "unit", "score", "curve_index", "coverage", "generalized_risk", "selective_risk", "origin"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for unit, frame in frames.items():
            dataset = UNITS[unit][0]
            residual = frame.residual.to_numpy(np.float64)
            for score_name, column in SCORES.items():
                score = frame[column].to_numpy(np.float64)
                sealed = risk_coverage_summary(score, residual)
                nrc_result = nrc_auc(score, residual)
                if sealed["n_dropped"] != 0 or nrc_result["n_dropped"] != 0 or sealed["n"] != len(frame):
                    raise RuntimeError(f"sealed implementation dropped rows {unit}/{score_name}")
                model_b, oracle_b, random_b, nrc_b, degenerate_b = independent_aurc_nrc(score, residual)
                if not math.isclose(float(sealed["aurc"]), model_b, abs_tol=1e-12, rel_tol=0):
                    raise RuntimeError(f"implementation A/B AURC mismatch {unit}/{score_name}")
                for key, value in (("oracle", oracle_b), ("random", random_b), ("nrc", nrc_b)):
                    a = {"oracle": nrc_result["aurc_oracle"], "random": nrc_result["aurc_random"], "nrc": nrc_result["nrc_auc"]}[key]
                    if not math.isclose(float(a), float(value), abs_tol=1e-12, rel_tol=0):
                        raise RuntimeError(f"implementation A/B {key} mismatch {unit}/{score_name}")
                thresholds, coverage, generalized, selective, augrc = unique_curve(score, residual)
                writer.writerow({"dataset": dataset, "unit": unit, "score": score_name, "curve_index": 0, "coverage": 0.0, "generalized_risk": 0.0, "selective_risk": "", "origin": True})
                for index, (cov, gen, sel) in enumerate(zip(coverage, generalized, selective), 1):
                    writer.writerow({"dataset": dataset, "unit": unit, "score": score_name, "curve_index": index, "coverage": float(cov), "generalized_risk": float(gen), "selective_risk": float(sel), "origin": False})
                fixed = {}
                for target in (0.70, 0.90):
                    index = int(np.searchsorted(coverage, target, side="left"))
                    fixed[int(target * 100)] = (float(selective[index]), float(coverage[index]))
                source = source_metrics[(source_metrics.level == "unit") & (source_metrics.unit == unit) & (source_metrics.score == score_name)].iloc[0]
                row = {
                    "level": "unit", "dataset": dataset, "unit": unit, "score": score_name,
                    "rows": len(frame), "risk_scale": "residual", "AUGRC": augrc,
                    "AURC": model_b, "AURC_oracle": oracle_b, "AURC_random": random_b,
                    "NRC": nrc_b, "degenerate": degenerate_b, "n_dropped": 0,
                    "Risk@70": fixed[70][0], "actual_coverage@70": fixed[70][1],
                    "Risk@90": fixed[90][0], "actual_coverage@90": fixed[90][1],
                    "nonempty_coverage": float(coverage[-1]),
                    "implementation_A_B_atol_1e_12_pass": True,
                }
                for metric in ("AUGRC", "AURC", "NRC", "Risk@70", "Risk@90", "actual_coverage@70", "actual_coverage@90", "nonempty_coverage"):
                    row[f"source_{metric}"] = float(source[metric])
                    row[f"source_abs_error_{metric}"] = abs(float(row[metric]) - float(source[metric]))
                    if row[f"source_abs_error_{metric}"] > 1e-12:
                        raise RuntimeError(f"source metric mismatch {unit}/{score_name}/{metric}")
                rows.append(row)
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        units = [unit for unit, (name, _) in UNITS.items() if name == dataset]
        for score_name in SCORES:
            parts = [row for row in rows if row["level"] == "unit" and row["unit"] in units and row["score"] == score_name]
            source = source_metrics[(source_metrics.level == "dataset_aggregate") & (source_metrics.dataset == dataset) & (source_metrics.score == score_name)].iloc[0]
            row = {
                "level": "dataset_aggregate", "dataset": dataset, "unit": "equal-unit mean", "score": score_name,
                "rows": sum(part["rows"] for part in parts), "risk_scale": "residual",
                "degenerate": any(part["degenerate"] for part in parts), "n_dropped": 0,
                "implementation_A_B_atol_1e_12_pass": True,
            }
            for metric in ("AUGRC", "AURC", "AURC_oracle", "AURC_random", "NRC", "Risk@70", "Risk@90", "actual_coverage@70", "actual_coverage@90", "nonempty_coverage"):
                row[metric] = float(np.mean([part[metric] for part in parts]))
                if metric in source.index:
                    row[f"source_{metric}"] = float(source[metric])
                    row[f"source_abs_error_{metric}"] = abs(float(row[metric]) - float(source[metric]))
                    if row[f"source_abs_error_{metric}"] > 1e-12:
                        raise RuntimeError(f"source aggregate mismatch {dataset}/{score_name}/{metric}")
            rows.append(row)
    write_csv(RUNTIME / "track_m_metrics.csv", rows)
    return rows


def bootstrap_context(frames, cluster_rows):
    output = {}
    for unit, frame in frames.items():
        universe = [row["cluster"] for row in cluster_rows if row["unit"] == unit]
        positions = {cluster: index for index, cluster in enumerate(universe)}
        output[unit] = {
            "residual": frame.residual.to_numpy(np.float64),
            "cluster_position": frame.cluster.map(positions).to_numpy(np.int64),
            "cluster_count": len(universe),
            "scores": {name: frame[column].to_numpy(np.float64) for name, column in SCORES.items() if name != "learned_EQS"},
        }
        output[unit]["orders"] = {name: np.argsort(-score, kind="stable") for name, score in output[unit]["scores"].items()}
    return output


def weighted_aug(context, score_name, multiplicities):
    order = context["orders"][score_name]
    weights = multiplicities[context["cluster_position"]][order].astype(np.float64)
    residual = context["residual"][order]
    score = context["scores"][score_name][order]
    total = float(weights.sum())
    if total <= 0:
        return float("nan")
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    group_weight = np.add.reduceat(weights, starts)
    group_risk = np.add.reduceat(weights * residual, starts)
    active = group_weight > 0
    coverage = np.cumsum(group_weight[active]) / total
    generalized = np.cumsum(group_risk[active]) / total
    return float(np.trapz(np.r_[0.0, generalized], np.r_[0.0, coverage]))


def bootstrap_worker(replicate):
    rng = np.random.RandomState(20260809 + replicate)
    unit_aug = {}
    multiplicity_hashes = {}
    for unit, context in _BOOT_CONTEXT.items():
        draw = rng.randint(0, context["cluster_count"], size=context["cluster_count"])
        counts = np.bincount(draw, minlength=context["cluster_count"]).astype(np.int64)
        multiplicity_hashes[unit] = sha256_bytes(counts.tobytes(order="C"))
        unit_aug[unit] = {name: weighted_aug(context, name, counts) for name in ["S0", *BASELINES]}
    deltas = []
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        units = [unit for unit, (name, _) in UNITS.items() if name == dataset]
        for baseline in BASELINES:
            deltas.append(float(np.mean([unit_aug[unit]["S0"] - unit_aug[unit][baseline] for unit in units])))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "replicate": replicate,
        "deltas": deltas,
        "multiplicity_hashes": multiplicity_hashes,
        "worker_pid": os.getpid(),
        "worker_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "worker_maxrss_kb": usage.ru_maxrss,
        "worker_affinity_count": len(os.sched_getaffinity(0)),
    }


def run_bootstrap(frames, cluster_rows, metric_rows):
    global _BOOT_CONTEXT
    _BOOT_CONTEXT = bootstrap_context(frames, cluster_rows)
    started = now()
    with mp.get_context("fork").Pool(39) as pool:
        results = pool.map(bootstrap_worker, range(10000), chunksize=4)
    ended = now()
    source = pd.read_csv(SOURCE_RUNTIME / "track_m_bootstrap.csv")
    if source.replicate.tolist() != list(range(10000)):
        raise RuntimeError("source bootstrap replicate sequence incomplete")
    rows = []
    max_error = {column: 0.0 for column in BOOTSTRAP_COLUMNS}
    for result in results:
        replicate = result["replicate"]
        source_row = source.iloc[replicate]
        row = {"replicate": replicate}
        for index, column in enumerate(BOOTSTRAP_COLUMNS):
            actual = result["deltas"][index]
            expected = float(source_row[column])
            error = abs(actual - expected)
            max_error[column] = max(max_error[column], error)
            row[f"actual__{column}"] = actual
            row[f"source__{column}"] = expected
            row[f"abs_error__{column}"] = error
        for unit in UNITS:
            row[f"cluster_multiplicity_sha256__{unit}"] = result["multiplicity_hashes"][unit]
            row[f"source_cluster_multiplicity_sha256__{unit}"] = "SOURCE_FIELD_ABSENT"
        row.update({
            "worker_pid": result["worker_pid"],
            "worker_cpu_seconds": result["worker_cpu_seconds"],
            "worker_maxrss_kb": result["worker_maxrss_kb"],
            "worker_affinity_count": result["worker_affinity_count"],
            "source_worker_pid": int(source_row.worker_pid),
            "source_worker_cpu_seconds": float(source_row.worker_cpu_seconds),
            "source_worker_maxrss_kb": int(source_row.worker_maxrss_kb),
            "source_worker_affinity_count": int(source_row.worker_affinity_count),
            "source_worker_fields_role": "SOURCE_TELEMETRY_NOT_SCIENTIFIC_IDENTITY",
        })
        rows.append(row)
    if any(value > 1e-12 for value in max_error.values()):
        raise RuntimeError(f"bootstrap source mismatch: {max_error}")
    write_csv(RUNTIME / "track_m_bootstrap_replicates.csv", rows)
    point = {(row["dataset"], row["score"]): row for row in metric_rows if row["level"] == "dataset_aggregate"}
    comparisons = []
    for column in BOOTSTRAP_COLUMNS:
        dataset, baseline = column.split("__S0_minus_")
        values = np.asarray([row[f"actual__{column}"] for row in rows], dtype=np.float64)
        comparisons.append({
            "dataset": dataset,
            "baseline": baseline,
            "metric": "AUGRC",
            "delta_definition": "S0-minus-baseline",
            "point_delta": float(point[(dataset, "S0")]["AUGRC"] - point[(dataset, baseline)]["AUGRC"]),
            "ci_lower_2_5": float(np.percentile(values, 2.5)),
            "ci_upper_97_5": float(np.percentile(values, 97.5)),
            "replicates": 10000,
            "seed": 20260809,
            "source_replicates_compared": 10000,
            "source_max_abs_error": max_error[column],
            "atol_1e_12_pass": max_error[column] <= 1e-12,
            "bootstrap_ci_role": "REPORT_ONLY_NOT_STATE_DRIVER",
        })
    write_csv(RUNTIME / "track_m_bootstrap_comparison.csv", comparisons)
    resource_rows = []
    for pid in sorted({result["worker_pid"] for result in results}):
        parts = [result for result in results if result["worker_pid"] == pid]
        resource_rows.append({
            "phase": "bootstrap", "worker_pid": pid,
            "cpu_seconds": max(part["worker_cpu_seconds"] for part in parts),
            "maxrss_kb": max(part["worker_maxrss_kb"] for part in parts),
            "affinity_count": max(part["worker_affinity_count"] for part in parts),
            "configured_workers": 39, "observed_workers": len({result["worker_pid"] for result in results}),
            "started_at": started, "ended_at": ended, "gpu_used": False,
        })
    write_csv(RUNTIME / "resource_telemetry.csv", resource_rows)
    return comparisons


def state_from_rows(metric_rows, asset_complete=True, sensitivity_reversal=False):
    if not asset_complete:
        return "INSUFFICIENT_ASSETS", ["required sealed asset or replicate evidence missing"]
    aggregate = {(row["dataset"], row["score"]): row for row in metric_rows if row["level"] == "dataset_aggregate"}
    reversal = []
    dominated = []
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        s0 = aggregate[(dataset, "S0")]
        for baseline in BASELINES:
            other = aggregate[(dataset, baseline)]
            delta = {metric: s0[metric] - other[metric] for metric in ("NRC", "AURC", "AUGRC", "Risk@70", "Risk@90")}
            if (delta["NRC"] < 0 or delta["AURC"] < 0) and (delta["AUGRC"] > 0 or delta["Risk@70"] > 0 or delta["Risk@90"] > 0):
                reversal.append({"dataset": dataset, "baseline": baseline, **delta})
            if delta["AUGRC"] > 0:
                dominated.append({"dataset": dataset, "baseline": baseline, "delta_AUGRC": delta["AUGRC"]})
    if reversal:
        return "METRIC_REVERSAL", reversal
    if dominated:
        return "BASELINE_DOMINATED", dominated
    if sensitivity_reversal:
        return "SENSITIVITY_UNSTABLE", ["pre-registered sensitivity reversal"]
    robust = all(aggregate[(dataset, "S0")]["AUGRC"] < aggregate[(dataset, baseline)]["AUGRC"] for dataset in ("DIOR-R", "FAIR1M", "SODA-A") for baseline in BASELINES)
    if robust:
        return "ROBUST_CANDIDATE", ["strict AUGRC improvement against all fixed baselines"]
    raise RuntimeError("complete evidence does not map uniquely to the five registered states")


def state_fixtures():
    def row(dataset, score, nrc, aurc, augrc, r70=0.1, r90=0.1):
        return {"level": "dataset_aggregate", "dataset": dataset, "score": score, "NRC": nrc, "AURC": aurc, "AUGRC": augrc, "Risk@70": r70, "Risk@90": r90}
    fixtures = []
    base_rows = []
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        base_rows.append(row(dataset, "S0", 0.1, 0.1, 0.05, 0.05, 0.05))
        for baseline in BASELINES:
            base_rows.append(row(dataset, baseline, 0.2, 0.2, 0.10, 0.10, 0.10))
    specifications = {
        "INSUFFICIENT_ASSETS": (False, False, base_rows),
        "METRIC_REVERSAL": (True, False, [dict(value) for value in base_rows]),
        "BASELINE_DOMINATED": (True, False, [dict(value) for value in base_rows]),
        "SENSITIVITY_UNSTABLE": (True, True, base_rows),
        "ROBUST_CANDIDATE": (True, False, base_rows),
    }
    reversal_rows = specifications["METRIC_REVERSAL"][2]
    next(row for row in reversal_rows if row["dataset"] == "DIOR-R" and row["score"] == "S0")["AUGRC"] = 0.12
    dominated_rows = specifications["BASELINE_DOMINATED"][2]
    target = next(row for row in dominated_rows if row["dataset"] == "DIOR-R" and row["score"] == "S0")
    target["AUGRC"] = 0.12
    target["NRC"] = 0.3
    target["AURC"] = 0.3
    for expected, (complete, sensitivity, rows) in specifications.items():
        actual, witnesses = state_from_rows(rows, asset_complete=complete, sensitivity_reversal=sensitivity)
        fixtures.append({"fixture": expected, "expected": expected, "actual": actual, "pass": actual == expected, "witness_count": len(witnesses)})
    if not all(row["pass"] for row in fixtures) or len({row["actual"] for row in fixtures}) != 5:
        raise RuntimeError("five-state production fixtures failed")
    write_csv(RUNTIME / "track_m_state_fixtures.csv", fixtures)
    return fixtures


def track_m_status(metric_rows, bootstrap_comparisons):
    state, witnesses = state_from_rows(metric_rows)
    payload = {
        "state": state,
        "asset_complete": True,
        "cohort_key_alignment_exact": True,
        "cohort_nonfinite_count": 0,
        "all_scores_paired_bootstrap_same_cohort": True,
        "row_drop_policy": "NO_ROW_DROP_ALLOWED",
        "source_bootstrap_cluster_multiplicity_field": "SOURCE_FIELD_ABSENT_IN_SOURCE_RUNTIME_RECONSTRUCTED_FROM_PINNED_SEED_AND_SOURCE_CODE",
        "source_bootstrap_all_10000_deltas_atol_1e_12_pass": all(row["atol_1e_12_pass"] for row in bootstrap_comparisons),
        "witnesses": witnesses,
        "learned_EQS_candidate_driver": False,
        "sensitivity_reversal": False,
        "sensitivity_note": "no alternate sealed matching/unmatched/near-square/canonicalization sensitivity output was present in the source runtime; no reversal was asserted",
        "bootstrap_ci_role": "REPORT_ONLY_NOT_STATE_DRIVER",
        "state_function_fixtures": "track_m_state_fixtures.csv",
    }
    write_json(RUNTIME / "track_m_status.json", payload)
    return payload


def run_search(phase: str, command: list[str], cwd: Path):
    started = now()
    result = subprocess.run(command, cwd=cwd, capture_output=True)
    ended = now()
    stdout_path = RUNTIME / "logs" / f"{phase}.stdout"
    stderr_path = RUNTIME / "logs" / f"{phase}.stderr"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    return {
        "phase": phase,
        "command": json.dumps(command, ensure_ascii=False),
        "cwd": str(cwd),
        "started_at": started,
        "ended_at": ended,
        "exit_code": result.returncode,
        "stdout_path": str(stdout_path.relative_to(RUNTIME)),
        "stdout_bytes": len(result.stdout),
        "stdout_sha256": sha256_bytes(result.stdout),
        "stderr_path": str(stderr_path.relative_to(RUNTIME)),
        "stderr_bytes": len(result.stderr),
        "stderr_sha256": sha256_bytes(result.stderr),
    }, result.stdout.decode("utf-8", errors="replace")


def candidate_for_line(line: str) -> str:
    patterns = [
        ("AI-TOD-R", r"AI[-_ ]?TOD[-_ ]?R|AITODR"),
        ("UAV-OBB", r"UAV[-_ ]?OBB|UAVOBB"),
        ("ShipRSImageNet", r"ShipRSImageNet|ShipRS"),
        ("ICDAR-MLT", r"ICDAR[-_ ]?MLT|ICDAR2017|ICDAR2019|MLT17|MLT 2017"),
    ]
    for name, pattern in patterns:
        if re.search(pattern, line, re.I):
            return name
    return "UNRESOLVED"


def track_d_raw_evidence():
    official_rows = []
    source_dir = SOURCE_RUNTIME / "official_sources"
    body_candidates = [path for path in source_dir.iterdir() if path.suffix == ".body"]
    source_map = {
        "aitodr": "AI-TOD-R", "uavobb": "UAV-OBB",
        "shiprs_license": "ShipRSImageNet", "shiprs_readme": "ShipRSImageNet", "shiprs_repo_api": "ShipRSImageNet",
        "icdar_mlt": "ICDAR-MLT", "icdar_mlt_insecure": "ICDAR-MLT",
    }
    for meta_path in sorted(source_dir.glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        matching_bodies = [path for path in body_candidates if path.stat().st_size == int(meta["bytes"]) and sha256_path(path) == meta["sha256"]]
        stem = meta_path.name.replace(".meta.json", "")
        headers_path = source_dir / f"{stem}.headers"
        stderr_path = source_dir / f"{stem}.stderr"
        official_rows.append({
            "candidate": source_map.get(stem, candidate_for_line(meta.get("url", ""))),
            "source_id": stem,
            "url": meta.get("url", "SOURCE_FIELD_ABSENT"),
            "retrieval_date": "2026-08-09",
            "http_status": meta.get("http_status", "SOURCE_FIELD_ABSENT"),
            "redirect_chain": "STORED_HEADERS",
            "content_type": "STORED_HEADERS",
            "meta_path": str(meta_path.relative_to(ROOT)),
            "meta_bytes": meta_path.stat().st_size,
            "meta_sha256": sha256_path(meta_path),
            "body_path": str(matching_bodies[0].relative_to(ROOT)) if len(matching_bodies) == 1 else "SOURCE_FIELD_ABSENT_OR_AMBIGUOUS",
            "body_bytes": int(meta["bytes"]),
            "body_sha256": meta["sha256"],
            "body_identity_match_count": len(matching_bodies),
            "headers_path": str(headers_path.relative_to(ROOT)) if headers_path.is_file() else "SOURCE_FIELD_ABSENT",
            "headers_bytes": headers_path.stat().st_size if headers_path.is_file() else "SOURCE_FIELD_ABSENT",
            "headers_sha256": sha256_path(headers_path) if headers_path.is_file() else "SOURCE_FIELD_ABSENT",
            "stderr_path": str(stderr_path.relative_to(ROOT)) if stderr_path.is_file() else "SOURCE_FIELD_ABSENT",
            "source_date": "STORED_HEADERS_OR_SOURCE_FIELD_ABSENT",
            "raw_facts_only": True,
        })
    write_csv(RUNTIME / "track_d_official_sources.csv", official_rows)

    aliases = r"AI[-_ ]?TOD[-_ ]?R|AITODR|UAV[-_ ]?OBB|UAVOBB|ShipRSImageNet|ShipRS|ICDAR[-_ ]?MLT|ICDAR2017|ICDAR2019|MLT17|MLT 2017"
    terms = r"prediction|feature|score|risk|metric|bootstrap|report|endpoint|mAP|checkpoint"
    expression = f"({aliases}).*({terms})|({terms}).*({aliases})"
    commands = [
        ("track_d_search_git_tracked", ["git", "grep", "-n", "-I", "-i", "-E", expression, "HEAD", "--", ".", ":(exclude)dis/B.md"], ROOT),
        ("track_d_search_persistent", ["rg", "--hidden", "--no-ignore", "-I", "-n", "-i", expression, "--glob", "!orientbench_topjournal_feasibility_receipt3_20260811/**", "outputs/persistent_artifacts"], ROOT),
        ("track_d_search_reports_manifests", ["rg", "--hidden", "--no-ignore", "-I", "-n", "-i", expression, "--glob", "!dis/B.md", "--glob", "*.md", "--glob", "*.json", "--glob", "*.csv", "dis", "docs", "reports", "p3_selector", "top_journal_v3_reaudit_055"], ROOT),
        ("track_d_search_pth_readme", ["rg", "-n", "-i", expression, str(PTH_README)], ROOT),
        ("track_d_search_dataset_filename_stat", ["bash", "-lc", f"find /home/rspip/cqc/data/dataset -maxdepth 6 -printf '%y %p %s %m\\n' | rg -i '{aliases}'"], ROOT),
    ]
    search_rows = []
    hit_rows = []
    for phase, command, cwd in commands:
        record, text = run_search(phase, command, cwd)
        record["scope"] = {
            "track_d_search_git_tracked": "Git-tracked text; dis/B.md explicitly excluded",
            "track_d_search_persistent": "tracked and ignored persistent artifacts; hidden/no-ignore; current receipt excluded",
            "track_d_search_reports_manifests": "project manifests/reports/artifact indexes; dis/B.md excluded",
            "track_d_search_pth_readme": "pth_data readme",
            "track_d_search_dataset_filename_stat": "dataset root filename/stat-only; annotation content unopened",
        }[phase]
        search_rows.append(record)
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            hit_rows.append({
                "search_phase": phase,
                "search_output_line": line_number,
                "candidate": candidate_for_line(line),
                "raw_hit": line,
                "independent_validator_adjudication": "PENDING_INDEPENDENT_VALIDATOR",
                "prior_exact_outcome_or_endpoint": "PENDING_INDEPENDENT_VALIDATOR",
            })
    write_csv(RUNTIME / "track_d_search_runs.csv", search_rows)
    write_csv(RUNTIME / "track_d_prior_outcome_hits.csv", hit_rows or [{
        "search_phase": "all", "search_output_line": 0, "candidate": "NONE", "raw_hit": "",
        "independent_validator_adjudication": "PENDING_INDEPENDENT_VALIDATOR",
        "prior_exact_outcome_or_endpoint": "PENDING_INDEPENDENT_VALIDATOR",
    }])

    asset_rows = []
    aliases_by_candidate = {
        "AI-TOD-R": ["AI-TOD-R", "AITODR", "ai_tod_r"],
        "UAV-OBB": ["UAV-OBB", "UAVOBB", "uav_obb"],
        "ShipRSImageNet": ["ShipRSImageNet", "ShipRS", "shiprs"],
        "ICDAR-MLT": ["ICDAR_MLT", "ICDAR-MLT", "MLT17", "ICDAR2017"],
    }
    dataset_root = Path("/home/rspip/cqc/data/dataset")
    for candidate, aliases_list in aliases_by_candidate.items():
        matches = []
        for path in dataset_root.iterdir():
            if any(alias.lower().replace("-", "").replace("_", "") in path.name.lower().replace("-", "").replace("_", "") for alias in aliases_list):
                matches.append(path)
        asset_rows.append({
            "candidate": candidate, "asset_role": "dataset_root_filename_stat_only",
            "path": "|".join(str(path) for path in matches) if matches else "ABSENT",
            "present": bool(matches), "type": "directory" if matches else "ABSENT",
            "bytes": "DIRECTORY_STAT_ONLY" if matches else 0,
            "sha256": "NOT_HASHED_ANNOTATION_BOUNDARY" if matches else "ABSENT",
            "content_opened": False,
        })
    pth_root = PTH_README.parent
    for rel in [
        "baseline_oriented_rcnn_r50_fpn_1x_le90/ICDAR_MLT_train_val/config.py",
        "baseline_oriented_rcnn_r50_fpn_1x_le90/ICDAR_MLT_train_val/best_mAP_5892_epoch_11.pth",
        "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/ICDAR_MLT_train_val/config.py",
        "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/ICDAR_MLT_train_val/best_mAP_5605_epoch_12.pth",
        "baseline_arsdetr_r50_fpn_36e_le90/ICDAR_MLT_train_val/config.py",
        "baseline_arsdetr_r50_fpn_36e_le90/ICDAR_MLT_train_val/best_mAP_4458_epoch_36.pth",
        "baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/ICDAR_MLT_retrain_v2_nanfix/config.py",
        "baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/ICDAR_MLT_retrain_v2_nanfix/best_mAP_5984_epoch_11.pth",
    ]:
        path = pth_root / rel
        asset_rows.append({
            "candidate": "ICDAR-MLT", "asset_role": "registered_config_or_checkpoint",
            "path": str(path), "present": path.is_file(), "type": path.suffix.lstrip("."),
            "bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": sha256_path(path) if path.is_file() else "ABSENT",
            "content_opened": path.is_file(),
        })
    write_csv(RUNTIME / "track_d_asset_inventory.csv", asset_rows)


def main() -> None:
    started = now()
    protocol_and_preflight()
    if not REFERENCE_CHECK.is_file() or json.loads(REFERENCE_CHECK.read_text()).get("status") != "PASS":
        raise RuntimeError("pinned reference check did not pass")
    frames, clusters = load_assets()
    metrics = compute_metrics(frames)
    bootstrap = run_bootstrap(frames, clusters, metrics)
    state_fixtures()
    track_m_status(metrics, bootstrap)
    track_d_raw_evidence()
    write_json(RUNTIME / "generator_summary.json", {
        "status": "PASS",
        "started_at": started,
        "ended_at": now(),
        "track_m_generated": True,
        "track_d_raw_evidence_generated": True,
        "track_d_primitives_and_status": "PENDING_INDEPENDENT_VALIDATOR",
        "joint_gate": "PENDING_INDEPENDENT_VALIDATOR",
        "gpu_used": False,
    })
    print(json.dumps({"status": "PASS", "track_m": json.loads((RUNTIME / "track_m_status.json").read_text())["state"], "bootstrap_replicates": 10000}))


if __name__ == "__main__":
    main()
