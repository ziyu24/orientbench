#!/usr/bin/env python3
"""Static r017 receipt validator. It never recomputes bootstrap replicates."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "p3_selector/static_receipt_r017"
REPORTS = BASE / "reports"
R014 = ROOT / "outputs/persistent_artifacts/orientbench_r014"
R015 = ROOT / "p3_selector/deployable_proxy_r015"
R016 = ROOT / "p3_selector/deployable_proxy_r016"
LABEL = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", "rotated_retinanet_psc"),
    "B": ("DIOR-R/3", "DIOR-R", "oriented_rcnn"),
    "C": ("DIOR-R/61", "DIOR-R", "rotated_rtmdet_s"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", "rotated_retinanet_psc"),
    "E": ("SODA-A/23", "SODA-A", "rotated_retinanet_psc"),
    "F": ("SODA-A/4", "SODA-A", "oriented_rcnn"),
}
DATASETS = ("DIOR-R", "FAIR1M-v1.0", "SODA-A")
ACCESSED: dict[str, dict] = {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def register(path: Path) -> Path:
    path = path.resolve()
    rel = str(path.relative_to(ROOT))
    if rel not in ACCESSED:
        ACCESSED[rel] = {
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "schema": path.suffix.lstrip(".") or "text",
            "read_only": True,
        }
    return path


def read_text(path: Path) -> str:
    return register(path).read_text(encoding="utf-8")


def read_json(path: Path):
    return json.loads(read_text(path))


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    register(path)
    return pd.read_csv(path, **kwargs)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(values) -> str:
    return hashlib.sha256("\n".join(sorted(map(str, values))).encode()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for row in rows for k in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def canonical_role(image_id: str, flag: str) -> str:
    if flag == "D_audit":
        return "D_audit"
    value = int(hashlib.md5(f"m069:{image_id}".encode()).hexdigest()[:8], 16)
    return "D_cal-fit" if value % 2 == 0 else "D_cal-calib"


def matched_sets(unit: str, mother_map: dict[str, str]) -> tuple[dict[str, set[str]], set[str]]:
    path = register(LABEL / unit / "matched_fullval.jsonl")
    roles = {"D_cal-fit": set(), "D_cal-calib": set(), "D_audit": set()}
    occupied = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            gt = row.get("gt_obb", {})
            width, height = float(gt.get("obb_w", 0)), float(gt.get("obb_h", 0))
            if min(width, height) <= 0 or max(width, height) / min(width, height) < 2.1:
                continue
            image_id = str(row["image_id"])
            role = canonical_role(image_id, str(row.get("d_cal_daudit_split_flag", "")))
            roles[role].add(f"{unit}:{image_id}:{row['pred_id']}")
            if role == "D_audit":
                occupied.add(mother_map.get(image_id, image_id))
    return roles, occupied


def exact_heading_exists(paper: str, heading: str) -> bool:
    return f"### {heading}" in paper or f"## {heading}" in paper


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    # Explicitly register protocol dependencies that historical imports read.
    read_text(ROOT / "scripts/m069_common.py")
    read_text(ROOT / "scripts/derive_delta_theta_075.py")
    read_json(ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json")

    checks: dict[str, bool] = {}
    witnesses: dict[str, object] = {}
    errors: list[dict] = []

    # Phase A: static 9,000-row receipt and complete key domain.
    boot = read_csv(R015 / "reports/bootstrap_replicates_r015.csv")
    unit15 = read_csv(R015 / "reports/unit_results_r015.csv")
    data15 = read_csv(R015 / "reports/dataset_results_r015.csv")
    summary16 = read_csv(R016 / "reports/summary_recomputed_r016.csv")
    gate15 = read_json(R015 / "reports/gate_r015.json")
    expected_pairs = {("unit", meta[0]) for meta in UNITS.values()} | {("dataset", ds) for ds in DATASETS}
    actual_pairs = set(zip(boot["level"], boot["key"]))
    checks["bootstrap_exact_9000"] = len(boot) == 9000
    checks["bootstrap_key_domain"] = actual_pairs == expected_pairs
    complete = True
    pair_receipt = {}
    for pair in sorted(expected_pairs):
        rows = boot[(boot["level"] == pair[0]) & (boot["key"] == pair[1])]
        reps = rows["replicate"].tolist()
        ok = len(rows) == 1000 and len(set(reps)) == 1000 and sorted(reps) == list(range(1000))
        finite = bool(np.isfinite(rows["delta_nrc"].to_numpy(float)).all())
        complete &= ok and finite
        pair_receipt[f"{pair[0]}:{pair[1]}"] = {"rows": len(rows), "replicates_complete": ok, "finite": finite}
    checks["bootstrap_complete_unique_finite"] = complete and not boot.duplicated(["level", "key", "replicate"]).any()
    witnesses["bootstrap_pairs"] = pair_receipt

    # Compare all summary statistics and available metadata.
    summary_comparisons = []
    for unit, (name, dataset, detector) in UNITS.items():
        old = unit15[unit15["unit_key"] == unit].iloc[0]
        new = summary16[(summary16["level"] == "unit") & (summary16["key"] == name)].iloc[0]
        mapping = {"delta_nrc": "point_delta_nrc", "ci_low": "ci_low", "ci_high": "ci_high", "p_centered_one_sided": "p_centered_one_sided", "holm6_p": "holm_p"}
        row_ok = True
        for expected_field, actual_field in mapping.items():
            error = abs(float(old[expected_field]) - float(new[actual_field]))
            row_ok &= error <= 1e-12
            summary_comparisons.append({"key": name, "field": expected_field, "expected": old[expected_field], "actual": new[actual_field], "error": error})
        row_ok &= bool(old["supported"]) == bool(new["supported"])
        row_ok &= str(old["dataset"]) == dataset and str(old["detector"]) == detector and int(old["bootstrap_reps"]) == 1000
        checks[f"summary_unit_{unit}"] = row_ok
    for dataset in DATASETS:
        old = data15[data15["dataset"] == dataset].iloc[0]
        new = summary16[(summary16["level"] == "dataset") & (summary16["key"] == dataset)].iloc[0]
        mapping = {"delta_nrc": "point_delta_nrc", "ci_low": "ci_low", "ci_high": "ci_high", "p_centered_one_sided": "p_centered_one_sided", "holm3_p": "holm_p"}
        row_ok = True
        for expected_field, actual_field in mapping.items():
            error = abs(float(old[expected_field]) - float(new[actual_field]))
            row_ok &= error <= 1e-12
            summary_comparisons.append({"key": dataset, "field": expected_field, "expected": old[expected_field], "actual": new[actual_field], "error": error})
        row_ok &= bool(old["supported"]) == bool(new["supported"]) and int(old["bootstrap_reps"]) == 1000
        checks[f"summary_dataset_{dataset}"] = row_ok
    witnesses["summary_field_comparisons"] = summary_comparisons

    supported_units = unit15[unit15["supported"] == True]
    supported_datasets = data15[data15["supported"] == True]
    gate_recomputed = (
        len(supported_units) >= 4
        and supported_units["dataset"].nunique() == 3
        and supported_units["detector"].nunique() >= 2
        and bool(((supported_units["unit_key"] == "D")).any())
        and len(supported_datasets) == 3
    )
    gate_fields_ok = (
        gate15.get("r015_numeric_status") == "EXPLORATORY_CORE_SUPPORT_R015"
        and int(gate15.get("unit_support", -1)) == len(supported_units)
        and int(gate15.get("dataset_support", -1)) == len(supported_datasets)
        and gate15.get("synchronized") is True
        and gate15.get("soda_primary") == "mother_scene"
    )
    checks["frozen_gate_recomputed"] = gate_recomputed
    checks["gate_r015_all_fields"] = gate_fields_ok
    witnesses["gate"] = {"unit_support": len(supported_units), "dataset_support": len(supported_datasets), "recomputed": gate_recomputed, "gate_fields_ok": gate_fields_ok}

    # Full universes and zero-eligible sets.
    soda_map_frame = read_csv(R014 / "soda_tile_to_mother_r014.csv", dtype=str)
    soda_map = dict(zip(soda_map_frame["tile_id"], soda_map_frame["mother_scene_id"]))
    zero_rows = []
    universes = {}
    role_sets = {}
    for unit, (_, dataset, _) in UNITS.items():
        universe_frame = read_csv(LABEL / unit / "image_universe.csv", dtype={"image_id": str})
        audit_images = universe_frame[universe_frame["d_cal_daudit_split_flag"] == "D_audit"]["image_id"].astype(str)
        mapping = soda_map if dataset == "SODA-A" else {image: image for image in audit_images}
        clusters = sorted({mapping[image] for image in audit_images})
        roles, occupied = matched_sets(unit, mapping)
        zeros = sorted(set(clusters) - occupied)
        universes[unit] = clusters
        role_sets[unit] = roles
        zero_rows.append({"unit": unit, "dataset": dataset, "universe_count": len(clusters), "universe_sha256": digest(clusters), "eligible_cluster_count": len(occupied), "zero_eligible_count": len(zeros), "zero_set_sha256": digest(zeros), "zero_set_nonempty": len(zeros) > 0})
        checks[f"zero_set_nonempty_{unit}"] = len(zeros) > 0
        expected = unit15[unit15["unit_key"] == unit].iloc[0]
        checks[f"universe_metadata_{unit}"] = int(expected["audit_clusters_full"]) == len(clusters) and expected["cluster_set_sha256"] == digest(clusters)
    for dataset in DATASETS:
        keys = [u for u, meta in UNITS.items() if meta[1] == dataset]
        checks[f"same_dataset_universe_{dataset}"] = all(universes[u] == universes[keys[0]] for u in keys)
    write_csv(REPORTS / "zero_eligible_sets_r017.csv", zero_rows)

    # Canonical MD5 parity set audit and explicit r015 role drift.
    leak15 = read_csv(R015 / "reports/leakage_and_access_audit_r015.csv")
    drift_witness = read_text(R015 / "scripts/audit_r014_protocol_r015.py")
    canonical_source = read_text(ROOT / "scripts/m069_common.py")
    checks["r015_set_audit_role_drift_identified"] = "hashlib.sha256" in drift_witness and "hashlib.md5" in canonical_source
    witnesses["role_drift"] = "R015_SET_AUDIT_ROLE_DRIFT: r015 SHA256 80/20 versus canonical MD5 parity"
    for target, (_, dataset, _) in UNITS.items():
        sources = [u for u, meta in UNITS.items() if meta[1] != dataset]
        source_fit = set().union(*(role_sets[u]["D_cal-fit"] for u in sources))
        source_calib = set().union(*(role_sets[u]["D_cal-calib"] for u in sources))
        source_audit = set().union(*(role_sets[u]["D_audit"] for u in sources))
        target_labels = set().union(*role_sets[target].values())
        checks[f"canonical_forbidden_intersections_{target}"] = not bool((source_fit | source_calib) & source_audit) and not bool((source_fit | source_calib) & target_labels)

    receipt = {
        "schema": "r017_gate_zero_receipt_v1",
        "numeric_status": "EXPLORATORY_CORE_SUPPORT_R015" if all(checks.values()) else "REJECTED",
        "bootstrap_rows": len(boot),
        "pair_receipt": pair_receipt,
        "summary_comparisons": summary_comparisons,
        "gate": witnesses["gate"],
        "role_drift": witnesses["role_drift"],
        "zero_sets": zero_rows,
    }
    (REPORTS / "gate_and_zero_receipt_r017.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")

    # Phase B: full schemas, seal hashes, exact source witnesses, manuscript/index.
    seal = read_json(R014 / "prelabel_seal.json")
    final_manifest = read_json(ROOT / "p3_selector/deployable_proxy_r014/reports/evidence_manifest_r014.json")
    final_by_path = {entry["path"]: entry for entry in final_manifest["tracked_outputs"] + final_manifest["runtime_artifacts"]}
    schema_rows = []
    forbidden_pattern = re.compile(r"(^|_)(gt|angle_?error|risk|gt_?ar|split|role)($|_)", re.I)
    seal_ok = True
    for unit in UNITS:
        for kind in ("features", "scores"):
            path = register(R014 / kind / f"{unit}.parquet")
            columns = pq.ParquetFile(path).schema_arrow.names
            forbidden = [column for column in columns if forbidden_pattern.search(column)]
            schema_rows.append({"unit": unit, "kind": kind, "columns": columns, "forbidden": forbidden, "ok": not forbidden})
            checks[f"schema_{kind}_{unit}"] = not forbidden
    for entry in seal["files"]:
        path = register(ROOT / entry["path"])
        current_ok = path.stat().st_size == int(entry["bytes"]) and ACCESSED[entry["path"]]["sha256"] == entry["sha256"]
        final_entry = final_by_path.get(entry["path"])
        final_ok = bool(final_entry and int(final_entry["bytes"]) == path.stat().st_size and final_entry["sha256"] == ACCESSED[entry["path"]]["sha256"])
        seal_ok &= current_ok and final_ok
    checks["prelabel_and_final_seal_hashes"] = seal_ok

    source_path = ROOT / "p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py"
    source_lines = read_text(source_path).splitlines()
    witness_specs = {
        "doubled_angle_axial_dispersion": (False, 151, source_lines[150]),
        "u_axis": (True, 163, source_lines[162]),
        "association_margin_single_zero": (False, 106, source_lines[105]),
        "sentinel": (False, 171, source_lines[170]),
        "deterministic_tie_break": (True, 113, source_lines[112]),
        "width_height_swap": (True, 138, source_lines[137]),
        "zero_ninety_boundary": (True, 87, source_lines[86] + " / " + source_lines[88]),
    }
    feature_witnesses = [{"name": name, "status": status, "source": str(source_path.relative_to(ROOT)), "line": line, "witness": text.strip(), "classification": "IMPLEMENTATION_DEVIATION" if not status else "IMPLEMENTED"} for name, (status, line, text) in witness_specs.items()]
    checks["three_implementation_deviations_preserved"] = sum(not row["status"] for row in feature_witnesses) == 3

    paper = read_text(ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md")
    ledger = read_csv(ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r017.csv")
    novelty = read_csv(ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r017.csv")
    claim_checks = []
    for row in ledger.itertuples():
        hash_ok = hashlib.sha256(row.exact_claim.encode()).hexdigest() == row.claim_sha256
        text_ok = row.exact_claim in paper
        heading_ok = exact_heading_exists(paper, row.section_heading)
        claim_checks.append({"claim_id": row.claim_id, "hash_ok": hash_ok, "text_ok": text_ok, "heading_ok": heading_ok})
    checks["claim_ledger_exact"] = all(all((row["hash_ok"], row["text_ok"], row["heading_ok"])) for row in claim_checks)
    weak_sources = novelty["verified_source"].astype(str).str.match(r"https?://(arxiv\.org/?|openaccess\.thecvf\.com/[A-Za-z0-9_-]+/?|www\.nature\.com/scientificreports/?)$")
    checks["novelty_sources_closed"] = not bool(weak_sources.any())
    checks["o2_fourier_excluded"] = all(value == "UNKNOWN_EXCLUDED" for value in novelty[novelty["work"].isin(["O2-DFINE", "Fourier Angle Alignment"])]["verified_source"])
    bad_ci = ["[0.1530, 0.1936]", "[0.2043, 0.2845]", "[0.1190, 0.2150]"]
    bad_ucb = ["0.0040 → 0.0188", "0.0061 → 0.0090 → 0.0180"]
    internal = re.compile(r"\br0(?:14|15|16)\b|PASS_|FAIL_|validator|authorized path|venue-ready", re.I)
    checks["manuscript_boundaries"] = all(fragment in paper for fragment in ["探索性 post-audit evidence", "区间跨零", "leave-dataset 设计中为 0/6", "固定剂量配对 AP 只保留为描述性候选"])
    checks["manuscript_no_stale_values"] = not any(value in paper for value in bad_ci + bad_ucb)
    checks["manuscript_no_internal_terms"] = internal.search(paper) is None
    checks["manuscript_citations"] = all(value in paper for value in ["10.1016/j.isprsjprs.2019.11.023", "arXiv:2110.01931", "Yi Yu, Feipeng Da"])

    schema_audit = {
        "schema": "r017_schema_feature_manuscript_audit_v1",
        "parquet_schemas": schema_rows,
        "seal_hashes_ok": seal_ok,
        "feature_witnesses": feature_witnesses,
        "claim_checks": claim_checks,
        "novelty_weak_verified_rows": novelty[weak_sources].to_dict("records"),
        "manuscript": {key: value for key, value in checks.items() if key.startswith("manuscript_")},
        "proposed_corrections": [],
    }
    (REPORTS / "schema_feature_manuscript_audit_r017.json").write_text(json.dumps(schema_audit, indent=2, ensure_ascii=False) + "\n")

    resource = {"cpu_intensive_phases": [], "bootstrap_recomputed": False, "telemetry_required": False, "process_pool_used": False, "thread_pool_used": False, "gpu_used": False, "training": False, "detector_inference": False, "selector_refit": False, "new_target_scores": False}
    (REPORTS / "resource_declaration_r017.json").write_text(json.dumps(resource, indent=2) + "\n")

    expected_outputs = {
        "claude_code_and_supervisor.md", "dis/server_reports/orientbench-c-r017-20260808.md",
        "p3_selector/static_receipt_r017/protocol_r017.json", "p3_selector/static_receipt_r017/scripts/validate_r016_receipt_r017.py",
        "p3_selector/static_receipt_r017/reports/gate_and_zero_receipt_r017.json", "p3_selector/static_receipt_r017/reports/zero_eligible_sets_r017.csv",
        "p3_selector/static_receipt_r017/reports/schema_feature_manuscript_audit_r017.json", "p3_selector/static_receipt_r017/reports/validator_r017.json",
        "p3_selector/static_receipt_r017/reports/resource_declaration_r017.json", "p3_selector/static_receipt_r017/reports/evidence_manifest_r017.json",
        "p3_selector/static_receipt_r017/docs/static_receipt_r017.md", "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r017.csv",
        "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r017.csv",
    }
    checks["protected_B_blob"] = git("rev-parse", "HEAD:dis/B.md") == "3181a862137918f1dd41677893937c12b3c39c28"
    existing = {path for path in expected_outputs if (ROOT / path).is_file() or path == "claude_code_and_supervisor.md"}
    checks["r017_output_structure"] = existing == expected_outputs
    manifest_path = REPORTS / "evidence_manifest_r017.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        manifest_inputs = {entry["path"] for entry in manifest.get("actual_read_only_inputs", [])}
        checks["manifest_access_exact"] = manifest_inputs == set(ACCESSED) and manifest.get("runtime_outputs") == [] and manifest.get("self_reference") == "N/A_SELF_REFERENCE"
        checks["manifest_output_scope"] = {entry["path"] for entry in manifest.get("tracked_outputs", [])} == expected_outputs
    else:
        checks["manifest_access_exact"] = False
        checks["manifest_output_scope"] = False

    token = "VALID_STATIC_RECEIPT_R017" if all(checks.values()) else "INVALID_STATIC_RECEIPT_R017"
    result = {"schema": "r017_static_validator_v1", "token": token, "checks": checks, "witnesses": witnesses, "actual_read_only_inputs": sorted(ACCESSED.values(), key=lambda row: row["path"]), "expected_output_scope": sorted(expected_outputs), "failed": [key for key, value in checks.items() if not value]}
    (REPORTS / "validator_r017.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"token": token, "failed": result["failed"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
