#!/usr/bin/env python3
"""Strict command-069 reproduction and submission-freeze auditor.

The default shell entry point rebuilds CPU-only tables from persisted inputs,
then invokes this file with ``--final``. This auditor never trains, evaluates,
or runs detector inference. It fails closed on incomplete lineage, stale hashes,
schema drift, volatile inputs, or an invalid formal statistical claim. Missing
real double annotations are represented as HUMAN_BLOCKED, not fabricated data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pickle
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REP = ROOT / "top_journal_v3_reaudit_055" / "reports"
OUT = ROOT / "reports"
LOG_DIR = ROOT / "logs"
STATUS_CSV = OUT / "069_final_reproduction_status.csv"
GATE_CSV = OUT / "069_submission_freeze_gate.csv"
SNAPSHOT_JSON = LOG_DIR / ".069_reproduction_frozen_snapshot.json"
REPRO_SCRIPT = ROOT / "scripts" / "reproduce_all_main_tables.sh"
CURRENT_MANUSCRIPT = (
    ROOT / "docs/paper_zh_post_k1k4_068/orientation_reliability_paper_zh.md"
)
ORIGINAL_068_MANUSCRIPT_SHA = "8104f4c059428cf7330179cc83939049c0a4ff47e37e84bf3fc107e51b0c35b0"

THRESHOLD_SHA = "b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORMAL_SCOPE_SHA = "33bf3ddab6374fea807018b8e82ccfc1629a34e735cb2f020daf4fe7fa93ffef"
M3_PROTOCOL_SHA = "d88e0d4f3866ced04efc6e06dfb10ea55502bf409d827cb8b2eb7d048492a8e5"
M4_DELTA_JSON_SHA = "80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb"
M4_DELTA_CURVE_SHA = "25ed7c7bb86b23cdefc7a0090ac64c41bf84f1e08476a6bbee96badc83a9ff65"
M4_DELTA_STABILITY_SHA = "b2e2bb7b46671d0496ad059aee8a13d23041075084a3924551bc1ce58d6597f5"
PHASE1_START = "2026-07-12 20:14:39 -0700"
PHASE1_DEADLINE = "2026-08-23 20:14:39 -0700"
PHASE1_PREREG_SHA = "c1f88a6a975d158e42e6c26ddd936a12d269ecbd05ac7999dc11980c45292f7f"
PSC_K_GRID = [0.25, 0.50, 0.75, 0.90, 1.00, 1.10, 1.25, 1.50, 2.00, 4.00]
PSC_EXPECTED = {
    "DIOR-R": {"n_images": 11738, "n_gt": 124445},
    "SODA-A": {"n_images": 22994, "n_gt": 449644},
}

SPLIT_HASHES = {
    "outputs/bench_core/splits/D_audit_dior_trainval.csv": "11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b",
    "outputs/bench_core/splits/D_audit_dota10_train.csv": "d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7",
    "outputs/bench_core/splits/D_audit_dota15_train.csv": "ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856",
    "outputs/bench_core/splits/D_audit_fair1m_train.csv": "140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e",
    "outputs/bench_core/splits/D_audit_hrsc_trainval.csv": "55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679",
    "outputs/bench_core/splits/D_cal_dior_trainval.csv": "f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632",
    "outputs/bench_core/splits/D_cal_dota10_train.csv": "48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4",
    "outputs/bench_core/splits/D_cal_dota15_train.csv": "aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364",
    "outputs/bench_core/splits/D_cal_fair1m_train.csv": "84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0",
    "outputs/bench_core/splits/D_cal_hrsc_trainval.csv": "bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0",
}

HOSTS = {
    "rhino": {
        "lock": "outputs/training/rhino/SNAPSHOT_LOCK.json",
        "lock_sha": "b38f2420e0125d64558e479aa8c414e6f66ba0b9595612b8066756d8413f65c7",
        "checkpoint_sha": "55a90abbace429276e593f8e4418fad002240ff1951912172367d997b474f9d9",
    },
    "a4_host": {
        "lock": "outputs/training/a4_host/SNAPSHOT_LOCK.json",
        "lock_sha": "f6790f8bba0a17d8286ece9324f82b2e0e30b298f660e62ddbbe6740d9725c85",
        "checkpoint_sha": "3e32fa11114ced82c2fb5ecdb25031ff45c1d2815b034a315b1af11ef8487e32",
    },
}

DOTA_DUMPS = {
    "G_dota_orcnn": (
        "top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance/DOTA_orcnn.jsonl",
        "055d415b6e9ec86b4f339c33a17108a02317b4bde7edf3190bbc36178dbbf79d",
    ),
    "H_dota_rtmdet": (
        "top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance/DOTA_rtmdet.jsonl",
        "4c19f140c395757b83ca868aab7763fdd0e01f99de2e345461f330a7a8c73e3e",
    ),
}

FULLVAL_CELLS = {
    "A": ("DIOR-R", "rotated_retinanet_psc"),
    "B": ("DIOR-R", "oriented_rcnn"),
    "C": ("DIOR-R", "rotated_rtmdet_s"),
    "D": ("FAIR1M-v1.0", "rotated_retinanet_psc"),
    "E": ("SODA-A", "rotated_retinanet_psc"),
    "F": ("SODA-A", "oriented_rcnn"),
}
MAIN_CELLS = set(FULLVAL_CELLS) | set(DOTA_DUMPS)

PTH_DATA = Path("/home/rspip/cqc/pro/study/pth_data")
FULLVAL_EXPECTED = {
    "A": {
        "n_images": 11738,
        "n_gt": 124445,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
        "checkpoint": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth",
    },
    "B": {
        "n_images": 11738,
        "n_gt": 124445,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
        "checkpoint": PTH_DATA / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth",
    },
    "C": {
        "n_images": 11738,
        "n_gt": 124445,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
        "checkpoint": PTH_DATA / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth",
    },
    "D": {
        "n_images": 4362,
        "n_gt": 78644,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
        "checkpoint": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_3462_epoch_12.pth",
    },
    "E": {
        "n_images": 22994,
        "n_gt": 449644,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
        "checkpoint": PTH_DATA / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth",
    },
    "F": {
        "n_images": 22994,
        "n_gt": 449644,
        "gt": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl",
        "config": PTH_DATA / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py",
        "checkpoint": PTH_DATA / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth",
    },
}

TASK_REQUIRED_FIELDS = {
    "assignment_version",
    "annotator_slot",
    "task_order",
    "anon_id",
    "dataset",
    "image_id",
    "pred_id",
    "crop_relpath",
    "long_side_angle_deg_le90",
    "cannot_determine",
    "annotator_id",
    "annotation_timestamp_utc",
}
TASK_FORBIDDEN_FIELDS = {
    "angle_error",
    "gt_angle",
    "gt_obb",
    "model_angle",
    "pred_angle",
    "pred_theta",
    "obb_theta",
    "phase_mod",
    "score",
    "matched_gt_class",
    "matched_gt_area_px2",
    "matched_gt_size_bin",
    "matched_gt_aspect_ratio",
    "matched_gt_ar_bin",
    "formal_ar21_eligible",
    "formal_stratum",
    "formal_geometry_source",
    "formal_class_source",
    "locator_geometry_source",
    "locator_cx",
    "locator_cy",
    "locator_box_xmin",
    "locator_box_ymin",
    "locator_box_xmax",
    "locator_box_ymax",
}

ROOT_REPORT_ALIAS_NAMES = (
    "m1_all_main_results_ar21.csv",
    "m1_sensitivity_ar16_ar13.csv",
    "m1_old_vs_ar21_direction_audit.csv",
    "m1_decision.csv",
    "m2_g2doubleprime_ar21.csv",
    "m2_g2doubleprime_cell_bin_intervals.csv",
    "m2_g2doubleprime_decision.csv",
    "m3_image_level_ltt.csv",
    "m3_instance_vs_image_comparison.csv",
    "m3_image_event_secondary_endpoint.csv",
    "m3_instance_weighted_empirical.csv",
    "m3_input_lineage_manifest.json",
    "m3_image_level_protocol_frozen.json",
    "m3_decision.csv",
    "m4_geometry_normalized_risk.csv",
    "m4_fixed_angle_sensitivity.csv",
    "m4_delta_theta_075_frozen.json",
    "m4_delta_theta_tau_curve.csv",
    "m4_delta_theta_direct_solve_stability.csv",
    "m4_observed_ar_numerical_stability.csv",
    "m4_input_lineage_audit.csv",
    "m4_human_annotation_sampling_manifest.csv",
    "m4_human_annotation_disagreement.csv",
    "m4_gt_jitter_proxy_reference.csv",
    "m4_human_annotation_build_audit.json",
    "m4_human_annotation_pairs.csv",
    "m4_human_annotation_merge_audit.json",
    "m4_human_annotation_analysis_audit.json",
    "psc_phase1_radial_scaling.csv",
    "psc_phase1_branch_decision.csv",
    "psc_phase1_dissection.csv",
    "psc_phase1_score_comparison.csv",
    "psc_phase1_nontriviality_audit.csv",
    "psc_phase1_split_gate_decision.csv",
    "psc_phase1_artifact_manifest.csv",
    "k2_go_no_go_decision_067.csv",
    "k2_artifact_manifest_067.csv",
    "k4b_dota_full_val_metrics.csv",
)


@dataclass
class Check:
    phase: str
    scope: str
    check: str
    status: str
    blocking: bool
    evidence: str
    artifact_sha256: str = ""


class Audit:
    def __init__(self, phase: str):
        self.phase = phase
        self.rows: list[Check] = []

    def add(
        self,
        scope: str,
        name: str,
        ok: bool,
        evidence: Any,
        *,
        artifact_sha256: str = "",
        blocking: bool = True,
    ) -> None:
        self.rows.append(
            Check(
                self.phase,
                scope,
                name,
                "PASS" if ok else "FAIL",
                bool(blocking and not ok),
                compact(evidence),
                artifact_sha256,
            )
        )

    def human_blocked(self, name: str, evidence: Any) -> None:
        self.rows.append(Check(self.phase, "human", name, "HUMAN_BLOCKED", True, compact(evidence)))

    @property
    def machine_failures(self) -> list[Check]:
        return [row for row in self.rows if row.status == "FAIL" and row.blocking]


def compact(value: Any, limit: int = 1000) -> str:
    text = str(value).replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_files_parallel(paths: Iterable[Path]) -> dict[Path, str]:
    unique = sorted({Path(path) for path in paths}, key=str)
    if not unique:
        return {}
    workers = min(40, len(unique))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        values = executor.map(sha256_file, unique)
        return dict(zip(unique, values))


def atomic_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def load_csv(path: Path, required: Iterable[str] = (), min_rows: int = 1) -> tuple[list[dict], list[str]]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty: {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    missing = set(required).difference(fields)
    if missing:
        raise ValueError(f"{path.name} missing columns {sorted(missing)}")
    if len(rows) < min_rows:
        raise ValueError(f"{path.name} has {len(rows)} rows, expected >= {min_rows}")
    return rows, fields


def load_json(path: Path) -> Any:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_nonempty_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(bool(line.strip()) for line in handle)


def resolve_recorded_path(value: Any, *, base: Path = ROOT, within_root: bool = True) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        path = base / path
    resolved = path.resolve()
    if within_root:
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"recorded path escapes project root: {value}") from exc
    if "/dev/shm" in str(resolved):
        raise ValueError(f"volatile recorded path: {value}")
    return resolved


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def all_finite(rows: Iterable[dict], fields: Iterable[str]) -> bool:
    return all(finite(row.get(field)) for row in rows for field in fields)


def same_number(value: Any, target: float, tolerance: float = 1e-9) -> bool:
    return finite(value) and abs(float(value) - target) <= tolerance


def audit_hb_pvalue(empirical_mean: float, alpha: float, n: int) -> float:
    """Independent Hoeffding-Bentkus check for a bounded [0,1] mean."""
    from scipy.stats import binom

    if n <= 0 or empirical_mean >= alpha:
        return 1.0
    q = min(max(empirical_mean, 1e-12), 1.0 - 1e-12)
    p = min(max(alpha, 1e-12), 1.0 - 1e-12)
    kl = q * math.log(q / p) + (1.0 - q) * math.log((1.0 - q) / (1.0 - p))
    return float(min(1.0, math.exp(-n * kl), math.e * binom.cdf(math.ceil(n * empirical_mean), n, alpha)))


def audit_hb_ucb(empirical_mean: float, n: int, delta: float) -> float:
    lo, hi = empirical_mean, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if audit_hb_pvalue(empirical_mean, mid, n) <= delta:
            hi = mid
        else:
            lo = mid
    return hi


def decision(path: Path) -> str:
    rows, fields = load_csv(path)
    key = "decision" if "decision" in fields else fields[0]
    return str(rows[0].get(key, "")).strip().upper()


def add_exception(audit: Audit, scope: str, name: str, func) -> Any:
    try:
        value, evidence, artifact_sha = func()
        audit.add(scope, name, bool(value), evidence, artifact_sha256=artifact_sha)
        return value
    except Exception as exc:  # fail closed and retain exact local evidence
        audit.add(scope, name, False, f"{type(exc).__name__}: {exc}")
        return None


def frozen_asset_snapshot(audit: Audit) -> dict[str, str]:
    snapshot: dict[str, str] = {}

    def fixed_file(scope: str, label: str, relpath: str, expected: str) -> None:
        path = ROOT / relpath
        actual = sha256_file(path) if path.is_file() else "MISSING"
        snapshot[relpath] = actual
        audit.add(scope, label, actual == expected, f"expected={expected}; actual={actual}", artifact_sha256=actual)

    fixed_file("frozen", "thresholds.yaml SHA-256", "configs/thresholds.yaml", THRESHOLD_SHA)
    for relpath, expected in SPLIT_HASHES.items():
        fixed_file("frozen", f"frozen split {Path(relpath).name}", relpath, expected)
    fixed_file(
        "frozen",
        "formal/exploratory scope SHA-256",
        "outputs/bench_core/reports/full_matrix_execution_plan.csv",
        FORMAL_SCOPE_SHA,
    )
    fixed_file(
        "frozen",
        "M3 frozen protocol SHA-256",
        "top_journal_v3_reaudit_055/reports/m3_image_level_protocol_frozen.json",
        M3_PROTOCOL_SHA,
    )
    fixed_file(
        "frozen",
        "PSC Phase 1 preregistration SHA-256",
        "docs/psc_phase1_preregistration.md",
        PHASE1_PREREG_SHA,
    )
    fixed_file(
        "frozen",
        "corrected M4 delta-theta JSON SHA-256",
        "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json",
        M4_DELTA_JSON_SHA,
    )
    fixed_file(
        "frozen",
        "corrected M4 delta-theta curve SHA-256",
        "top_journal_v3_reaudit_055/reports/m4_delta_theta_tau_curve.csv",
        M4_DELTA_CURVE_SHA,
    )
    fixed_file(
        "frozen",
        "corrected M4 direct-stability SHA-256",
        "top_journal_v3_reaudit_055/reports/m4_delta_theta_direct_solve_stability.csv",
        M4_DELTA_STABILITY_SHA,
    )

    for host, spec in HOSTS.items():
        lock_path = ROOT / spec["lock"]
        try:
            lock_sha = sha256_file(lock_path)
            lock = load_json(lock_path)
            checkpoint = ROOT / lock["best_checkpoint"]
            checkpoint_sha = sha256_file(checkpoint)
            ok = (
                lock_sha == spec["lock_sha"]
                and lock.get("best_sha256") == spec["checkpoint_sha"]
                and checkpoint_sha == spec["checkpoint_sha"]
            )
            snapshot[spec["lock"]] = lock_sha
            snapshot[str(checkpoint.relative_to(ROOT))] = checkpoint_sha
            audit.add(
                "frozen",
                f"locked host {host}",
                ok,
                f"lock={lock_sha}; checkpoint={checkpoint_sha}; path={checkpoint.relative_to(ROOT)}",
                artifact_sha256=checkpoint_sha,
            )
        except Exception as exc:
            audit.add("frozen", f"locked host {host}", False, f"{type(exc).__name__}: {exc}")

    delta_path = REP / "m4_delta_theta_075_frozen.json"
    try:
        delta_sha = sha256_file(delta_path)
        payload = load_json(delta_path)
        ar = [float(value) for value in payload["ar"]]
        theta_values = payload.get("dtheta_075", payload.get("delta_theta_deg"))
        if theta_values is None:
            raise ValueError("frozen geometry curve lacks dtheta_075 values")
        theta = [None if value is None else float(value) for value in theta_values]
        defined_main = [value for aspect_ratio, value in zip(ar, theta) if aspect_ratio >= 2.1]
        ok = (
            delta_sha == M4_DELTA_JSON_SHA
            and payload.get("schema_version") == "m4_delta_theta_075_v2"
            and payload.get("frozen_at") == PHASE1_START
            and payload.get("definition_changed") is False
            and payload.get("tau_main") == 0.75
            and payload.get("angle_convention") == "le90_pi_periodic_long_axis"
            and payload.get("geometry_model") == "concentric_same_scale_congruent_rectangles"
            and payload.get("solve_method")
            == "first_lobe_minimum_bracket_then_deterministic_bisection_on_polygon_iou"
            and payload.get("threshold_semantics")
            == "smallest_strict_crossing_on_le90_first_lobe"
            and payload.get("high_ar_policy")
            == "conservative_inverse_ar_tail_minus_2solve_tol"
            and payload.get("stability_all_pass") is True
            and 0 < float(payload.get("solve_tolerance_deg", 999)) <= 0.001
            and len(ar) == len(theta) >= 50
            and all(y > x for x, y in zip(ar, ar[1:]))
            and max(ar) == 1024.0
            and float(payload.get("ar_grid_max", 0)) == 1024.0
            and len(defined_main) > 0
            and all(value is not None and 0 < value <= 90 for value in defined_main)
        )
        snapshot[str(delta_path.relative_to(ROOT))] = delta_sha
        audit.add(
            "frozen",
            "geometry risk curve frozen definition",
            ok,
            f"sha={delta_sha}; ar_domain=[{min(ar)},{max(ar)}]; n={len(ar)}; tolerance={payload.get('solve_tolerance_deg')}",
            artifact_sha256=delta_sha,
        )
    except Exception as exc:
        audit.add("frozen", "geometry risk curve frozen definition", False, f"{type(exc).__name__}: {exc}")
    return snapshot


def check_shell_policy(audit: Audit) -> None:
    try:
        text = REPRO_SCRIPT.read_text(encoding="utf-8")
        executable = "\n".join(
            line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
        )
        run_scripts = set(re.findall(r'run_step\s+"[^"]+"\s+"\$PY"\s+([^\s]+)', executable))
        expected = {
            "scripts/m1_ar21_unify.py",
            "scripts/m2_g2doubleprime_ar21.py",
            "scripts/recompute_m3_image_level_risk_control.py",
            "scripts/m4_risk_events.py",
            "scripts/derive_delta_theta_075.py",
            "scripts/psc_phase1.py",
            "scripts/merge_m4_human_annotations.py",
            "scripts/analyze_m4_human_disagreement.py",
            "scripts/m069_lineage_audit.py",
        }
        forbidden = [
            "torchrun",
            "dist_train",
            "inference.py",
            "eval_driver",
            "--fast",
        ]
        hits = [token for token in forbidden if token in executable]
        reuse_markers = {
            "k2_angle_coder_matrix",
            "psc_phase1_forward",
            "psc_actual_head_supplement",
            "dcl_csl_native_endpoints",
            "dota_clean_fullval",
            "dior_fullval_lineage",
        }
        observed_reuse = set(re.findall(r'reuse_verified\s+"([^"]+)"', executable))
        ok = (
            "set -Eeuo pipefail" in text
            and 'logs/reproduce_all_main_tables_069.log' in text
            and "export OMP_NUM_THREADS=40" in executable
            and "export M069_BOOTSTRAP_WORKERS=40" in executable
            and '"$PY" "$AUDITOR" --preflight' in executable
            and '"$PY" "$AUDITOR" --final' in executable
            and 'run_step "m4_delta_frozen_verify" "$PY" scripts/derive_delta_theta_075.py --verify-frozen' in executable
            and executable.count("scripts/derive_delta_theta_075.py") == 1
            and run_scripts == expected
            and observed_reuse == reuse_markers
            and not hits
        )
        audit.add(
            "reproduction",
            "one-click command whitelist/no K2-training-inference rerun",
            ok,
            f"run_scripts={sorted(run_scripts)}; reused={sorted(observed_reuse)}; forbidden_hits={hits}",
            artifact_sha256=sha256_file(REPRO_SCRIPT),
        )
    except Exception as exc:
        audit.add("reproduction", "one-click command whitelist/no K2-training-inference rerun", False, exc)


def fullval_source_paths(cell: str) -> tuple[Path, Path, Path]:
    base = ROOT / "outputs" / "persistent_artifacts" / "m069_fullval_reliability" / cell
    return base / "matched_fullval.jsonl", base / "image_universe.csv", base / "manifest.json"


def check_fullval_inputs(audit: Audit) -> None:
    failures = []
    summaries = []
    for cell, (dataset, detector) in FULLVAL_CELLS.items():
        matched, universe, manifest_path = fullval_source_paths(cell)
        try:
            manifest = load_json(manifest_path)
            expected = FULLVAL_EXPECTED[cell]
            matched_sha = sha256_file(matched)
            universe_sha = sha256_file(universe)
            status = str(manifest.get("status", "")).lower()
            n_images = int(manifest.get("n_images", 0))
            n_gt = int(manifest.get("n_gt", 0))
            n_matched = int(manifest.get("n_matched", -1))
            recorded_matched = resolve_recorded_path(manifest.get("matched_path"))
            recorded_universe = resolve_recorded_path(manifest.get("universe_path"))
            recorded_gt = resolve_recorded_path(manifest.get("gt_path"))
            recorded_config = resolve_recorded_path(
                manifest.get("config_path"), within_root=False
            )
            recorded_checkpoint = resolve_recorded_path(
                manifest.get("checkpoint_path"), within_root=False
            )
            with universe.open(newline="", encoding="utf-8") as handle:
                universe_reader = csv.DictReader(handle)
                universe_fields = set(universe_reader.fieldnames or [])
                universe_rows = list(universe_reader)
            required_universe = {
                "cell", "dataset", "image_id", "image_path",
                "d_cal_daudit_split_flag", "n_gt", "n_predictions",
            }
            universe_ids = [row.get("image_id", "") for row in universe_rows]
            with matched.open(encoding="utf-8") as handle:
                first_line = next((line for line in handle if line.strip()), "")
            first = json.loads(first_line) if first_line else {}
            required_matched = {
                "cell", "dataset", "detector", "image_id", "pred_id", "gt_id",
                "score", "pred_obb", "gt_obb", "match_iou", "angle_error", "size",
                "aspect_ratio", "d_cal_daudit_split_flag", "tta_circular_variance",
                "n_tta_angles", "checkpoint_sha256", "is_real_detector_output",
                "is_synthetic_or_proxy", "lineage",
            }
            residue = sorted(
                str(path.relative_to(manifest_path.parent))
                for pattern in ("*.partial", "*.tmp")
                for path in manifest_path.parent.glob(pattern)
            )
            log_path = ROOT / "top_journal_v3_reaudit_055/logs/m069/fullval_reliability" / f"{cell}.log"
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            ok = (
                status == "complete"
                and manifest.get("split") == "full-validation"
                and truth(manifest.get("can_recompute"))
                and manifest.get("dataset") == dataset
                and manifest.get("detector") == detector
                and matched.stat().st_size > 0
                and universe.stat().st_size > 0
                and manifest.get("matched_bytes") == matched.stat().st_size
                and manifest.get("universe_bytes") == universe.stat().st_size
                and matched_sha == manifest.get("matched_sha256")
                and universe_sha == manifest.get("universe_sha256")
                and recorded_matched == matched.resolve()
                and recorded_universe == universe.resolve()
                and recorded_gt == expected["gt"].resolve()
                and recorded_config == expected["config"].resolve()
                and recorded_checkpoint == expected["checkpoint"].resolve()
                and sha256_file(recorded_gt) == manifest.get("gt_sha256")
                and sha256_file(recorded_config) == manifest.get("config_sha256")
                and sha256_file(recorded_checkpoint) == manifest.get("checkpoint_sha256")
                and "orientbench_real_052" not in str(matched)
                and n_images == expected["n_images"]
                and n_gt == expected["n_gt"]
                and len(universe_rows) == n_images
                and len(universe_ids) == len(set(universe_ids))
                and all(universe_ids)
                and required_universe.issubset(universe_fields)
                and count_nonempty_lines(matched) == n_matched
                and n_matched > 0
                and required_matched.issubset(first)
                and first.get("cell") == cell
                and first.get("dataset") == dataset
                and first.get("detector") == detector
                and first.get("lineage") == "m069_fullval_reliability"
                and first.get("is_real_detector_output") is True
                and first.get("is_synthetic_or_proxy") is False
                and manifest.get("tta_enabled") is True
                and int(manifest.get("n_with_at_least_2_tta", 0)) > 0
                and not residue
                and f"DONE images={n_images} gt={n_gt}" in log_text
            )
            if not ok:
                failures.append(cell)
            summaries.append(
                f"{cell}:{status}:images={n_images}:gt={n_gt}:matched={n_matched}:"
                f"tta={manifest.get('tta_enabled')}:residue={residue}:{matched_sha[:12]}"
            )
        except Exception as exc:
            failures.append(cell)
            summaries.append(f"{cell}:{type(exc).__name__}:{exc}")
    audit.add(
        "dior_lineage",
        "A-F persisted full-val matched inputs and manifests",
        not failures,
        f"failures={failures}; " + "; ".join(summaries),
    )


def check_dota_inputs(audit: Audit) -> None:
    failures = []
    evidence = []
    for cell, (relpath, expected) in DOTA_DUMPS.items():
        path = ROOT / relpath
        try:
            actual = sha256_file(path)
            ok = path.stat().st_size > 0 and actual == expected and "/dev/shm" not in str(path)
            if not ok:
                failures.append(cell)
            evidence.append(f"{cell}:{actual}:{path.stat().st_size}")
        except Exception as exc:
            failures.append(cell)
            evidence.append(f"{cell}:{type(exc).__name__}:{exc}")
    audit.add("dota", "two clean DOTA full-val persisted dumps", not failures, f"failures={failures}; {evidence}")


def check_k2_persisted(audit: Audit) -> None:
    """Verify the 18 completed K2 eval artifacts without rerunning K2."""
    try:
        manifest_path = REP / "k2_artifact_manifest_067.csv"
        rows, _ = load_csv(
            manifest_path,
            {"run_id", "eval_json", "eval_sha", "evaluator", "can_recompute"},
            min_rows=18,
        )
        final_rows = [
            row
            for row in rows
            if row["run_id"].startswith("K2_final__")
            and row["run_id"].split("__")[1] in {"PSC", "CSL", "DCL"}
        ]
        failures = []
        identities = set()
        for row in final_rows:
            path = Path(row["eval_json"])
            if not path.is_absolute():
                path = ROOT / path
            if not path.is_file() or path.stat().st_size == 0:
                failures.append(f"missing:{row['run_id']}")
                continue
            actual = sha256_file(path)
            if not actual.startswith(row["eval_sha"]):
                failures.append(f"sha:{row['run_id']}")
                continue
            payload = load_json(path)
            identity = (payload.get("head"), payload.get("dataset"), str(payload.get("run_id", "")).rsplit("seed", 1)[-1])
            identities.add(identity)
            if not isinstance(payload.get("main_ar2.1"), dict) or "native_signal" not in payload:
                failures.append(f"schema:{row['run_id']}")
            if not truth(row["can_recompute"]):
                failures.append(f"can_recompute:{row['run_id']}")
        expected = {(head, dataset, str(seed)) for head in ("PSC", "CSL", "DCL") for dataset in ("DIOR-R", "SODA-A") for seed in range(3)}
        ok = len(final_rows) == 18 and identities == expected and not failures
        audit.add(
            "k2",
            "K2 18 full-converged eval artifacts reused with SHA verification",
            ok,
            f"rows={len(final_rows)}; identities={len(identities)}/18; failures={failures}",
            artifact_sha256=sha256_file(manifest_path),
        )
    except Exception as exc:
        audit.add("k2", "K2 18 full-converged eval artifacts reused with SHA verification", False, exc)

    try:
        rows, _ = load_csv(
            REP / "k2_go_no_go_decision_067.csv",
            {"decision", "outcome", "reversing_heads", "n_complete_blocks"},
        )
        row = rows[0]
        ok = row["decision"] == "PASS" and row["outcome"] == "A" and row["reversing_heads"] == "PSC" and int(row["n_complete_blocks"]) == 6
        audit.add("k2", "K2 PASS/outcome A frozen decision", ok, f"row={row}")
    except Exception as exc:
        audit.add("k2", "K2 PASS/outcome A frozen decision", False, exc)


def check_psc_forward_inputs(audit: Audit) -> None:
    """Fail closed unless all six frozen-checkpoint Phase-1 forward cells are complete."""
    artifact_index = REP / "k2_artifact_manifest_067.csv"
    try:
        index_rows, _ = load_csv(
            artifact_index,
            {"run_id", "checkpoint", "ckpt_sha", "eval_json", "eval_sha", "can_recompute"},
            min_rows=18,
        )
        by_run = {row["run_id"]: row for row in index_rows}
        artifact_index_sha = sha256_file(artifact_index)
    except Exception as exc:
        audit.add("psc", "PSC raw forward six-cell artifact chain", False, exc)
        return

    failures: list[str] = []
    summaries: list[str] = []
    for dataset in PSC_EXPECTED:
        for seed in range(3):
            run_id = f"K2_final__PSC__{dataset}__seed{seed}"
            out_dir = ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}"
            manifest_path = out_dir / "manifest.json"
            try:
                manifest = load_json(manifest_path)
                expected = PSC_EXPECTED[dataset]
                row = by_run[run_id]
                cfg_name = "psc_dior_seed0.py" if dataset == "DIOR-R" else "psc_soda_seed0.py"
                expected_cfg = REP.parent / "work_dirs/k2" / run_id / cfg_name
                expected_checkpoint = REP.parent / "work_dirs/k2" / run_id / "epoch_12.pth"
                expected_summary = out_dir / "radial_full_evaluator.csv"
                expected_matched = out_dir / "matched_phase.jsonl"
                expected_gt = ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt" / (
                    "DIOR-R_test_fullval_gt.jsonl"
                    if dataset == "DIOR-R"
                    else "SODA-A_val_tiled_fullval_gt.jsonl"
                )

                config = resolve_recorded_path(manifest.get("config_path"))
                checkpoint = resolve_recorded_path(manifest.get("checkpoint_path"))
                k2_index = resolve_recorded_path(manifest.get("k2_artifact_manifest_path"))
                k2_eval = resolve_recorded_path(manifest.get("k2_eval_path"))
                gt = resolve_recorded_path(manifest.get("gt_path"))
                summary = resolve_recorded_path(manifest.get("summary_path"))
                matched = resolve_recorded_path(manifest.get("matched_path"))

                with expected_summary.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    radial_fields = set(reader.fieldnames or [])
                    radial_rows = list(reader)
                required_radial = {
                    "dataset", "seed", "k", "n_images", "n_predictions", "n_matched",
                    "AP50", "AP75", "mean_angle_error_deg", "mean_phase_mod_primary",
                    "decoded_angle_median_diff_deg", "decoded_angle_p95_diff_deg",
                    "post_nms_exact_image_proportion",
                    "post_nms_score_label_count_equal_proportion",
                }
                observed_k = [float(item["k"]) for item in radial_rows]
                radial_ok = (
                    len(radial_rows) == len(PSC_K_GRID)
                    and required_radial.issubset(radial_fields)
                    and all(abs(left - right) <= 1e-12 for left, right in zip(observed_k, PSC_K_GRID))
                    and all(item["dataset"] == dataset and int(item["seed"]) == seed for item in radial_rows)
                    and all(int(item["n_images"]) == expected["n_images"] for item in radial_rows)
                    and all(int(item["n_predictions"]) > 0 and int(item["n_matched"]) > 0 for item in radial_rows)
                    and all_finite(
                        radial_rows,
                        required_radial.difference({"dataset", "seed"}),
                    )
                )

                with matched.open(encoding="utf-8") as handle:
                    first_line = next((line for line in handle if line.strip()), "")
                first = json.loads(first_line) if first_line else {}
                matched_required = {
                    "dataset", "seed", "image_id", "pred_id", "class", "score",
                    "angle_error", "aspect_ratio", "size", "decoded_angle", "objectness",
                    "boundary_distance_deg", "wrapping_condition", "phase_mod_primary",
                    "phase_mod_secondary", "phase_angle_primary", "phase_angle_secondary",
                    "multi_frequency_disagreement_deg", "unwrap_candidate_energy_gap",
                    "phase_direction_margin", "angle_vector_norm",
                    "tta_phase_direction_circular_variance", "n_tta_phase_angles",
                }
                matched_rows = int(manifest.get("matched_rows", -1))

                post_items = manifest.get("postnms_artifacts", [])
                post_by_k = {float(item.get("k")): item for item in post_items}
                post_ok = len(post_items) == len(PSC_K_GRID) and set(post_by_k) == set(PSC_K_GRID)
                for k in PSC_K_GRID:
                    item = post_by_k.get(k, {})
                    expected_post = out_dir / f"postnms_k{k:.2f}.pklstream"
                    post_path = resolve_recorded_path(item.get("path"))
                    if (
                        post_path != expected_post.resolve()
                        or not post_path.is_file()
                        or post_path.stat().st_size <= 0
                        or post_path.stat().st_size != int(item.get("bytes", -1))
                        or sha256_file(post_path) != item.get("sha256")
                        or "pickle stream" not in str(item.get("schema", "")).lower()
                    ):
                        post_ok = False
                        continue
                    with post_path.open("rb") as handle:
                        sample = pickle.load(handle)
                    if not isinstance(sample, tuple) or len(sample) != 4:
                        post_ok = False
                        continue
                    _, boxes, scores, labels = sample
                    if (
                        getattr(boxes, "ndim", -1) != 2
                        or getattr(boxes, "shape", (0, 0))[1:] != (5,)
                        or getattr(scores, "ndim", -1) != 1
                        or getattr(labels, "ndim", -1) != 1
                        or len(boxes) != len(scores)
                        or len(boxes) != len(labels)
                    ):
                        post_ok = False

                residue = sorted(
                    str(path.relative_to(out_dir))
                    for pattern in ("*.partial", "*.tmp")
                    for path in out_dir.glob(pattern)
                )
                forward_log = REP.parent / "logs/m069/psc_phase1_forward" / f"{dataset}_seed{seed}.log"
                log_text = forward_log.read_text(encoding="utf-8", errors="replace")
                coder = manifest.get("coder", {})
                ok = (
                    manifest.get("status") == "complete"
                    and manifest.get("schema_version") == "psc_phase1_radial_scaling_v2"
                    and manifest.get("run_id") == run_id
                    and manifest.get("dataset") == dataset
                    and int(manifest.get("seed", -1)) == seed
                    and int(manifest.get("n_images", -1)) == expected["n_images"]
                    and int(manifest.get("n_gt", -1)) == expected["n_gt"]
                    and len(manifest.get("k_grid", [])) == len(PSC_K_GRID)
                    and all(
                        abs(float(left) - right) <= 1e-12
                        for left, right in zip(manifest.get("k_grid", []), PSC_K_GRID)
                    )
                    and manifest.get("no_training") is True
                    and manifest.get("objectness_available") is False
                    and manifest.get("tta_phase_direction") is (seed == 0)
                    and coder.get("dual_freq") is True
                    and int(coder.get("num_step", 0)) > 0
                    and "configured anchor-assigned" in str(manifest.get("loss_intervention", ""))
                    and config == expected_cfg.resolve()
                    and checkpoint == expected_checkpoint.resolve()
                    and k2_index == artifact_index.resolve()
                    and k2_eval == resolve_recorded_path(row["eval_json"])
                    and gt == expected_gt.resolve()
                    and summary == expected_summary.resolve()
                    and matched == expected_matched.resolve()
                    and sha256_file(config) == manifest.get("config_sha256")
                    and sha256_file(checkpoint) == manifest.get("checkpoint_sha256")
                    and manifest["checkpoint_sha256"].startswith(row["ckpt_sha"])
                    and sha256_file(k2_eval) == manifest.get("k2_eval_sha256")
                    and manifest["k2_eval_sha256"].startswith(row["eval_sha"])
                    and sha256_file(gt) == manifest.get("gt_sha256")
                    and manifest.get("k2_artifact_manifest_sha256") == artifact_index_sha
                    and truth(row.get("can_recompute"))
                    and summary.stat().st_size == int(manifest.get("summary_bytes", -1))
                    and matched.stat().st_size == int(manifest.get("matched_bytes", -1))
                    and sha256_file(summary) == manifest.get("summary_sha256")
                    and sha256_file(matched) == manifest.get("matched_sha256")
                    and count_nonempty_lines(matched) == matched_rows
                    and matched_rows > 0
                    and matched_required.issubset(first)
                    and first.get("dataset") == dataset
                    and int(first.get("seed", -1)) == seed
                    and radial_ok
                    and post_ok
                    and not residue
                    and f"{dataset} seed={seed} DONE images={expected['n_images']}" in log_text
                    and "/dev/shm" not in json.dumps(manifest)
                )
                if not ok:
                    failures.append(run_id)
                summaries.append(
                    f"{run_id}:status={manifest.get('status')}:images={manifest.get('n_images')}:"
                    f"gt={manifest.get('n_gt')}:matched={matched_rows}:postnms={len(post_items)}:"
                    f"residue={residue}:ok={ok}"
                )
            except Exception as exc:
                failures.append(run_id)
                summaries.append(f"{run_id}:{type(exc).__name__}:{exc}")
    audit.add(
        "psc",
        "PSC raw forward six-cell v2 manifests/post-NMS/K2 lineage",
        not failures,
        f"failures={failures}; " + "; ".join(summaries),
        artifact_sha256=artifact_index_sha,
    )


def check_psc_actual_loss_supplements(audit: Audit) -> None:
    """Require the corrected network-coordinate actual-head statistics for all six runs."""
    artifact_index = REP / "k2_artifact_manifest_067.csv"
    try:
        index_rows, _ = load_csv(
            artifact_index,
            {"run_id", "checkpoint", "ckpt_sha", "eval_json", "eval_sha", "can_recompute"},
            min_rows=18,
        )
        by_run = {row["run_id"]: row for row in index_rows}
        artifact_index_sha = sha256_file(artifact_index)
    except Exception as exc:
        audit.add("psc", "PSC corrected actual-head six-cell supplements", False, exc)
        return

    actual_fields = {
        "actual_head_mean_angle_loss",
        "actual_head_mean_abs_radial_gradient",
        "actual_head_mean_tangential_gradient_norm",
        "actual_head_mean_abs_radial_gradient_wrt_base_z",
        "actual_head_mean_tangential_gradient_norm_wrt_base_z",
        "actual_head_mean_abs_dloss_dk",
        "actual_head_mean_positive_anchors",
    }
    failures: list[str] = []
    summaries: list[str] = []
    for dataset in PSC_EXPECTED:
        for seed in range(3):
            run_id = f"K2_final__PSC__{dataset}__seed{seed}"
            out_dir = ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}"
            summary_path = out_dir / "actual_head_loss_network_space.csv"
            manifest_path = out_dir / "actual_head_loss_network_space_manifest.json"
            try:
                manifest = load_json(manifest_path)
                expected = PSC_EXPECTED[dataset]
                row = by_run[run_id]
                cfg_name = "psc_dior_seed0.py" if dataset == "DIOR-R" else "psc_soda_seed0.py"
                expected_config = REP.parent / "work_dirs/k2" / run_id / cfg_name
                expected_checkpoint = REP.parent / "work_dirs/k2" / run_id / "epoch_12.pth"
                expected_eval = resolve_recorded_path(row["eval_json"])
                expected_gt = ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt" / (
                    "DIOR-R_test_fullval_gt.jsonl"
                    if dataset == "DIOR-R"
                    else "SODA-A_val_tiled_fullval_gt.jsonl"
                )
                recorded_paths = {
                    "summary": resolve_recorded_path(manifest.get("summary_path")),
                    "config": resolve_recorded_path(manifest.get("config_path")),
                    "checkpoint": resolve_recorded_path(manifest.get("checkpoint_path")),
                    "k2_index": resolve_recorded_path(manifest.get("k2_artifact_manifest_path")),
                    "k2_eval": resolve_recorded_path(manifest.get("k2_eval_path")),
                    "gt": resolve_recorded_path(manifest.get("gt_path")),
                }
                expected_paths = {
                    "summary": summary_path.resolve(),
                    "config": expected_config.resolve(),
                    "checkpoint": expected_checkpoint.resolve(),
                    "k2_index": artifact_index.resolve(),
                    "k2_eval": expected_eval,
                    "gt": expected_gt.resolve(),
                }
                with summary_path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    fields = set(reader.fieldnames or [])
                    rows = list(reader)
                required_fields = {"dataset", "seed", "k", "n_images", "n_gt"} | actual_fields
                grid_ok = (
                    len(rows) == len(PSC_K_GRID)
                    and [float(item["k"]) for item in rows] == PSC_K_GRID
                )
                numeric_ok = (
                    required_fields.issubset(fields)
                    and all_finite(rows, {"seed", "k", "n_images", "n_gt"} | actual_fields)
                    and all(float(item[field]) >= 0 for item in rows for field in actual_fields)
                    and all(float(item["actual_head_mean_positive_anchors"]) > 0 for item in rows)
                )
                flags = (
                    "only_actual_head_loss_statistics", "no_decode", "no_matching",
                    "no_nms", "no_ap_evaluation", "no_training",
                )
                residue = sorted(
                    str(path.relative_to(out_dir))
                    for pattern in (
                        "actual_head_loss_network_space.csv.tmp",
                        "actual_head_loss_network_space_manifest.json.tmp",
                    )
                    for path in out_dir.glob(pattern)
                )
                log_path = REP.parent / "logs/m069/psc_phase1_actual_loss" / f"{dataset}_seed{seed}.log"
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
                ok = (
                    manifest.get("status") == "complete"
                    and manifest.get("schema_version") == "psc_phase1_actual_head_loss_network_space_v1"
                    and manifest.get("run_id") == run_id
                    and manifest.get("dataset") == dataset
                    and int(manifest.get("seed", -1)) == seed
                    and int(manifest.get("n_images", -1)) == expected["n_images"]
                    and int(manifest.get("n_gt", -1)) == expected["n_gt"]
                    and manifest.get("gt_coordinate_space") == "network_input_after_validation_scale_factor"
                    and all(manifest.get(field) is True for field in flags)
                    and len(manifest.get("k_grid", [])) == len(PSC_K_GRID)
                    and all(
                        abs(float(left) - right) <= 1e-12
                        for left, right in zip(manifest.get("k_grid", []), PSC_K_GRID)
                    )
                    and recorded_paths == expected_paths
                    and sha256_file(summary_path) == manifest.get("summary_sha256")
                    and summary_path.stat().st_size == int(manifest.get("summary_bytes", -1))
                    and sha256_file(expected_config) == manifest.get("config_sha256")
                    and sha256_file(expected_checkpoint) == manifest.get("checkpoint_sha256")
                    and manifest["checkpoint_sha256"].startswith(row["ckpt_sha"])
                    and manifest.get("k2_artifact_manifest_sha256") == artifact_index_sha
                    and sha256_file(expected_eval) == manifest.get("k2_eval_sha256")
                    and manifest["k2_eval_sha256"].startswith(row["eval_sha"])
                    and sha256_file(expected_gt) == manifest.get("gt_sha256")
                    and truth(row["can_recompute"])
                    and grid_ok
                    and numeric_ok
                    and all(
                        item["dataset"] == dataset
                        and int(item["seed"]) == seed
                        and int(item["n_images"]) == expected["n_images"]
                        and int(item["n_gt"]) == expected["n_gt"]
                        for item in rows
                    )
                    and f"{dataset} seed={seed} DONE images={expected['n_images']} gt={expected['n_gt']}" in log_text
                    and "scripts/m069_psc_actual_loss_supplement.py" in str(manifest.get("generation_command", ""))
                    and not residue
                    and "/dev/shm" not in json.dumps(manifest)
                )
                if not ok:
                    failures.append(run_id)
                summaries.append(
                    f"{run_id}:status={manifest.get('status')}:images={manifest.get('n_images')}:"
                    f"gt={manifest.get('n_gt')}:rows={len(rows)}:residue={residue}:"
                    f"sha={sha256_file(manifest_path)[:12]}:ok={ok}"
                )
            except Exception as exc:
                failures.append(run_id)
                summaries.append(f"{run_id}:{type(exc).__name__}:{exc}")
    audit.add(
        "psc",
        "PSC corrected actual-head six-cell network-coordinate supplements",
        not failures,
        f"failures={failures}; " + "; ".join(summaries),
        artifact_sha256=artifact_index_sha,
    )


def check_psc_native_endpoint_inputs(audit: Audit) -> None:
    """Validate the twelve targeted DCL/CSL geometry-endpoint native dumps."""
    artifact_index = REP / "k2_artifact_manifest_067.csv"
    try:
        index_rows, _ = load_csv(
            artifact_index,
            {
                "run_id", "checkpoint", "ckpt_sha", "log", "log_sha",
                "eval_json", "eval_sha", "can_recompute",
            },
            min_rows=18,
        )
        by_run = {row["run_id"]: row for row in index_rows}
        artifact_index_sha = sha256_file(artifact_index)
    except Exception as exc:
        audit.add("psc", "DCL/CSL twelve-cell geometry-endpoint native dumps", False, exc)
        return

    failures: list[str] = []
    summaries: list[str] = []
    for head in ("DCL", "CSL"):
        for dataset in PSC_EXPECTED:
            for seed in range(3):
                run_id = f"K2_final__{head}__{dataset}__seed{seed}"
                slug = "dior" if dataset == "DIOR-R" else "soda"
                out_dir = (
                    ROOT / "outputs/persistent_artifacts/m069_psc_phase1/native_signals"
                    / head / dataset / f"seed{seed}"
                )
                manifest_path = out_dir / "manifest.json"
                matched_path = out_dir / "matched_native.jsonl"
                try:
                    manifest = load_json(manifest_path)
                    expected = PSC_EXPECTED[dataset]
                    row = by_run[run_id]
                    expected_config = REP.parent / "work_dirs/k2" / run_id / f"{head.lower()}_{slug}_seed0.py"
                    expected_checkpoint = REP.parent / "work_dirs/k2" / run_id / "epoch_12.pth"
                    expected_eval = resolve_recorded_path(row["eval_json"])
                    expected_train_log = resolve_recorded_path(row["log"])
                    expected_gt = ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt" / (
                        "DIOR-R_test_fullval_gt.jsonl"
                        if dataset == "DIOR-R"
                        else "SODA-A_val_tiled_fullval_gt.jsonl"
                    )
                    eval_payload = load_json(expected_eval)
                    expected_matched = int(eval_payload.get("n_matched", -1))
                    expected_signal = (
                        "csl_softmax_top1_top2_margin"
                        if head == "CSL"
                        else "dcl_mean_sigmoid_bit_margin"
                    )
                    recorded = {
                        "matched": resolve_recorded_path(manifest.get("matched_path")),
                        "config": resolve_recorded_path(manifest.get("config_path")),
                        "checkpoint": resolve_recorded_path(manifest.get("checkpoint_path")),
                        "k2_index": resolve_recorded_path(manifest.get("k2_artifact_manifest_path")),
                        "k2_eval": resolve_recorded_path(manifest.get("k2_eval_path")),
                        "gt": resolve_recorded_path(manifest.get("gt_path")),
                    }
                    expected_paths = {
                        "matched": matched_path.resolve(),
                        "config": expected_config.resolve(),
                        "checkpoint": expected_checkpoint.resolve(),
                        "k2_index": artifact_index.resolve(),
                        "k2_eval": expected_eval,
                        "gt": expected_gt.resolve(),
                    }
                    required_row = {
                        "head", "dataset", "seed", "image_id", "pred_id", "gt_id", "class",
                        "detection_score", "native_score", "native_signal", "angle_error",
                        "aspect_ratio", "size", "pred_box", "gt_box", "match_iou", "post_nms",
                    }
                    n_rows = 0
                    row_schema_ok = True
                    unique_keys: set[tuple[str, int]] = set()
                    with matched_path.open(encoding="utf-8") as handle:
                        for line in handle:
                            if not line.strip():
                                continue
                            item = json.loads(line)
                            if not required_row.issubset(item):
                                row_schema_ok = False
                                break
                            numeric = (
                                "detection_score", "native_score", "angle_error",
                                "aspect_ratio", "size", "match_iou",
                            )
                            if not all(finite(item[field]) for field in numeric):
                                row_schema_ok = False
                                break
                            boxes_ok = all(
                                isinstance(item[field], list)
                                and len(item[field]) == 5
                                and all(finite(value) for value in item[field])
                                for field in ("pred_box", "gt_box")
                            )
                            identity_ok = (
                                item["head"] == head
                                and item["dataset"] == dataset
                                and int(item["seed"]) == seed
                                and item["native_signal"] == expected_signal
                                and item["post_nms"] is True
                            )
                            range_ok = (
                                0 <= float(item["detection_score"]) <= 1
                                and 0 <= float(item["native_score"]) <= 1
                                and 0 <= float(item["angle_error"]) <= 90
                                and float(item["aspect_ratio"]) >= 1
                                and float(item["size"]) > 0
                                and 0.5 <= float(item["match_iou"]) <= 1
                            )
                            key = (str(item["image_id"]), int(item["pred_id"]))
                            if not boxes_ok or not identity_ok or not range_ok or key in unique_keys:
                                row_schema_ok = False
                                break
                            unique_keys.add(key)
                            n_rows += 1
                    residue = sorted(
                        str(path.relative_to(out_dir))
                        for pattern in ("*.tmp", "*.partial")
                        for path in out_dir.glob(pattern)
                    )
                    log_path = (
                        REP.parent / "logs/m069/psc_phase1_native_signals"
                        / f"{head}_{dataset}_seed{seed}.log"
                    )
                    log_text = log_path.read_text(encoding="utf-8", errors="replace")
                    ok = (
                        manifest.get("status") == "complete"
                        and manifest.get("schema_version") == "psc_phase1_frozen_k2_native_endpoint_v1"
                        and manifest.get("run_id") == run_id
                        and manifest.get("head") == head
                        and manifest.get("dataset") == dataset
                        and int(manifest.get("seed", -1)) == seed
                        and int(manifest.get("n_images", -1)) == expected["n_images"]
                        and int(manifest.get("n_gt", -1)) == expected["n_gt"]
                        and int(manifest.get("n_predictions", -1)) > 0
                        and int(manifest.get("n_matched", -1)) == expected_matched
                        and n_rows == expected_matched > 0
                        and manifest.get("native_signal") == expected_signal
                        and manifest.get("identity_only") is True
                        and manifest.get("post_nms_own_detector_matching") is True
                        and manifest.get("no_tta") is True
                        and manifest.get("no_ap_evaluation") is True
                        and manifest.get("no_training") is True
                        and "post-NMS" in str(manifest.get("matching", ""))
                        and recorded == expected_paths
                        and sha256_file(matched_path) == manifest.get("matched_sha256")
                        and matched_path.stat().st_size == int(manifest.get("matched_bytes", -1))
                        and sha256_file(expected_config) == manifest.get("config_sha256")
                        and sha256_file(expected_checkpoint) == manifest.get("checkpoint_sha256")
                        and manifest["checkpoint_sha256"].startswith(row["ckpt_sha"])
                        and manifest.get("k2_artifact_manifest_sha256") == artifact_index_sha
                        and sha256_file(expected_eval) == manifest.get("k2_eval_sha256")
                        and manifest["k2_eval_sha256"].startswith(row["eval_sha"])
                        and sha256_file(expected_train_log).startswith(row["log_sha"])
                        and sha256_file(expected_gt) == manifest.get("gt_sha256")
                        and truth(row["can_recompute"])
                        and row_schema_ok
                        and not residue
                        and f"{head} {dataset} seed={seed} DONE images={expected['n_images']} gt={expected['n_gt']} matched={expected_matched}" in log_text
                        and "scripts/m069_psc_native_signal_dump.py" in str(manifest.get("generation_command", ""))
                        and "/dev/shm" not in json.dumps(manifest)
                    )
                    if not ok:
                        failures.append(run_id)
                    summaries.append(
                        f"{run_id}:images={manifest.get('n_images')}:gt={manifest.get('n_gt')}:"
                        f"matched={n_rows}/{expected_matched}:residue={residue}:"
                        f"sha={sha256_file(manifest_path)[:12]}:ok={ok}"
                    )
                except Exception as exc:
                    failures.append(run_id)
                    summaries.append(f"{run_id}:{type(exc).__name__}:{exc}")
    audit.add(
        "psc",
        "DCL/CSL twelve-cell geometry-endpoint native dumps",
        not failures,
        f"failures={failures}; " + "; ".join(summaries),
        artifact_sha256=artifact_index_sha,
    )


def parse_phase_timeline(row: dict) -> tuple[datetime, datetime]:
    start_text = str(row.get("start", ""))
    deadline_text = str(row.get("deadline", ""))
    start = datetime.strptime(start_text, "%Y-%m-%d %H:%M:%S %z")
    deadline = datetime.strptime(deadline_text, "%Y-%m-%d %H:%M:%S %z")
    if start_text != PHASE1_START or deadline_text != PHASE1_DEADLINE:
        raise ValueError(f"timeline changed: start={start_text}; deadline={deadline_text}")
    if deadline - start != timedelta(days=42):
        raise ValueError(f"deadline is not start+42 days: {deadline-start}")
    return start, deadline


def check_psc_persisted(audit: Audit, *, detailed: bool) -> str:
    decision_value = ""
    gate: dict = {}
    branch_rows: list[dict] = []
    radial: list[dict] = []
    scores: list[dict] = []
    nontriviality: list[dict] = []
    try:
        gate_rows, _ = load_csv(
            REP / "psc_phase1_split_gate_decision.csv",
            {
                "decision", "start", "deadline", "branch",
                "cond1_intervenable_structural_cause",
                "cond2_nontrivial_registered_score",
                "cond3_beats_negative_phase_mod_two_datasets_frozen_cells",
                "cond4_no_retrain_box_class_ap_unchanged",
                "cond4_evidence", "cond4_failures",
                "winning_candidate", "candidate_evidence_json",
            },
        )
        if len(gate_rows) != 1:
            raise ValueError(f"split gate must have exactly one row, got {len(gate_rows)}")
        gate = gate_rows[0]
        parse_phase_timeline(gate)
        decision_value = str(gate["decision"]).upper()
        ok = decision_value in {"PASS", "FAIL", "DEADLINE"} and gate.get("branch") in {"A", "B"}
        evidence = json.loads(gate["candidate_evidence_json"])
        condition_fields = (
            "cond1_intervenable_structural_cause",
            "cond2_nontrivial_registered_score",
            "cond3_beats_negative_phase_mod_two_datasets_frozen_cells",
            "cond4_no_retrain_box_class_ap_unchanged",
        )
        if decision_value == "PASS":
            ok = ok and all(truth(gate.get(field)) for field in condition_fields)
            ok = ok and bool(gate.get("winning_candidate"))
        if decision_value == "FAIL":
            ok = ok and not all(truth(gate.get(field)) for field in condition_fields)
        ok = ok and isinstance(evidence, dict) and bool(evidence)
        audit.add(
            "psc",
            "PSC Phase 1 original timeline and terminal decision",
            ok,
            f"decision={decision_value}; branch={gate.get('branch')}; start={gate.get('start')}; deadline={gate.get('deadline')}",
            artifact_sha256=sha256_file(REP / "psc_phase1_split_gate_decision.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC Phase 1 original timeline and terminal decision", False, exc)

    if not detailed:
        return decision_value

    try:
        branch_rows, _ = load_csv(
            REP / "psc_phase1_branch_decision.csv",
            {
                "scope", "dataset", "seed", "branch", "decoded_median_max_deg",
                "decoded_p95_max_deg", "loss_relative_change_max",
                "post_nms_score_label_count_equal_min",
                "decoded_gate_lt_0.5median_lt_1p95", "loss_gate_rel_lt_1e-3",
                "structural_cause_intervention_verified", "branch_consistent_all_six",
                "start", "deadline",
            },
            min_rows=7,
        )
        cell_rows = [row for row in branch_rows if row["scope"] == "dataset_seed"]
        overall = [row for row in branch_rows if row["scope"] == "overall"]
        identities = {(row["dataset"], int(row["seed"])) for row in cell_rows}
        expected_identities = {(dataset, seed) for dataset in PSC_EXPECTED for seed in range(3)}
        timeline_ok = all(not parse_phase_timeline(row) is None for row in branch_rows)
        ok = (
            len(branch_rows) == 7
            and identities == expected_identities
            and len(overall) == 1
            and overall[0]["branch"] == ("A" if all(row["branch"] == "A" for row in cell_rows) else "B")
            and all(row["branch"] in {"A", "B"} for row in branch_rows)
            and all_finite(
                branch_rows,
                (
                    "decoded_median_max_deg", "decoded_p95_max_deg",
                    "loss_relative_change_max", "post_nms_score_label_count_equal_min",
                ),
            )
            and timeline_ok
        )
        audit.add(
            "psc",
            "PSC six-cell radial branch decision and frozen timeline",
            ok,
            f"rows={len(branch_rows)}; identities={sorted(identities)}; overall={overall[0].get('branch') if overall else ''}",
            artifact_sha256=sha256_file(REP / "psc_phase1_branch_decision.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC six-cell radial branch decision and frozen timeline", False, exc)

    try:
        radial, radial_fields = load_csv(
            REP / "psc_phase1_radial_scaling.csv",
            {
                "dataset", "seed", "k", "n_images", "n_predictions", "n_matched",
                "AP50", "AP75", "mean_angle_error_deg", "mean_phase_mod_primary",
                "actual_head_mean_angle_loss", "actual_head_mean_abs_radial_gradient",
                "actual_head_mean_tangential_gradient_norm",
                "actual_head_mean_abs_radial_gradient_wrt_base_z",
                "actual_head_mean_tangential_gradient_norm_wrt_base_z",
                "actual_head_mean_abs_dloss_dk", "actual_head_mean_positive_anchors",
                "decoded_angle_median_diff_deg", "decoded_angle_p95_diff_deg",
                "post_nms_exact_image_proportion", "post_nms_score_label_count_equal_proportion",
                "actual_head_loss_relative_change_vs_k1", "controlled_phase_mod_ratio_vs_k1",
                "manifest_sha256", "actual_head_supplement_manifest_sha256",
                "actual_head_statistics_source", "legacy_actual_head_fields_superseded",
                "checkpoint_sha256", "mask_definition",
            },
            min_rows=60,
        )
        identities = {(row["dataset"], int(row["seed"])) for row in radial}
        expected_identities = {(dataset, seed) for dataset in PSC_EXPECTED for seed in range(3)}
        grid_ok = all(
            [float(row["k"]) for row in radial if row["dataset"] == dataset and int(row["seed"]) == seed]
            == PSC_K_GRID
            for dataset, seed in expected_identities
        )
        numeric = {
            "k", "n_images", "n_predictions", "n_matched", "AP50", "AP75",
            "mean_angle_error_deg", "mean_phase_mod_primary", "actual_head_mean_angle_loss",
            "actual_head_mean_abs_radial_gradient", "actual_head_mean_tangential_gradient_norm",
            "actual_head_mean_abs_radial_gradient_wrt_base_z",
            "actual_head_mean_tangential_gradient_norm_wrt_base_z",
            "actual_head_mean_abs_dloss_dk", "actual_head_mean_positive_anchors",
            "decoded_angle_median_diff_deg",
            "decoded_angle_p95_diff_deg", "post_nms_exact_image_proportion",
            "post_nms_score_label_count_equal_proportion", "actual_head_loss_relative_change_vs_k1",
            "controlled_phase_mod_ratio_vs_k1",
        }
        ok = (
            len(radial) == 60
            and identities == expected_identities
            and grid_ok
            and all_finite(radial, numeric)
            and all(int(row["n_images"]) == PSC_EXPECTED[row["dataset"]]["n_images"] for row in radial)
            and all(int(row["n_predictions"]) > 0 and int(row["n_matched"]) > 0 for row in radial)
            and all(0 <= float(row["AP50"]) <= 1 and 0 <= float(row["AP75"]) <= 1 for row in radial)
            and all(
                row["actual_head_statistics_source"] == "targeted_network_coordinate_supplement"
                and truth(row["legacy_actual_head_fields_superseded"])
                and row["actual_head_supplement_manifest_sha256"]
                == sha256_file(
                    ROOT / "outputs/persistent_artifacts/m069_psc_phase1"
                    / row["dataset"] / f"seed{int(row['seed'])}"
                    / "actual_head_loss_network_space_manifest.json"
                )
                for row in radial
            )
            and all(float(row["actual_head_mean_positive_anchors"]) > 0 for row in radial)
            and all("radial intervention" in row["mask_definition"] for row in radial)
            and all("network-coordinate targeted supplement" in row["mask_definition"] for row in radial)
        )
        audit.add(
            "psc",
            "PSC radial-scaling preregistered measurements",
            ok,
            f"rows={len(radial)}; identities={sorted(identities)}; grid_ok={grid_ok}; fields={radial_fields}",
            artifact_sha256=sha256_file(REP / "psc_phase1_radial_scaling.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC radial-scaling preregistered measurements", False, exc)

    try:
        scores, fields = load_csv(
            REP / "psc_phase1_score_comparison.csv",
            {
                "dataset", "seed", "score", "score_family", "formula", "endpoint",
                "mask_definition", "n", "n_images", "nrc", "nrc_ci_lo", "nrc_ci_hi",
                "aurc", "risk70", "risk90", "reference_score", "bootstrap_unit",
                "bootstrap_replicates", "comparison_status", "source_file", "source_sha256",
            },
        )
        registered = [row for row in scores if row["score_family"] == "registered_psc_phase1"]
        native = [row for row in scores if row["score_family"] == "frozen_k2_native_phase1_endpoint"]
        names = {row["score"] for row in registered}
        required_names = {
            "phase_mod",
            "negative_phase_mod",
            "detection_score",
            "tta_phase_direction_consistency",
            "multi_frequency_consistency",
            "unwrap_candidate_energy_gap",
            "phase_direction_margin",
        }
        expected_registered = {
            (dataset, seed, score)
            for dataset in PSC_EXPECTED
            for seed in range(3)
            for score in required_names
        }
        observed_registered = {(row["dataset"], int(row["seed"]), row["score"]) for row in registered}
        comparable = [row for row in registered if row["comparison_status"] == "PAIRED_COMPARABLE"]
        unavailable = [row for row in registered if row["comparison_status"] == "UNAVAILABLE"]
        required_metrics = (
            "nrc", "nrc_ci_lo", "nrc_ci_hi", "aurc", "aurc_ci_lo", "aurc_ci_hi",
            "risk70", "risk70_ci_lo", "risk70_ci_hi", "risk90", "risk90_ci_lo", "risk90_ci_hi",
            "delta_nrc", "delta_nrc_ci_lo", "delta_nrc_ci_hi",
            "delta_aurc", "delta_aurc_ci_lo", "delta_aurc_ci_hi",
            "delta_risk70", "delta_risk70_ci_lo", "delta_risk70_ci_hi",
            "delta_risk90", "delta_risk90_ci_lo", "delta_risk90_ci_hi",
        )
        expected_native = {
            (dataset, seed, score)
            for dataset in PSC_EXPECTED
            for seed in range(3)
            for score in (
                "dcl_native", "dcl_detection_score",
                "csl_native", "csl_detection_score",
            )
        }
        observed_native = {(row["dataset"], int(row["seed"]), row["score"]) for row in native}
        ok = (
            names == required_names
            and observed_registered == expected_registered
            and observed_native == expected_native
            and len(scores) == len(registered) + len(native)
            and not any(row["comparison_status"] == "REFERENCE_ONLY_ENDPOINT_MISMATCH" for row in scores)
            and all(row["endpoint"] == "geometry_normalized_severe_event" for row in registered)
            and all(row["mask_definition"] == "aspect_ratio>=2.1" for row in registered)
            and all(row["reference_score"] == "negative_phase_mod" for row in registered)
            and all(row["bootstrap_unit"] == "image" for row in registered)
            and all(int(row["bootstrap_replicates"]) >= 800 for row in registered)
            and all_finite(comparable, ("n", "n_images", *required_metrics))
            and all(int(row["n"]) >= 50 and int(row["n_images"]) > 1 for row in comparable)
            and all(
                row["score"] == "tta_phase_direction_consistency" and int(row["seed"]) in {1, 2}
                for row in unavailable
            )
            and all(
                row["endpoint"] == "geometry_normalized_severe_event"
                and row["mask_definition"] == "aspect_ratio>=2.1"
                and row["comparison_status"] == "PAIRED_SAME_HEAD_DETECTION_BASELINE"
                and row["bootstrap_unit"] == "image"
                and int(row["bootstrap_replicates"]) >= 800
                and row["reference_score"]
                == ("dcl_detection_score" if row["score"].startswith("dcl_") else "csl_detection_score")
                for row in native
            )
            and all_finite(native, ("n", "n_images", *required_metrics))
            and all(int(row["n"]) >= 50 and int(row["n_images"]) > 1 for row in native)
        )
        audit.add(
            "psc",
            "PSC preregistered score comparison completeness",
            ok,
            f"registered={len(registered)}; comparable={len(comparable)}; unavailable={len(unavailable)}; native_geometry_endpoint={len(native)}; scores={sorted(names)}; fields={fields}",
            artifact_sha256=sha256_file(REP / "psc_phase1_score_comparison.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC preregistered score comparison completeness", False, exc)

    try:
        dissection, _ = load_csv(
            REP / "psc_phase1_dissection.csv",
            {
                "analysis_id", "analysis_name", "dataset", "seed", "mask_definition",
                "risk_event", "group_type", "group_value", "statistic", "estimate",
                "n", "status", "note", "evidence_json",
            },
            min_rows=72,
        )
        identities = {(row["dataset"], int(row["seed"])) for row in dissection}
        analyses_by_identity = {
            identity: {int(row["analysis_id"]) for row in dissection if (row["dataset"], int(row["seed"])) == identity}
            for identity in identities
        }
        expected_identities = {(dataset, seed) for dataset in PSC_EXPECTED for seed in range(3)}
        ok = (
            identities == expected_identities
            and all(analyses_by_identity[identity] == set(range(1, 13)) for identity in expected_identities)
            and all(row["mask_definition"] == "aspect_ratio>=2.1" for row in dissection)
            and all(row["risk_event"] == "angle_error>delta_theta_0.75(aspect_ratio)" for row in dissection)
            and all(row["status"] in {"COMPLETE", "UNAVAILABLE"} for row in dissection)
        )
        audit.add(
            "psc",
            "PSC twelve preregistered mechanism analyses",
            ok,
            f"rows={len(dissection)}; identities={sorted(identities)}; analysis_ids={sorted(set(int(row['analysis_id']) for row in dissection))}",
            artifact_sha256=sha256_file(REP / "psc_phase1_dissection.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC twelve preregistered mechanism analyses", False, exc)

    try:
        nontriviality, _ = load_csv(
            REP / "psc_phase1_nontriviality_audit.csv",
            {
                "dataset", "seed", "candidate", "n", "formula",
                "spearman_vs_negative_phase_mod", "kendall_vs_negative_phase_mod",
                "rank_disagreement", "top10_overlap", "isotonic_r2_best_direction",
                "depends_on_gt", "inference_side", "target_domain_fit",
                "simple_monotone_transform", "nontrivial",
                "beats_negative_phase_mod_all_metrics", "status",
            },
            min_rows=24,
        )
        candidates = {
            "tta_phase_direction_consistency", "multi_frequency_consistency",
            "unwrap_candidate_energy_gap", "phase_direction_margin",
        }
        expected = {
            (dataset, seed, candidate)
            for dataset in PSC_EXPECTED
            for seed in range(3)
            for candidate in candidates
        }
        observed = {(row["dataset"], int(row["seed"]), row["candidate"]) for row in nontriviality}
        complete = [row for row in nontriviality if row["status"] == "COMPLETE"]
        unavailable = [row for row in nontriviality if row["status"] == "UNAVAILABLE"]
        ok = (
            len(nontriviality) == 24
            and observed == expected
            and all(not truth(row["depends_on_gt"]) and truth(row["inference_side"]) and not truth(row["target_domain_fit"]) for row in nontriviality)
            and all_finite(
                complete,
                (
                    "n", "spearman_vs_negative_phase_mod", "kendall_vs_negative_phase_mod",
                    "rank_disagreement", "top10_overlap", "isotonic_r2_best_direction",
                ),
            )
            and all(
                row["candidate"] == "tta_phase_direction_consistency" and int(row["seed"]) in {1, 2}
                for row in unavailable
            )
        )
        audit.add(
            "psc",
            "PSC registered-score nontriviality audit",
            ok,
            f"rows={len(nontriviality)}; complete={len(complete)}; unavailable={len(unavailable)}; candidates={sorted(candidates)}",
            artifact_sha256=sha256_file(REP / "psc_phase1_nontriviality_audit.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC registered-score nontriviality audit", False, exc)

    try:
        if not gate or not branch_rows or not radial or not scores or not nontriviality:
            raise ValueError("one or more PSC gate evidence tables unavailable")
        cell_rows = [row for row in branch_rows if row["scope"] == "dataset_seed"]
        overall = next(row for row in branch_rows if row["scope"] == "overall")
        derived_cell_branches = []
        for row in cell_rows:
            decoded = (
                float(row["decoded_median_max_deg"]) < 0.5
                and float(row["decoded_p95_max_deg"]) < 1.0
            )
            weak_loss = float(row["loss_relative_change_max"]) < 1e-3
            derived = "A" if decoded and weak_loss else "B"
            derived_cell_branches.append((row, derived, decoded, weak_loss))
        all_a = all(derived == "A" for _, derived, _, _ in derived_cell_branches)
        all_b = all(derived == "B" for _, derived, _, _ in derived_cell_branches)
        decoded_sensitive_all = all(not decoded for _, _, decoded, _ in derived_cell_branches)
        magnitude_semantics_all = all(not weak_loss for _, _, _, weak_loss in derived_cell_branches)
        cond1 = all_a or (all_b and (decoded_sensitive_all or magnitude_semantics_all))
        branch_ok = (
            all(row["branch"] == derived for row, derived, _, _ in derived_cell_branches)
            and overall["branch"] == ("A" if all_a else "B")
            and truth(overall["structural_cause_intervention_verified"]) == cond1
            and truth(overall["branch_consistent_all_six"]) == (all_a or all_b)
        )

        mechanism_candidates = {
            "tta_phase_direction_consistency", "multi_frequency_consistency",
            "unwrap_candidate_energy_gap", "phase_direction_margin",
        }
        winners = []
        any_nontrivial = False
        for candidate in mechanism_candidates:
            expected = (
                {(dataset, 0) for dataset in PSC_EXPECTED}
                if candidate == "tta_phase_direction_consistency"
                else {(dataset, seed) for dataset in PSC_EXPECTED for seed in range(3)}
            )
            nt = [row for row in nontriviality if row["candidate"] == candidate
                  and (row["dataset"], int(row["seed"])) in expected]
            metric = [row for row in scores
                      if row["score_family"] == "registered_psc_phase1"
                      and row["score"] == candidate
                      and (row["dataset"], int(row["seed"])) in expected]
            complete = (
                {(row["dataset"], int(row["seed"])) for row in nt} == expected
                and {(row["dataset"], int(row["seed"])) for row in metric} == expected
                and all(row["status"] == "COMPLETE" for row in nt)
            )
            nontrivial_all = complete and all(truth(row["nontrivial"]) for row in nt)
            beats_all = complete and all(
                row["comparison_status"] == "PAIRED_COMPARABLE"
                and all(float(row[f"delta_{name}_ci_hi"]) < 0
                        for name in ("nrc", "aurc", "risk70", "risk90"))
                for row in metric
            )
            any_nontrivial = any_nontrivial or nontrivial_all
            if nontrivial_all and beats_all:
                winners.append(candidate)
        cond2 = any_nontrivial
        cond3 = bool(winners)

        cond4_failures = []
        source_by_key = {}
        for dataset in PSC_EXPECTED:
            for seed in range(3):
                manifest_path = ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}" / "manifest.json"
                manifest = load_json(manifest_path)
                if manifest.get("no_training") is not True:
                    cond4_failures.append(f"{dataset}/seed{seed}:no_training_false")
                matched_path = ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}" / "matched_phase.jsonl"
                source_by_key[(dataset, seed)] = (str(matched_path.relative_to(ROOT)), sha256_file(matched_path))
        for row in nontriviality:
            if row["candidate"] not in winners:
                continue
            if not (
                not truth(row["depends_on_gt"])
                and truth(row["inference_side"])
                and not truth(row["target_domain_fit"])
            ):
                cond4_failures.append(
                    f"{row['dataset']}/seed{row['seed']}:{row['candidate']}:not_ranking_only"
                )
        for row in scores:
            if row["score"] not in winners:
                continue
            identity = (row["dataset"], int(row["seed"]))
            if (row["source_file"], row["source_sha256"]) != source_by_key[identity]:
                cond4_failures.append(
                    f"{row['dataset']}/seed{row['seed']}:{row['score']}:source_identity_changed"
                )
        cond4 = not cond4_failures
        expected_decision = "PASS" if cond1 and cond2 and cond3 and cond4 else "FAIL"
        reported = [
            truth(gate["cond1_intervenable_structural_cause"]),
            truth(gate["cond2_nontrivial_registered_score"]),
            truth(gate["cond3_beats_negative_phase_mod_two_datasets_frozen_cells"]),
            truth(gate["cond4_no_retrain_box_class_ap_unchanged"]),
        ]
        reconstructed = [cond1, cond2, cond3, cond4]
        ok = (
            branch_ok
            and reported == reconstructed
            and decision_value == expected_decision
            and set(filter(None, gate.get("winning_candidate", "").split(";"))) == set(winners)
            and set(filter(None, gate.get("cond4_failures", "").split(";"))) == set(cond4_failures)
        )
        audit.add(
            "psc",
            "PSC four-condition split gate independently reconstructed",
            ok,
            f"reported={reported}; reconstructed={reconstructed}; expected_decision={expected_decision}; winners={sorted(winners)}; cond4_failures={cond4_failures}; branch_ok={branch_ok}",
        )
    except Exception as exc:
        audit.add("psc", "PSC four-condition split gate independently reconstructed", False, exc)

    try:
        manifest, fields = load_csv(
            REP / "psc_phase1_artifact_manifest.csv",
            {"artifact", "role", "status", "sha256", "bytes", "source", "can_recompute"},
        )
        failures = []
        for row in manifest:
            path = resolve_recorded_path(row["artifact"])
            if not path.is_file() or path.stat().st_size <= 0:
                failures.append(f"missing:{row['artifact']}")
                continue
            actual = sha256_file(path)
            if row.get("sha256") != actual or int(row.get("bytes", -1)) != path.stat().st_size:
                failures.append(f"sha:{row['artifact']}")
            if not row.get("can_recompute") or row.get("status") not in {"complete", "frozen", "validated_input"}:
                failures.append(f"schema:{row['artifact']}")
        represented = {resolve_recorded_path(row["artifact"]) for row in manifest}
        required_outputs = {
            REP / "psc_phase1_radial_scaling.csv",
            REP / "psc_phase1_branch_decision.csv",
            REP / "psc_phase1_dissection.csv",
            REP / "psc_phase1_score_comparison.csv",
            REP / "psc_phase1_nontriviality_audit.csv",
            REP / "psc_phase1_split_gate_decision.csv",
            ROOT / "docs/psc_phase1_radial_scaling_intervention.md",
            ROOT / "docs/psc_phase1_split_gate_report.md",
            ROOT / "docs/psc_phase1_preregistration.md",
        }
        for dataset in PSC_EXPECTED:
            for seed in range(3):
                supplement_dir = (
                    ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}"
                )
                required_outputs.update(
                    {
                        supplement_dir / "actual_head_loss_network_space_manifest.json",
                        supplement_dir / "actual_head_loss_network_space.csv",
                        REP.parent / "logs/m069/psc_phase1_actual_loss" / f"{dataset}_seed{seed}.log",
                    }
                )
                for head in ("DCL", "CSL"):
                    native_dir = (
                        ROOT / "outputs/persistent_artifacts/m069_psc_phase1/native_signals"
                        / head / dataset / f"seed{seed}"
                    )
                    required_outputs.update(
                        {
                            native_dir / "manifest.json",
                            native_dir / "matched_native.jsonl",
                            REP.parent / "logs/m069/psc_phase1_native_signals"
                            / f"{head}_{dataset}_seed{seed}.log",
                        }
                    )
        missing_roles = sorted(str(path.relative_to(ROOT)) for path in required_outputs - represented)
        audit.add(
            "psc",
            "PSC artifact manifest SHA alignment",
            not failures and not missing_roles,
            f"rows={len(manifest)}; failures={failures}; missing_required={missing_roles}; fields={fields}",
            artifact_sha256=sha256_file(REP / "psc_phase1_artifact_manifest.csv"),
        )
    except Exception as exc:
        audit.add("psc", "PSC artifact manifest SHA alignment", False, exc)
    return decision_value


def check_human_machine_package(audit: Audit, *, final: bool) -> str:
    manifest_path = REP / "m4_human_annotation_sampling_manifest.csv"
    build_audit_path = REP / "m4_human_annotation_build_audit.json"
    tool = ROOT / "annotation_tools" / "m4_angle_annotation"
    task_a_path = tool / "annotatorA_tasks.csv"
    task_b_path = tool / "annotatorB_tasks.csv"
    try:
        required_manifest = {
            "anon_id", "dataset", "image_id", "pred_id", "matched_gt_class",
            "matched_gt_area_px2", "matched_gt_size_bin", "matched_gt_aspect_ratio",
            "matched_gt_ar_bin", "formal_ar21_eligible", "formal_stratum",
            "formal_geometry_source", "formal_class_source", "locator_geometry_source",
            "source_image_path",
            "source_image_sha256", "image_width", "image_height", "locator_cx",
            "locator_cy", "locator_box_xmin", "locator_box_ymin", "locator_box_xmax",
            "locator_box_ymax", "crop_xmin", "crop_ymin", "crop_xmax", "crop_ymax",
            "crop_relpath", "crop_sha256", "source_record_path", "source_record_sha256",
            "source_record_line", "sampling_seed", "sampling_rank",
        }
        manifest, manifest_fields = load_csv(
            manifest_path, required_manifest, min_rows=600
        )
        tasks_a, fields_a = load_csv(task_a_path, TASK_REQUIRED_FIELDS, min_rows=len(manifest))
        tasks_b, fields_b = load_csv(task_b_path, TASK_REQUIRED_FIELDS, min_rows=len(manifest))
        build = load_json(build_audit_path)
        ids_manifest = [row["anon_id"] for row in manifest]
        ids_a = [row["anon_id"] for row in tasks_a]
        ids_b = [row["anon_id"] for row in tasks_b]
        counts = {dataset: sum(row["dataset"] == dataset for row in manifest) for dataset in ("DIOR-R", "FAIR1M-v1.0", "SODA-A")}
        expected_counts = {
            dataset: min(500, int(build.get("per_dataset", {}).get(dataset, {}).get("candidate_count", 0)))
            for dataset in counts
        }
        target_counts_ok = all(
            counts[dataset] >= 200
            and counts[dataset] == expected_counts[dataset]
            and (counts[dataset] == 500 or expected_counts[dataset] < 500)
            for dataset in counts
        )
        no_prefill = all(
            not str(row.get(field, "")).strip()
            for row in tasks_a + tasks_b
            for field in (
                "long_side_angle_deg_le90", "cannot_determine", "annotator_id",
                "annotation_timestamp_utc",
            )
        )
        slots_ok = all(row.get("annotator_slot") == "A" for row in tasks_a) and all(
            row.get("annotator_slot") == "B" for row in tasks_b
        )
        forbidden = (TASK_FORBIDDEN_FIELDS & set(fields_a)) | (TASK_FORBIDDEN_FIELDS & set(fields_b))

        manifest_by_id = {row["anon_id"]: row for row in manifest}
        assignment_versions = {
            row.get("assignment_version", "") for row in tasks_a + tasks_b
        }
        task_rows_bound = all(
            row.get("anon_id") in manifest_by_id
            and row.get("dataset") == manifest_by_id[row["anon_id"]]["dataset"]
            and row.get("image_id") == manifest_by_id[row["anon_id"]]["image_id"]
            and row.get("pred_id") == manifest_by_id[row["anon_id"]]["pred_id"]
            and row.get("crop_relpath") == manifest_by_id[row["anon_id"]]["crop_relpath"]
            for row in tasks_a + tasks_b
        )
        orders_ok = all(
            sorted(int(row["task_order"]) for row in rows) == list(range(1, len(rows) + 1))
            for rows in (tasks_a, tasks_b)
        )

        resolved_assets: dict[str, tuple[Path, Path, Path]] = {}
        for row in manifest:
            crop = resolve_recorded_path(row["crop_relpath"], base=tool)
            crop.relative_to((tool / "crops").resolve())
            source_image = resolve_recorded_path(
                row["source_image_path"], within_root=False
            )
            source_record = resolve_recorded_path(row["source_record_path"])
            for asset in (crop, source_image, source_record):
                if not asset.is_file() or asset.stat().st_size <= 0:
                    raise ValueError(f"human package asset missing/empty: {asset}")
            resolved_assets[row["anon_id"]] = (crop, source_image, source_record)
        asset_sha = sha256_files_parallel(
            asset
            for assets in resolved_assets.values()
            for asset in assets
        )

        crop_failures = []
        source_record_failures = []
        requested_lines: dict[Path, dict[int, dict[str, str]]] = {}
        strata: dict[str, dict[str, set[str]]] = {
            dataset: {"size": set(), "ar": set(), "class": set()} for dataset in counts
        }
        for row in manifest:
            try:
                dataset = row["dataset"]
                if dataset not in counts:
                    raise ValueError(f"unexpected dataset {dataset}")
                if row["formal_stratum"] != (
                    f"{row['matched_gt_class']}|{row['matched_gt_size_bin']}|"
                    f"{row['matched_gt_ar_bin']}"
                ):
                    raise ValueError("stratum components drifted")
                strata[dataset]["size"].add(row["matched_gt_size_bin"])
                strata[dataset]["ar"].add(row["matched_gt_ar_bin"])
                strata[dataset]["class"].add(row["matched_gt_class"])
                aspect_ratio = float(row["matched_gt_aspect_ratio"])
                gt_area = float(row["matched_gt_area_px2"])
                if not math.isfinite(aspect_ratio) or aspect_ratio < 1:
                    raise ValueError("invalid matched-GT aspect ratio")
                if not math.isfinite(gt_area) or gt_area <= 0:
                    raise ValueError("invalid matched-GT area")
                expected_ar_bin = (
                    "ar<1.6" if aspect_ratio < 1.6
                    else ("1.6<=ar<2.1" if aspect_ratio < 2.1 else "ar>=2.1")
                )
                expected_size_bin = (
                    "small" if gt_area < 32.0**2
                    else ("medium" if gt_area < 96.0**2 else "large")
                )
                if row["matched_gt_ar_bin"] != expected_ar_bin:
                    raise ValueError("invalid ar stratum")
                if row["matched_gt_size_bin"] != expected_size_bin:
                    raise ValueError("invalid size stratum")
                if truth(row["formal_ar21_eligible"]) != (aspect_ratio >= 2.1):
                    raise ValueError("formal ar>=2.1 flag drifted")
                if row["formal_geometry_source"] != "matched_GT_box_nonangular":
                    raise ValueError("formal strata are not bound to matched GT")
                if row["formal_class_source"] != "matched_GT_class_via_class_constrained_match":
                    raise ValueError("formal class is not bound to the class-constrained GT match")
                if row["locator_geometry_source"] != "matched_prediction_box_nonangular":
                    raise ValueError("locator is not bound to matched prediction")

                crop, source_image, source_record = resolved_assets[row["anon_id"]]
                if asset_sha[crop] != row["crop_sha256"]:
                    raise ValueError("crop missing/empty/SHA mismatch")
                if asset_sha[source_image] != row["source_image_sha256"]:
                    raise ValueError("source image SHA mismatch")

                width, height = int(row["image_width"]), int(row["image_height"])
                crop_box = [int(row[key]) for key in ("crop_xmin", "crop_ymin", "crop_xmax", "crop_ymax")]
                locator = [float(row[key]) for key in (
                    "locator_cx", "locator_cy", "locator_box_xmin", "locator_box_ymin",
                    "locator_box_xmax", "locator_box_ymax",
                )]
                if (
                    width <= 0 or height <= 0 or not all(math.isfinite(value) for value in locator)
                    or not (0 <= crop_box[0] < crop_box[2] <= width)
                    or not (0 <= crop_box[1] < crop_box[3] <= height)
                    or not (0 <= locator[0] <= width and 0 <= locator[1] <= height)
                ):
                    raise ValueError("invalid image/crop/locator geometry")

                if asset_sha[source_record] != row["source_record_sha256"]:
                    raise ValueError("source record missing/SHA mismatch")
                line_number = int(row["source_record_line"])
                if line_number <= 0:
                    raise ValueError("invalid source line")
                requested_lines.setdefault(source_record, {})[line_number] = row
            except Exception as exc:
                crop_failures.append(f"{row.get('anon_id')}:{type(exc).__name__}:{exc}")

        for source_record, wanted in requested_lines.items():
            found: set[int] = set()
            try:
                with source_record.open(encoding="utf-8") as handle:
                    for line_number, line in enumerate(handle, 1):
                        if line_number not in wanted:
                            continue
                        source = json.loads(line)
                        manifest_row = wanted[line_number]
                        if (
                            str(source.get("image_id")) != manifest_row["image_id"]
                            or str(source.get("pred_id")) != manifest_row["pred_id"]
                            or str(source.get("dataset")) != manifest_row["dataset"]
                        ):
                            source_record_failures.append(
                                f"{manifest_row['anon_id']}:source identity mismatch"
                            )
                        try:
                            gt = source["gt_obb"]
                            pred = source["pred_obb"]
                            gt_w, gt_h = abs(float(gt["obb_w"])), abs(float(gt["obb_h"]))
                            gt_area = gt_w * gt_h
                            gt_ar = max(gt_w, gt_h) / min(gt_w, gt_h)
                            gt_size = (
                                "small" if gt_area < 32.0**2
                                else ("medium" if gt_area < 96.0**2 else "large")
                            )
                            gt_ar_bin = (
                                "ar<1.6" if gt_ar < 1.6
                                else ("1.6<=ar<2.1" if gt_ar < 2.1 else "ar>=2.1")
                            )
                            pred_cx, pred_cy = float(pred["obb_cx"]), float(pred["obb_cy"])
                            pred_w, pred_h = abs(float(pred["obb_w"])), abs(float(pred["obb_h"]))
                            image_width, image_height = (
                                int(manifest_row["image_width"]), int(manifest_row["image_height"])
                            )
                            half = max(48.0, 0.90 * max(pred_w, pred_h))
                            expected_crop = (
                                max(0, int(math.floor(pred_cx - half))),
                                max(0, int(math.floor(pred_cy - half))),
                                min(image_width, int(math.ceil(pred_cx + half))),
                                min(image_height, int(math.ceil(pred_cy + half))),
                            )
                            observed_crop = tuple(
                                int(manifest_row[key])
                                for key in ("crop_xmin", "crop_ymin", "crop_xmax", "crop_ymax")
                            )
                            if (
                                str(source.get("class", "unknown")) != manifest_row["matched_gt_class"]
                                or float(source.get("match_iou", 0.0)) < 0.5
                                or not math.isclose(
                                    gt_area, float(manifest_row["matched_gt_area_px2"]),
                                    rel_tol=0.0, abs_tol=5e-4,
                                )
                                or not math.isclose(
                                    gt_ar, float(manifest_row["matched_gt_aspect_ratio"]),
                                    rel_tol=0.0, abs_tol=5e-7,
                                )
                                or gt_size != manifest_row["matched_gt_size_bin"]
                                or gt_ar_bin != manifest_row["matched_gt_ar_bin"]
                                or not math.isclose(
                                    pred_cx, float(manifest_row["locator_cx"]),
                                    rel_tol=0.0, abs_tol=0.005,
                                )
                                or not math.isclose(
                                    pred_cy, float(manifest_row["locator_cy"]),
                                    rel_tol=0.0, abs_tol=0.005,
                                )
                                or expected_crop != observed_crop
                            ):
                                source_record_failures.append(
                                    f"{manifest_row['anon_id']}:formal-GT or prediction-locator binding mismatch"
                                )
                        except Exception as exc:
                            source_record_failures.append(
                                f"{manifest_row['anon_id']}:geometry binding {type(exc).__name__}:{exc}"
                            )
                        found.add(line_number)
                missing_lines = set(wanted).difference(found)
                if missing_lines:
                    source_record_failures.append(
                        f"{source_record.relative_to(ROOT)}:missing lines {sorted(missing_lines)[:10]}"
                    )
            except Exception as exc:
                source_record_failures.append(
                    f"{source_record}:{type(exc).__name__}:{exc}"
                )

        strata_ok = all(
            values["size"]
            == set(build.get("per_dataset", {}).get(dataset, {}).get("available_size_bins", []))
            == set(build.get("per_dataset", {}).get(dataset, {}).get("selected_size_bins", []))
            and values["ar"]
            == set(build.get("per_dataset", {}).get(dataset, {}).get("available_ar_bins", []))
            == set(build.get("per_dataset", {}).get(dataset, {}).get("selected_ar_bins", []))
            and values["class"]
            == set(build.get("per_dataset", {}).get(dataset, {}).get("available_classes", []))
            == set(build.get("per_dataset", {}).get(dataset, {}).get("selected_classes", []))
            and values["ar"] == {"ar<1.6", "1.6<=ar<2.1", "ar>=2.1"}
            and len(values["size"]) >= 2
            and len(values["class"]) >= 2
            for dataset, values in strata.items()
        )
        build_ok = (
            build.get("status") == "READY_FOR_TWO_INDEPENDENT_HUMAN_ANNOTATORS"
            and int(build.get("minimum_per_dataset", 0)) == 200
            and int(build.get("target_per_dataset", 0)) == 500
            and build.get("same_target_set") is True
            and build.get("different_random_order") is True
            and build.get("gt_or_model_angle_exported") is False
            and build.get("gt_or_model_obb_exported_to_tasks") is False
            and build.get("formal_strata_geometry") == "matched_GT_box_nonangular"
            and build.get("formal_class_source") == "matched_GT_class_via_class_constrained_match"
            and build.get("formal_mask_definition") == "matched_GT_aspect_ratio>=2.1"
            and build.get("locator_geometry") == "matched_prediction_box_nonangular"
            and build.get("task_schema_is_exact_allowlist") is True
            and build.get("crops_materialized") is True
            and build.get("crop_sha256_bound_in_manifest") is True
            and build.get("source_record_sha256_bound_in_manifest") is True
            and build.get("manifest", {}).get("sha256") == sha256_file(manifest_path)
            and int(build.get("manifest", {}).get("rows", -1)) == len(manifest)
            and build.get("annotator_a_task", {}).get("sha256") == sha256_file(task_a_path)
            and build.get("annotator_b_task", {}).get("sha256") == sha256_file(task_b_path)
            and int(build.get("annotator_a_task", {}).get("rows", -1)) == len(tasks_a)
            and int(build.get("annotator_b_task", {}).get("rows", -1)) == len(tasks_b)
        )
        tool_text = "\n".join(
            (tool / name).read_text(encoding="utf-8", errors="replace")
            for name in ("index.html", "angle_convention.md", "instructions.md")
        ).lower()
        ok = (
            len(ids_manifest) == len(set(ids_manifest))
            and set(ids_a) == set(ids_b) == set(ids_manifest)
            and ids_a != ids_b
            and len(tasks_a) == len(tasks_b) == len(manifest)
            and target_counts_ok
            and set(manifest_fields) == required_manifest
            and set(fields_a) == set(fields_b) == TASK_REQUIRED_FIELDS
            and not forbidden
            and no_prefill
            and slots_ok
            and task_rows_bound
            and orders_ok
            and assignment_versions == {str(build.get("assignment_version", ""))}
            and bool(next(iter(assignment_versions), ""))
            and strata_ok
            and build_ok
            and not crop_failures
            and not source_record_failures
            and "long" in tool_text and "le90" in tool_text
        )
        audit.add(
            "human",
            "stratified mutually-blind dual-task machine package",
            ok,
            f"crop_failures={crop_failures[:5]}; source_failures={source_record_failures[:5]}; forbidden={sorted(forbidden)}; counts={counts}; expected={expected_counts}; same_targets={set(ids_a)==set(ids_b)==set(ids_manifest)}; different_order={ids_a!=ids_b}; versions={assignment_versions}; strata_ok={strata_ok}; build_ok={build_ok}; build_status={build.get('status')}",
            artifact_sha256=sha256_file(manifest_path),
        )
        if not ok:
            return "INVALID_MACHINE_PACKAGE"
    except Exception as exc:
        audit.add("human", "stratified mutually-blind dual-task machine package", False, exc)
        return "INVALID_MACHINE_PACKAGE"

    if not final:
        raw_a = tool / "annotatorA_raw.csv"
        raw_b = tool / "annotatorB_raw.csv"
        if not raw_a.is_file() or not raw_b.is_file():
            audit.human_blocked("real independent double annotations", "annotatorA_raw.csv and/or annotatorB_raw.csv absent")
            return "HUMAN_BLOCKED"
        return "LABELS_PRESENT_UNVERIFIED"

    try:
        merge = load_json(REP / "m4_human_annotation_merge_audit.json")
        analysis = load_json(REP / "m4_human_annotation_analysis_audit.json")
        status = str(merge.get("status", ""))
        if status == "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION":
            counts = merge.get("usable_pairs_by_dataset", {})
            ok = (
                merge.get("same_target_set") is True
                and merge.get("different_random_order") is True
                and merge.get("independent_annotator_ids_verified") is True
                and all(int(counts.get(dataset, 0)) >= 200 for dataset in ("DIOR-R", "FAIR1M-v1.0", "SODA-A"))
                and analysis.get("status") == status
            )
            audit.add("human", "real independent double-annotation audit", ok, f"status={status}; counts={counts}")
            return "COMPLETE" if ok else "INVALID_LABELS"
        if status in {"HUMAN_BLOCKED", "PENDING_INDEPENDENCE_VERIFICATION", "INSUFFICIENT_USABLE_PAIRS"}:
            audit.human_blocked("real independent double annotations", f"merge_status={status}")
            return "HUMAN_BLOCKED"
        audit.add("human", "real independent double-annotation audit", False, f"merge_status={status}")
        return "INVALID_LABELS"
    except Exception as exc:
        audit.human_blocked("real independent double annotations", f"audit unavailable: {type(exc).__name__}: {exc}")
        return "HUMAN_BLOCKED"


def check_m1(audit: Audit) -> str:
    verdict = ""
    try:
        path = REP / "m1_all_main_results_ar21.csv"
        rows, fields = load_csv(
            path,
            {
                "cell", "dataset", "detector", "score_type", "mask_definition", "ar_threshold",
                "retained_count", "retained_ratio", "nrc", "aurc", "risk70", "risk90",
                "evaluation_scope",
            },
            min_rows=20,
        )
        cells = {row["cell"] for row in rows}
        scores = {row["score_type"] for row in rows}
        required_scores = {
            "detection_score", "geometry_upper_bound", "tta_neg_circular_var", "phase_mod",
            "negative_phase_mod", "native_PSC", "score_PSC", "native_CSL", "score_CSL",
            "native_DCL", "score_DCL",
        }
        numeric = [
            "ar_threshold", "retained_count", "retained_ratio", "nrc", "aurc", "risk70",
            "risk90", "nrc_ci_lo", "nrc_ci_hi",
        ]
        k2_expected_cells = {
            f"K2:K2_final__{head}__{dataset}__seed{seed}"
            for head in ("PSC", "CSL", "DCL")
            for dataset in ("DIOR-R", "SODA-A")
            for seed in range(3)
        }
        k2_rows = [row for row in rows if row["cell"].startswith("K2:")]
        k2_groups = {
            cell: [row for row in k2_rows if row["cell"] == cell]
            for cell in k2_expected_cells
        }
        k2_lineage_ok = True
        k2_lineage_failures = []
        for cell, group in k2_groups.items():
            match = re.fullmatch(
                r"K2:K2_final__(PSC|CSL|DCL)__(DIOR-R|SODA-A)__seed([012])", cell
            )
            if match is None:
                k2_lineage_ok = False
                k2_lineage_failures.append(f"invalid identity {cell}")
                continue
            head, dataset, seed_text = match.groups()
            seed = int(seed_text)
            manifest_path = (
                ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset
                / f"seed{seed}" / "manifest.json"
                if head == "PSC"
                else ROOT / "outputs/persistent_artifacts/m069_psc_phase1/native_signals"
                / head / dataset / f"seed{seed}" / "manifest.json"
            )
            expected_sha = sha256_file(manifest_path) if manifest_path.is_file() else "MISSING"
            expected_lineage = (
                "m069_psc_phase1_frozen_k2_per_instance"
                if head == "PSC"
                else "m069_psc_phase1_targeted_native_frozen_k2"
            )
            expected_scores = {f"native_{head}", f"score_{head}"}
            group_ok = (
                len(group) == 2
                and {row["score_type"] for row in group} == expected_scores
                and all(row.get("source_lineage") == expected_lineage for row in group)
                and all(f"source_manifest_sha256={expected_sha}" in row.get("note", "") for row in group)
                and (
                    head != "PSC"
                    or all(
                        "phase_mod" in row.get("note", "")
                        for row in group if row["score_type"] == "native_PSC"
                    )
                )
            )
            if not group_ok:
                k2_lineage_ok = False
                k2_lineage_failures.append(
                    f"{cell}:rows={len(group)} scores={sorted(row['score_type'] for row in group)} lineage={[row.get('source_lineage') for row in group]}"
                )
        ok = (
            MAIN_CELLS.issubset(cells)
            and required_scores.issubset(scores)
            and {row["cell"] for row in k2_rows} == k2_expected_cells
            and len(k2_rows) == 36
            and k2_lineage_ok
            and all(same_number(row["ar_threshold"], 2.1) for row in rows)
            and all(
                row["mask_definition"]
                == "matched_gt_ar_ge_thr_exclude_pred_or_gt_near_square"
                for row in rows
            )
            and all(row.get("metric_completeness") == "complete" for row in rows)
            and all(
                row["evaluation_scope"]
                == ("frozen_full_validation_endpoint" if row["cell"].startswith("K2:")
                    else "clean_fullval_D_audit" if row["cell"].startswith(("G_", "H_"))
                    else "D_audit")
                for row in rows
            )
            and all_finite(rows, numeric)
            and all(float(row["nrc_ci_lo"]) <= float(row["nrc_ci_hi"]) for row in rows)
            and all(int(float(row["retained_count"])) > 0 for row in rows)
            and all(0 < float(row["retained_ratio"]) <= 1 for row in rows)
        )
        audit.add(
            "m1",
            "M1 ar>=2.1 sole main-table schema and numeric completeness",
            ok,
            f"rows={len(rows)}; k2_rows={len(k2_rows)}; k2_cells={len(k2_groups)}; k2_lineage_failures={k2_lineage_failures}; cells={sorted(cells)}; scores={sorted(scores)}; fields={fields}",
            artifact_sha256=sha256_file(path),
        )
    except Exception as exc:
        audit.add("m1", "M1 ar>=2.1 sole main-table schema and numeric completeness", False, exc)

    try:
        path = REP / "m1_sensitivity_ar16_ar13.csv"
        rows, _ = load_csv(
            path,
            {
                "cell", "score_type", "ar_threshold", "mask_definition", "retained_count",
                "retained_ratio", "nrc", "aurc", "risk70", "risk90", "source_lineage",
                "metric_completeness", "note", "evaluation_scope",
            },
        )
        thresholds = {float(row["ar_threshold"]) for row in rows if finite(row.get("ar_threshold"))}
        detection_pairs = {(row["cell"], float(row["ar_threshold"])) for row in rows if row["score_type"] == "detection_score"}
        expected_pairs = {(cell, threshold) for cell in MAIN_CELLS for threshold in (1.3, 1.6)}
        k2_rows = [row for row in rows if row["cell"].startswith("K2:")]
        k2_cells = {
            f"K2:K2_final__{head}__{dataset}__seed{seed}"
            for head in ("PSC", "CSL", "DCL")
            for dataset in ("DIOR-R", "SODA-A")
            for seed in range(3)
        }
        k2_groups = {
            (cell, threshold): [
                row for row in k2_rows
                if row["cell"] == cell and same_number(row["ar_threshold"], threshold)
            ]
            for cell in k2_cells for threshold in (1.3, 1.6)
        }
        k2_groups_ok = all(
            len(group) == 2
            and {row["score_type"] for row in group}
            == {
                f"native_{cell.split('__')[1]}",
                f"score_{cell.split('__')[1]}",
            }
            for (cell, _), group in k2_groups.items()
        )
        ok = (
            thresholds == {1.3, 1.6}
            and expected_pairs.issubset(detection_pairs)
            and len(k2_rows) == 72
            and {row["cell"] for row in k2_rows} == k2_cells
            and k2_groups_ok
            and all(
                row["mask_definition"]
                == "matched_gt_ar_ge_thr_exclude_pred_or_gt_near_square"
                for row in rows
            )
            and all(row.get("metric_completeness") == "complete" for row in rows)
            and all(
                row["evaluation_scope"]
                == ("frozen_full_validation_endpoint" if row["cell"].startswith("K2:")
                    else "clean_fullval_D_audit" if row["cell"].startswith(("G_", "H_"))
                    else "D_audit")
                for row in rows
            )
            and all_finite(
                rows,
                ["retained_count", "retained_ratio", "nrc", "aurc", "risk70", "risk90"],
            )
            and all(int(float(row["retained_count"])) > 0 for row in rows)
            and all(0 < float(row["retained_ratio"]) <= 1 for row in rows)
        )
        audit.add("m1", "M1 ar1.6/ar1.3 sensitivity isolated from main", ok, f"rows={len(rows)}; k2_rows={len(k2_rows)}; thresholds={thresholds}; missing_pairs={sorted(expected_pairs-detection_pairs)}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("m1", "M1 ar1.6/ar1.3 sensitivity isolated from main", False, exc)

    try:
        direction_rows, _ = load_csv(
            REP / "m1_old_vs_ar21_direction_audit.csv",
            {"metric", "old_ar16_value", "new_ar21_value", "conclusion_changed"},
        )
        verdict = decision(REP / "m1_decision.csv")
        ok = verdict == "PASS" and len(direction_rows) > 0 and all_finite(
            direction_rows, ["old_ar16_value", "new_ar21_value"]
        )
        audit.add("m1", "M1 direction audit and decision", ok, f"decision={verdict}; rows={len(direction_rows)}")
    except Exception as exc:
        audit.add("m1", "M1 direction audit and decision", False, exc)
    return verdict


def check_m2(audit: Audit) -> str:
    verdict = ""
    try:
        path = REP / "m2_g2doubleprime_ar21.csv"
        required = {
            "cell", "size_bin", "ar_threshold", "n_instances", "n_images", "nrc_detection",
            "nrc_linear_score_ar", "nrc_linear_score_ar_size", "nrc_nonlinear_geometry",
            "paired_nrc_diff_lin_minus_nl", "ci_lo", "ci_hi", "fit_target", "source_lineage",
            "selector_fit_split", "conformal_calibration_split", "evaluation_split",
            "mask_definition", "retained_count", "retained_ratio", "nonlinear_better_sig",
            "evaluation_mask_geometry", "selector_geometry", "fixed_size_bin_geometry",
            "bootstrap_unit", "bootstrap_replicates",
        }
        rows, _ = load_csv(path, required, min_rows=1)
        by_cell = {cell: sum(row["cell"] == cell for row in rows) for cell in FULLVAL_CELLS}
        ok = (
            len({(row["cell"], row["size_bin"]) for row in rows}) == len(rows)
            and all(row["cell"] in FULLVAL_CELLS for row in rows)
            and all(row["size_bin"] in {"small", "medium", "large"} for row in rows)
            and all(same_number(row["ar_threshold"], 2.1) for row in rows)
            and all_finite(
                rows,
                [
                    "n_instances", "n_images", "nrc_detection", "nrc_linear_score_ar",
                    "nrc_linear_score_ar_size", "nrc_nonlinear_geometry",
                    "paired_nrc_diff_lin_minus_nl", "ci_lo", "ci_hi",
                ],
            )
            and all("target" in row["fit_target"].lower() and "gt" in row["fit_target"].lower() for row in rows)
            and all(row["selector_fit_split"] == "D_cal-fit" for row in rows)
            and all(row["conformal_calibration_split"].startswith("D_cal-calib") for row in rows)
            and all(row["evaluation_split"] == "D_audit" for row in rows)
            and all(row["source_lineage"] == "m069_fullval_same_forward" for row in rows)
            and all(row["mask_definition"] == "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square" for row in rows)
            and all(row["evaluation_mask_geometry"] == "matched_GT_aspect_ratio" for row in rows)
            and all(row["selector_geometry"] == "prediction_box_only" for row in rows)
            and all(row["fixed_size_bin_geometry"] == "prediction_box_area" for row in rows)
            and all(row["bootstrap_unit"] == "evaluation_image_cluster" and int(row["bootstrap_replicates"]) == 1000 for row in rows)
            and all(truth(row["nonlinear_better_sig"]) == (float(row["ci_lo"]) > 0) for row in rows)
            and all(int(row["retained_count"]) == int(row["n_instances"]) for row in rows)
            and all(0 < float(row["retained_ratio"]) <= 1 for row in rows)
            and all(float(row["ci_lo"]) <= float(row["ci_hi"]) for row in rows)
        )
        audit.add("m2", "M2 fixed-size-bin paired image-cluster intervals", ok, f"rows={len(rows)}; by_cell={by_cell}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("m2", "M2 fixed-size-bin paired image-cluster intervals", False, exc)

    try:
        interval_path = REP / "m2_g2doubleprime_cell_bin_intervals.csv"
        intervals, interval_fields = load_csv(
            interval_path,
            {
                "cell", "size_bin", "lower_area_inclusive", "upper_area_exclusive",
                "n_total", "n_fit", "n_audit", "status", "frozen", "mask_definition",
            },
            min_rows=18,
        )
        expected_keys = {(cell, size_bin) for cell in FULLVAL_CELLS for size_bin in ("small", "medium", "large")}
        observed_keys = {(row["cell"], row["size_bin"]) for row in intervals}
        expected_bounds = {
            "small": (0.0, "1024.0"),
            "medium": (1024.0, "9216.0"),
            "large": (9216.0, "inf"),
        }
        eligible = {
            (row["cell"], row["size_bin"])
            for row in intervals
            if row["status"] == "eligible"
        }
        result_rows, _ = load_csv(REP / "m2_g2doubleprime_ar21.csv", {"cell", "size_bin"})
        result_keys = {(row["cell"], row["size_bin"]) for row in result_rows}
        ok = (
            len(intervals) == 18
            and observed_keys == expected_keys
            and all_finite(intervals, ["lower_area_inclusive", "n_total", "n_fit", "n_audit"])
            and all(
                same_number(row["lower_area_inclusive"], expected_bounds[row["size_bin"]][0])
                and row["upper_area_exclusive"] == expected_bounds[row["size_bin"]][1]
                for row in intervals
            )
            and all(int(row["n_total"]) >= int(row["n_fit"]) + int(row["n_audit"]) for row in intervals)
            and all(
                row["status"]
                == ("eligible" if int(row["n_fit"]) >= 150 and int(row["n_audit"]) >= 100 else "insufficient_preregistered_minimum")
                for row in intervals
            )
            and result_keys == eligible
            and all("fixed before audit" in row["frozen"].lower() for row in intervals)
            and all(row["mask_definition"] == "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square" for row in intervals)
        )
        audit.add(
            "m2",
            "M2 preregistered size-bin boundaries",
            ok,
            f"rows={len(intervals)}; eligible={sorted(eligible)}; result_keys={sorted(result_keys)}; fields={interval_fields}",
            artifact_sha256=sha256_file(interval_path),
        )
    except Exception as exc:
        audit.add("m2", "M2 preregistered size-bin boundaries", False, exc)

    try:
        decision_rows, _ = load_csv(
            REP / "m2_g2doubleprime_decision.csv",
            {"decision", "supporting_cells", "n_bins_total", "n_bins_nonlinear_sig", "note"},
            min_rows=1,
        )
        if len(decision_rows) != 1:
            raise ValueError(f"M2 decision rows={len(decision_rows)}")
        decision_row = decision_rows[0]
        verdict = decision_row["decision"].upper()
        result_rows, _ = load_csv(
            REP / "m2_g2doubleprime_ar21.csv",
            {"cell", "size_bin", "ci_lo", "nonlinear_better_sig"},
            min_rows=1,
        )
        supporting = sorted(
            cell for cell in FULLVAL_CELLS
            if sum(float(row["ci_lo"]) > 0 for row in result_rows if row["cell"] == cell) >= 2
        )
        n_sig = sum(float(row["ci_lo"]) > 0 for row in result_rows)
        expected_verdict = "PASS" if len(supporting) >= 2 and n_sig >= 3 else "FAIL"
        doc = (ROOT / "docs" / "m2_g2doubleprime_ar21_size_control.md").read_text(encoding="utf-8")
        ok = (
            verdict == expected_verdict
            and set(filter(None, decision_row["supporting_cells"].split("|"))) == set(supporting)
            and int(decision_row["n_bins_total"]) == len(result_rows)
            and int(decision_row["n_bins_nonlinear_sig"]) == n_sig
            and all(truth(row["nonlinear_better_sig"]) == (float(row["ci_lo"]) > 0) for row in result_rows)
        )
        if verdict == "FAIL":
            ok = ok and ("appendix" in doc.lower() or "附录" in doc)
        audit.add("m2", "M2 binary decision independently reconstructed", ok, f"decision={verdict}; expected={expected_verdict}; supporting={supporting}; sig_bins={n_sig}/{len(result_rows)}; appendix_demotion={('appendix' in doc.lower() or '附录' in doc)}")
    except Exception as exc:
        audit.add("m2", "M2 binary decision independently reconstructed", False, exc)
    return verdict


def check_m3(audit: Audit, m2_verdict: str) -> str:
    verdict = ""
    try:
        path = REP / "m3_image_level_ltt.csv"
        required = {
            "cell", "score", "result_role", "risk_event", "mask_definition", "ar_threshold",
            "alpha", "threshold_source", "selected", "calib_mean_image_risk", "risk_ucb_calib",
            "calib_images", "mean_image_risk_audit", "nonempty_image_prop", "mean_instance_cov",
            "audit_images", "audit_retained", "audit_used_for_selection", "formal_guarantee_unit",
            "protocol_sha256", "matched_sha256", "universe_id_sha256", "family_id",
            "candidate_index", "fixed_sequence_state", "certified", "hb_pvalue_calib",
            "delta", "target_coverage", "threshold", "fit_instances",
            "fit_realized_instance_coverage", "calib_nonempty_image_prop",
            "calib_mean_instance_cov", "calib_realized_instance_coverage",
            "calib_eligible_instances", "calib_retained", "audit_realized_instance_coverage",
            "audit_eligible_instances", "empirical_instance_risk_audit",
            "risk_event_curve_sha256", "aspect_ratio_source", "eligible_instance_definition",
        }
        rows, fields = load_csv(path, required, min_rows=60)
        primary = [row for row in rows if row["result_role"] == "PRIMARY"]
        appendix = [row for row in rows if row["result_role"].startswith("APPENDIX")]
        score_menu = [row for row in rows if row["result_role"] == "PREREGISTERED_SCORE_MENU"]
        families = {(row["cell"], float(row["alpha"])) for row in primary if finite(row["alpha"])}
        expected = {(cell, alpha) for cell in FULLVAL_CELLS for alpha in (0.03, 0.05, 0.1)}
        expected_cells_by_score = {
            "detection_score": set(FULLVAL_CELLS),
            "geometry_score_upper_bound": set(FULLVAL_CELLS),
            "tta_neg_circular_var": set(FULLVAL_CELLS),
            "phase_mod": {"A", "D", "E"},
            "negative_phase_mod": {"A", "D", "E"},
        }
        expected_score_families = {
            (cell, score, alpha)
            for score, cells in expected_cells_by_score.items()
            for cell in cells
            for alpha in (0.03, 0.05, 0.1)
        }
        observed_score_families = {
            (row["cell"], row["score"], float(row["alpha"])) for row in rows
            if finite(row.get("alpha"))
        }
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row["family_id"], []).append(row)
        sequence_ok = True
        for family_rows in grouped.values():
            ordered = sorted(family_rows, key=lambda row: int(row["candidate_index"]))
            indices = [int(row["candidate_index"]) for row in ordered]
            coverages = [float(row["target_coverage"]) for row in ordered]
            thresholds = [float(row["threshold"]) for row in ordered]
            states = [row["fixed_sequence_state"] for row in ordered]
            selected = [row for row in ordered if truth(row["selected"])]
            first_failure = [index for index, state in enumerate(states) if state == "FIRST_FAILURE"]
            sequence_ok = sequence_ok and len(ordered) == 10 and indices == list(range(10))
            sequence_ok = sequence_ok and all(abs(value - (index + 1) / 10) <= 1e-12 for index, value in enumerate(coverages))
            sequence_ok = sequence_ok and all(thresholds[index] >= thresholds[index + 1] for index in range(9))
            sequence_ok = sequence_ok and len(first_failure) <= 1 and len(selected) <= 1
            reached = True
            certified_indices = []
            for index, row in enumerate(ordered):
                mean = float(row["calib_mean_image_risk"])
                alpha = float(row["alpha"])
                n_images = int(float(row["calib_images"]))
                delta = float(row["delta"])
                pvalue = audit_hb_pvalue(mean, alpha, n_images)
                ucb = audit_hb_ucb(mean, n_images, delta)
                certified = reached and pvalue <= delta
                expected_state = "CERTIFIED" if certified else "FIRST_FAILURE" if reached else "NOT_TESTED_AFTER_FAILURE"
                sequence_ok = sequence_ok and row["fixed_sequence_state"] == expected_state
                sequence_ok = sequence_ok and truth(row["certified"]) == certified
                sequence_ok = sequence_ok and abs(float(row["hb_pvalue_calib"]) - pvalue) <= 1e-9
                sequence_ok = sequence_ok and abs(float(row["risk_ucb_calib"]) - ucb) <= 1e-9
                if certified:
                    certified_indices.append(index)
                elif reached:
                    reached = False
            expected_selected = certified_indices[-1] if certified_indices else None
            sequence_ok = sequence_ok and (
                ([int(row["candidate_index"]) for row in selected] == [expected_selected])
                if expected_selected is not None else not selected
            )
            if first_failure:
                stop = first_failure[0]
                sequence_ok = sequence_ok and all(state == "CERTIFIED" for state in states[:stop])
                sequence_ok = sequence_ok and all(state == "NOT_TESTED_AFTER_FAILURE" for state in states[stop + 1 :])
            else:
                sequence_ok = sequence_ok and all(state == "CERTIFIED" for state in states)
            sequence_ok = sequence_ok and all(truth(row["certified"]) for row in selected)
        ok = (
            expected.issubset(families)
            and observed_score_families == expected_score_families
            and len(grouped) == len(expected_score_families) == 72
            and len(rows) == 720
            and sequence_ok
            and all(row["score"] == "detection_score" for row in primary)
            and all(row["score"] == "geometry_score_upper_bound" for row in appendix)
            and {row["score"] for row in score_menu}
            == {"tta_neg_circular_var", "phase_mod", "negative_phase_mod"}
            and all(
                row["result_role"]
                == (
                    "PRIMARY" if row["score"] == "detection_score"
                    else "APPENDIX_GT_FIT_UPPER_BOUND"
                    if row["score"] == "geometry_score_upper_bound"
                    else "PREREGISTERED_SCORE_MENU"
                )
                for row in rows
            )
            and all(row["risk_event"] == "geometry_normalized_severe" for row in rows)
            and all(same_number(row["ar_threshold"], 2.1) for row in rows)
            and all(row["threshold_source"] == "D_cal-fit_only" for row in rows)
            and all(not truth(row["audit_used_for_selection"]) for row in rows)
            and all(row["formal_guarantee_unit"] == "complete_evaluation_image" for row in rows)
            and all(row["protocol_sha256"] == M3_PROTOCOL_SHA for row in rows)
            and all(row["risk_event_curve_sha256"] == M4_DELTA_JSON_SHA for row in rows)
            and all(row["aspect_ratio_source"] == "matched_GT_box" for row in rows)
            and all("IoU_ge_0.5" in row["eligible_instance_definition"] for row in rows)
            and all_finite(
                rows,
                ["alpha", "delta", "target_coverage", "threshold", "fit_instances",
                 "fit_realized_instance_coverage", "calib_mean_image_risk", "risk_ucb_calib",
                 "hb_pvalue_calib", "calib_nonempty_image_prop", "calib_mean_instance_cov",
                 "calib_realized_instance_coverage", "calib_images", "calib_eligible_instances",
                 "calib_retained", "mean_image_risk_audit", "nonempty_image_prop",
                 "mean_instance_cov", "audit_realized_instance_coverage", "audit_images",
                 "audit_eligible_instances", "audit_retained", "empirical_instance_risk_audit"],
            )
            and all(0 <= float(row["calib_mean_image_risk"]) <= 1 for row in rows)
            and all(0 <= float(row["risk_ucb_calib"]) <= 1 for row in rows)
            and all(0 <= float(row["mean_image_risk_audit"]) <= 1 for row in rows)
            and all(0 <= float(row["nonempty_image_prop"]) <= 1 for row in rows)
            and all(0 <= float(row["mean_instance_cov"]) <= 1 for row in rows)
            and all(int(float(row["calib_images"])) > 0 and int(float(row["audit_images"])) > 0 for row in rows)
            and "exact_binomial" not in {field.lower() for field in fields}
        )
        if m2_verdict == "FAIL":
            ok = ok and bool(appendix) and not any(
                row["score"] == "geometry_score_upper_bound" for row in primary
            )
        audit.add("m3", "M3 complete-image HB LTT formal table", ok, f"rows={len(rows)}; families={len(grouped)}; expected_families={len(expected_score_families)}; sequence_ok={sequence_ok}; primary={len(primary)}; appendix={len(appendix)}; score_menu={len(score_menu)}; missing_families={sorted(expected_score_families-observed_score_families)}; extra_families={sorted(observed_score_families-expected_score_families)}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("m3", "M3 complete-image HB LTT formal table", False, exc)

    try:
        comparison, _ = load_csv(
            REP / "m3_instance_vs_image_comparison.csv",
            {"cell", "score", "result_role", "alpha", "formal_guarantee", "old_instance_iid_cp_ucb_calib_audit_only", "audit_instance_coverage_drop_old_minus_new", "ucb_change_image_minus_old_iid", "note"},
            min_rows=12,
        )
        expected_comparison = {
            (cell, score, alpha)
            for score, cells in {
                "detection_score": set(FULLVAL_CELLS),
                "geometry_score_upper_bound": set(FULLVAL_CELLS),
                "tta_neg_circular_var": set(FULLVAL_CELLS),
                "phase_mod": {"A", "D", "E"},
                "negative_phase_mod": {"A", "D", "E"},
            }.items()
            for cell in cells for alpha in (0.03, 0.05, 0.1)
        }
        observed_comparison = {(row["cell"], row["score"], float(row["alpha"])) for row in comparison}
        ok = len(comparison) == 72 and observed_comparison == expected_comparison and all(row["formal_guarantee"] == "new_image_level_only" for row in comparison) and all(
            "audit" in row.get("note", "").lower() or "counterfactual" in row.get("note", "").lower() for row in comparison
        )
        audit.add("m3", "M3 old instance-iid comparison is audit-only", ok, f"rows={len(comparison)}", artifact_sha256=sha256_file(REP / "m3_instance_vs_image_comparison.csv"))
    except Exception as exc:
        audit.add("m3", "M3 old instance-iid comparison is audit-only", False, exc)

    try:
        secondary, _ = load_csv(
            REP / "m3_image_event_secondary_endpoint.csv",
            {"cell", "result_role", "risk_event", "alpha", "delta", "candidate_index",
             "target_coverage", "fixed_sequence_state", "certified", "selected",
             "calib_image_events", "calib_images", "exact_clopper_pearson_ucb_calib",
             "audit_used_for_selection", "note"},
            min_rows=30,
        )
        secondary_groups = {}
        for row in secondary:
            secondary_groups.setdefault((row["cell"], float(row["alpha"])), []).append(row)
        sequence_ok = True
        for group in secondary_groups.values():
            ordered = sorted(group, key=lambda row: int(row["candidate_index"]))
            sequence_ok = sequence_ok and len(ordered) == 10
            sequence_ok = sequence_ok and [int(row["candidate_index"]) for row in ordered] == list(range(10))
            sequence_ok = sequence_ok and [float(row["target_coverage"]) for row in ordered] == [index / 10 for index in range(1, 11)]
            selected = [row for row in ordered if truth(row["selected"])]
            certified = [row for row in ordered if truth(row["certified"])]
            sequence_ok = sequence_ok and len(selected) <= 1
            sequence_ok = sequence_ok and (
                (selected and certified and selected[0]["candidate_index"] == certified[-1]["candidate_index"])
                or (not selected and not certified)
            )
        ok = len(secondary) == 180 and len(secondary_groups) == 18 and sequence_ok and all(row["result_role"] == "SECONDARY" for row in secondary) and all(
            "secondary" in row["note"].lower() for row in secondary
        ) and all(not truth(row["audit_used_for_selection"]) for row in secondary) and all(
            row["risk_event"] == "image_has_any_geometry_normalized_severe" for row in secondary
        )
        audit.add("m3", "M3 exact-binomial restricted to secondary image event", ok, f"rows={len(secondary)}", artifact_sha256=sha256_file(REP / "m3_image_event_secondary_endpoint.csv"))
    except Exception as exc:
        audit.add("m3", "M3 exact-binomial restricted to secondary image event", False, exc)

    try:
        empirical, _ = load_csv(
            REP / "m3_instance_weighted_empirical.csv",
            {"cell", "score", "alpha", "selected_threshold_exists", "empirical_instance_weighted_risk", "image_cluster_bootstrap_ci_lo", "image_cluster_bootstrap_ci_hi", "formal_guarantee", "note"},
        )
        empirical_keys = {(row["cell"], row["score"], float(row["alpha"])) for row in empirical}
        ok = len(empirical) == 72 and len(empirical_keys) == 72 and all(not truth(row["formal_guarantee"]) for row in empirical) and all(
            "image-cluster bootstrap" in row["note"] for row in empirical
        ) and all(
            (all(finite(row[field]) for field in ("empirical_instance_weighted_risk", "image_cluster_bootstrap_ci_lo", "image_cluster_bootstrap_ci_hi"))
             if truth(row["selected_threshold_exists"])
             else not any(str(row[field]).strip() for field in ("empirical_instance_weighted_risk", "image_cluster_bootstrap_ci_lo", "image_cluster_bootstrap_ci_hi")))
            for row in empirical
        )
        audit.add("m3", "M3 instance risk empirical with image-cluster CI", ok, f"rows={len(empirical)}", artifact_sha256=sha256_file(REP / "m3_instance_weighted_empirical.csv"))
    except Exception as exc:
        audit.add("m3", "M3 instance risk empirical with image-cluster CI", False, exc)

    try:
        lineage = load_json(REP / "m3_input_lineage_manifest.json")
        cells = {row.get("cell") for row in lineage}
        ok = cells == set(FULLVAL_CELLS) and len(lineage) == 6
        for row in lineage:
            matched_path = Path(str(row.get("matched_path", "")))
            if not matched_path.is_absolute():
                matched_path = ROOT / matched_path
            universe_path = Path(str(row.get("universe_path", "")))
            if not universe_path.is_absolute():
                universe_path = ROOT / universe_path
            expected_images = FULLVAL_EXPECTED[row["cell"]]["n_images"]
            ok = ok and (
                row.get("lineage_status") == "FULLVAL_VALIDATED"
                and row.get("can_recompute") is True
                and "/dev/shm" not in str(matched_path)
                and "/dev/shm" not in str(universe_path)
                and matched_path.is_file()
                and sha256_file(matched_path) == row.get("matched_sha256")
                and universe_path.is_file()
                and sha256_file(universe_path) == row.get("universe_sha256")
                and int(row.get("universe_images", -1)) == expected_images
                and int(row.get("fit_images", 0)) + int(row.get("calib_images", 0)) + int(row.get("audit_images", 0)) == expected_images
                and row.get("protocol_sha256") == M3_PROTOCOL_SHA
                and row.get("risk_event_curve_sha256") == M4_DELTA_JSON_SHA
            )
        audit.add("m3", "M3 input lineage manifest and SHA alignment", ok, f"cells={sorted(cells)}; rows={len(lineage)}", artifact_sha256=sha256_file(REP / "m3_input_lineage_manifest.json"))
    except Exception as exc:
        audit.add("m3", "M3 input lineage manifest and SHA alignment", False, exc)

    try:
        verdict = decision(REP / "m3_decision.csv")
        decision_rows, _ = load_csv(REP / "m3_decision.csv", {"decision", "primary_score", "primary_risk_event", "n_primary_selected", "n_primary_nondegenerate", "n_appendix_selected", "n_preregistered_score_menu_selected", "audit_used_for_selection", "protocol_sha256"})
        if len(decision_rows) != 1:
            raise ValueError(f"M3 decision rows={len(decision_rows)}")
        row = decision_rows[0]
        ltt_rows, _ = load_csv(REP / "m3_image_level_ltt.csv", {"result_role", "selected", "target_coverage", "calib_nonempty_image_prop"})
        selected_primary = [value for value in ltt_rows if value["result_role"] == "PRIMARY" and truth(value["selected"])]
        selected_appendix = [value for value in ltt_rows if value["result_role"] == "APPENDIX_GT_FIT_UPPER_BOUND" and truth(value["selected"])]
        selected_menu = [value for value in ltt_rows if value["result_role"] == "PREREGISTERED_SCORE_MENU" and truth(value["selected"])]
        nondegenerate = [value for value in selected_primary if float(value["target_coverage"]) >= 0.3 and float(value["calib_nonempty_image_prop"]) >= 0.3]
        expected_verdict = "PASS" if nondegenerate else "PARTIAL" if selected_primary else "FAIL"
        ok = (
            verdict == expected_verdict
            and row["primary_score"] == "detection_score"
            and row["primary_risk_event"] == "geometry_normalized_severe"
            and int(row["n_primary_selected"]) == len(selected_primary)
            and int(row["n_primary_nondegenerate"]) == len(nondegenerate)
            and int(row["n_appendix_selected"]) == len(selected_appendix)
            and int(row["n_preregistered_score_menu_selected"]) == len(selected_menu)
            and not truth(row["audit_used_for_selection"])
            and row["protocol_sha256"] == M3_PROTOCOL_SHA
        )
        audit.add("m3", "M3 decision independently reconstructed from calibration only", ok, f"decision={verdict}; expected={expected_verdict}; primary_selected={len(selected_primary)}; nondegenerate={len(nondegenerate)}")
    except Exception as exc:
        audit.add("m3", "M3 decision uses calibration only", False, exc)
    return verdict


def check_m4(audit: Audit) -> None:
    try:
        path = REP / "m4_geometry_normalized_risk.csv"
        rows, _ = load_csv(
            path,
            {"cell", "dataset", "detector", "mask_definition", "aspect_ratio_source",
             "ar_threshold", "retained_count", "retained_ratio", "severe_event_rate",
             "event_def", "angle_convention", "geometry_model", "solve_tolerance_deg",
             "delta_theta_curve_sha256", "threshold_semantics", "high_ar_policy",
             "input_lineage_status", "interpretation"},
            min_rows=8,
        )
        cells = {row["cell"] for row in rows}
        ok = len(rows) == 8 and cells == MAIN_CELLS and all(same_number(row["ar_threshold"], 2.1) for row in rows) and all_finite(
            rows, ["retained_count", "retained_ratio", "severe_event_rate"]
        ) and all(
            row["event_def"] == "angle_error_le90 > delta_theta_0.75(matched_GT_aspect_ratio)"
            and row["mask_definition"] == "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square"
            and row["aspect_ratio_source"] == "matched_GT_box"
            and row["angle_convention"] == "le90_pi_periodic_long_axis"
            and row["geometry_model"] == "concentric_same_scale_congruent_rectangles"
            and same_number(row["solve_tolerance_deg"], 0.001)
            and row["delta_theta_curve_sha256"] == M4_DELTA_JSON_SHA
            and row["threshold_semantics"] == "smallest_strict_crossing_on_le90_first_lobe"
            and row["high_ar_policy"] == "conservative_inverse_ar_tail_minus_2solve_tol"
            and row["input_lineage_status"] == "PASS_FULLVAL_LINEAGE"
            and "not a claim" in row["interpretation"]
            for row in rows
        )
        audit.add("m4", "geometry-normalized severe-event table", ok, f"rows={len(rows)}; cells={sorted(cells)}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("m4", "geometry-normalized severe-event table", False, exc)

    try:
        path = REP / "m4_fixed_angle_sensitivity.csv"
        rows, _ = load_csv(
            path,
            {"cell", "dataset", "mask_definition", "aspect_ratio_source", "ar_threshold",
             "angle_threshold_deg", "event_rate", "interp", "noise_sensitive", "proxy_role",
             "angle_convention", "geometry_model", "solve_tolerance_deg",
             "delta_theta_curve_sha256", "threshold_semantics", "input_lineage_status"},
            min_rows=24,
        )
        pairs = {(row["cell"], int(float(row["angle_threshold_deg"]))) for row in rows}
        expected = {(cell, angle) for cell in MAIN_CELLS for angle in (5, 10, 15)}
        noise_ok = all(
            truth(row["noise_sensitive"]) == (row["dataset"] in {"FAIR1M-v1.0", "SODA-A"})
            for row in rows
        )
        ok = len(rows) == 24 and pairs == expected and noise_ok and all(same_number(row["ar_threshold"], 2.1) for row in rows) and all_finite(rows, ["event_rate"]) and all(
            row["interp"] == ("fine-risk" if same_number(row["angle_threshold_deg"], 5) else "interpretive sensitivity")
            and row["proxy_role"] == "corner-jitter proxy only; not sigma_gt or human disagreement"
            and row["mask_definition"] == "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square"
            and row["aspect_ratio_source"] == "matched_GT_box"
            and row["angle_convention"] == "le90_pi_periodic_long_axis"
            and row["geometry_model"] == "concentric_same_scale_congruent_rectangles"
            and same_number(row["solve_tolerance_deg"], 0.001)
            and row["delta_theta_curve_sha256"] == M4_DELTA_JSON_SHA
            and row["threshold_semantics"] == "smallest_strict_crossing_on_le90_first_lobe"
            and row["input_lineage_status"] == "PASS_FULLVAL_LINEAGE"
            for row in rows
        )
        audit.add("m4", "5/10/15-degree sensitivity and noise flags", ok, f"pairs={len(pairs)}/{len(expected)}; noise_sensitive_5deg={noise_ok}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("m4", "5/10/15-degree sensitivity and noise flags", False, exc)

    try:
        human, human_fields = load_csv(
            REP / "m4_human_annotation_disagreement.csv",
            {"source_kind", "is_proxy", "dataset", "n_pairs", "status"},
        )
        proxy, proxy_fields = load_csv(
            REP / "m4_gt_jitter_proxy_reference.csv",
            {"source_kind", "is_proxy", "dataset", "status"},
        )
        ok = (
            "sigma_gt" not in {field.lower() for field in human_fields + proxy_fields}
            and all(row["source_kind"] == "HUMAN_INDEPENDENT_DOUBLE_ANNOTATION" and not truth(row["is_proxy"]) for row in human)
            and all(row["source_kind"] == "GT_CORNER_JITTER_PROXY" and truth(row["is_proxy"]) for row in proxy)
        )
        audit.add("m4", "GT-noise proxy strictly separated from human labels", ok, f"human_rows={len(human)}; proxy_rows={len(proxy)}")
    except Exception as exc:
        audit.add("m4", "GT-noise proxy strictly separated from human labels", False, exc)

    try:
        observed, _ = load_csv(
            REP / "m4_observed_ar_numerical_stability.csv",
            {
                "cell", "dataset", "ar_threshold", "n_main", "ar_max",
                "n_ar_gt_legacy8", "n_ar_gt_grid_max", "solve_tolerance_deg",
                "grid_max_ar", "high_ar_policy", "legacy_ar8_clamp_used",
                "nonfinite_delta_count", "stability_pass",
            },
            min_rows=8,
        )
        direct, _ = load_csv(
            REP / "m4_delta_theta_direct_solve_stability.csv",
            {
                "ar", "tau", "solve_tolerance_deg", "direct_bracket_ok",
                "curve_monotone_nonincreasing", "stability_pass",
            },
            min_rows=10,
        )
        lineage, _ = load_csv(
            REP / "m4_input_lineage_audit.csv",
            {"cell", "source_path", "source_sha256", "lineage_status", "can_recompute_cpu"},
            min_rows=8,
        )
        ok = (
            {row["cell"] for row in observed} == MAIN_CELLS
            and {row["cell"] for row in lineage} == MAIN_CELLS
            and len(direct) == 20
            and {1.0, 1.05, 1.1, 2.1}.issubset(
                {round(float(row["ar"]), 6) for row in direct}
            )
            and all(same_number(row["tau"], 0.75) for row in direct)
            and all(same_number(row["ar_threshold"], 2.1) for row in observed)
            and all(not truth(row["legacy_ar8_clamp_used"]) for row in observed)
            and all(int(row["n_ar_gt_grid_max"]) == 0 for row in observed)
            and all(int(row["nonfinite_delta_count"]) == 0 for row in observed)
            and all(truth(row["stability_pass"]) for row in observed)
            and all(float(row["grid_max_ar"]) >= float(row["ar_max"]) for row in observed)
            and all(same_number(row["solve_tolerance_deg"], 0.001) for row in observed + direct)
            and all(truth(row["direct_bracket_ok"]) and truth(row["curve_monotone_nonincreasing"]) and truth(row["stability_pass"]) for row in direct)
            and all(row["lineage_status"] == "PASS_FULLVAL_LINEAGE" and truth(row["can_recompute_cpu"]) for row in lineage)
            and all("/dev/shm" not in row["source_path"] for row in lineage)
        )
        audit.add(
            "m4",
            "M4 direct-solve/high-AR numerical stability and full-val lineage",
            ok,
            f"observed={len(observed)}; direct={len(direct)}; lineage={len(lineage)}; max_ar={max(float(row['ar_max']) for row in observed)}",
            artifact_sha256=sha256_file(REP / "m4_observed_ar_numerical_stability.csv"),
        )
    except Exception as exc:
        audit.add("m4", "M4 direct-solve/high-AR numerical stability and full-val lineage", False, exc)


def check_dior_resolution(audit: Audit) -> None:
    try:
        path = ROOT / "reports" / "069_dior_partial_gt_lineage_audit.csv"
        rows, fields = load_csv(path, min_rows=3)
        cell_field = "cell" if "cell" in fields else "cell_id" if "cell_id" in fields else ""
        status_field = "status" if "status" in fields else "lineage_status" if "lineage_status" in fields else ""
        if not cell_field or not status_field:
            raise ValueError(f"lineage audit needs cell/status fields; got {fields}")
        aliases = {"A": "A", "B": "B", "C": "C", "DIOR-R/22": "A", "DIOR-R/3": "B", "DIOR-R/61": "C"}
        formal = [row for row in rows if row.get(cell_field) in aliases]
        grouped = {cell: [row for row in formal if aliases[row[cell_field]] == cell] for cell in ("A", "B", "C")}
        ok = all(
            any("FULLVAL" in row.get(status_field, "").upper() for row in grouped[cell])
            for cell in grouped
        )
        for row in formal:
            status = row.get(status_field, "").upper()
            if "PARTIAL" in status and "SUPERSEDED" not in status:
                ok = False
            if "FULLVAL" in status and row.get("n_gt") and finite(row["n_gt"]):
                ok = ok and int(float(row["n_gt"])) == 124445
            for key, value in row.items():
                if "path" in key.lower() and value and "SUPERSEDED" not in status:
                    ok = ok and "/dev/shm" not in value
        doc = (ROOT / "docs" / "069_dior_partial_gt_lineage_resolution.md").read_text(encoding="utf-8")
        ok = ok and "124445" in doc and "supersed" in doc.lower()
        group_counts = {key: len(value) for key, value in grouped.items()}
        audit.add("dior_lineage", "DIOR partial-GT lineage cleared and superseded", ok, f"rows={len(rows)}; grouped={group_counts}; fields={fields}", artifact_sha256=sha256_file(path))
    except Exception as exc:
        audit.add("dior_lineage", "DIOR partial-GT lineage cleared and superseded", False, exc)

    try:
        rows, _ = load_csv(
            REP / "k1_table1_gt_manifest_065.csv", {"dataset_split", "n_gt", "gt_path"}
        )
        dior = [row for row in rows if row["dataset_split"] == "DIOR-R_test"]
        ok = len(dior) == 1 and int(dior[0]["n_gt"]) == 124445 and "/dev/shm" not in dior[0]["gt_path"]
        audit.add("dior_lineage", "K1 DIOR full-test GT anchor", ok, f"rows={dior}")
    except Exception as exc:
        audit.add("dior_lineage", "K1 DIOR full-test GT anchor", False, exc)


def check_dota_outputs(audit: Audit) -> None:
    try:
        rows, _ = load_csv(
            REP / "k4b_dota_full_val_metrics.csv",
            {"cell", "detector", "AP50", "AP75", "n_gt_fullval", "checkpoint", "gt_source", "can_recompute", "evaluator", "provenance"},
            min_rows=2,
        )
        expected_cells = {"DOTA-v1.0/orcnn", "DOTA-v1.0/rtmdet"}
        clean = [row for row in rows if row["cell"] in expected_cells]
        ok = (
            len(rows) == 2
            and {row["cell"] for row in clean} == expected_cells
            and all(int(row["n_gt_fullval"]) == 55804 for row in clean)
            and all_finite(clean, ["AP50", "AP75"])
            and all(0 < float(row["AP75"]) <= float(row["AP50"]) <= 1 for row in clean)
            and all(truth(row["can_recompute"]) for row in clean)
            and all("VOC-AP" in row["evaluator"] or "DOTAMetric" in row["evaluator"] for row in clean)
            and all("full-val" in row["provenance"].lower() for row in clean)
            and all("val" in row["gt_source"].lower() for row in clean)
            and not any(row["cell"].endswith("/20") or "DOTA#20" == row["cell"] for row in rows)
        )
        audit.add("dota", "DOTA clean full-val metrics and DOTA#20 exclusion", ok, f"rows={len(rows)}; clean_cells={[row['cell'] for row in clean]}", artifact_sha256=sha256_file(REP / "k4b_dota_full_val_metrics.csv"))
    except Exception as exc:
        audit.add("dota", "DOTA clean full-val metrics and DOTA#20 exclusion", False, exc)


def check_no_dev_shm(audit: Audit) -> None:
    paths = [REP / name for name in ROOT_REPORT_ALIAS_NAMES]
    hits = []
    missing = []
    for path in paths:
        if not path.is_file():
            missing.append(str(path.relative_to(ROOT)))
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "/dev/shm" in line:
                hits.append(f"{path.relative_to(ROOT)}:{line_number}")
    audit.add("reproduction", "no /dev/shm formal-table dependency", not hits and not missing, f"hits={hits}; missing={missing}")


def check_manuscript_semantics(
    audit: Audit,
    m2_verdict: str,
    human_status: str,
    psc_verdict: str,
) -> None:
    try:
        text = CURRENT_MANUSCRIPT.read_text(encoding="utf-8")
        manuscript_sha = sha256_file(CURRENT_MANUSCRIPT)
        required_patterns = {
            "ar21_main": r"ar\s*(?:>=|≥)\s*2\.1.{0,80}(?:主口径|主分析|main)|(?:主口径|主分析|main).{0,80}ar\s*(?:>=|≥)\s*2\.1",
            "ar16_ar13_sensitivity": r"ar\s*(?:>=|≥)\s*1\.6.{0,100}ar\s*(?:>=|≥)\s*1\.3.{0,100}(?:敏感性|sensitivity)|(?:敏感性|sensitivity).{0,100}ar\s*(?:>=|≥)\s*1\.6.{0,100}ar\s*(?:>=|≥)\s*1\.3",
            "m2_fixed_size_decision": r"(?:G2_double_prime|G2[′'\"]{2}|M2).{0,160}(?:固定.{0,20}(?:尺寸|size).{0,20}(?:分箱|bin)|fixed.{0,20}size.{0,20}bin)",
            "geometry_appendix": r"(?:几何(?:感知)?打分|geometry score).{0,160}(?:附录|appendix)|(?:附录|appendix).{0,160}(?:几何(?:感知)?打分|geometry score)",
            "image_exchangeable_unit": r"(?:图像|image).{0,50}(?:可交换|exchangeable).{0,30}(?:单元|unit)|(?:可交换|exchangeable).{0,50}(?:单元|unit).{0,50}(?:图像|image)",
            "bounded_loss_ltt": r"L_I.{0,300}(?:Hoeffding[- ]Bentkus|HB).{0,300}(?:Learn[- ]Then[- ]Test|LTT)|(?:Hoeffding[- ]Bentkus|HB).{0,300}L_I",
            "secondary_image_event": r"Z_I.{0,220}(?:exact binomial|精确二项).{0,100}(?:次级|secondary)|(?:次级|secondary).{0,220}Z_I",
            "instance_empirical_only": r"(?:实例加权|instance-weighted).{0,180}(?:图像(?:级)?聚类自助|image-cluster bootstrap)",
            "geometry_normalized_event": r"(?:angle[_ ]?error|角度误差|e_?\{?\\?theta\}?).{0,80}(?:>|超过).{0,80}(?:delta_theta_0\.75|δθ_?\{?0\.75\}?|\\delta\\theta_?\{?0\.75\}?).{0,120}(?:aspect.?ratio|长宽比|\bar\b)",
            "fixed_angle_sensitivity": r"5°.{0,120}10°.{0,120}15°|15°.{0,120}10°.{0,120}5°",
            "five_degree_fine_risk": r"5°.{0,100}fine[- ]risk|fine[- ]risk.{0,100}5°",
            "proxy_human_separation": r"(?:proxy|代理).{0,180}(?:人工双标|human).{0,120}(?:区分|分列|不是|非)|(?:人工双标|human).{0,180}(?:proxy|代理).{0,120}(?:区分|分列|不是|非)",
            "psc_phase1": r"PSC Phase 1.{0,240}(?:radial|径向|z\s*'?\s*=\s*k\s*z).{0,240}(?:Branch|分支)",
            "psc_terminal_gate": rf"(?:拆篇|split).{{0,160}}(?:{re.escape(psc_verdict)}|通过|失败|截止)|(?:{re.escape(psc_verdict)}).{{0,160}}(?:拆篇|split)",
            "dota20_excluded": r"DOTA#?20.{0,100}(?:排除|不进入|excluded)",
            "geometry_gt_fit_upper_bound": r"(?:几何(?:感知)?打分|geometry score).{0,200}(?:目标域真值|target-domain GT).{0,160}(?:上界|upper-bound)",
        }
        missing = [
            label for label, pattern in required_patterns.items()
            if re.search(pattern, text, re.I | re.S) is None
        ]
        if m2_verdict == "FAIL" and re.search(
            r"(?:G2_double_prime|M2).{0,120}(?:FAIL|失败|未通过)", text, re.I | re.S
        ) is None:
            missing.append("m2_fail_explicit")
        if human_status == "HUMAN_BLOCKED" and re.search(
            r"(?:人工双标|双人.{0,20}标注).{0,180}(?:HUMAN_BLOCKED|尚未|未完成|待真实标注|缺失)",
            text,
            re.I | re.S,
        ) is None:
            missing.append("human_blocker_explicit")

        forbidden_patterns = {
            "old_ar16_main": r"表\s*4\s*主列取\s*masked\s*ar\s*(?:>=|≥)\s*1\.6|主口径.{0,40}ar\s*(?:>=|≥)\s*1\.6",
            "old_ar20_main": r"主口径最接近档\s*ar\s*(?:>=|≥)\s*2\.0|主档\s*ar\s*(?:>=|≥)\s*2\.0",
            "instance_exchangeability": r"承认实例级可交换性假设|实例(?:是|作为).{0,30}(?:正式)?可交换单元",
            "exact_binomial_primary": r"尾部（示性）损失用精确二项|主(?:风险|损失|保证).{0,120}(?:exact binomial|精确二项)|(?:exact binomial|精确二项).{0,120}主(?:风险|损失|保证)",
            "m2_still_open": r"固定框尺寸分箱.{0,100}仍是开放问题|fixed-size-bin.{0,100}(?:open problem|待完成)",
            "proxy_called_sigma_gt": r"sigma_gt|σ_?gt",
            "placeholders": r"\bTODO\b|\bTBD\b|待补|占位符",
        }
        if m2_verdict == "FAIL":
            forbidden_patterns.update({
                "stale_geometry_significant_gain": r"非线性几何(?:感知)?打分.{0,120}显著低于",
                "stale_geometry_all_six_gain": r"几何(?:感知)?打分.{0,160}六单元均显著低于|六单元.{0,160}几何(?:感知)?打分.{0,80}显著",
                "stale_geometry_safe_candidate": r"几何(?:感知)?打分.{0,160}安全的诊断性|安全的诊断性.{0,160}几何(?:感知)?打分",
                "stale_geometry_no_harm_claim": r"几何(?:感知)?打分.{0,200}带来增益.{0,100}不损害",
            })
        forbidden_hits = {
            label: match.group(0)[:240]
            for label, pattern in forbidden_patterns.items()
            if (match := re.search(pattern, text, re.I | re.S)) is not None
        }
        for line_number, line in enumerate(text.splitlines(), 1):
            lowered = line.lower()
            sensitivity_context = any(
                token in lowered
                for token in ("敏感性", "sensitivity", "此前", "旧口径", "历史", "supersed")
            )
            if (
                re.search(r"ar\s*(?:>=|≥)\s*1\.6", line, re.I)
                and not sensitivity_context
                and (
                    "masked" in lowered
                    or re.search(r"(?:n|nrc|aurc|risk)[（(].*ar\s*(?:>=|≥)\s*1\.6", line, re.I)
                )
            ):
                forbidden_hits.setdefault(
                    "ar16_formal_row_without_sensitivity_label",
                    f"line {line_number}: {line[:220]}",
                )
            if (
                re.search(r"(?:exact binomial|精确二项)", line, re.I)
                and not any(
                    token in lowered
                    for token in ("次级", "secondary", "旧", "审计", "audit", "对照", "不使用", "禁止", "不能")
                )
            ):
                forbidden_hits.setdefault(
                    "exact_binomial_not_labeled_secondary_or_audit",
                    f"line {line_number}: {line[:220]}",
                )
        extra_manuscripts = sorted(
            str(path.relative_to(ROOT))
            for path in (ROOT / "docs").glob("paper_zh_post_k1k4_069*")
        )
        ok = (
            manuscript_sha != ORIGINAL_068_MANUSCRIPT_SHA
            and not missing
            and not forbidden_hits
            and not extra_manuscripts
        )
        audit.add(
            "manuscript",
            "same-path Chinese manuscript integrates final 069 semantics",
            ok,
            f"path={CURRENT_MANUSCRIPT.relative_to(ROOT)}; sha={manuscript_sha}; original_068_changed={manuscript_sha != ORIGINAL_068_MANUSCRIPT_SHA}; missing={missing}; forbidden_hits={forbidden_hits}; duplicate_069_manuscripts={extra_manuscripts}; m2={m2_verdict}; human={human_status}; psc={psc_verdict}",
            artifact_sha256=manuscript_sha,
        )
    except Exception as exc:
        audit.add(
            "manuscript",
            "same-path Chinese manuscript integrates final 069 semantics",
            False,
            f"{type(exc).__name__}: {exc}",
        )


def ensure_root_report_aliases(audit: Audit) -> None:
    failures = []
    created = []
    for name in ROOT_REPORT_ALIAS_NAMES:
        canonical = REP / name
        alias = OUT / name
        try:
            if not canonical.is_file() or canonical.stat().st_size <= 0:
                failures.append(f"missing_canonical:{name}")
                continue
            expected_target = os.path.relpath(canonical, alias.parent)
            if alias.is_symlink():
                if os.readlink(alias) != expected_target or alias.resolve() != canonical.resolve():
                    failures.append(f"wrong_symlink:{name}->{os.readlink(alias)}")
                continue
            if alias.exists():
                failures.append(f"regular_file_conflict:{name}")
                continue
            alias.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(expected_target, alias)
            created.append(name)
        except Exception as exc:
            failures.append(f"{name}:{type(exc).__name__}:{exc}")
    audit.add(
        "reproduction",
        "root report aliases point to canonical historical-069 namespace",
        not failures,
        f"aliases={len(ROOT_REPORT_ALIAS_NAMES)}; created={created}; failures={failures}",
    )


def write_authoritative_artifact_manifest(audit: Audit) -> None:
    entries: list[tuple[str, Path, str, str, str]] = []
    setup_failures: list[str] = []
    for name in ROOT_REPORT_ALIAS_NAMES:
        if name in {
            "m3_image_level_protocol_frozen.json", "m4_delta_theta_075_frozen.json",
            "m4_delta_theta_tau_curve.csv", "m4_delta_theta_direct_solve_stability.csv",
        }:
            role, recompute = "FROZEN_PROTOCOL", "immutable"
        elif name.startswith("k2_") or name == "k4b_dota_full_val_metrics.csv":
            role, recompute = "VALIDATED_HISTORICAL_RESULT", "revalidate only; no 069 rerun"
        elif name.startswith("m4_human_annotation_build") or name.startswith("m4_human_annotation_sampling"):
            role, recompute = "HUMAN_ANNOTATION_MACHINE_PACKAGE", "rebuild only before real labels exist"
        else:
            role, recompute = "AUTHORITATIVE_DERIVED_REPORT", "bash scripts/reproduce_all_main_tables.sh"
        entries.append(
            (
                name,
                REP / name,
                role,
                f"reports/{name}",
                recompute,
            )
        )
    entries.extend(
        [
            ("thresholds", ROOT / "configs/thresholds.yaml", "FROZEN_ASSET", "", "immutable"),
            ("M3 protocol", REP / "m3_image_level_protocol_frozen.json", "FROZEN_PROTOCOL", "", "immutable"),
            ("PSC preregistration", ROOT / "docs/psc_phase1_preregistration.md", "FROZEN_PROTOCOL", "", "immutable"),
            ("current Chinese manuscript", CURRENT_MANUSCRIPT, "AUTHORITATIVE_MANUSCRIPT", "", "same-path integration; never create a duplicate 069 manuscript"),
            ("DIOR lineage audit", OUT / "069_dior_partial_gt_lineage_audit.csv", "AUTHORITATIVE_LINEAGE", "", "python scripts/m069_lineage_audit.py"),
            ("DOTA artifact manifest", OUT / "069_dota_clean_artifact_manifest.csv", "AUTHORITATIVE_LINEAGE", "", "python scripts/m069_lineage_audit.py"),
            ("one-click script", REPRO_SCRIPT, "REPRODUCTION_ENTRYPOINT", "", "source code"),
            ("strict final auditor", ROOT / "scripts/m069_freeze_and_repro.py", "REPRODUCTION_CODE", "", "source code"),
            ("one-click log", LOG_DIR / "reproduce_all_main_tables_069.log", "REPRODUCTION_LOG", "", "rerun one-click"),
        ]
    )
    for relpath in (
        "docs/m1_ar21_protocol_unification.md",
        "docs/m2_g2doubleprime_ar21_size_control.md",
        "docs/m3_image_level_risk_control.md",
        "docs/m4_risk_event_definition.md",
        "docs/m4_human_angle_annotation_audit.md",
        "docs/psc_phase1_preregistration.md",
        "docs/psc_phase1_radial_scaling_intervention.md",
        "docs/psc_phase1_split_gate_report.md",
        "docs/069_dior_partial_gt_lineage_resolution.md",
    ):
        entries.append((Path(relpath).name, ROOT / relpath, "AUTHORITATIVE_PROTOCOL_OR_DECISION", "", "reproduction chain or frozen protocol"))
    for relpath in (
        "scripts/m069_lineage_audit.py",
        "scripts/m1_ar21_unify.py",
        "scripts/m2_g2doubleprime_ar21.py",
        "scripts/recompute_m3_image_level_risk_control.py",
        "scripts/m3_image_level_risk.py",
        "scripts/derive_delta_theta_075.py",
        "scripts/m4_risk_events.py",
        "scripts/psc_phase1.py",
        "scripts/build_m4_human_annotation.py",
        "scripts/merge_m4_human_annotations.py",
        "scripts/analyze_m4_human_disagreement.py",
    ):
        entries.append((Path(relpath).name, ROOT / relpath, "REPRODUCTION_CODE", "", "source code"))
    annotation_tool = ROOT / "annotation_tools/m4_angle_annotation"
    for name in ("index.html", "angle_convention.md", "instructions.md", "annotatorA_tasks.csv", "annotatorB_tasks.csv"):
        entries.append((f"human annotation {name}", annotation_tool / name, "HUMAN_ANNOTATION_MACHINE_PACKAGE", "", "rebuild only before real labels exist"))
    for raw_name in ("annotatorA_raw.csv", "annotatorB_raw.csv"):
        raw_path = annotation_tool / raw_name
        if raw_path.is_file():
            entries.append((f"real human annotation {raw_name}", raw_path, "HUMAN_ANNOTATION_RAW_LABEL", "", "immutable after validated merge"))
    try:
        sampling_rows, _ = load_csv(REP / "m4_human_annotation_sampling_manifest.csv", {"anon_id", "crop_relpath", "crop_sha256"}, min_rows=600)
        for row in sampling_rows:
            entries.append((f"human crop {row['anon_id']}", annotation_tool / row["crop_relpath"], "HUMAN_ANNOTATION_CROP", "", "rebuild from SHA-bound source image and record"))
    except Exception as exc:
        setup_failures.append(f"annotation_inputs:{type(exc).__name__}:{exc}")
    for relpath in SPLIT_HASHES:
        entries.append((Path(relpath).name, ROOT / relpath, "FROZEN_SPLIT", "", "immutable"))
    for cell in FULLVAL_CELLS:
        matched, universe, manifest = fullval_source_paths(cell)
        entries.extend(
            [
                (f"fullval {cell} matched", matched, "VALIDATED_INPUT", "", "frozen checkpoint forward only"),
                (f"fullval {cell} universe", universe, "VALIDATED_INPUT", "", "frozen checkpoint forward only"),
                (f"fullval {cell} manifest", manifest, "VALIDATED_INPUT_MANIFEST", "", "source manifest"),
            ]
        )
    for cell, (relpath, _) in DOTA_DUMPS.items():
        entries.append((cell, ROOT / relpath, "VALIDATED_INPUT", "", "persisted clean full-val dump"))
    for dataset in PSC_EXPECTED:
        for seed in range(3):
            base = ROOT / "outputs/persistent_artifacts/m069_psc_phase1" / dataset / f"seed{seed}"
            for name, path, role in (
                (f"PSC {dataset} seed{seed} forward manifest", base / "manifest.json", "VALIDATED_INPUT_MANIFEST"),
                (f"PSC {dataset} seed{seed} radial source", base / "radial_full_evaluator.csv", "VALIDATED_INPUT"),
                (f"PSC {dataset} seed{seed} matched", base / "matched_phase.jsonl", "VALIDATED_INPUT"),
                (f"PSC {dataset} seed{seed} actual supplement manifest", base / "actual_head_loss_network_space_manifest.json", "VALIDATED_INPUT_MANIFEST"),
                (f"PSC {dataset} seed{seed} actual supplement", base / "actual_head_loss_network_space.csv", "VALIDATED_INPUT"),
            ):
                entries.append((name, path, role, "", "targeted frozen-checkpoint artifact"))
            for head in ("DCL", "CSL"):
                native = (
                    ROOT / "outputs/persistent_artifacts/m069_psc_phase1/native_signals"
                    / head / dataset / f"seed{seed}"
                )
                entries.extend(
                    [
                        (f"{head} {dataset} seed{seed} native manifest", native / "manifest.json", "VALIDATED_INPUT_MANIFEST", "", "targeted identity-only native endpoint"),
                        (f"{head} {dataset} seed{seed} native matched", native / "matched_native.jsonl", "VALIDATED_INPUT", "", "targeted identity-only native endpoint"),
                    ]
                )

    failures = list(setup_failures)
    rows = []
    seen: set[Path] = set()
    for topic, path, role, alias, can_recompute in entries:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            if not path.is_file() or path.stat().st_size <= 0:
                raise ValueError("missing or empty")
            if "/dev/shm" in str(resolved):
                raise ValueError("volatile /dev/shm path")
            rows.append(
                {
                    "topic": topic,
                    "artifact": str(path.relative_to(ROOT)),
                    "role": role,
                    "status": "VERIFIED",
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "canonical_path": str(path.relative_to(ROOT)),
                    "root_alias": alias,
                    "can_recompute": can_recompute,
                    "notes": "single canonical artifact; root report paths are symlinks, not copies",
                }
            )
        except Exception as exc:
            failure = f"{path}:{type(exc).__name__}:{exc}"
            failures.append(failure)
            rows.append(
                {
                    "topic": topic,
                    "artifact": str(path.relative_to(ROOT)),
                    "role": role,
                    "status": "FAILED_VALIDATION",
                    "sha256": "",
                    "bytes": path.stat().st_size if path.exists() else 0,
                    "canonical_path": str(path.relative_to(ROOT)),
                    "root_alias": alias,
                    "can_recompute": can_recompute,
                    "notes": failure,
                }
            )
    atomic_csv(
        OUT / "069_artifact_manifest.csv",
        [
            "topic", "artifact", "role", "status", "sha256", "bytes",
            "canonical_path", "root_alias", "can_recompute", "notes",
        ],
        rows,
    )
    audit.add(
        "reproduction",
        "069 authoritative artifact manifest",
        not failures,
        f"rows={len(rows)}; failures={failures}; path=reports/069_artifact_manifest.csv",
        artifact_sha256=sha256_file(OUT / "069_artifact_manifest.csv"),
    )


def write_takeover_task_status(decisions: dict[str, str], final_state: str) -> None:
    m2_status = (
        "FAILED_BY_PREREGISTERED_GATE"
        if decisions.get("m2") == "FAIL"
        else "VERIFIED_COMPLETE"
    )
    psc_status = (
        "FAILED_BY_PREREGISTERED_GATE"
        if decisions.get("psc") in {"FAIL", "DEADLINE"}
        else "VERIFIED_COMPLETE"
    )
    human_status = (
        "VERIFIED_COMPLETE"
        if decisions.get("human") == "COMPLETE"
        else "HUMAN_BLOCKED"
    )
    freeze_status = "VERIFIED_COMPLETE" if final_state == "FROZEN" else human_status
    rows = [
        ("M1 ar>=2.1 protocol unification", "VERIFIED_COMPLETE", "reports/m1_all_main_results_ar21.csv", "All primary rows use ar>=2.1; ar1.6/ar1.3 are sensitivity only."),
        ("M2 G2_double_prime", m2_status, "reports/m2_g2doubleprime_decision.csv", f"Preregistered decision={decisions.get('m2')}; a FAIL is complete evidence and demotes geometry score to appendix."),
        ("M3 image-level risk control", "VERIFIED_COMPLETE", "reports/m3_image_level_ltt.csv", "Complete-image bounded-loss HB LTT is the formal guarantee; instance-i.i.d. is audit-only."),
        ("geometry-normalized risk event", "VERIFIED_COMPLETE", "reports/m4_geometry_normalized_risk.csv", "Frozen first-crossing delta_theta_0.75 and ar>=2.1 lineage verified."),
        ("5/10/15 degree sensitivity", "VERIFIED_COMPLETE", "reports/m4_fixed_angle_sensitivity.csv", "Fixed-angle endpoints are sensitivity results; 5-degree results are noise-sensitive where specified."),
        ("real independent human double annotation", human_status, "reports/m4_human_annotation_disagreement.csv", "Machine package is complete; no labels are fabricated."),
        ("PSC Phase 1 radial scaling", "VERIFIED_COMPLETE", "reports/psc_phase1_radial_scaling.csv", "Original preregistered start/deadline retained; persisted intervention and actual-head supplement verified."),
        ("PSC Phase 1 preregistered analyses", "VERIFIED_COMPLETE", "reports/psc_phase1_score_comparison.csv", "Only preregistered analyses and frozen K2/native endpoints are used."),
        ("PSC split gate", psc_status, "reports/psc_phase1_split_gate_decision.csv", f"Terminal preregistered decision={decisions.get('psc')}; FAIL/DEADLINE closes the split branch without blocking the main protocol."),
        ("DOTA clean full-val", "VERIFIED_COMPLETE", "reports/k4b_dota_full_val_metrics.csv", "Exactly two clean full-val cells; DOTA#20 excluded."),
        ("one-click reproduction", "VERIFIED_COMPLETE", "logs/reproduce_all_main_tables_069.log", "Actual CPU-only end-to-end rebuild completed; historical K2/forward/DOTA artifacts were hash-revalidated rather than rerun."),
        ("submission freeze gate", freeze_status, "reports/069_submission_freeze_gate.csv", f"Final state={final_state}."),
        ("DIOR partial-GT lineage debt", "VERIFIED_COMPLETE", "reports/069_dior_partial_gt_lineage_audit.csv", "All formal DIOR reliability inputs are full-val; 052 partial/wrong-split values remain superseded only."),
        ("same-path Chinese manuscript integration", "VERIFIED_COMPLETE", "docs/paper_zh_post_k1k4_068/orientation_reliability_paper_zh.md", "Final M1/M2/M3/M4/PSC semantics are integrated into the existing 068 manuscript path; no duplicate paper version."),
        ("historical sentinel integrity audit", "VERIFIED_COMPLETE", "reports/069_final_reproduction_status.csv", "Completion was established from schema, values, normal-end logs, manifests and SHA-256, never sentinel existence alone."),
    ]
    atomic_csv(
        OUT / "069_takeover_task_status.csv",
        ["work_package", "status", "evidence", "authoritative_artifact", "notes"],
        [
            {
                "work_package": work_package,
                "status": status,
                "evidence": notes,
                "authoritative_artifact": artifact,
                "notes": "No duplicate namespace or repeated detector/K2 computation.",
            }
            for work_package, status, artifact, notes in rows
        ],
    )


def write_third_party_reproduction_doc(decisions: dict[str, str], final_state: str) -> None:
    human_text = (
        "complete and independently validated"
        if decisions.get("human") == "COMPLETE"
        else "HUMAN_BLOCKED: two real mutually blind annotation files have not been supplied"
    )
    text = f"""# Command 069 one-click reproduction

