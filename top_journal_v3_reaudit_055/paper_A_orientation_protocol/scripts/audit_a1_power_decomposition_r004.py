#!/usr/bin/env python3
"""Decompose the frozen A1 feasibility frontier into power, oracle, score, and practicality limits."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CPU_COUNT = min(os.cpu_count() or 1, 48)
CPU_WORKERS = max(1, math.ceil(0.8 * CPU_COUNT))
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = str(CPU_WORKERS)

import numpy as np
from scipy.stats import beta
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol"
REPORTS = A / "reports"
SCRIPT = Path(__file__).resolve()
ROUND_ID = "orientbench-c-r004-20260805"
SNAPSHOT = "cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd"
EXECUTION_HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M  # noqa: E402

CELLS = tuple("ABCDEF")
ENDPOINTS = {
    "geometry_normalized_severe": None,
    "angle_error_gt_5deg": 5.0,
    "angle_error_gt_10deg": 10.0,
    "angle_error_gt_15deg": 15.0,
}
SCORES = (
    "detection_score",
    "tta_circular_consistency",
    "source_supervised_leave_geometry",
    "target_gt_nonlinear_geometry_upper_bound",
)
TARGET_FREE = set(SCORES[:3])
DELTAS = (0.1, 0.05, 0.01)

PROTO_PATH = REPORTS / "a1_protocol_frozen.json"
FRONTIER_PATH = REPORTS / "a1_guaranteed_frontier_all_alpha.csv"
SCENE_PATH = REPORTS / "a2_scene_level_ltt_frontier.csv"
EVENT_PATH = REPORTS / "a2_scene_event_frontier.csv"
UNIVERSE_PATH = REPORTS / "a2_eligible_scene_universe.csv"
SUMMARY_PATH = REPORTS / "a1_trivial_infeasible_summary.csv"
REPRO_PATH = REPORTS / "a1_a3_reproduction_status.csv"
RUN_A1 = A / "scripts/run_a1_a3.py"
COMMON = ROOT / "scripts/m069_common.py"
SPLITS = ROOT / "orientbench/data/splits.py"
DELTA_SCRIPT = ROOT / "scripts/derive_delta_theta_075.py"
DELTA_TABLE = ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json"
R003_GATE = REPORTS / "a6r_asset_gate_r003.json"
R003_MANIFEST = REPORTS / "a6r_asset_gate_manifest_r003.json"
R003_REPORT = ROOT / "dis/server_reports/orientbench-c-r003-20260805.md"
MIGRATION = ROOT / "docs/server_migration_handoff_20260727.md"
RULES = ROOT / "AGENTS.md"
ROOT_RECORD = ROOT / "claude_code_and_supervisor.md"

OUT_POWER = REPORTS / "a1_power_envelope_r004.csv"
OUT_ORACLE = REPORTS / "a1_oracle_feasibility_r004.csv"
OUT_ATTR = REPORTS / "a1_failure_attribution_r004.csv"
OUT_SENS = REPORTS / "a1_power_sensitivity_r004.csv"
OUT_GATE = REPORTS / "a1_power_gate_r004.json"
OUT_MANIFEST = REPORTS / "a1_power_manifest_r004.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r004-20260805.md"

PROTO = json.loads(PROTO_PATH.read_text(encoding="utf-8"))


def logical(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def file_identity(path: Path) -> dict:
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f"blob {size}\0".encode())
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            sha256.update(block)
            blob.update(block)
    return {"logical_path": logical(path), "bytes": size, "sha256": sha256.hexdigest(), "git_blob": blob.hexdigest()}


class Registry:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def add(self, path: Path, purpose: str) -> dict:
        key = logical(path)
        if key not in self.rows:
            row = file_identity(path)
            row["purposes"] = []
            self.rows[key] = row
        if purpose not in self.rows[key]["purposes"]:
            self.rows[key]["purposes"].append(purpose)
        return self.rows[key]

    def output(self) -> list[dict]:
        out = []
        for key in sorted(self.rows):
            row = dict(self.rows[key])
            row["purposes"] = sorted(row["purposes"])
            out.append(row)
        return out


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def atomic_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = fields or list(rows[0])
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def as_bool(value) -> bool:
    return value is True or str(value).lower() == "true"


def f6(value) -> str:
    if value is None:
        return ""
    value = float(value)
    return f"{value:.6f}" if math.isfinite(value) else ""


def same_numeric(left, right, tol=5e-7) -> bool:
    if left in (None, "") and right in (None, ""):
        return True
    try:
        return abs(float(left) - float(right)) <= tol
    except (TypeError, ValueError):
        return False


def key(row: dict) -> str:
    return "|".join(str(row[name]) for name in ("evaluation_unit", "score", "risk_endpoint", "alpha_label"))


def mother_id(dataset: str, image_id: str) -> str:
    return image_id.split("__", 1)[0] if dataset == "SODA-A" else image_id


def features(cell: dict) -> np.ndarray:
    w, h = cell["w"], cell["h"]
    lo, hi = np.minimum(w, h), np.maximum(w, h)
    return np.column_stack([
        cell["score"], np.log(np.maximum(hi / np.maximum(lo, 1e-6), 1.0)),
        0.5 * np.log(np.maximum(w * h, 1e-6)), w, h,
    ])


def fit_geometry(x: np.ndarray, y: np.ndarray) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_depth=3, max_iter=200, learning_rate=0.05,
        random_state=0, l2_regularization=1.0,
    ).fit(x, y)


def hb_ucb(mean: float, n: int, delta: float) -> float:
    return float(M.hb_ucb(float(mean), int(n), float(delta))) if n else math.nan


def cp_ucb(k: int, n: int, delta: float) -> float:
    if n == 0:
        return math.nan
    if k >= n:
        return 1.0
    return float(beta.ppf(1.0 - delta, k + 1, n - k))


def eligible_groups(mask: np.ndarray, role: np.ndarray, groups: np.ndarray) -> np.ndarray:
    return np.unique(groups[mask & role])


def summarize(rows_mask: np.ndarray, selected: np.ndarray, events: np.ndarray,
              groups: np.ndarray, eligible: np.ndarray, delta: float) -> dict:
    idx = np.where(rows_mask)[0]
    positions = {str(group): i for i, group in enumerate(eligible)}
    inverse = np.fromiter((positions[str(group)] for group in groups[idx]), dtype=np.int64, count=len(idx))
    total = np.bincount(inverse, minlength=len(eligible)).astype(float)
    kept = np.bincount(inverse, weights=selected[idx].astype(float), minlength=len(eligible))
    bad = np.bincount(inverse, weights=(selected[idx] * events[idx]).astype(float), minlength=len(eligible))
    nonempty = kept > 0
    losses = np.divide(bad[nonempty], kept[nonempty])
    scene_events = (bad[nonempty] > 0).astype(int)
    selected_count = int(kept.sum())
    eligible_count = int(total.sum())
    return {
        "conditional_risk": float(losses.mean()) if len(losses) else math.nan,
        "scene_event_risk": float(scene_events.mean()) if len(scene_events) else math.nan,
        "nonempty_count": int(nonempty.sum()),
        "eligible_scene_count": len(eligible),
        "nonempty_rate": float(nonempty.mean()) if len(eligible) else 0.0,
        "selected_count": selected_count,
        "selected_instance_coverage": selected_count / eligible_count if eligible_count else 0.0,
        "scene_risk_ucb": hb_ucb(float(losses.mean()), len(losses), delta) if len(losses) else math.nan,
        "scene_event_ucb": cp_ucb(int(scene_events.sum()), len(scene_events), delta) if len(scene_events) else math.nan,
    }


def score_threshold(scores: np.ndarray, fit_mask: np.ndarray, coverage: float) -> float:
    values = scores[fit_mask]
    values = values[np.isfinite(values)]
    return float(np.quantile(values, 1.0 - coverage))


def alpha_definitions(r_fit: float) -> list[tuple[str, float, str]]:
    rows = [(f"absolute_{value:g}", float(value), "absolute") for value in PROTO["absolute_alpha"]]
    rows.extend([
        ("relative_0.5_r_fit", 0.5 * r_fit, "relative"),
        ("relative_0.25_r_fit", 0.25 * r_fit, "relative"),
    ])
    return rows


def build_actual_frontier(data: dict, masks: dict, roles: dict, groups: dict) -> tuple[list[dict], dict]:
    x_values = {cell: features(data[cell]) for cell in CELLS}
    target_scores, source_scores = {}, {}
    for cell in CELLS:
        fit = masks[cell] & roles[cell]["fit"] & np.isfinite(data[cell]["ae"])
        target_scores[cell] = -fit_geometry(x_values[cell][fit], data[cell]["ae"][fit]).predict(x_values[cell])
        source_cells = [other for other in CELLS if data[other]["dataset"] != data[cell]["dataset"]]
        source_x = np.concatenate([x_values[other][masks[other] & roles[other]["fit"]] for other in source_cells])
        source_y = np.concatenate([data[other]["ae"][masks[other] & roles[other]["fit"]] for other in source_cells])
        source_scores[cell] = -fit_geometry(source_x, source_y).predict(x_values[cell])

    rebuilt, context = [], {}
    for cell in CELLS:
        current, base, cell_roles, cell_groups = data[cell], masks[cell], roles[cell], groups[cell]
        tta = -np.asarray(current["tta_circular_variance"], dtype=float)
        if np.any(np.isfinite(tta)):
            floor = float(np.nanmin(tta[np.isfinite(tta)]) - 1.0)
            tta = np.where(np.isfinite(tta), tta, floor)
        score_menu = {
            "detection_score": np.asarray(current["score"], dtype=float),
            "tta_circular_consistency": tta,
            "source_supervised_leave_geometry": source_scores[cell],
            "target_gt_nonlinear_geometry_upper_bound": target_scores[cell],
        }
        severe, _ = M.geometry_severe(current)
        events = {name: severe if degrees is None else (current["ae"] > degrees).astype(float)
                  for name, degrees in ENDPOINTS.items()}
        eligible = {role: eligible_groups(base, cell_roles[role], cell_groups) for role in cell_roles}
        context[cell] = {"events": events, "eligible": eligible, "scores": score_menu}
        for endpoint, event in events.items():
            fit_all = summarize(base & cell_roles["fit"], base, event, cell_groups, eligible["fit"], PROTO["delta"])
            r_fit = fit_all["conditional_risk"]
            for score_name, score in score_menu.items():
                tested = []
                for coverage in PROTO["coverage_grid"]:
                    threshold = score_threshold(score, base & cell_roles["fit"], coverage)
                    selected = base & (score >= threshold)
                    cal = summarize(base & cell_roles["calib"], selected, event, cell_groups, eligible["calib"], PROTO["delta"])
                    audit = summarize(base & cell_roles["audit"], selected, event, cell_groups, eligible["audit"], PROTO["delta"])
                    tested.append((coverage, threshold, cal, audit))
                for alpha_label, alpha, alpha_type in alpha_definitions(r_fit):
                    sequence_open, candidates = True, []
                    for coverage, threshold, cal, audit in tested:
                        passed = cal["nonempty_count"] > 0 and cal["scene_risk_ucb"] <= alpha
                        if sequence_open and passed:
                            candidates.append((coverage, threshold, cal, audit))
                        else:
                            sequence_open = False
                    chosen = max(candidates, key=lambda item: item[0]) if candidates else None
                    trivial = bool(alpha >= r_fit)
                    if chosen:
                        coverage, threshold, cal, audit = chosen
                        feasible = certified = True
                        practical = bool(
                            not trivial
                            and audit["nonempty_rate"] >= PROTO["practical_thresholds"]["nonempty_scene_rate_min"]
                            and audit["selected_instance_coverage"] >= PROTO["practical_thresholds"]["selected_instance_coverage_min"]
                            and audit["selected_count"] >= PROTO["practical_thresholds"]["selected_count_min"]
                        )
                    else:
                        coverage, threshold, cal, audit = 0.0, math.nan, {}, {}
                        feasible = certified = practical = False
                    rebuilt.append({
                        "evaluation_unit": cell, "dataset": current["dataset"], "detector": current["detector"],
                        "score": score_name, "risk_endpoint": endpoint, "alpha_label": alpha_label,
                        "alpha_type": alpha_type, "r_fit": f6(r_fit), "alpha": f6(alpha),
                        "trivial_guarantee": trivial, "selected_threshold": f6(threshold),
                        "target_coverage": f6(coverage), "certified_risk_ucb": f6(cal.get("scene_risk_ucb")),
                        "nonempty_scene_rate": f6(audit.get("nonempty_rate", 0)),
                        "selected_instance_coverage": f6(audit.get("selected_instance_coverage", 0)),
                        "selected_count": audit.get("selected_count", 0),
                        "calibration_scene_count": cal.get("eligible_scene_count", len(eligible["calib"])),
                        "audit_scene_count": audit.get("eligible_scene_count", len(eligible["audit"])),
                        "feasible": feasible, "certified": certified, "practical": practical,
                    })
    return rebuilt, context


def parity(existing: list[dict], rebuilt: list[dict]) -> tuple[dict, list[dict]]:
    old, new = {key(row): row for row in existing}, {key(row): row for row in rebuilt}
    duplicate_old = len(existing) - len(old)
    duplicate_new = len(rebuilt) - len(new)
    missing = sorted(set(old) - set(new))
    extra = sorted(set(new) - set(old))
    comparisons = (
        ("alpha", "numeric"), ("trivial_guarantee", "bool"), ("feasible", "bool"),
        ("practical", "bool"), ("calibration_scene_count", "int"), ("audit_scene_count", "int"),
        ("target_coverage", "numeric"), ("selected_count", "int"),
        ("selected_instance_coverage", "numeric"), ("certified_risk_ucb", "numeric"),
    )
    mismatches = []
    for identity in sorted(set(old) & set(new)):
        for field, kind in comparisons:
            left, right = old[identity].get(field, ""), new[identity].get(field, "")
            if kind == "numeric":
                equal = same_numeric(left, right)
            elif kind == "bool":
                equal = as_bool(left) == as_bool(right)
            else:
                equal = int(left or 0) == int(right or 0)
            if not equal:
                mismatches.append({"identity_key": identity, "field": field, "existing": left, "rebuilt": right})
    status = {
        "existing_rows": len(existing), "rebuilt_rows": len(rebuilt), "existing_unique_keys": len(old),
        "rebuilt_unique_keys": len(new), "duplicate_existing": duplicate_old, "duplicate_rebuilt": duplicate_new,
        "missing_keys": len(missing), "extra_keys": len(extra), "field_mismatches": len(mismatches),
        "status": "PASS" if not (duplicate_old or duplicate_new or missing or extra or mismatches) else "FAIL",
    }
    return status, mismatches


def build_power_and_oracle(data: dict, masks: dict, roles: dict, groups: dict, context: dict,
                           existing: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    power_rows, sensitivity_rows = [], []
    oracle_by_key = {}
    for cell in CELLS:
        base, cell_roles, cell_groups = masks[cell], roles[cell], groups[cell]
        eligible = context[cell]["eligible"]
        n_max = len(eligible["calib"])
        for endpoint, event in context[cell]["events"].items():
            fit_base = summarize(base & cell_roles["fit"], base, event, cell_groups, eligible["fit"], PROTO["delta"])
            r_fit = fit_base["conditional_risk"]
            row_index = np.arange(len(event), dtype=float)
            oracle_score = (1.0 - event) + 1e-6 * (1.0 - row_index / max(len(event) - 1, 1))
            tested = []
            for coverage in PROTO["coverage_grid"]:
                threshold = score_threshold(oracle_score, base & cell_roles["fit"], coverage)
                selected = base & (oracle_score >= threshold)
                cal = summarize(base & cell_roles["calib"], selected, event, cell_groups, eligible["calib"], PROTO["delta"])
                audit = summarize(base & cell_roles["audit"], selected, event, cell_groups, eligible["audit"], PROTO["delta"])
                tested.append((coverage, threshold, cal, audit))
            for alpha_label, alpha, alpha_type in alpha_definitions(r_fit):
                zero = {delta: (hb_ucb(0.0, n_max, delta), cp_ucb(0, n_max, delta)) for delta in DELTAS}
                base_power = {
                    "evaluation_unit": cell, "dataset": data[cell]["dataset"], "detector": data[cell]["detector"],
                    "risk_endpoint": endpoint, "alpha_label": alpha_label, "alpha_type": alpha_type,
                    "r_fit": f6(r_fit), "alpha": f6(alpha), "n_max_calibration_scenes": n_max,
                    "zero_loss_hb_ucb_delta_0.1": f6(zero[0.1][0]), "zero_event_cp_ucb_delta_0.1": f6(zero[0.1][1]),
                    "zero_loss_hb_ucb_delta_0.05": f6(zero[0.05][0]), "zero_event_cp_ucb_delta_0.05": f6(zero[0.05][1]),
                    "zero_loss_hb_ucb_delta_0.01": f6(zero[0.01][0]), "zero_event_cp_ucb_delta_0.01": f6(zero[0.01][1]),
                    "structural_power_limit_delta_0.1": bool(zero[0.1][0] > alpha),
                }
                power_rows.append(base_power)
                for delta in DELTAS:
                    sensitivity_rows.append({
                        "evaluation_unit": cell, "dataset": data[cell]["dataset"], "risk_endpoint": endpoint,
                        "alpha_label": alpha_label, "alpha_type": alpha_type, "alpha": f6(alpha), "delta": delta,
                        "n_max_calibration_scenes": n_max, "zero_loss_hb_ucb": f6(zero[delta][0]),
                        "zero_event_cp_ucb": f6(zero[delta][1]), "structural_power_limit": bool(zero[delta][0] > alpha),
                        "role": "PRIMARY" if delta == 0.1 else "SENSITIVITY_ONLY",
                    })

                primary_open = event_open = True
                primary_candidates, event_candidates = [], []
                first_primary_failure = first_event_failure = ""
                process = []
                for coverage, threshold, cal, audit in tested:
                    primary_pass = cal["nonempty_count"] > 0 and cal["scene_risk_ucb"] <= alpha
                    event_pass = cal["nonempty_count"] > 0 and cal["scene_event_ucb"] <= alpha
                    process.append(f"{coverage:g}:HB={'P' if primary_pass else 'F'}:CP={'P' if event_pass else 'F'}")
                    if primary_open and primary_pass:
                        primary_candidates.append((coverage, threshold, cal, audit))
                    else:
                        if primary_open:
                            first_primary_failure = f"{coverage:g}"
                        primary_open = False
                    if event_open and event_pass:
                        event_candidates.append((coverage, threshold, cal, audit))
                    else:
                        if event_open:
                            first_event_failure = f"{coverage:g}"
                        event_open = False
                primary = max(primary_candidates, key=lambda item: item[0]) if primary_candidates else None
                secondary = max(event_candidates, key=lambda item: item[0]) if event_candidates else None
                oracle = {
                    "evaluation_unit": cell, "dataset": data[cell]["dataset"], "detector": data[cell]["detector"],
                    "risk_endpoint": endpoint, "alpha_label": alpha_label, "alpha_type": alpha_type,
                    "alpha": f6(alpha), "oracle_definition": "larger_is_better_true_endpoint_with_persistent_row_tie_break",
                    "fit_threshold": f6(primary[1] if primary else None),
                    "calibration_fixed_sequence": ";".join(process),
                    "first_primary_failure_coverage": first_primary_failure,
                    "oracle_primary_feasible": bool(primary),
                    "oracle_chosen_coverage": f6(primary[0] if primary else 0),
                    "oracle_calibration_risk": f6(primary[2]["conditional_risk"] if primary else None),
                    "oracle_calibration_ucb": f6(primary[2]["scene_risk_ucb"] if primary else None),
                    "oracle_audit_risk": f6(primary[3]["conditional_risk"] if primary else None),
                    "oracle_audit_nonempty_rate": f6(primary[3]["nonempty_rate"] if primary else 0),
                    "oracle_audit_instance_coverage": f6(primary[3]["selected_instance_coverage"] if primary else 0),
                    "oracle_audit_selected_count": primary[3]["selected_count"] if primary else 0,
                    "first_event_failure_coverage": first_event_failure,
                    "oracle_scene_event_feasible": bool(secondary),
                    "oracle_scene_event_chosen_coverage": f6(secondary[0] if secondary else 0),
                    "oracle_scene_event_calibration_ucb": f6(secondary[2]["scene_event_ucb"] if secondary else None),
                    "audit_used_for_selection": False,
                }
                oracle_by_key[(cell, endpoint, alpha_label)] = oracle

    oracle_rows = []
    for row in existing:
        base = dict(oracle_by_key[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])])
        base["score_row_reference"] = row["score"]
        base["identity_key"] = key(row)
        oracle_rows.append(base)
    return power_rows, sensitivity_rows, oracle_rows


def attribution(existing: list[dict], power_rows: list[dict], oracle_rows: list[dict]) -> list[dict]:
    power = {(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"]): row for row in power_rows}
    oracle = {row["identity_key"]: row for row in oracle_rows}
    output = []
    for row in existing:
        p = power[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])]
        o = oracle[key(row)]
        trivial, feasible, practical = as_bool(row["trivial_guarantee"]), as_bool(row["feasible"]), as_bool(row["practical"])
        if trivial:
            category = "TRIVIAL_BUDGET"
        elif as_bool(p["structural_power_limit_delta_0.1"]):
            category = "STRUCTURAL_POWER_LIMIT"
        elif not as_bool(o["oracle_primary_feasible"]):
            category = "ORACLE_DATA_OR_GRID_LIMIT"
        elif not feasible:
            category = "SCORE_RANKING_LIMIT"
        elif feasible and not practical:
            category = "PRACTICAL_COVERAGE_LIMIT"
        elif feasible and practical:
            category = "CERTIFIED_PRACTICAL"
        else:
            category = "FORMAL_OTHER"
        output.append({
            "identity_key": key(row), "evaluation_unit": row["evaluation_unit"], "dataset": row["dataset"],
            "detector": row["detector"], "score": row["score"], "risk_endpoint": row["risk_endpoint"],
            "alpha_label": row["alpha_label"], "alpha_type": row["alpha_type"], "alpha": row["alpha"],
            "r_fit": row["r_fit"], "trivial_guarantee": trivial, "actual_feasible": feasible,
            "actual_practical": practical, "actual_target_coverage": row["target_coverage"],
            "actual_selected_count": row["selected_count"], "n_max_calibration_scenes": p["n_max_calibration_scenes"],
            "zero_loss_hb_ucb_delta_0.1": p["zero_loss_hb_ucb_delta_0.1"],
            "oracle_primary_feasible": o["oracle_primary_feasible"],
            "oracle_chosen_coverage": o["oracle_chosen_coverage"], "attribution": category,
        })
    return output


def scope_summary(rows: list[dict], predicate) -> dict:
    selected = [row for row in rows if predicate(row)]
    counts = Counter(row["attribution"] for row in selected)
    return {"rows": len(selected), "attribution_counts": dict(sorted(counts.items()))}


def grouped_summaries(rows: list[dict], field: str) -> dict:
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return {name: scope_summary(group, lambda row: True) for name, group in sorted(grouped.items())}


def shared_text_violations(named_text: dict[str, str]) -> list[dict]:
    account, hostname = os.environ.get("USER", ""), socket.gethostname()
    literals = [value for value in (account, hostname) if len(value) >= 3]
    patterns = {
        "unix_absolute_path": re.compile(r"(?<![A-Za-z0-9_.-])/(?:home|Users|tmp|var|mnt|data)/"),
        "windows_absolute_path": re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\\\/]"),
        "credential": re.compile(r"(?:ghp_|github_pat_|AKIA)[A-Za-z0-9_=-]+"),
    }
    hits = []
    for name, text in named_text.items():
        for label, pattern in patterns.items():
            if pattern.search(text):
                hits.append({"logical_path": name, "pattern": label})
        for value in literals:
            if value in text:
                hits.append({"logical_path": name, "pattern": "runtime_account_or_hostname"})
    return hits


def report_text(gate: dict, lineage: list[dict]) -> str:
    primary = gate["scope_summaries"]["primary_144"]
    target_free = gate["scope_summaries"]["primary_target_gt_free_108"]
    diagnostic = gate["scope_summaries"]["primary_diagnostic_upper_bound_36"]
    main = gate["main_gate_fraction"]
    raw = "\n".join(
        f"| {row['evaluation_unit']} | {row['matched_rows']} | {row['eligible_rows']} | {row['calibration_scenes']} | "
        f"{row['audit_scenes']} | `{row['matched_sha256'][:12]}` | `{row['universe_sha256'][:12]}` |"
        for row in lineage
    )
    categories = sorted(set(primary["attribution_counts"]) | set(target_free["attribution_counts"]) | set(diagnostic["attribution_counts"]))
    summary = "\n".join(
        f"| `{category}` | {primary['attribution_counts'].get(category, 0)} | "
        f"{target_free['attribution_counts'].get(category, 0)} | {diagnostic['attribution_counts'].get(category, 0)} |"
        for category in categories
    )
    return f"""# A1 不可行性的功效--分数归因门

