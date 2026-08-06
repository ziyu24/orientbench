#!/usr/bin/env python3
"""Deterministic r008 claim-ledger and manuscript reconciliation validator."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs"
REPORT = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports"
V077 = DOC / "orientation_reliability_paper_A_zh_v077.md"
V078 = DOC / "orientation_reliability_paper_A_zh_v078.md"
LEDGER = REPORT / "a1_claim_reconciliation_r008.csv"
GATE = REPORT / "a1_claim_reconciliation_gate_r008.json"

SCHEMA = ["claim_id","source_section","source_line","source_text","source_text_sha256",
          "claim_class","datasets","units","estimand","evidence_paths","evidence_status",
          "action","target_section","target_text","target_text_sha256","reason"]
CLAIM_RE = re.compile(r"(?:\d|%|显著|优于|认证|保证|部署|首次|首个|系统|证明|稳健|普适|LTT|FWER|Holm|certif|guarantee|deploy)", re.I)
FORBIDDEN = re.compile(r"正式认证|认证通过|保证控制|部署保证|formal certification|certified guarantee|FWER controlled|PASS_SPLIT_FST|PASS_BROAD_TARGET_FREE", re.I)
CONTEXT = re.compile(r"历史|撤回|无效|未闭环|探索性|不构成|history|withdrawn|invalid|inconclusive|exploratory|not", re.I)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()

def extracted(path: Path):
    rows = []
    section = ""
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            section = line.lstrip("#").strip()
        if CLAIM_RE.search(line):
            rows.append((n, section, line))
    return rows

def main() -> int:
    errors = []
    if not V077.exists() or not V078.exists() or not LEDGER.exists():
        errors.append("required input/output missing")
    old = V077.read_bytes(); new = V078.read_bytes()
    old_rows = extracted(V077); new_rows = extracted(V078)
    with LEDGER.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != SCHEMA:
            errors.append("ledger schema mismatch")
        ledger = list(reader)
    ids = [r["claim_id"] for r in ledger]
    if len(ids) != len(set(ids)):
        errors.append("duplicate claim_id")
    if len(ledger) != len(old_rows):
        errors.append(f"source coverage mismatch {len(ledger)} != {len(old_rows)}")
    old_keys = {(int(r["source_line"]), r["source_text_sha256"]) for r in ledger}
    expected_keys = {(n, sha(text.encode("utf-8"))) for n, _, text in old_rows}
    if old_keys != expected_keys:
        errors.append("source claim mapping mismatch")
    for row in ledger:
        if row["evidence_status"] not in {"VALID","QUALIFIED","INVALID","UNRESOLVED"}:
            errors.append(f"bad evidence status {row['claim_id']}")
        if row["action"] not in {"RETAIN","QUALIFY","QUARANTINE","REMOVE"}:
            errors.append(f"bad action {row['claim_id']}")
        try:
            paths = json.loads(row["evidence_paths"])
        except Exception:
            errors.append(f"bad evidence_paths {row['claim_id']}"); continue
        for p in paths:
            if not (ROOT / p).exists():
                errors.append(f"missing evidence path {p}")
        if row["target_text_sha256"] != sha(row["target_text"].encode("utf-8")):
            errors.append(f"target hash mismatch {row['claim_id']}")
    if len(new_rows) != len(ledger):
        errors.append("target coverage mismatch")
    for n, section, text in new_rows:
        if not any(int(r["source_line"]) == n and r["target_text"] == text for r in ledger):
            errors.append(f"unmapped target line {n}")
    old_text = V077.read_text(encoding="utf-8")
    new_text = V078.read_text(encoding="utf-8")
    def tokens(s, pat): return sorted(set(re.findall(pat, s, re.I)))
    if tokens(old_text, r"\d+(?:\.\d+)?%?") != tokens(new_text, r"\d+(?:\.\d+)?%?"):
        errors.append("numeric token set changed")
    if tokens(old_text, r"DIOR-R|FAIR1M(?:-v1\.0)?|SODA-A|DOTA(?:-v1\.0)?") != tokens(new_text, r"DIOR-R|FAIR1M(?:-v1\.0)?|SODA-A|DOTA(?:-v1\.0)?"):
        errors.append("dataset token set changed")
    forbidden = []
    for n, line in enumerate(new_text.splitlines(), 1):
        if FORBIDDEN.search(line) and not CONTEXT.search(line):
            forbidden.append({"line": n, "text": line, "decision": "FAIL"})
    if forbidden:
        errors.append("unqualified forbidden phrase")
    result = {
        "round": "orientbench-c-r008-20260806",
        "v077_sha256": sha(old), "v078_sha256": sha(new),
        "v077_bytes": len(old), "v078_bytes": len(new),
        "v077_git_blob": blob(V077), "v078_git_blob": blob(V078),
        "ledger_rows": len(ledger), "source_claims": len(old_rows), "target_claims": len(new_rows),
        "source_to_ledger_coverage": 1.0 if not errors or len(ledger) == len(old_rows) else 0.0,
        "target_to_ledger_coverage": 1.0 if len(new_rows) == len(ledger) else 0.0,
        "forbidden_phrase_scan": forbidden,
        "operation_counts": {"training": 0, "detector_inference": 0, "score_regressor": 0, "gpu": 0, "download": 0, "external_data_access": 0},
        "errors": errors,
        "hygiene_gate": "PASS_CLAIM_QUARANTINE_R008" if not errors else "FAIL_CLAIM_QUARANTINE_R008",
        "measurement_core_status": "SUFFICIENT_FOR_MEASUREMENT_REVISION" if len(ledger) >= 3 else "INCONCLUSIVE_CORE_EVIDENCE",
    }
    GATE.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