This is the authoritative collaborator-facing reproduction entry for 069-CONTINUATION.
It rebuilds CPU-only statistical tables from persistent, SHA-bound detector artifacts. It
does not train, run detector inference, rerun K2, change thresholds, or change D_cal/D_audit.

## Exact entry point

```bash
bash scripts/reproduce_all_main_tables.sh
```

There is no `--fast` formal mode. `--preflight-only` validates frozen assets and persisted
inputs but is not completion evidence.

## Covered outputs

1. M1 ar>=2.1 main results and ar1.6/ar1.3 sensitivity.
2. M2 fixed-size-bin G2_double_prime decision and intervals.
3. M3 complete-image bounded-loss HB LTT.
4. Secondary binary image event and instance-vs-image comparison.
5. Geometry-normalized severe event using frozen delta_theta_0.75.
6. Fixed 5/10/15 degree sensitivity.
7. Human disagreement analysis when two real label files exist; otherwise HUMAN_BLOCKED.
8. PSC Phase 1 radial intervention, preregistered analyses, and terminal split gate.
9. Two persisted DOTA clean full-val cells with DOTA#20 excluded.
10. DIOR full-val lineage and supersession of 052 partial/wrong-split values.
11. Frozen thresholds, D_cal/D_audit, host locks, and formal/exploratory scope checks.
12. Final reproduction status, artifact inventory, root report aliases, and submission gate.

