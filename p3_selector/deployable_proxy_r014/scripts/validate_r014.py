#!/usr/bin/env python3
"""Read-only dynamic validator for the completed r014 evidence chain."""
from __future__ import annotations

import csv
import hashlib
import json
import pickle
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "p3_selector/deployable_proxy_r014"
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
ALLOWED = {
    "claude_code_and_supervisor.md",
    "dis/server_reports/orientbench-c-r014-20260808.md",
    "p3_selector/deployable_proxy_r014/protocol_r014.json",
    "p3_selector/deployable_proxy_r014/runtime_registry_r014.json",
    "p3_selector/deployable_proxy_r014/scripts/inventory_and_repair_provenance_r014.py",
    "p3_selector/deployable_proxy_r014/scripts/run_tta_forward_r014.py",
    "p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py",
    "p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py",
    "p3_selector/deployable_proxy_r014/scripts/evaluate_hrsc_r014.py",
    "p3_selector/deployable_proxy_r014/scripts/validate_r014.py",
    "p3_selector/deployable_proxy_r014/reports/completion_status_r014.json",
    "p3_selector/deployable_proxy_r014/reports/provenance_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/fair_universe_join_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/transform_sanity_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/feature_summary_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/source_cv_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/unit_results_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/dataset_results_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/bootstrap_replicates_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/hrsc_results_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/gate_r014.json",
    "p3_selector/deployable_proxy_r014/reports/resource_telemetry_r014.csv",
    "p3_selector/deployable_proxy_r014/reports/evidence_manifest_r014.json",
    "p3_selector/deployable_proxy_r014/docs/deployable_proxy_r014.md",
    "p3_selector/deployable_proxy_r014/docs/deployable_proxy_r014.svg",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/equivariance_selector_r014.svg",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r014.csv",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r014.csv",
}