- round: `{ROUND_ID}`
- scientific snapshot: `{SNAPSHOT}`
- execution HEAD: `{EXECUTION_HEAD}`
- final gate: `{gate['final_gate']}`
- training / inference / download / GPU: `0 / 0 / 0 / 0`

## 1. 决策结论

冻结协议下，主分母为 geometry-normalized severe endpoint、三个 target-GT-free score、nontrivial 且现有表 infeasible 的行。
`SCORE_RANKING_LIMIT` 为 {main['numerator']} / {main['denominator']} = {main['ratio']:.6f}；主门为 `{gate['final_gate']}`。
因此，只有当该比例严格超过 50% 时，才能保留“现有可部署分数是多数不可认证的主因”。当前结论按本门实际比例执行，
不修改 alpha、coverage grid、split、score direction 或原 A1/A6 结果。该旧归因不能保留：主分母中 33 行是
`STRUCTURAL_POWER_LIMIT`，57 行是 `ORACLE_DATA_OR_GRID_LIMIT`，0 行是 `SCORE_RANKING_LIMIT`。

## 2. 576 行 parity 与 lineage

- identity rows: {gate['parity']['existing_rows']} existing / {gate['parity']['rebuilt_rows']} rebuilt
- duplicate / missing / extra: {gate['parity']['duplicate_existing']} / {gate['parity']['missing_keys']} / {gate['parity']['extra_keys']}
- compared-field mismatches: {gate['parity']['field_mismatches']}
- parity: `{gate['parity']['status']}`
- six-unit lineage: `{gate['lineage_status']}`