## Authoritative lineage

Formal tables live in `top_journal_v3_reaudit_055/reports/`. Matching paths under
`reports/` are relative symlinks to that single historical-069 namespace, not copies.
Inputs are the persistent M069 A-F full-val matched/universe manifests, frozen K2 index,
PSC per-instance Phase 1 artifacts, targeted DCL/CSL native endpoints, and the two clean
DOTA full-val dumps. No formal table depends on `/dev/shm`.

The frozen M4 artifacts are SHA-256 `{M4_DELTA_JSON_SHA}` (definition),
`{M4_DELTA_CURVE_SHA}` (curve), and `{M4_DELTA_STABILITY_SHA}` (direct-solve audit).
PSC Phase 1 retains start `{PHASE1_START}` and deadline `{PHASE1_DEADLINE}`.

## Decisions from this run

- M1: `{decisions.get('m1')}`.
- M2: `{decisions.get('m2')}`; on FAIL, geometry score is appendix-only.
- M3: `{decisions.get('m3')}`; image is the formal exchangeable unit.
- PSC Phase 1 split gate: `{decisions.get('psc')}`.
- Human annotation: {human_text}.
- Submission freeze: `{final_state}`.

Detailed checks are in `reports/069_final_reproduction_status.csv`; the freeze decision is
in `reports/069_submission_freeze_gate.csv`; hashes and recomputation lineage are in
`reports/069_artifact_manifest.csv`.
"""
    atomic_text(ROOT / "docs/third_party_reproduction_log.md", text)


def write_continuation_log(decisions: dict[str, str], final_state: str, log_path: Path) -> None:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    human = decisions.get("human", "")
    lines = [
        f"[{timestamp}] command=069-CONTINUATION status=machine_chain_complete final_state={final_state}",
        "continuation_of=069-REPLACEMENT new_command_number=false duplicate_namespace=false",
        f"decisions=M1:{decisions.get('m1')},M2:{decisions.get('m2')},M3:{decisions.get('m3')},PSC:{decisions.get('psc')},human:{human}",
        f"phase1_start={PHASE1_START} phase1_deadline={PHASE1_DEADLINE}",
        f"thresholds_sha256={THRESHOLD_SHA} d_cal_d_audit_changed=false host_retrained=false k2_rerun=false detector_inference=false",
        f"one_click_log={log_path.relative_to(ROOT)} sha256={sha256_file(log_path)}",
        f"task_status=reports/069_takeover_task_status.csv sha256={sha256_file(OUT / '069_takeover_task_status.csv')}",
        f"artifact_manifest=reports/069_artifact_manifest.csv sha256={sha256_file(OUT / '069_artifact_manifest.csv')}",
        f"remaining_blocker={'none' if human == 'COMPLETE' else 'real independent mutually-blind human double annotation only'}",
        "next_formal_command=070",
    ]
    atomic_text(LOG_DIR / "069_codex_continuation.log", "\n".join(lines) + "\n")


def append_supervisor_continuation_record(decisions: dict[str, str], final_state: str) -> None:
    path = ROOT / "claude_code_and_supervisor.md"
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    start_marker = "<!-- CODEX_069_CONTINUATION_FINAL_START -->"
    end_marker = "<!-- CODEX_069_CONTINUATION_FINAL_END -->"
    record = f"""{start_marker}

