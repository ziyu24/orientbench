#!/usr/bin/env python3
"""Read-only validator for the r014 Git-preflight stop package."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "p3_selector/deployable_proxy_r014"
EXPECTED = {
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/DIOR-R_22_P.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/DIOR-R_3_D.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/DIOR-R_61_S.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/FAIR1M-v1_0_24_P.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/SODA-A_23_D.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/SODA-A_4_S.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_DIOR-R_22_P.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_DIOR-R_3_D.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_DIOR-R_61_S.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_FAIR1M-v1_0_24_P.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_SODA-A_23_D.err",
    "top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/surv_SODA-A_4_S.err",
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    completion = json.loads((BASE / "reports/completion_status_r014.json").read_text())
    gate = json.loads((BASE / "reports/gate_r014.json").read_text())
    check(completion["execution_completion"] == "INCOMPLETE_BLOCKED", "completion class")
    check(completion["scientific_verdict"] == "NOT_EVALUATED", "scientific class")
    check(gate["core_eqs"] == gate["hrsc"] == "NOT_EVALUATED", "science must not be evaluated")
    check(gate["target_labels_attached"] is False, "target labels")
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True)
    observed = {line[3:] for line in status.splitlines() if line.startswith("?? ") and "/risk_logs/" in line}
    check(observed == EXPECTED, "dirty-tree witnesses changed")
    check(subprocess.check_output(["git", "hash-object", "dis/B.md"], cwd=ROOT, text=True).strip() == "3181a862137918f1dd41677893937c12b3c39c28", "protected file changed")
    print("VALID_R014_INCOMPLETE_BLOCKED")


if __name__ == "__main__":
    main()