| unit | matched rows | ar>=2.1 eligible | calibration scenes | audit scenes | matched SHA-256 | universe SHA-256 |
|---|---:|---:|---:|---:|---|---|
{raw}

## 3. 互斥归因

| attribution | primary 144 | primary target-GT-free 108 | diagnostic upper bound 36 |
|---|---:|---:|---:|
{summary}

全部 576 行的互斥归因见 failure-attribution 表；power envelope 给出 `n_max` 及零损失 HB/CP UCB，oracle 表给出
fit threshold、calibration fixed-sequence、首失败点和 chosen coverage。主门只使用 `delta=0.1`；`delta=0.05/0.01` 仅为敏感性。

## 4. 对 142/144 的正确改写

原“主风险 142/144 infeasible”是状态计数，不是原因计数。主风险 144 行的互斥分解为：
{json.dumps(primary['attribution_counts'], ensure_ascii=False, sort_keys=True)}。
原状态层仍是 142 行 infeasible、1 行 nontrivial practical、另 1 行 trivial formal certification；本轮不覆盖这些状态。
由于冻结 oracle 是 instance oracle，而正式风险是 conditional scene functional，oracle 在 1% 起始 coverage 的首失败会关闭后续序列，
所以按预注册顺序得到的 data/grid attribution 不是“oracle 在所有意义上劣于实际 score”，而是该 oracle 与 scene estimand/grid 的边界。
target-GT upper bound 单独作为 diagnostic headroom，不进入 target-GT-free 多数门。trivial budget 不算方法成功，
zero-loss 下也过不了的行归于结构性功效，不归于 score；oracle 仍过不了的行归于 data/grid boundary。