## [{timestamp}] 069-CONTINUATION Codex 续跑收口

- 指令来源：用户 069-CONTINUATION；本轮续原 069，不占新编号，下一正式编号为 070。
- 执行动作：核验并复用历史 069 产物，仅补齐缺口；实际执行 CPU-only 一键复算与严格最终审计；原路径内更新现有 068 中文稿，未新建论文版本；未训练、未运行 detector inference、未重跑 K2、未新建重复命名空间。
- 决策：M1={decisions.get('m1')}；M2={decisions.get('m2')}（FAIL 时 geometry score 仅附录）；M3={decisions.get('m3')}；PSC Phase 1={decisions.get('psc')}；human={decisions.get('human')}；freeze={final_state}。
- 关键产物：`reports/069_final_reproduction_status.csv`、`reports/069_submission_freeze_gate.csv`、`reports/069_takeover_task_status.csv`、`reports/069_artifact_manifest.csv`、`logs/reproduce_all_main_tables_069.log`、`logs/069_codex_continuation.log`、`docs/third_party_reproduction_log.md`。
- 停止条件：M2 预注册门控若 FAIL 已按规则停止 geometry-specific 正文 claim；人工双标未完成时是唯一剩余 blocker，门控保持 NOT_FROZEN；PSC FAIL/DEADLINE 时停止拆篇但不阻塞主线。
- 冻结与合规：thresholds SHA-256=`{THRESHOLD_SHA}`；D_cal/D_audit 未变；host 未重训；formal/exploratory 未改；DOTA#20 排除；Phase 1 起止时间未重置。
- 下一步建议：仅在本 069 门控状态基础上进入正式命令 070；不得把缺失人工标签伪造为完成。

