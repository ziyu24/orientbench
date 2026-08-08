#!/usr/bin/env python3
"""Read-only validator for the r012 provenance-stop package."""
import csv
import hashlib
import json
import pickle
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "p3_selector/deployable_proxy_r012"
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r012"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    a0 = json.loads((RUNTIME / "a0_preflight.json").read_text())
    require(a0["status"] == "FAIL_PROVENANCE_R012", "unexpected A0 state")
    fair = {row["source"]: row for row in a0["fair"]}
    require(fair["split"]["set_size"] == 4362, "FAIR split size")
    require(fair["gt"]["prediction_or_gt_count"] == 78644, "FAIR GT count")
    require(fair["r011_raw"]["set_size"] == 3896, "r011 raw universe")
    require(fair["r011_raw"]["missing_vs_split"] == 466, "missing-image count")
    require(fair["m069_universe"]["set_size"] == 4362, "m069 universe")
    require(fair["m069_universe"]["prediction_or_gt_count"] == 488194, "m069 prediction count")
    split_dir = Path("/home/rspip/cqc/data/dataset/fair1m1.0/split/val/annfiles")
    split_ids = {p.stem for p in split_dir.glob("*.xml")}
    require(len(split_ids) == 4362, "live FAIR split size")
    raw_path = ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds/FAIR1M-v1.0_24/identity.pkl"
    raw = pickle.load(raw_path.open("rb"))
    raw_ids = {str(row["img_id"]) for row in raw}
    require(len(raw_ids) == 3896 and len(split_ids - raw_ids) == 466, "live FAIR raw mismatch")
    require(sum(len(row["pred_instances"]["scores"]) for row in raw) == 484332, "live FAIR raw prediction count")
    m069_ids = {row["image_id"] for row in csv.DictReader((ROOT / "outputs/persistent_artifacts/m069_fullval_reliability/D/image_universe.csv").open())}
    require(m069_ids == split_ids, "live m069 universe")
    soda_tiles = {p.stem for p in Path("/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/images").iterdir() if p.is_file()}
    require(len(soda_tiles) == 22994 and all("__" in tile for tile in soda_tiles), "live SODA mother map")
    provenance = list(csv.DictReader((BASE / "reports/provenance_r012.csv").open()))
    require(len(provenance) == 6, "Core-6 provenance rows")
    require(sum(r["status"] == "PASS_PROVENANCE_R012" for r in provenance) == 5, "expected 5/6 clean units")
    fair_row = next(r for r in provenance if r["dataset"] == "FAIR1M-v1.0")
    require(fair_row["status"] == "FAIL_PROVENANCE_R012", "FAIR must fail")
    gate = json.loads((BASE / "reports/gate_r012.json").read_text())
    require(gate["status"] == "FAIL_PROVENANCE_R012", "gate state")
    require(gate["target_labels_attached"] is False, "target labels must remain unattached")
    for report in ("transform_sanity_r012.csv", "feature_summary_r012.csv", "source_cv_r012.csv", "leave_dataset_results_r012.csv", "bootstrap_replicates_r012.csv"):
        rows = list(csv.DictReader((BASE / "reports" / report).open()))
        require(rows and all(r.get("status") == "NOT_RUN_PROVENANCE_GATE" for r in rows), report)
    require(not any((RUNTIME / name).exists() for name in ("models", "scores") if any((RUNTIME / name).iterdir())), "unexpected fitted model or score")
    manifest = json.loads((BASE / "reports/evidence_manifest_r012.json").read_text())
    require(manifest["status"] == "FAIL_PROVENANCE_R012", "manifest state")
    for row in manifest["outputs"]:
        if row["sha256"] == "N/A_SELF_REFERENCE":
            continue
        path = ROOT / row["path"]
        require(path.stat().st_size == row["bytes"] and sha256(path) == row["sha256"], f"manifest identity {row['path']}")
    manuscript = (ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md").read_text()
    for forbidden in ("PASS_", "FAIL_", "TGRS-ready", "CVPR-ready", "JSTARS-ready", "authorized paths", "fixed-dose raw incomplete"):
        require(forbidden not in manuscript, f"manuscript forbidden token {forbidden}")
    ledger = list(csv.DictReader((ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r012.csv").open()))
    for row in ledger:
        claim = row["exact_claim"]
        require(claim in manuscript, f"ledger claim absent {row['claim_id']}")
        require(hashlib.sha256(claim.encode()).hexdigest() == row["claim_sha256"], f"ledger hash {row['claim_id']}")
    allowed = set(manifest["authorization"])
    status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True)
    for line in status.splitlines():
        path = line[3:]
        if path.startswith("top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/"):
            continue
        require(path in allowed, f"unauthorized worktree path {path}")
    require(subprocess.check_output(["git", "hash-object", "dis/B.md"], cwd=ROOT, text=True).strip() == "3181a862137918f1dd41677893937c12b3c39c28", "protected dis/B.md changed")
    print("VALID_R012_PROVENANCE_STOP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
