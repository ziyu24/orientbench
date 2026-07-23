#!/usr/bin/env python3
"""Verify SUPERVISOR_051 handoff/recovery artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "top_journal_v3"
REPORTS = OUT / "reports"
DOCS = OUT / "docs"
MANIFEST = ROOT / "outputs/persistent_artifacts/manifest_051.json"

REQUIRED = [
    "docs/codex_handoff_map_051.md",
    "reports/artifact_locator_051.csv",
    "reports/real_cell_artifact_status_051.csv",
    "docs/real_evidence_gap_plan_051.md",
    "docs/evidence_recovery_decision_051.md",
    "reports/heartbeat_051.json",
    "docs/codex_latest_report.md",
]


FORBIDDEN = [
    "TPAMI ready",
    "CVPR ready",
    "full project complete",
    "DOTA SOTA",
    "PSC angle head finally proven broken",
    "proxy/synthetic final evidence",
]


def git_status(path: str) -> str:
    p = subprocess.run(["git", "status", "--short", "--", path], cwd=ROOT, capture_output=True, text=True, check=False)
    return p.stdout.strip()


def main() -> int:
    failures = []
    checks = []

    for rel in REQUIRED:
        p = OUT / rel
        ok = p.exists() and p.stat().st_size > 0
        checks.append({"check": f"required {rel}", "pass": ok})
        if not ok:
            failures.append(f"missing:{rel}")

    latest = (DOCS / "codex_latest_report.md").read_text(encoding="utf-8") if (DOCS / "codex_latest_report.md").exists() else ""
    ok = latest.startswith("👇👇👇👇👇👇\n") and latest.rstrip().endswith("👆👆👆👆👆👆")
    checks.append({"check": "latest report has entrance/exit", "pass": ok})
    if not ok:
        failures.append("latest_report_fence")

    status = pd.read_csv(REPORTS / "real_cell_artifact_status_051.csv") if (REPORTS / "real_cell_artifact_status_051.csv").exists() else pd.DataFrame()
    ok = len(status) >= 12 and {"cell_id", "real_raw_post_nms_exists", "schema_17field_exists", "matched_table_exists"}.issubset(status.columns)
    checks.append({"check": "real cell artifact status covers required cells", "pass": ok})
    if not ok:
        failures.append("cell_status_incomplete")

    if MANIFEST.exists():
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        arts = m.get("artifacts", [])
        needed = {"sha256", "source_checkpoint", "split", "can_recompute"}
        ok = bool(arts) and all(needed.issubset(a.keys()) and a.get("sha256") for a in arts)
        checks.append({"check": "manifest_051 has sha256/source checkpoint/split/can_recompute", "pass": ok})
        if not ok:
            failures.append("manifest_fields")
        policy_ok = not m.get("host_training_started") and not m.get("thresholds_modified") and not m.get("dcal_daudit_modified") and not m.get("full_matrix_added")
        checks.append({"check": "manifest records no forbidden action", "pass": policy_ok})
        if not policy_ok:
            failures.append("manifest_policy")
    else:
        checks.append({"check": "manifest_051 optional exists", "pass": False})
        failures.append("manifest_missing")

    for rel in ["configs/thresholds.yaml", "outputs/bench_core/splits"]:
        st = git_status(rel)
        ok = st == "" or all(line.startswith("??") for line in st.splitlines())
        checks.append({"check": f"no tracked modification {rel}", "pass": ok, "status": st})
        if not ok:
            failures.append(f"git_modified:{rel}")

    all_text = ""
    for p in OUT.rglob("*"):
        if "__pycache__" in p.parts:
            continue
        if p.name.startswith("verification_") or p.name.startswith("verify_"):
            continue
        if p.is_file() and p.suffix.lower() in {".md", ".csv", ".json", ".py", ".txt"}:
            all_text += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    for bad in FORBIDDEN:
        ok = bad not in all_text
        checks.append({"check": f"forbidden text absent: {bad}", "pass": ok})
        if not ok:
            failures.append(f"forbidden:{bad}")

    large = [str(p.relative_to(ROOT)) for p in OUT.rglob("*") if p.is_file() and p.stat().st_size > 50 * 1024 * 1024]
    ok = not large
    checks.append({"check": "git no large files under top_journal_v3", "pass": ok, "large_files": large})
    if not ok:
        failures.append("large_files")

    result = {"status": "pass" if not failures else "fail", "failures": failures, "checks": checks}
    (REPORTS / "verification_handoff_recovery_051.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPORTS / "verification_handoff_recovery_051.md").write_text(
        "# Verification 051\n\n"
        f"status: {result['status']}\n\n"
        + "\n".join(f"- {'PASS' if c['pass'] else 'FAIL'}: {c['check']}" for c in checks)
        + "\n",
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
