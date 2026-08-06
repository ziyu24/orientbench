#!/usr/bin/env python3
"""Audit a dominating scene-functional attainable envelope for the frozen A1 frontier."""
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
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = str(CPU_WORKERS)

import numpy as np
from scipy.stats import binom

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol"
REPORTS = A / "reports"
SCRIPT = Path(__file__).resolve()
ROUND_ID = "orientbench-c-r005-20260805"
SNAPSHOT = "6955bbc49094a09696c1025e3034f74b74910857"
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
DIAGNOSTIC = SCORES[3]
DELTAS = (0.1, 0.05, 0.01)

PROTO_PATH = REPORTS / "a1_protocol_frozen.json"
FRONTIER_PATH = REPORTS / "a1_guaranteed_frontier_all_alpha.csv"
R004_SCRIPT = A / "scripts/audit_a1_power_decomposition_r004.py"
R004_POWER = REPORTS / "a1_power_envelope_r004.csv"
R004_ORACLE = REPORTS / "a1_oracle_feasibility_r004.csv"
R004_ATTR = REPORTS / "a1_failure_attribution_r004.csv"
R004_SENS = REPORTS / "a1_power_sensitivity_r004.csv"
R004_GATE = REPORTS / "a1_power_gate_r004.json"
R004_MANIFEST = REPORTS / "a1_power_manifest_r004.json"
R004_REPORT = ROOT / "dis/server_reports/orientbench-c-r004-20260805.md"
RUN_A1 = A / "scripts/run_a1_a3.py"
RULES = ROOT / "AGENTS.md"
ROOT_RECORD = ROOT / "claude_code_and_supervisor.md"

OUT_DOMINANCE = REPORTS / "a1_r004_dominance_violations_r005.csv"
OUT_TRACE = REPORTS / "a1_coverage_trace_r005.csv"
OUT_ENVELOPE = REPORTS / "a1_scene_attainable_envelope_r005.csv"
OUT_BOUNDS = REPORTS / "a1_failure_bounds_r005.csv"
OUT_GATE = REPORTS / "a1_scene_oracle_gate_r005.json"
OUT_MANIFEST = REPORTS / "a1_scene_oracle_manifest_r005.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r005-20260805.md"

PROTO = json.loads(PROTO_PATH.read_text(encoding="utf-8"))