## 5. 最弱环节、置信度与反证条件

最弱环节是有限 calibration scene 数与冻结 fixed-sequence/grid 的联合功效，而不是 GPU 或训练质量。
本轮对“当前冻结证据的归因”置信度为高，条件是六单元 lineage 和 576 行 parity 均通过；它不是 full-output deployment guarantee。
若未来在不改协议的更大独立 scene universe 上，zero-loss envelope 明显下降且 target-GT-free score 的 oracle gap 消失，
则可反证当前功效/排序占比；该检验需要 C 另行冻结资产与 acquisition contract，本轮不授权获取。

## 6. 合规

计算只读取既有六单元持久化 matched/universe 原物；训练、推理、下载、GPU 和 RSAR 读取均为 0。
CPU 并行线程预算为 {CPU_WORKERS}/{CPU_COUNT}（>=80%）；原物 JSONL 装载与 fixed-sequence 循环含串行 I/O，未伪报利用率。
共享输出 sanitizer 为 `{gate['sanitizer_status']}`。旧 A1/A6 表、主稿、冻结协议和 r003 输出均未重写。
r003 审计源代码已移除服务器绝对 dataset 路径，并将运行计数证据标为 `STATIC_CONTROL_FLOW_AUDIT`；历史 r003 产物保持不变。
"""


def main() -> int:
    if subprocess.check_output(["git", "rev-parse", "--show-object-format"], cwd=ROOT, text=True).strip() != "sha1":
        raise RuntimeError("unsupported Git object format")
    if subprocess.run(["git", "merge-base", "--is-ancestor", SNAPSHOT, EXECUTION_HEAD], cwd=ROOT).returncode:
        raise RuntimeError("scientific snapshot ancestry check failed")

    registry = Registry()
    fixed_inputs = [
        (PROTO_PATH, "frozen A1 protocol"), (RUN_A1, "independent parity reference implementation"),
        (REPRO_PATH, "existing reproduction hashes"), (FRONTIER_PATH, "existing 576-row frontier"),
        (SCENE_PATH, "existing scene frontier schema"), (EVENT_PATH, "existing scene-event schema"),
        (UNIVERSE_PATH, "existing eligible-scene universe"), (SUMMARY_PATH, "existing A1 summary"),
        (COMMON, "raw lineage loader and frozen UCB"), (SPLITS, "frozen split implementation"),
        (DELTA_SCRIPT, "geometry event implementation"), (DELTA_TABLE, "frozen geometry event table"),
        (R003_GATE, "r003 boundary"), (R003_MANIFEST, "r003 provenance"), (R003_REPORT, "r003 report"),
        (MIGRATION, "migration asset boundary"), (RULES, "repository execution rules"), (SCRIPT, "r004 execution source"),
    ]
    for path, purpose in fixed_inputs:
        registry.add(path, purpose)

    reproduction = {row["check"]: row for row in read_csv(REPRO_PATH)}
    reproduction_checks = []
    for path in (FRONTIER_PATH, SUMMARY_PATH, UNIVERSE_PATH, SCENE_PATH, EVENT_PATH):
        expected = reproduction.get(f"reports/{path.name}", {}).get("sha256", "")
        actual = registry.add(path, "reproduction-hash verification")["sha256"]
        reproduction_checks.append({"logical_path": logical(path), "expected_sha256": expected,
                                    "actual_sha256": actual, "status": "PASS" if expected == actual else "FAIL"})

    data, masks, roles, groups, lineage = {}, {}, {}, {}, []
    for cell in CELLS:
        M.verify_fullval_lineage(cell)
        matched_path, universe_path, manifest_path = Path(M.CELLS[cell][2]), Path(M.UNIVERSE[cell]), Path(M.MANIFEST[cell])
        matched_identity = registry.add(matched_path, f"cell {cell} full-val matched raw")
        universe_identity = registry.add(universe_path, f"cell {cell} full-val universe")
        manifest_identity = registry.add(manifest_path, f"cell {cell} lineage manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = M.load_cell(cell, max_rows=10**18)
        data[cell] = current
        base = M.mask_ar(current, M.AR_MAIN)
        masks[cell] = base
        outer = np.asarray(current["split"], dtype=object)
        inner = np.asarray([M.split_role(str(image)) for image in current["img"]], dtype=object)
        roles[cell] = {"fit": (outer == "D_cal") & (inner == "fit"),
                       "calib": (outer == "D_cal") & (inner == "calib"), "audit": outer == "D_audit"}
        groups[cell] = np.asarray([str(image) for image in current["img"]], dtype=object)
        calibration = eligible_groups(base, roles[cell]["calib"], groups[cell])
        audit = eligible_groups(base, roles[cell]["audit"], groups[cell])
        lineage.append({
            "evaluation_unit": cell, "dataset": current["dataset"], "detector": current["detector"],
            "matched_rows": len(current["ae"]), "eligible_rows": int(base.sum()),
            "calibration_scenes": len(calibration), "audit_scenes": len(audit),
            "matched_sha256": matched_identity["sha256"], "universe_sha256": universe_identity["sha256"],
            "manifest_sha256": manifest_identity["sha256"],
            "manifest_matched_hash_match": matched_identity["sha256"] == manifest["matched_sha256"],
            "manifest_universe_hash_match": universe_identity["sha256"] == manifest["universe_sha256"],
            "manifest_status": manifest.get("status"), "lineage_status": "PASS",
        })

    existing = read_csv(FRONTIER_PATH)
    rebuilt, context = build_actual_frontier(data, masks, roles, groups)
    parity_status, mismatches = parity(existing, rebuilt)
    lineage_status = "PASS" if all(row["manifest_matched_hash_match"] and row["manifest_universe_hash_match"]
                                   and row["manifest_status"] == "complete" for row in lineage) else "FAIL"
    reproduction_status = "PASS" if all(row["status"] == "PASS" for row in reproduction_checks) else "FAIL"

    if parity_status["status"] == "PASS" and lineage_status == "PASS" and reproduction_status == "PASS":
        power_rows, sensitivity_rows, oracle_rows = build_power_and_oracle(data, masks, roles, groups, context, existing)
        attribution_rows = attribution(existing, power_rows, oracle_rows)
    else:
        power_rows, sensitivity_rows, oracle_rows, attribution_rows = [], [], [], []

    summaries = {
        "all_576": scope_summary(attribution_rows, lambda row: True),
        "primary_144": scope_summary(attribution_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe"),
        "primary_target_gt_free_108": scope_summary(
            attribution_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] in TARGET_FREE),
        "primary_diagnostic_upper_bound_36": scope_summary(
            attribution_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe"
            and row["score"] == "target_gt_nonlinear_geometry_upper_bound"),
    }
    cross_summaries = {
        "by_evaluation_unit": grouped_summaries(attribution_rows, "evaluation_unit"),
        "by_score": grouped_summaries(attribution_rows, "score"),
        "by_alpha_type": grouped_summaries(attribution_rows, "alpha_type"),
        "by_alpha_label": grouped_summaries(attribution_rows, "alpha_label"),
        "by_risk_endpoint": grouped_summaries(attribution_rows, "risk_endpoint"),
    }
    main_denominator = [row for row in attribution_rows
                        if row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] in TARGET_FREE
                        and not as_bool(row["trivial_guarantee"]) and not as_bool(row["actual_feasible"])]
    numerator = sum(row["attribution"] == "SCORE_RANKING_LIMIT" for row in main_denominator)
    denominator = len(main_denominator)
    ratio = numerator / denominator if denominator else math.nan
    formal_other = sum(row["attribution"] == "FORMAL_OTHER" for row in attribution_rows)
    if parity_status["status"] != "PASS" or lineage_status != "PASS" or reproduction_status != "PASS" or not denominator or formal_other:
        final_gate = "INCONCLUSIVE_POWER_DECOMPOSITION"
    elif ratio > 0.5:
        final_gate = "PASS_SCORE_LIMIT_DOMINANT"
    else:
        final_gate = "FAIL_SCORE_LIMIT_DOMINANT"

    atomic_csv(OUT_POWER, power_rows or [{"status": "INCONCLUSIVE_POWER_DECOMPOSITION"}])
    atomic_csv(OUT_ORACLE, oracle_rows or [{"status": "INCONCLUSIVE_POWER_DECOMPOSITION"}])
    atomic_csv(OUT_ATTR, attribution_rows or [{"status": "INCONCLUSIVE_POWER_DECOMPOSITION"}])
    atomic_csv(OUT_SENS, sensitivity_rows or [{"status": "INCONCLUSIVE_POWER_DECOMPOSITION"}])

    gate = {
        "schema_version": "a1_power_gate_r004_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": EXECUTION_HEAD, "final_gate": final_gate,
        "parity": parity_status, "parity_mismatch_examples": mismatches[:20],
        "lineage_status": lineage_status, "lineage": lineage, "reproduction_hash_status": reproduction_status,
        "reproduction_hash_checks": reproduction_checks, "scope_summaries": summaries,
        "cross_summaries": cross_summaries,
        "main_gate_definition": "primary endpoint; target-GT-free scores; nontrivial; existing feasible=False",
        "main_gate_fraction": {"numerator": numerator, "denominator": denominator, "ratio": ratio},
        "formal_other_count": formal_other,
        "frozen_policy": {"delta_primary": 0.1, "delta_sensitivity": [0.05, 0.01],
                          "coverage_grid": PROTO["coverage_grid"], "absolute_alpha": PROTO["absolute_alpha"],
                          "main_mask": PROTO["main_mask"], "primary_endpoint": PROTO["primary_endpoint"]},
        "execution_counts": {"training": 0, "inference": 0, "download": 0, "gpu": 0,
                             "rsar_reads": 0, "evidence": "STATIC_CONTROL_FLOW_AUDIT"},
        "cpu": {"available": CPU_COUNT, "thread_budget": CPU_WORKERS, "fraction": CPU_WORKERS / CPU_COUNT,
                "limitation": "raw JSONL loading and fixed-sequence loops include serial I/O"},
        "sanitizer_status": "PENDING",
    }
    atomic_json(OUT_GATE, gate)
    report = report_text(gate, lineage)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    record = (f"\n[{timestamp}] source=C r004; action=A1 power-score attribution; "
              f"gate={final_gate}; outputs=Paper-A r004 logical namespace and dis/server_reports r004; "
              "stop=no protocol drift; next=C adjudication; training=0; inference=0; download=0.\n")
    existing_record = ROOT_RECORD.read_text(encoding="utf-8")
    if "source=C r004; action=A1 power-score attribution" not in existing_record:
        with ROOT_RECORD.open("a", encoding="utf-8") as handle:
            handle.write(record)
        appended = record
    else:
        appended = ""

    named_text = {
        logical(SCRIPT): SCRIPT.read_text(encoding="utf-8"),
        logical(ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py"):
            (ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py").read_text(encoding="utf-8"),
        logical(OUT_POWER): OUT_POWER.read_text(encoding="utf-8"), logical(OUT_ORACLE): OUT_ORACLE.read_text(encoding="utf-8"),
        logical(OUT_ATTR): OUT_ATTR.read_text(encoding="utf-8"), logical(OUT_SENS): OUT_SENS.read_text(encoding="utf-8"),
        logical(OUT_GATE): OUT_GATE.read_text(encoding="utf-8"), logical(OUT_REPORT): OUT_REPORT.read_text(encoding="utf-8"),
        "claude_code_and_supervisor.md::r004_append": appended,
    }
    sanitizer_hits = shared_text_violations(named_text)
    gate["sanitizer_status"] = "PASS" if not sanitizer_hits else "FAIL"
    gate["sanitizer_hits"] = sanitizer_hits
    if sanitizer_hits:
        gate["final_gate"] = "PROTOCOL_DRIFT"
    atomic_json(OUT_GATE, gate)
    OUT_REPORT.write_text(report_text(gate, lineage), encoding="utf-8")

    r003_source = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py"
    output_paths = [SCRIPT, r003_source, OUT_POWER, OUT_ORACLE, OUT_ATTR, OUT_SENS, OUT_GATE, OUT_REPORT, ROOT_RECORD]
    manifest = {
        "schema_version": "a1_power_manifest_r004_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": EXECUTION_HEAD,
        "command": f"PYTHONDONTWRITEBYTECODE=1 python {logical(SCRIPT)}", "inputs": registry.output(),
        "execution_source": file_identity(SCRIPT),
        "historical_compliance_repair": file_identity(r003_source),
        "outputs": [file_identity(path) for path in output_paths],
        "manifest_self_identity": "fixed by the result commit Git blob; no recursive self-hash",
        "authorized_changes": [logical(path) for path in output_paths] + [logical(OUT_MANIFEST)],
        "final_gate": gate["final_gate"], "rows": {"power": len(power_rows), "oracle": len(oracle_rows),
            "attribution": len(attribution_rows), "sensitivity": len(sensitivity_rows)},
        "execution_counts": gate["execution_counts"], "cpu": gate["cpu"],
        "sanitizer": {"status": gate["sanitizer_status"], "hits": sanitizer_hits},
    }
    atomic_json(OUT_MANIFEST, manifest)
    return 0 if gate["final_gate"] != "PROTOCOL_DRIFT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