def check(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(name: str) -> list[dict]:
    with (BASE / "reports" / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    checks = 0
    def ok(value, message):
        nonlocal checks
        check(bool(value), message); checks += 1

    protocol = json.loads((BASE / "protocol_r014.json").read_text())
    ok(protocol["protocol_frozen"] and protocol["bootstrap_replicates"] == 1000, "protocol")
    ok(protocol["minimum_effect_nrc"] == 0.02 and len(protocol["core_units"]) == 6, "frozen gates")

    fair_gt = ROOT / "top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/annfiles_dotaformat"
    ok(len(list(fair_gt.glob("*.txt"))) == 4362, "FAIR annotation universe")
    gt_count = sum(len(path.read_text(errors="ignore").splitlines()) for path in fair_gt.glob("*.txt"))
    ok(gt_count == 78644, f"FAIR GT count: {gt_count}")
    for view in ("identity", "hflip", "vflip"):
        with (RUNTIME / f"raw/fair24/{view}.pkl").open("rb") as handle:
            raw = pickle.load(handle)
        ok(len(raw) == 4362 and len({str(row['img_id']) for row in raw}) == 4362, f"FAIR {view}")
    with (RUNTIME / "raw/fair24/identity.pkl").open("rb") as handle:
        fair_identity = pickle.load(handle)
    ok(sum(len(row["pred_instances"]["scores"]) for row in fair_identity) == 488194, "FAIR prediction count")

    provenance = rows("provenance_r014.csv")
    ok(len(provenance) == 6 and all(row["status"] == "PASS_PROVENANCE_R014" for row in provenance), "provenance 6/6")
    fair_row = next(row for row in provenance if row["unit"] == "FAIR1M-v1.0/24")
    ok(abs(float(fair_row["official_AP50"]) - 0.3461585939) <= 2e-3, "FAIR AP50")
    ok(abs(float(fair_row["official_AP75"]) - 0.2422395200) <= 2e-3, "FAIR AP75")
    inventory = rows("tta_inventory_r014.csv")
    ok(len(inventory) == 18 and all(int(row["image_records"]) > 0 for row in inventory), "Core TTA inventory")
    transform = rows("transform_sanity_r014.csv")
    ok(len(transform) == 2 and all(row["status"] == "PASS" for row in transform), "transform smoke")

    features = rows("feature_summary_r014.csv")
    ok({row["unit"] for row in features} >= set(protocol["core_units"] + ["HRSC2016/LSKNet"]), "feature registry")
    forbidden = {"gt", "angle_error", "risk", "aspect_ratio", "d_cal_daudit_split_flag"}
    for key in "ABCDEFGH":
        path = RUNTIME / f"features/{key}.parquet"
        if path.is_file():
            ok(not (forbidden & set(pd.read_parquet(path, columns=None).columns)), f"feature leakage {key}")

    seal = json.loads((RUNTIME / "prelabel_seal.json").read_text())
    ok(not seal["source_early_stop_targets"], "source early stop")
    for entry in seal["files"]:
        path = ROOT / entry["path"]
        ok(path.stat().st_size == entry["bytes"] and sha256(path) == entry["sha256"], f"seal {path}")
    source = rows("source_cv_r014.csv")
    ok(len(source) == 12 and all(row["status"] == "NO_EARLY_STOP" for row in source), "nested source CV")

    unit = rows("unit_results_r014.csv")
    ok(len(unit) == 6, "unit count")
    ok(all(float(row["delta_nrc"]) >= .02 and float(row["ci_low"]) > 0 and float(row["holm6_p"]) < .05 and row["supported"] == "True" for row in unit), "unit gate")
    dataset = rows("dataset_results_r014.csv")
    ok(len(dataset) == 3 and all(float(row["delta_nrc"]) >= .02 and float(row["ci_low"]) > 0 and float(row["holm3_p"]) < .05 and row["supported"] == "True" for row in dataset), "dataset gate")
    boot = rows("bootstrap_replicates_r014.csv")
    counts = {}
    for row in boot:
        counts[(row["level"], row["key"])] = counts.get((row["level"], row["key"]), 0) + 1
    ok(len(counts) == 9 and all(value == 1000 for value in counts.values()), "paired bootstrap counts")

    hrsc = rows("hrsc_results_r014.csv")
    ok(len(hrsc) == 1 and hrsc[0]["status"] == "INCONCLUSIVE_INDEPENDENT_HRSC_R014", "HRSC verdict")
    ok(int(hrsc[0]["bootstrap_reps"]) == 1000 and hrsc[0]["target_angle_labels_used_for_fit"] == "False", "HRSC seal")
    ok(abs(float(hrsc[0]["ap50"]) - .905) <= .002 and abs(float(hrsc[0]["ap75"]) - .894) <= .002, "HRSC AP parity")
    ok(float(hrsc[0]["delta_linear_minus_eqs"]) >= .02 and float(hrsc[0]["ci_low"]) <= 0 < float(hrsc[0]["ci_high"]), "HRSC inconclusive interval")

    manuscript = (ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md").read_text()
    ok("0.1608" in manuscript and "0.0602" in manuscript and "区间跨零" in manuscript, "manuscript results")
    ok("3,896 image IDs" not in manuscript and "EQS 收益" not in manuscript, "superseded r012 text")
    ledger = rows("../../../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r014.csv") if False else None
    with (ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r014.csv").open(newline="", encoding="utf-8") as handle:
        ledger = list(csv.DictReader(handle))
    for row in ledger:
        ok(row["exact_claim"] in manuscript, f"claim text {row['claim_id']}")
        ok(hashlib.sha256(row["exact_claim"].encode()).hexdigest() == row["claim_sha256"], f"claim hash {row['claim_id']}")

    completion = json.loads((BASE / "reports/completion_status_r014.json").read_text())
    gate = json.loads((BASE / "reports/gate_r014.json").read_text())
    ok(completion["execution_completion"] == "FULL_COMPLETION", "completion")
    ok(gate["status"] == "PASS_DEPLOYABLE_EQS_R014" and gate["unit_support"] == 6 and gate["dataset_support"] == 3, "final gate")
    manifest = json.loads((BASE / "reports/evidence_manifest_r014.json").read_text())
    ok(manifest["self_reference"]["sha256"] == "N/A_SELF_REFERENCE", "manifest self reference")
    ok(manifest["counts"]["core_unit_bootstrap_replicates"] == 6000 and manifest["counts"]["hrsc_bootstrap_replicates"] == 1000, "manifest counts")
    for entry in manifest["tracked_outputs"] + manifest["runtime_artifacts"]:
        path = ROOT / entry["path"]
        ok(path.is_file() and path.stat().st_size == entry["bytes"] and sha256(path) == entry["sha256"], f"manifest entry {path}")
    ok(subprocess.check_output(["git", "hash-object", "dis/B.md"], cwd=ROOT, text=True).strip() == "3181a862137918f1dd41677893937c12b3c39c28", "protected dis/B")
    changed = set(subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True).splitlines())
    paths = {line[3:] for line in changed if len(line) >= 4 and not line.endswith("scripts/__pycache__/")}
    ok(paths <= ALLOWED, f"write scope: {sorted(paths - ALLOWED)}")
    print(f"VALID_R014_FULL_COMPLETION checks={checks}")


if __name__ == "__main__":
    main()
