#!/usr/bin/env python3
"""Independent validator for the r031 G0 gated-early-stop evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/r031_circularity_asset_preflight"
DISPATCH = "98443feb40d786fb7eb8faf8f36444496fe6b2c5"
PLAN_SHA = "5b95da060237d5dc37d77996483c2c7d8e4e0a1b2666e3d6543ecce0bb60d6d4"
PTH_SHA = "eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c"
EXPECTED_DIRTY = {
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_final/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_v2/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/error.json",
    "top_journal_v3_reaudit_055/measurement_validity_r022_20260813/",
    "top_journal_v3_reaudit_055/measurement_validity_r023_20260813/",
}
FULL_INVENTORY_OUTPUTS = {
    "source_inventory.csv",
    "field_availability.csv",
    "join_feasibility.csv",
    "official_annotation_inventory.csv",
    "dota_gt_provenance.json",
    "r032_readiness.json",
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    preflight = json.loads((OUT / "preflight.json").read_text())
    check("dispatch_identity", preflight["post_pull_head"] == DISPATCH, preflight["post_pull_head"])
    check("completion_mapping", preflight["completion_mode"] == "gated_early_stop" and preflight["execution_status"] == "complete", {"completion_mode": preflight["completion_mode"], "execution_status": preflight["execution_status"]})
    check("g0_dirty_recorded", preflight["gate_results"]["G0_IDENTITY"] == "EARLY_STOP_DIRTY_WORKTREE" and not preflight["worktree_clean"], preflight["gate_results"])
    check("initial_dirty_set", set(preflight["pre_existing_untracked_paths"]) == EXPECTED_DIRTY, preflight["pre_existing_untracked_paths"])
    check("index_was_clean", preflight["index_clean"] is True, preflight["index_clean"])
    check("worker_identity", preflight["worker_id"] == "server-primary" and run("git", "config", "--local", "--get", "paper.worker-id") == "server-primary", preflight["worker_id"])
    plan = ROOT / "dis/plans/C/c-r031-circularity-asset-preflight-20260813/sug.md"
    active = ROOT / "dis/sug.md"
    check("plan_hash", sha256(plan) == PLAN_SHA and sha256(active) == PLAN_SHA, {"plan": sha256(plan), "active": sha256(active)})
    check("dispatch_is_ancestor", subprocess.run(["git", "merge-base", "--is-ancestor", DISPATCH, "HEAD"], cwd=ROOT).returncode == 0, preflight["post_pull_head"])
    check("current_index_clean", subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0, run("git", "diff", "--cached", "--name-only"))
    pth_readme = Path(preflight["pth_readme_path"])
    check("pth_readme", pth_readme.is_file() and sha256(pth_readme) == PTH_SHA, {"readable": pth_readme.is_file(), "sha256": sha256(pth_readme) if pth_readme.is_file() else None})
    check("no_scientific_asset_inspection", preflight["scientific_asset_inspection_started"] is False and preflight["tasks_not_run"] == ["T1", "T2", "T3", "T4", "T5"], {"started": preflight["scientific_asset_inspection_started"], "tasks_not_run": preflight["tasks_not_run"]})
    existing_forbidden = sorted(name for name in FULL_INVENTORY_OUTPUTS if (OUT / name).exists())
    check("no_post_stop_inventory_outputs", not existing_forbidden, existing_forbidden)
    check("no_readiness_adjudication", preflight["readiness_status"] == "NOT_EMITTED_G0_EARLY_STOP" and preflight["scientific_outcome"] == "NOT_ADJUDICATED", {"readiness": preflight["readiness_status"], "scientific_outcome": preflight["scientific_outcome"]})

    manifest_path = OUT / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"artifacts": []}
    manifest_checks = []
    for row in manifest.get("artifacts", []):
        path = ROOT / row["path"]
        manifest_checks.append(path.is_file() and path.stat().st_size == row["bytes"] and sha256(path) == row["sha256"])
    check("artifact_manifest", bool(manifest_checks) and all(manifest_checks), {"entries": len(manifest_checks), "passed": sum(manifest_checks)})

    result = {
        "schema_version": 1,
        "dispatch_id": "orientbench-c-r031-circularity-asset-preflight-20260813",
        "validation_scope": "G0_GATED_EARLY_STOP_ONLY",
        "status": "PASS" if all(row["passed"] for row in checks) else "FAIL",
        "checks": checks,
        "mutation_tests": {
            "status": "NOT_RUN_NOT_APPLICABLE_AFTER_G0",
            "reason": "The four preregistered mutations apply to T1-T5 inventory artifacts, which the G0 early stop prohibited creating."
        },
    }
    (OUT / "validation_r031.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