{end_marker}
"""
    existing = path.read_text(encoding="utf-8")
    if start_marker in existing:
        before, remainder = existing.split(start_marker, 1)
        if end_marker not in remainder:
            raise ValueError("unterminated existing 069 continuation supervisor record")
        _, after = remainder.split(end_marker, 1)
        updated = before.rstrip() + "\n\n" + record.rstrip() + after
    else:
        updated = existing.rstrip() + "\n\n---\n\n" + record
    atomic_text(path, updated.rstrip() + "\n")


def write_final_continuation_records(
    audit: Audit,
    decisions: dict[str, str],
    final_state: str,
    log_path: Path,
) -> None:
    try:
        write_takeover_task_status(decisions, final_state)
        write_third_party_reproduction_doc(decisions, final_state)
        write_continuation_log(decisions, final_state, log_path)
        append_supervisor_continuation_record(decisions, final_state)
        required = [
            OUT / "069_takeover_task_status.csv",
            OUT / "069_artifact_manifest.csv",
            ROOT / "docs/third_party_reproduction_log.md",
            LOG_DIR / "069_codex_continuation.log",
            ROOT / "claude_code_and_supervisor.md",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file() or path.stat().st_size <= 0]
        audit.add(
            "reproduction",
            "069 continuation task inventory and final project records",
            not missing,
            f"missing={missing}; task_rows={len(load_csv(OUT / '069_takeover_task_status.csv')[0])}; supervisor_marker=true",
            artifact_sha256=sha256_file(OUT / "069_takeover_task_status.csv"),
        )
    except Exception as exc:
        audit.add(
            "reproduction",
            "069 continuation task inventory and final project records",
            False,
            f"{type(exc).__name__}: {exc}",
        )


def check_reproduction_log(audit: Audit, log_path: Path) -> None:
    try:
        text = log_path.read_text(encoding="utf-8")
        required = {
            "REPRO_069_START",
            "STEP_OK lineage_artifact_verification",
            "STEP_OK preflight",
            "STEP_OK m4_delta_frozen_verify",
            "STEP_OK m1_ar21",
            "STEP_OK m2_fixed_size",
            "STEP_OK m3_image_level_ltt",
            "STEP_OK m4_risk_events",
            "STEP_OK psc_phase1_aggregation",
            "STEP_OK human_merge",
            "STEP_OK human_analysis",
            "REUSED_VERIFIED k2_angle_coder_matrix",
            "REUSED_VERIFIED psc_phase1_forward",
            "REUSED_VERIFIED psc_actual_head_supplement",
            "REUSED_VERIFIED dcl_csl_native_endpoints",
            "REUSED_VERIFIED dota_clean_fullval",
            "REUSED_VERIFIED dior_fullval_lineage",
            "REPRO_069_MACHINE_CHAIN_COMPLETE",
            "REPRO_069_MACHINE_LOG_SEALED",
        }
        missing = sorted(token for token in required if token not in text)
        audit.add("reproduction", "actual end-to-end machine-chain log", not missing, f"log={log_path.relative_to(ROOT)}; missing_markers={missing}", artifact_sha256=sha256_file(log_path))
    except Exception as exc:
        audit.add("reproduction", "actual end-to-end machine-chain log", False, exc)


def project_processes() -> list[str]:
    own = set()
    pid = os.getpid()
    while pid > 1 and pid not in own:
        own.add(pid)
        try:
            stat = (Path("/proc") / str(pid) / "stat").read_text().split()
            pid = int(stat[3])
        except Exception:
            break
    output = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True)
    patterns = re.compile(
        r"torchrun|dist_train|inference|evaluation|bootstrap|annotation.*server|"
        r"reproduce_all_main_tables|m069_fullval_reliability_dump|m069_psc_phase1_forward|"
        r"m069_psc_actual_loss_supplement|m069_psc_native_signal_dump|scripts/psc_phase1\.py|"
        r"scripts/m[1-4]_[^ ]+\.py|m069_lineage_audit|build_m4_human_annotation|"
        r"merge_m4_human_annotations|analyze_m4_human_disagreement",
        re.I,
    )
    found = []
    for line in output.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        process_pid, command = int(parts[0]), parts[1]
        if process_pid in own:
            continue
        if str(ROOT) in command and patterns.search(command):
            found.append(f"pid={process_pid} cmd={command}")
    return found


def check_snapshot_unchanged(audit: Audit, current: dict[str, str]) -> None:
    try:
        before = load_json(SNAPSHOT_JSON)
        changed = {key: (before.get(key), current.get(key)) for key in set(before) | set(current) if before.get(key) != current.get(key)}
        audit.add("frozen", "frozen assets unchanged during reproduction", not changed, f"changed={changed}; assets={len(current)}")
    except Exception as exc:
        audit.add("frozen", "frozen assets unchanged during reproduction", False, exc)


def preflight(log_path: Path) -> tuple[Audit, str]:
    audit = Audit("PREFLIGHT")
    snapshot = frozen_asset_snapshot(audit)
    check_shell_policy(audit)
    check_fullval_inputs(audit)
    check_dota_inputs(audit)
    check_k2_persisted(audit)
    check_psc_forward_inputs(audit)
    check_psc_actual_loss_supplements(audit)
    check_psc_native_endpoint_inputs(audit)
    check_dior_resolution(audit)
    human = check_human_machine_package(audit, final=False)
    atomic_json(SNAPSHOT_JSON, snapshot)
    final_state = "NOT_FROZEN"
    write_outputs(audit, final_state, decisions={"human": human}, phase_only=True)
    return audit, final_state


def final_audit(log_path: Path) -> tuple[Audit, str]:
    audit = Audit("FINAL")
    snapshot = frozen_asset_snapshot(audit)
    check_snapshot_unchanged(audit, snapshot)
    check_shell_policy(audit)
    check_fullval_inputs(audit)
    check_dota_inputs(audit)
    check_k2_persisted(audit)
    check_psc_forward_inputs(audit)
    check_psc_actual_loss_supplements(audit)
    check_psc_native_endpoint_inputs(audit)
    m1 = check_m1(audit)
    m2 = check_m2(audit)
    m3 = check_m3(audit, m2)
    check_m4(audit)
    human = check_human_machine_package(audit, final=True)
    psc = check_psc_persisted(audit, detailed=True)
    check_manuscript_semantics(audit, m2, human, psc)
    check_dior_resolution(audit)
    check_dota_outputs(audit)
    ensure_root_report_aliases(audit)
    write_authoritative_artifact_manifest(audit)
    check_no_dev_shm(audit)
    check_reproduction_log(audit, log_path)
    try:
        running = project_processes()
        audit.add("reproduction", "no active project computation after chain", not running, f"processes={running}")
    except Exception as exc:
        audit.add("reproduction", "no active project computation after chain", False, exc)

    decisions = {"m1": m1, "m2": m2, "m3": m3, "human": human, "psc": psc}
    preliminary_state = (
        "FROZEN" if not audit.machine_failures and human == "COMPLETE" else "NOT_FROZEN"
    )
    if not audit.machine_failures:
        write_final_continuation_records(audit, decisions, preliminary_state, log_path)
    final_state = "FROZEN" if not audit.machine_failures and human == "COMPLETE" else "NOT_FROZEN"
    write_outputs(
        audit,
        final_state,
        decisions=decisions,
        phase_only=False,
    )
    return audit, final_state


def scope_ok(audit: Audit, scope: str) -> bool:
    rows = [row for row in audit.rows if row.scope == scope]
    return bool(rows) and not any(row.status == "FAIL" for row in rows)


def write_outputs(
    audit: Audit,
    final_state: str,
    *,
    decisions: dict[str, str],
    phase_only: bool,
) -> None:
    status_fields = ["phase", "scope", "check", "status", "blocking", "evidence", "artifact_sha256"]
    atomic_csv(STATUS_CSV, status_fields, [asdict(row) for row in audit.rows])

    human_complete = decisions.get("human") == "COMPLETE"
    human_gate = gate_row(
        "human independent double annotation",
        human_complete,
        f"status={decisions.get('human')}",
        "collect and validate two real mutually-blind annotations",
    )
    if decisions.get("human") == "HUMAN_BLOCKED":
        human_gate["status"] = "HUMAN_BLOCKED"

    if phase_only:
        blockers = [row.check for row in audit.rows if row.blocking]
        gate = [
            {
                "condition": "PREFLIGHT",
                "status": "PASS" if not audit.machine_failures else "FAIL",
                "evidence": f"machine_failures={[row.check for row in audit.machine_failures]}",
                "blocking": bool(audit.machine_failures),
                "required_action": "resolve failed persisted-input or frozen-asset checks, then rerun",
            },
            {
                "condition": "FINAL",
                "status": "NOT_FROZEN",
                "evidence": f"preflight_only; blockers={blockers}",
                "blocking": True,
                "required_action": "run the complete one-click chain after preflight passes",
            },
        ]
    else:
        machine_ok = not audit.machine_failures
        gate = [
            gate_row("M1 ar>=2.1 unified", scope_ok(audit, "m1"), decisions.get("m1", ""), "fix M1 tables"),
            gate_row("M2 decided", scope_ok(audit, "m2") and decisions.get("m2") in {"PASS", "FAIL"}, f"decision={decisions.get('m2')}; geometry score remains a GT-fit upper-bound pending Deployable", "complete M2 decision"),
            gate_row("M3 image-level guarantee", scope_ok(audit, "m3"), f"decision={decisions.get('m3')}", "fix image-level LTT artifacts"),
            gate_row("geometry-normalized risk", scope_ok(audit, "m4"), "M4 geometry event and fixed-angle sensitivity", "fix M4 artifacts"),
            human_gate,
            gate_row("one-click reproduction", machine_ok, f"machine_failures={[row.check for row in audit.machine_failures]}", "resolve failing machine checks and rerun"),
            gate_row("PSC Phase 1 terminal decision", scope_ok(audit, "psc") and decisions.get("psc") in {"PASS", "FAIL", "DEADLINE"}, f"decision={decisions.get('psc')}; original deadline={PHASE1_DEADLINE}", "complete preregistered PSC artifacts or record DEADLINE"),
            gate_row("Chinese manuscript protocol integration", scope_ok(audit, "manuscript"), "same authoritative 068 path; no duplicate 069 paper", "integrate final M1/M2/M3/M4/PSC semantics into the current manuscript"),
            gate_row("DIOR full-val lineage", scope_ok(audit, "dior_lineage"), "partial-GT values must be superseded", "resolve DIOR lineage"),
            gate_row("frozen assets", scope_ok(audit, "frozen"), "thresholds/splits/hosts/scope/protocol", "restore frozen assets"),
        ]
        gate.append(
            {
                "condition": "FINAL",
                "status": final_state,
                "evidence": f"machine_ok={machine_ok}; human={decisions.get('human')}",
                "blocking": final_state != "FROZEN",
                "required_action": "none" if final_state == "FROZEN" else "resolve listed blocking conditions and rerun",
            }
        )
    atomic_csv(
        GATE_CSV,
        ["condition", "status", "evidence", "blocking", "required_action"],
        gate,
    )


def gate_row(condition: str, ok: bool, evidence: Any, action: str) -> dict[str, Any]:
    return {
        "condition": condition,
        "status": "PASS" if ok else "FAIL",
        "evidence": compact(evidence),
        "blocking": not ok,
        "required_action": "none" if ok else action,
    }


def failure_outputs(step: str, exit_code: int, log_path: Path) -> None:
    audit = Audit("FAILED_RUN")
    audit.add(
        "reproduction",
        "one-click machine chain",
        False,
        f"failed_step={step}; exit_code={exit_code}; log={log_path}",
    )
    write_outputs(audit, "NOT_FROZEN", decisions={}, phase_only=False)


def self_test() -> None:
    assert truth("True") and truth("1") and not truth("False")
    assert finite("0.0") and not finite("") and not finite("nan")
    start, deadline = parse_phase_timeline({"start": PHASE1_START, "deadline": PHASE1_DEADLINE})
    assert deadline - start == timedelta(days=42)
    try:
        parse_phase_timeline({"start": PHASE1_START, "deadline": "2026-08-24 20:14:39 -0700"})
    except ValueError:
        pass
    else:
        raise AssertionError("extended Phase 1 deadline was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "fixture.csv"
        atomic_csv(path, ["ar_threshold", "value"], [{"ar_threshold": 2.1, "value": 1}])
        rows, _ = load_csv(path, {"ar_threshold", "value"})
        assert all(same_number(row["ar_threshold"], 2.1) for row in rows)
        rows[0]["ar_threshold"] = "1.6"
        assert not all(same_number(row["ar_threshold"], 2.1) for row in rows)

    policy_audit = Audit("SELF_TEST")
    check_shell_policy(policy_audit)
    assert not policy_audit.machine_failures, policy_audit.machine_failures
    print("M069_FREEZE_REPRO_SELF_TEST_PASS")


def resolve_log(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--final", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--failure", metavar="STEP")
    parser.add_argument("--exit-code", type=int, default=1)
    parser.add_argument("--log", default="logs/reproduce_all_main_tables_069.log")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    log_path = resolve_log(args.log)

    if args.self_test:
        self_test()
        return 0
    if args.failure:
        failure_outputs(args.failure, args.exit_code, log_path)
        if not args.quiet:
            print(f"REPRO_STATUS NOT_FROZEN failed_step={args.failure}")
        return 0
    if args.preflight:
        audit, _ = preflight(log_path)
        if audit.machine_failures:
            print(f"PREFLIGHT_FAIL machine_failures={[row.check for row in audit.machine_failures]}")
            return 2
        print("PREFLIGHT_PASS")
        return 0

    audit, final_state = final_audit(log_path)
    if not args.quiet:
        print(
            f"FREEZE_GATE {final_state} machine_failures={[row.check for row in audit.machine_failures]}"
        )
    return 2 if audit.machine_failures else 0


if __name__ == "__main__":
    sys.exit(main())