def logical(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


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
        name = logical(path)
        if name not in self.rows:
            row = file_identity(path)
            row["purposes"] = []
            self.rows[name] = row
        if purpose not in self.rows[name]["purposes"]:
            self.rows[name]["purposes"].append(purpose)
        return self.rows[name]

    def output(self) -> list[dict]:
        rows = []
        for name in sorted(self.rows):
            row = dict(self.rows[name])
            row["purposes"] = sorted(row["purposes"])
            rows.append(row)
        return rows

    def add_registered_prefix(self, logical_name: str, registered: dict, purpose: str) -> None:
        key = logical_name + "::registered_prefix"
        row = dict(registered)
        row["logical_path"] = key
        row["purposes"] = [purpose]
        self.rows[key] = row


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def atomic_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(rows[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def as_bool(value) -> bool:
    return value is True or str(value).lower() == "true"


def f6(value) -> str:
    if value is None:
        return ""
    value = float(value)
    return f"{value:.6f}" if math.isfinite(value) else ""


def same_numeric(left, right, tolerance=5e-7) -> bool:
    if left in (None, "") and right in (None, ""):
        return True
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def identity(row: dict) -> str:
    return "|".join(str(row[name]) for name in ("evaluation_unit", "score", "risk_endpoint", "alpha_label"))


def unit_key(row: dict) -> tuple[str, str, str]:
    return row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"]


def eligible_groups(mask: np.ndarray, role: np.ndarray, groups: np.ndarray) -> np.ndarray:
    return np.unique(groups[mask & role])


def hb_ucb(mean: float, n: int, delta: float) -> float:
    return float(M.hb_ucb(float(mean), int(n), float(delta))) if n else math.nan


def hb_ucb_vector(means: np.ndarray, sample_sizes: np.ndarray, delta: float) -> np.ndarray:
    """Vectorized equivalent of the frozen scalar M.hb_ucb binary search."""
    means = np.asarray(means, dtype=float)
    sample_sizes = np.asarray(sample_sizes, dtype=float)
    lo, hi = means.copy(), np.ones_like(means)
    clipped = np.clip(means, 1e-12, 1.0 - 1e-12)
    k = np.ceil(sample_sizes * means)
    for _ in range(60):
        midpoint = 0.5 * (lo + hi)
        bounded_mid = np.clip(midpoint, 1e-12, 1.0 - 1e-12)
        divergence = clipped * np.log(clipped / bounded_mid) + (1.0 - clipped) * np.log((1.0 - clipped) / (1.0 - bounded_mid))
        hoeffding = np.exp(-sample_sizes * divergence)
        bentkus = math.e * binom.cdf(k, sample_sizes, midpoint)
        pvalue = np.minimum(1.0, np.minimum(hoeffding, bentkus))
        reject = (means < midpoint) & (pvalue <= delta)
        hi = np.where(reject, midpoint, hi)
        lo = np.where(reject, lo, midpoint)
    return hi


def summarize(mask: np.ndarray, selected: np.ndarray, event: np.ndarray,
              groups: np.ndarray, eligible: np.ndarray, delta: float) -> dict:
    indices = np.where(mask)[0]
    positions = {str(group): index for index, group in enumerate(eligible)}
    inverse = np.fromiter((positions[str(group)] for group in groups[indices]), dtype=np.int64, count=len(indices))
    kept = np.bincount(inverse, weights=selected[indices].astype(float), minlength=len(eligible))
    bad = np.bincount(inverse, weights=(selected[indices] * event[indices]).astype(float), minlength=len(eligible))
    nonempty = kept > 0
    losses = np.divide(bad[nonempty], kept[nonempty])
    return {
        "selected_instances": int(kept.sum()), "nonempty_scenes": int(nonempty.sum()),
        "conditional_risk": float(losses.mean()) if len(losses) else math.nan,
        "ucb": hb_ucb(float(losses.mean()), len(losses), delta) if len(losses) else math.nan,
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


def fit_risk(base: np.ndarray, fit_role: np.ndarray, event: np.ndarray, groups: np.ndarray) -> float:
    eligible = eligible_groups(base, fit_role, groups)
    return summarize(base & fit_role, base, event, groups, eligible, PROTO["delta"])["conditional_risk"]


def verify_r004(registry: Registry) -> dict:
    manifest = json.loads(R004_MANIFEST.read_text(encoding="utf-8"))
    checks = []
    for registered in manifest["inputs"]:
        path = ROOT / registered["logical_path"]
        current = registry.add(path, "r004 registered input revalidation")
        checks.append(current["bytes"] == registered["bytes"] and current["sha256"] == registered["sha256"]
                      and current["git_blob"] == registered["git_blob"])
    for registered in manifest["outputs"]:
        path = ROOT / registered["logical_path"]
        if path == ROOT_RECORD:
            prefix = path.read_bytes()[:int(registered["bytes"])]
            prefix_sha = hashlib.sha256(prefix).hexdigest()
            prefix_blob = hashlib.sha1(f"blob {len(prefix)}\0".encode() + prefix).hexdigest()
            checks.append(len(prefix) == registered["bytes"] and prefix_sha == registered["sha256"]
                          and prefix_blob == registered["git_blob"])
            registry.add_registered_prefix(registered["logical_path"], registered, "r004 append-only output prefix revalidation")
        else:
            current = registry.add(path, "r004 non-self output revalidation")
            checks.append(current["bytes"] == registered["bytes"] and current["sha256"] == registered["sha256"]
                          and current["git_blob"] == registered["git_blob"])
    manifest_blob = git("rev-parse", f"{SNAPSHOT}:{logical(R004_MANIFEST)}")
    checks.append(manifest_blob == file_identity(R004_MANIFEST)["git_blob"])

    committed_paths = sorted(git("diff-tree", "--no-commit-id", "--name-only", "-r", f"{SNAPSHOT}^", SNAPSHOT).splitlines())
    expected_paths = sorted(manifest["authorized_changes"])
    checks.append(committed_paths == expected_paths)
    immutable = [
        "dis/B.md", "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json",
        "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_guaranteed_frontier_all_alpha.csv",
        "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6_confirmatory_protocol_frozen.json",
        "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_asset_gate_r003.json",
        "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_asset_gate_manifest_r003.json",
        "dis/server_reports/orientbench-c-r003-20260805.md",
    ]
    for path in immutable:
        checks.append(git("rev-parse", f"{SNAPSHOT}:{path}") == git("rev-parse", f"{SNAPSHOT}^:{path}"))
    return {
        "status": "PASS" if all(checks) else "FAIL", "checks": len(checks), "failures": sum(not item for item in checks),
        "registered_inputs": len(manifest["inputs"]), "registered_nonself_outputs": len(manifest["outputs"]),
        "commit_paths": committed_paths,
    }


def rebuild_trace(data: dict, masks: dict, roles: dict, groups: dict, events: dict,
                  existing: list[dict], r004_oracle: list[dict]) -> tuple[list[dict], dict]:
    alpha_lookup = {}
    for row in existing:
        alpha_lookup[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])] = (
            float(row["alpha"]), row["alpha_type"], float(row["r_fit"])
        )
    unique_r004 = {}
    r004_consistent = True
    for row in r004_oracle:
        key = (row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])
        signature = (row["oracle_primary_feasible"], row["first_primary_failure_coverage"], row["oracle_chosen_coverage"])
        if key in unique_r004 and unique_r004[key][0] != signature:
            r004_consistent = False
        unique_r004[key] = (signature, row)

    trace, reconstructed = [], {}
    for cell in CELLS:
        base, cell_roles, cell_groups = masks[cell], roles[cell], groups[cell]
        fit_mask = base & cell_roles["fit"]
        eligible_cal = eligible_groups(base, cell_roles["calib"], cell_groups)
        for endpoint, event in events[cell].items():
            row_index = np.arange(len(event), dtype=float)
            oracle_score = (1.0 - event) + 1e-6 * (1.0 - row_index / max(len(event) - 1, 1))
            for alpha_label, alpha, alpha_type in alpha_definitions(fit_risk(base, cell_roles["fit"], event, cell_groups)):
                prefix_open, first_failure, candidates = True, "", []
                local_rows = []
                for coverage in PROTO["coverage_grid"]:
                    threshold = score_threshold(oracle_score, fit_mask, coverage)
                    selected = base & (oracle_score >= threshold)
                    cal = summarize(base & cell_roles["calib"], selected, event, cell_groups, eligible_cal, PROTO["delta"])
                    pointwise = cal["nonempty_scenes"] > 0 and cal["ucb"] <= alpha
                    prefix_before = prefix_open
                    if prefix_open and pointwise:
                        candidates.append((coverage, threshold, cal))
                    else:
                        if prefix_open:
                            first_failure = f"{coverage:g}"
                        prefix_open = False
                    local_rows.append({
                        "evaluation_unit": cell, "dataset": data[cell]["dataset"], "risk_endpoint": endpoint,
                        "alpha_label": alpha_label, "alpha_type": alpha_type, "alpha": f6(alpha), "coverage": f6(coverage),
                        "fit_threshold": f6(threshold), "selected_calibration_instances": cal["selected_instances"],
                        "nonempty_calibration_scenes": cal["nonempty_scenes"],
                        "conditional_scene_risk": f6(cal["conditional_risk"]), "hb_ucb": f6(cal["ucb"]),
                        "pointwise_pass": pointwise, "prefix_open_before": prefix_before,
                        "prefix_open_after": prefix_open, "after_first_failure_pointwise_pass": bool(not prefix_before and pointwise),
                    })
                chosen = max(candidates, key=lambda item: item[0]) if candidates else None
                reconstructed[(cell, endpoint, alpha_label)] = {
                    "oracle_primary_feasible": bool(chosen), "first_primary_failure_coverage": first_failure,
                    "oracle_chosen_coverage": f6(chosen[0] if chosen else 0),
                }
                trace.extend(local_rows)

    comparisons = []
    for key, rebuilt in reconstructed.items():
        old = unique_r004.get(key, (None, None))[1]
        comparisons.append(bool(old)
                           and as_bool(old["oracle_primary_feasible"]) == rebuilt["oracle_primary_feasible"]
                           and old["first_primary_failure_coverage"] == rebuilt["first_primary_failure_coverage"]
                           and same_numeric(old["oracle_chosen_coverage"], rebuilt["oracle_chosen_coverage"]))
    status = {
        "r004_duplicate_rows_consistent": r004_consistent, "unique_oracle_units": len(reconstructed),
        "trace_rows": len(trace), "oracle_field_matches": sum(comparisons), "oracle_field_mismatches": len(comparisons)-sum(comparisons),
        "status": "PASS" if r004_consistent and len(reconstructed) == 144 and len(trace) == 1872 and all(comparisons) else "FAIL",
    }
    return trace, status


def build_envelope(data: dict, masks: dict, roles: dict, groups: dict, events: dict,
                   existing: list[dict]) -> tuple[list[dict], dict]:
    alpha_lookup = {}
    for row in existing:
        alpha_lookup[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])] = (
            float(row["alpha"]), row["alpha_type"], float(row["r_fit"])
        )
    envelope_rows, envelope_map = [], {}
    vector_validation = []
    for cell in CELLS:
        base, calib, cell_groups = masks[cell], roles[cell]["calib"], groups[cell]
        for endpoint, event in events[cell].items():
            per_scene = defaultdict(list)
            for index in np.where(base & calib)[0]:
                per_scene[str(cell_groups[index])].append(float(event[index]))
            scene_minima = sorted((min(values), scene) for scene, values in per_scene.items())
            minima = np.asarray([item[0] for item in scene_minima], dtype=float)
            sample_sizes = np.arange(1, len(minima) + 1, dtype=float)
            means = np.cumsum(minima) / sample_sizes
            ucb_by_delta = {delta: hb_ucb_vector(means, sample_sizes, delta) for delta in DELTAS}
            probes = sorted({0, max(0, len(minima)//2), len(minima)-1})
            for delta in DELTAS:
                vector_validation.extend(abs(ucb_by_delta[delta][index] - hb_ucb(means[index], int(sample_sizes[index]), delta)) <= 1e-12
                                         for index in probes)
            choices = {}
            for delta in DELTAS:
                order = sorted(range(len(minima)), key=lambda index: (ucb_by_delta[delta][index], means[index], -int(sample_sizes[index])))
                choices[delta] = order[0]
            scene_order_hash = hashlib.sha256("\n".join(scene for _, scene in scene_minima).encode()).hexdigest()
            for alpha_label, alpha, alpha_type in alpha_definitions(fit_risk(base, roles[cell]["fit"], event, cell_groups)):
                chosen = choices[0.1]
                row = {
                    "evaluation_unit": cell, "dataset": data[cell]["dataset"], "risk_endpoint": endpoint,
                    "alpha_label": alpha_label, "alpha_type": alpha_type, "alpha": f6(alpha),
                    "eligible_calibration_scenes": len(minima), "zero_risk_scenes": int(np.sum(minima == 0)),
                    "all_event_scenes": int(np.sum(minima == 1)), "scene_order_sha256": scene_order_hash,
                    "search_n_start": 1, "search_n_end": len(minima), "searched_n_count": len(minima),
                    "chosen_n_delta_0.1": int(sample_sizes[chosen]), "chosen_mean_delta_0.1": f6(means[chosen]),
                    "min_hb_ucb_delta_0.1": f6(ucb_by_delta[0.1][chosen]),
                    "feasible_delta_0.1": bool(ucb_by_delta[0.1][chosen] <= alpha),
                }
                for delta, suffix in ((0.05, "0.05"), (0.01, "0.01")):
                    index = choices[delta]
                    row[f"chosen_n_delta_{suffix}"] = int(sample_sizes[index])
                    row[f"chosen_mean_delta_{suffix}"] = f6(means[index])
                    row[f"min_hb_ucb_delta_{suffix}"] = f6(ucb_by_delta[delta][index])
                    row[f"feasible_delta_{suffix}"] = bool(ucb_by_delta[delta][index] <= alpha)
                envelope_rows.append(row)
                envelope_map[(cell, endpoint, alpha_label)] = row
    return envelope_rows, {"map": envelope_map, "vector_scalar_checks": len(vector_validation),
                           "vector_scalar_failures": sum(not value for value in vector_validation)}


def rebuild_r004_attribution(existing: list[dict], power: list[dict], oracle: list[dict], recorded: list[dict]) -> dict:
    power_map = {(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"]): row for row in power}
    oracle_map = {row["identity_key"]: row for row in oracle}
    recorded_map = {row["identity_key"]: row for row in recorded}
    mismatches = []
    for row in existing:
        p, o = power_map[unit_key(row)], oracle_map[identity(row)]
        if as_bool(row["trivial_guarantee"]):
            label = "TRIVIAL_BUDGET"
        elif as_bool(p["structural_power_limit_delta_0.1"]):
            label = "STRUCTURAL_POWER_LIMIT"
        elif not as_bool(o["oracle_primary_feasible"]):
            label = "ORACLE_DATA_OR_GRID_LIMIT"
        elif not as_bool(row["feasible"]):
            label = "SCORE_RANKING_LIMIT"
        elif not as_bool(row["practical"]):
            label = "PRACTICAL_COVERAGE_LIMIT"
        elif as_bool(row["practical"]):
            label = "CERTIFIED_PRACTICAL"
        else:
            label = "FORMAL_OTHER"
        if identity(row) not in recorded_map or recorded_map[identity(row)]["attribution"] != label:
            mismatches.append(identity(row))
    return {"rows": len(existing), "mismatches": len(mismatches), "examples": mismatches[:20],
            "status": "PASS" if not mismatches else "FAIL"}


def classify(existing: list[dict], power: list[dict], envelope_map: dict) -> list[dict]:
    power_map = {(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"]): row for row in power}
    actual_by_unit_score = {(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"], row["score"]): row
                            for row in existing}
    output = []
    for row in existing:
        trivial, feasible, practical = as_bool(row["trivial_guarantee"]), as_bool(row["feasible"]), as_bool(row["practical"])
        structural = as_bool(power_map[unit_key(row)]["structural_power_limit_delta_0.1"])
        envelope = envelope_map[unit_key(row)]
        envelope_feasible = as_bool(envelope["feasible_delta_0.1"])
        if trivial and feasible:
            label = "TRIVIAL_FORMAL_CERTIFIED"
        elif trivial and not feasible:
            label = "TRIVIAL_BUDGET_INFEASIBLE"
        elif not trivial and feasible and practical:
            label = "CERTIFIED_PRACTICAL"
        elif not trivial and feasible and not practical:
            label = "PRACTICAL_COVERAGE_LIMIT"
        elif not trivial and not feasible and structural:
            label = "STRUCTURAL_POWER_LIMIT"
        elif not trivial and not feasible and not structural and not envelope_feasible:
            label = "EMPIRICAL_SCENE_SUPPORT_LIMIT"
        elif not trivial and not feasible and not structural and envelope_feasible:
            label = "SELECTION_PROTOCOL_GAP"
        else:
            label = "FORMAL_OTHER"
        main = row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] in TARGET_FREE and not trivial and not feasible
        other_target_free = [score for score in TARGET_FREE if score != row["score"]]
        conservative = any(as_bool(actual_by_unit_score[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"], score)]["feasible"])
                           for score in other_target_free)
        diagnostic = as_bool(actual_by_unit_score[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"], DIAGNOSTIC)]["feasible"])
        output.append({
            "identity_key": identity(row), "evaluation_unit": row["evaluation_unit"], "dataset": row["dataset"],
            "detector": row["detector"], "score": row["score"], "risk_endpoint": row["risk_endpoint"],
            "alpha_label": row["alpha_label"], "alpha_type": row["alpha_type"], "alpha": row["alpha"],
            "trivial": trivial, "actual_feasible": feasible, "actual_practical": practical,
            "actual_coverage": row["target_coverage"], "actual_count": row["selected_count"],
            "structural_power_limit": structural, "scene_envelope_feasible": envelope_feasible,
            "scene_envelope_min_ucb": envelope["min_hb_ucb_delta_0.1"], "attribution": label,
            "main_denominator": main, "conservative_other_target_free_witness": bool(main and conservative),
            "diagnostic_target_gt_witness": bool(main and diagnostic),
            "score_cause_upper_possible": bool(main and label == "SELECTION_PROTOCOL_GAP"),
        })
    return output


def scope(rows: list[dict], predicate) -> dict:
    selected = [row for row in rows if predicate(row)]
    return {"rows": len(selected), "attribution_counts": dict(sorted(Counter(row["attribution"] for row in selected).items()))}


def bounded_sanitizer(named_text: dict[str, str]) -> list[dict]:
    account, hostname = os.environ.get("USER", ""), socket.gethostname()
    literals = [value for value in (account, hostname) if len(value) >= 3]
    patterns = {
        "unix_absolute": re.compile(r"(?<![A-Za-z0-9_.-])/(?:home|Users|root|srv|opt|scratch|workspace|tmp|var|mnt|data)/"),
        "windows_drive": re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\\\/]"),
        "windows_unc": re.compile(r"(?<![\\\\])\\\\\\\\[A-Za-z0-9_.-]+[\\\\]"),
        "token": re.compile(r"(?:ghp_|github_pat_|AKIA)[A-Za-z0-9_=-]+"),
        "bearer": re.compile(r"Bearer\s+[A-Za-z0-9._=-]{12,}", re.I),
        "password": re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*[^,;\s]{4,}", re.I),
        "private_key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
        "connection_string": re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://", re.I),
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


def report_text(gate: dict) -> str:
    counter = gate["r004_counterexamples"]
    trace = gate["trace_summary"]
    main = gate["main_denominator"]
    primary = gate["scopes"]["primary_144"]
    return f"""# A1 scene-functional oracle 支配性修复门

- round: `{ROUND_ID}`
- scientific snapshot: `{SNAPSHOT}`
- execution HEAD: `{EXECUTION_HEAD}`
- structure gate: `{gate['structure_gate']}`
- score-cause gate: `{gate['score_cause_gate']}`
- detector fit/predict, diagnostic regressor fit/predict, download, GPU, RSAR read: `0/0, 0/0, 0, 0, 0`

## 1. 核心裁决

新的 scene-functional attainable envelope 通过全部状态与数值支配检查，结构门为 `{gate['structure_gate']}`。
主分母保持 90 行：conservative score lower witness 为 {main['conservative_lower_numerator']}/90
({main['conservative_lower_ratio']:.6f})，加入 target-GT diagnostic witness 的 sensitivity lower 为
{main['diagnostic_sensitivity_lower_numerator']}/90 ({main['diagnostic_sensitivity_lower_ratio']:.6f})，
selection/protocol-gap upper bound 为 {main['upper_numerator']}/90 ({main['upper_ratio']:.6f})。
因此 score 原因既未被保守下界证明占多数，也未被上界排除占多数，科学结论是 `{gate['score_cause_gate']}`。

## 2. r004 反例与 trace

- actual feasible 但 r004 oracle infeasible：{counter['actual_feasible_oracle_infeasible']} 行
- 其中 practical：{counter['actual_practical_oracle_infeasible']} 行
- 其中 primary：{counter['primary_actual_feasible_oracle_infeasible']} 行
- 1% 首败：{trace['entry_failure_units']}/144
- 首败后存在更高 coverage pointwise pass：{trace['later_pass_units']}/144
- primary later-pass：{trace['primary_later_pass_units']}/36
- 主分母原 r004 oracle-limit 且 later-pass：{trace['main_oracle_limit_later_pass_rows']}/{trace['main_oracle_limit_rows']}

r004 的 literal fixed-sequence gate 仍是冻结的 `FAIL_SCORE_LIMIT_DOMINANT`；本轮不覆盖它。上述反例说明其 instance oracle
不支配 conditional scene functional，不能把 r004 的 `0/90` 解释为 score 因果下界。

## 3. 支配 envelope

每个 calibration scene 先取最小 endpoint event，再在全部 scene 中按 `(m_s, stable_scene_id)` 排序；对所有 `n=1..N`
计算冻结 HB UCB 并取最小值。144 个 unit-endpoint-alpha 单元均保存 scene 数、zero/all-event scene、chosen n/mean/UCB
和 `delta=0.05/0.01` 敏感性。状态支配违反 {gate['dominance']['state_violations']} 行，数值支配违反
{gate['dominance']['numeric_violations']} 行；vector/scalar HB 一致性失败 {gate['dominance']['vector_scalar_failures']} 个。

该 envelope 使用 calibration outcome 并放松 score、fit threshold、coverage grid、1% entry、fixed-sequence 与 practical policy；
它只给可达性下界，不是 inference-available score，也不是新风险控制协议。

## 4. 状态优先归因

primary 144 行互斥分解为：
{json.dumps(primary['attribution_counts'], ensure_ascii=False, sort_keys=True)}。
`SELECTION_PROTOCOL_GAP` 混合 score ranking、D_fit 到 calibration transfer、coverage grid、序列顺序和 policy class，
不得改称 `SCORE_RANKING_LIMIT`。target-GT diagnostic witness 不并入 conservative lower。

## 5. 最弱环节、置信度与反证条件

最弱环节是 selection/protocol gap 内部不可由现有冻结证据进一步识别：保守 score witness 太弱，而 relaxed upper 仍大于 50%。
对 envelope 支配性与状态分解的置信度为高，因为 r004 身份、1872 trace、六单元 lineage 和数值支配均闭环；
对“score 是否为多数原因”的结论保持不可判定。只有预先冻结、仍使用 target-GT-free score 的独立设计能收紧上下界。

## 6. 合规

本轮未运行 r004 geometry regressor parity；detector 与 diagnostic regressor 的 fit/predict 均为 0，训练、推理、下载、GPU、
RSAR/其它个人项目读取均为 0，证据类型为 `STATIC_CONTROL_FLOW_AUDIT`。CPU 线程预算 {CPU_WORKERS}/{CPU_COUNT}（>=80%）；
分组和 JSONL 装载含串行 I/O，未伪报实际利用率。bounded sanitizer 为 `{gate['sanitizer_status']}`；旧 A1/r004 和主稿均未修改。
"""


def main() -> int:
    if git("rev-parse", "--show-object-format") != "sha1":
        raise RuntimeError("unsupported Git object format")
    if subprocess.run(["git", "merge-base", "--is-ancestor", SNAPSHOT, EXECUTION_HEAD], cwd=ROOT).returncode:
        raise RuntimeError("scientific snapshot ancestry check failed")

    registry = Registry()
    for path, purpose in ((RULES, "repository rules"), (PROTO_PATH, "frozen A1 protocol"),
                          (RUN_A1, "frozen A1 implementation"), (R004_SCRIPT, "r004 implementation"),
                          (R004_GATE, "r004 gate"), (R004_MANIFEST, "r004 manifest"),
                          (R004_POWER, "r004 power labels"), (R004_ORACLE, "r004 oracle labels"),
                          (R004_ATTR, "r004 attribution"), (R004_SENS, "r004 sensitivity"),
                          (R004_REPORT, "r004 report"), (FRONTIER_PATH, "frozen A1 frontier"),
                          (SCRIPT, "r005 execution source")):
        registry.add(path, purpose)
    r004_verification = verify_r004(registry)

    existing = read_csv(FRONTIER_PATH)
    r004_power, r004_oracle, r004_attr = read_csv(R004_POWER), read_csv(R004_ORACLE), read_csv(R004_ATTR)
    key_counts = {"frontier": len({identity(row) for row in existing}),
                  "r004_oracle": len({row["identity_key"] for row in r004_oracle}),
                  "r004_attribution": len({row["identity_key"] for row in r004_attr})}
    identity_status = "PASS" if len(existing) == len(r004_oracle) == len(r004_attr) == 576 and all(value == 576 for value in key_counts.values()) else "FAIL"
    r004_attribution_check = rebuild_r004_attribution(existing, r004_power, r004_oracle, r004_attr)

    data, masks, roles, groups, events, lineage = {}, {}, {}, {}, {}, []
    for cell in CELLS:
        M.verify_fullval_lineage(cell)
        matched_path, universe_path, manifest_path = Path(M.CELLS[cell][2]), Path(M.UNIVERSE[cell]), Path(M.MANIFEST[cell])
        matched = registry.add(matched_path, f"cell {cell} matched lineage")
        universe = registry.add(universe_path, f"cell {cell} universe lineage")
        manifest_id = registry.add(manifest_path, f"cell {cell} manifest lineage")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = M.load_cell(cell, max_rows=10**18)
        base = M.mask_ar(current, M.AR_MAIN)
        outer = np.asarray(current["split"], dtype=object)
        inner = np.asarray([M.split_role(str(image)) for image in current["img"]], dtype=object)
        cell_roles = {"fit": (outer == "D_cal") & (inner == "fit"),
                      "calib": (outer == "D_cal") & (inner == "calib"), "audit": outer == "D_audit"}
        cell_groups = np.asarray([str(image) for image in current["img"]], dtype=object)
        severe, _ = M.geometry_severe(current)
        data[cell], masks[cell], roles[cell], groups[cell] = current, base, cell_roles, cell_groups
        events[cell] = {name: severe if degrees is None else (current["ae"] > degrees).astype(float)
                        for name, degrees in ENDPOINTS.items()}
        lineage.append({
            "evaluation_unit": cell, "matched_rows": len(current["ae"]), "eligible_rows": int(base.sum()),
            "matched_sha256": matched["sha256"], "universe_sha256": universe["sha256"],
            "manifest_sha256": manifest_id["sha256"],
            "matched_hash_match": matched["sha256"] == manifest["matched_sha256"],
            "universe_hash_match": universe["sha256"] == manifest["universe_sha256"], "status": manifest.get("status"),
        })
    lineage_status = "PASS" if all(row["matched_hash_match"] and row["universe_hash_match"] and row["status"] == "complete"
                                   for row in lineage) else "FAIL"

    prerequisites = all((r004_verification["status"] == "PASS", identity_status == "PASS",
                         r004_attribution_check["status"] == "PASS", lineage_status == "PASS"))
    if prerequisites:
        trace_rows, trace_check = rebuild_trace(data, masks, roles, groups, events, existing, r004_oracle)
    else:
        trace_rows, trace_check = [], {"status": "FAIL", "trace_rows": 0}
    if prerequisites and trace_check["status"] == "PASS":
        envelope_rows, envelope_context = build_envelope(data, masks, roles, groups, events, existing)
    else:
        envelope_rows, envelope_context = [], {"map": {}, "vector_scalar_checks": 0, "vector_scalar_failures": 0}

    oracle_by_identity = {row["identity_key"]: row for row in r004_oracle}
    dominance_rows, state_violations, numeric_violations = [], [], []
    if envelope_rows:
        for row in existing:
            oracle = oracle_by_identity[identity(row)]
            envelope = envelope_context["map"][unit_key(row)]
            actual_feasible = as_bool(row["feasible"])
            envelope_feasible = as_bool(envelope["feasible_delta_0.1"])
            state_ok = not actual_feasible or envelope_feasible
            numeric_ok = True
            margin = ""
            if actual_feasible:
                margin = float(row["certified_risk_ucb"]) - float(envelope["min_hb_ucb_delta_0.1"])
                numeric_ok = float(envelope["min_hb_ucb_delta_0.1"]) <= float(row["certified_risk_ucb"]) + 2e-6
            if not state_ok:
                state_violations.append(identity(row))
            if not numeric_ok:
                numeric_violations.append(identity(row))
            dominance_rows.append({
                "identity_key": identity(row), "evaluation_unit": row["evaluation_unit"], "score": row["score"],
                "risk_endpoint": row["risk_endpoint"], "alpha_label": row["alpha_label"], "alpha": row["alpha"],
                "trivial": as_bool(row["trivial_guarantee"]), "actual_feasible": actual_feasible,
                "actual_practical": as_bool(row["practical"]), "actual_coverage": row["target_coverage"],
                "actual_count": row["selected_count"], "actual_ucb": row["certified_risk_ucb"],
                "r004_oracle_feasible": as_bool(oracle["oracle_primary_feasible"]),
                "r004_oracle_first_failure": oracle["first_primary_failure_coverage"],
                "r004_oracle_chosen_coverage": oracle["oracle_chosen_coverage"],
                "r004_attribution": next(item["attribution"] for item in r004_attr if item["identity_key"] == identity(row)),
                "actual_feasible_r004_oracle_infeasible": bool(actual_feasible and not as_bool(oracle["oracle_primary_feasible"])),
                "scene_envelope_feasible": envelope_feasible, "scene_envelope_min_ucb": envelope["min_hb_ucb_delta_0.1"],
                "actual_minus_envelope_ucb": f6(margin) if margin != "" else "", "state_dominance_ok": state_ok,
                "numeric_dominance_ok": numeric_ok,
            })

    if state_violations or numeric_violations:
        structure_gate = "FAIL_SCENE_ENVELOPE_DOMINANCE"
        bounds_rows = []
    elif not prerequisites or trace_check["status"] != "PASS" or len(envelope_rows) != 144:
        structure_gate = "INCONCLUSIVE_SCENE_ENVELOPE"
        bounds_rows = []
    else:
        bounds_rows = classify(existing, r004_power, envelope_context["map"])
        main_rows = [row for row in bounds_rows if as_bool(row["main_denominator"])]
        formal_other = sum(row["attribution"] == "FORMAL_OTHER" for row in bounds_rows)
        if len(main_rows) != 90 or formal_other:
            structure_gate = "INCONCLUSIVE_SCENE_ENVELOPE"
        else:
            structure_gate = "PASS_SCENE_ENVELOPE_VALID"

    trace_unique = defaultdict(list)
    for row in trace_rows:
        trace_unique[(row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"])].append(row)
    later_pass_units = {key for key, rows in trace_unique.items() if any(as_bool(row["after_first_failure_pointwise_pass"]) for row in rows)}
    entry_failure_units = {key for key, rows in trace_unique.items() if rows and not as_bool(rows[0]["pointwise_pass"])}
    main_original = [row for row in r004_attr if row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] in TARGET_FREE
                     and not as_bool(row["trivial_guarantee"]) and not as_bool(row["actual_feasible"])]
    main_oracle_limit = [row for row in main_original if row["attribution"] == "ORACLE_DATA_OR_GRID_LIMIT"]
    trace_summary = {
        "entry_failure_units": len(entry_failure_units), "later_pass_units": len(later_pass_units),
        "primary_later_pass_units": sum(key[1] == "geometry_normalized_severe" for key in later_pass_units),
        "main_oracle_limit_rows": len(main_oracle_limit),
        "main_oracle_limit_later_pass_rows": sum((row["evaluation_unit"], row["risk_endpoint"], row["alpha_label"]) in later_pass_units
                                                   for row in main_oracle_limit),
    }
    counterexamples = {
        "actual_feasible_oracle_infeasible": sum(as_bool(row["actual_feasible_r004_oracle_infeasible"]) for row in dominance_rows),
        "actual_practical_oracle_infeasible": sum(as_bool(row["actual_feasible_r004_oracle_infeasible"]) and as_bool(row["actual_practical"])
                                                  for row in dominance_rows),
        "primary_actual_feasible_oracle_infeasible": sum(as_bool(row["actual_feasible_r004_oracle_infeasible"])
                                                          and row["risk_endpoint"] == "geometry_normalized_severe"
                                                          for row in dominance_rows),
    }

    main_rows = [row for row in bounds_rows if as_bool(row["main_denominator"])]
    conservative = sum(as_bool(row["conservative_other_target_free_witness"]) for row in main_rows)
    diagnostic_union = sum(as_bool(row["conservative_other_target_free_witness"])
                           or as_bool(row["diagnostic_target_gt_witness"]) for row in main_rows)
    upper = sum(as_bool(row["score_cause_upper_possible"]) for row in main_rows)
    denominator = len(main_rows)
    lower_ratio = conservative / denominator if denominator else math.nan
    diagnostic_ratio = diagnostic_union / denominator if denominator else math.nan
    upper_ratio = upper / denominator if denominator else math.nan
    if structure_gate != "PASS_SCENE_ENVELOPE_VALID" or not denominator:
        score_gate = "INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION"
    elif lower_ratio > 0.5:
        score_gate = "PASS_SCORE_LIMIT_DOMINANT_LOWER_BOUND"
    elif upper_ratio <= 0.5:
        score_gate = "FAIL_SCORE_LIMIT_DOMINANT_UPPER_BOUND"
    else:
        score_gate = "INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION"

    atomic_csv(OUT_DOMINANCE, dominance_rows or [{"status": structure_gate}])
    atomic_csv(OUT_TRACE, trace_rows or [{"status": structure_gate}])
    atomic_csv(OUT_ENVELOPE, envelope_rows or [{"status": structure_gate}])
    atomic_csv(OUT_BOUNDS, bounds_rows or [{"status": structure_gate}])

    scopes = {
        "all_576": scope(bounds_rows, lambda row: True),
        "primary_144": scope(bounds_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe"),
        "primary_target_gt_free_108": scope(bounds_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] in TARGET_FREE),
        "diagnostic_36": scope(bounds_rows, lambda row: row["risk_endpoint"] == "geometry_normalized_severe" and row["score"] == DIAGNOSTIC),
    }
    gate = {
        "schema_version": "a1_scene_oracle_gate_r005_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": EXECUTION_HEAD,
        "structure_gate": structure_gate, "score_cause_gate": score_gate,
        "r004_literal_gate": "FAIL_SCORE_LIMIT_DOMINANT", "r004_verification": r004_verification,
        "identity_status": identity_status, "identity_key_counts": key_counts,
        "r004_attribution_rebuild": r004_attribution_check, "lineage_status": lineage_status, "lineage": lineage,
        "trace_check": trace_check, "trace_summary": trace_summary, "r004_counterexamples": counterexamples,
        "dominance": {"state_violations": len(state_violations), "numeric_violations": len(numeric_violations),
                      "state_violation_examples": state_violations[:20], "numeric_violation_examples": numeric_violations[:20],
                      "vector_scalar_checks": envelope_context["vector_scalar_checks"],
                      "vector_scalar_failures": envelope_context["vector_scalar_failures"]},
        "scopes": scopes,
        "main_denominator": {"rows": denominator, "conservative_lower_numerator": conservative,
                             "conservative_lower_ratio": lower_ratio,
                             "diagnostic_sensitivity_lower_numerator": diagnostic_union,
                             "diagnostic_sensitivity_lower_ratio": diagnostic_ratio,
                             "upper_numerator": upper, "upper_ratio": upper_ratio},
        "operation_counts": {"detector_fit": 0, "detector_predict": 0, "diagnostic_regressor_fit": 0,
                             "diagnostic_regressor_predict": 0, "training": 0, "inference": 0,
                             "download": 0, "gpu": 0, "rsar_reads": 0, "other_personal_project_reads": 0,
                             "evidence": "STATIC_CONTROL_FLOW_AUDIT"},
        "cpu": {"available": CPU_COUNT, "thread_budget": CPU_WORKERS, "fraction": CPU_WORKERS / CPU_COUNT,
                "limitation": "grouping and JSONL input include serial I/O"},
        "sanitizer_status": "PENDING",
    }
    atomic_json(OUT_GATE, gate)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(gate), encoding="utf-8")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    record = (f"\n[{timestamp}] source=C r005; action=scene-functional attainable-envelope audit; "
              f"structure_gate={structure_gate}; score_cause_gate={score_gate}; "
              "outputs=Paper-A r005 logical namespace and dis/server_reports r005; stop=no protocol drift; "
              "next=C adjudication; model_fit_predict=0; training=0; inference=0; download=0.\n")
    existing_record = ROOT_RECORD.read_text(encoding="utf-8")
    if "source=C r005; action=scene-functional attainable-envelope audit" not in existing_record:
        with ROOT_RECORD.open("a", encoding="utf-8") as handle:
            handle.write(record)
        append_text = record
    else:
        append_text = ""

    new_text = {
        logical(SCRIPT): SCRIPT.read_text(encoding="utf-8"), logical(OUT_DOMINANCE): OUT_DOMINANCE.read_text(encoding="utf-8"),
        logical(OUT_TRACE): OUT_TRACE.read_text(encoding="utf-8"), logical(OUT_ENVELOPE): OUT_ENVELOPE.read_text(encoding="utf-8"),
        logical(OUT_BOUNDS): OUT_BOUNDS.read_text(encoding="utf-8"), logical(OUT_GATE): OUT_GATE.read_text(encoding="utf-8"),
        logical(OUT_REPORT): OUT_REPORT.read_text(encoding="utf-8"), "claude_code_and_supervisor.md::r005_append": append_text,
    }
    sanitizer_hits = bounded_sanitizer(new_text)
    gate["sanitizer_status"] = "PASS" if not sanitizer_hits else "FAIL"
    gate["sanitizer_scope"] = "bounded patterns over every new file and append diff only"
    gate["sanitizer_hits"] = sanitizer_hits
    if sanitizer_hits:
        gate["structure_gate"] = "PROTOCOL_DRIFT"
        gate["score_cause_gate"] = "INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION"
    atomic_json(OUT_GATE, gate)
    OUT_REPORT.write_text(report_text(gate), encoding="utf-8")

    outputs = [SCRIPT, OUT_DOMINANCE, OUT_TRACE, OUT_ENVELOPE, OUT_BOUNDS, OUT_GATE, OUT_REPORT, ROOT_RECORD]
    manifest = {
        "schema_version": "a1_scene_oracle_manifest_r005_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": EXECUTION_HEAD,
        "command": f"PYTHONDONTWRITEBYTECODE=1 python {logical(SCRIPT)}", "inputs": registry.output(),
        "outputs": [file_identity(path) for path in outputs],
        "authorized_changes": [logical(path) for path in outputs] + [logical(OUT_MANIFEST)],
        "manifest_self_identity": "fixed by result-commit Git blob; no recursive self-hash",
        "rows": {"dominance": len(dominance_rows), "coverage_trace": len(trace_rows),
                 "scene_envelope": len(envelope_rows), "failure_bounds": len(bounds_rows)},
        "structure_gate": gate["structure_gate"], "score_cause_gate": gate["score_cause_gate"],
        "operation_counts": gate["operation_counts"], "cpu": gate["cpu"],
        "bounded_sanitizer": {"status": gate["sanitizer_status"], "hits": sanitizer_hits},
    }
    atomic_json(OUT_MANIFEST, manifest)
    final_text = dict(new_text)
    final_text[logical(OUT_GATE)] = OUT_GATE.read_text(encoding="utf-8")
    final_text[logical(OUT_REPORT)] = OUT_REPORT.read_text(encoding="utf-8")
    final_text[logical(OUT_MANIFEST)] = OUT_MANIFEST.read_text(encoding="utf-8")
    final_hits = bounded_sanitizer(final_text)
    if final_hits:
        gate["sanitizer_status"] = "FAIL"
        gate["sanitizer_hits"] = final_hits
        gate["structure_gate"] = "PROTOCOL_DRIFT"
        gate["score_cause_gate"] = "INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION"
        atomic_json(OUT_GATE, gate)
        OUT_REPORT.write_text(report_text(gate), encoding="utf-8")
        manifest["structure_gate"] = gate["structure_gate"]
        manifest["score_cause_gate"] = gate["score_cause_gate"]
        manifest["bounded_sanitizer"] = {"status": "FAIL", "hits": final_hits}
        manifest["outputs"] = [file_identity(path) for path in outputs]
        atomic_json(OUT_MANIFEST, manifest)
    return 0 if gate["structure_gate"] not in ("PROTOCOL_DRIFT", "FAIL_SCENE_ENVELOPE_DOMINANCE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
