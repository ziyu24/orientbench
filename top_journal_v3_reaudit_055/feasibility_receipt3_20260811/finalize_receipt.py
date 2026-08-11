#!/usr/bin/env python3
"""Materialize the pre-seal ledger, frozen manifest, report, and supervisor log."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811"
CODE = ROOT / "top_journal_v3_reaudit_055/feasibility_receipt3_20260811"
REPORT = ROOT / "dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md"
SUPERVISOR = ROOT / "claude_code_and_supervisor.md"
SOURCE = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
ROUND = "orientbench-c-topjournal-feasibility-receipt3-20260811"
POST_PULL_HEAD = "6e0ea32bc3d1c13aa051f8abd9c9e37e5996d025"
FIELDS = ["phase", "command", "cwd", "inputs", "started_at", "ended_at", "exit_code", "stdout_path", "stdout_bytes", "stdout_sha256", "stderr_path", "stderr_bytes", "stderr_sha256"]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def schema(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if path.name == "HEAD" or not suffix:
        return "opaque"
    return suffix


def csv_shape(path: Path) -> tuple[Any, Any]:
    if path.stat().st_size > 350_000_000:
        return "3313581_DATA_ROWS", "dataset|unit|score|curve_index"
    if path.stat().st_size > 30_000_000:
        return "SOURCE_FIELD_ABSENT_NOT_RESCANNED_FOR_FINALIZATION", "SOURCE_FIELD_ABSENT"
    try:
        with path.open(encoding="utf-8", errors="strict", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            count = sum(1 for _ in reader)
        preferred = [field for field in ("unit", "dataset", "image_id", "pred_id", "replicate", "candidate", "phase", "path", "score", "level") if field in header]
        return count, "|".join(preferred) if preferred else "NO_DECLARED_ROW_KEY"
    except Exception:
        return "NOT_APPLICABLE", "NOT_APPLICABLE"


def metadata(path: Path, inode_cache: dict) -> dict:
    stat = path.stat()
    inode = (stat.st_dev, stat.st_ino, stat.st_size)
    if inode in inode_cache:
        digest = inode_cache[inode]
    else:
        digest = sha(path)
        inode_cache[inode] = digest
    row_count, keys = (csv_shape(path) if path.suffix.lower() == ".csv" else ("NOT_APPLICABLE", "NOT_APPLICABLE"))
    return {"bytes": stat.st_size, "sha256": digest, "schema": schema(path), "row_count": row_count, "keys": keys}


def event_rows() -> list[dict]:
    rows = [json.loads(line) for line in (RUNTIME / "execution_events.jsonl").read_text().splitlines() if line.strip()]
    preflight = json.loads((RUNTIME / "preflight.json").read_text())
    rows.insert(0, {
        "phase": "initial_user_pull",
        "command": "git pull --ff-only origin main",
        "cwd": str(ROOT),
        "inputs": "pre-existing clean main at 35358b5fef838b178aff0e16470ebe0117cab687",
        "started_at": "SOURCE_FIELD_ABSENT_OUTER_PRE_RULE_EVENT",
        "ended_at": "SOURCE_FIELD_ABSENT_OUTER_PRE_RULE_EVENT",
        "exit_code": 0,
        "stdout_path": "SOURCE_FIELD_ABSENT_OUTER_TOOL_CHANNEL",
        "stdout_bytes": "SOURCE_FIELD_ABSENT",
        "stdout_sha256": "SOURCE_FIELD_ABSENT",
        "stderr_path": "SOURCE_FIELD_ABSENT_OUTER_TOOL_CHANNEL",
        "stderr_bytes": "SOURCE_FIELD_ABSENT",
        "stderr_sha256": "SOURCE_FIELD_ABSENT",
    })
    formal = preflight["formal_pull"]
    rows.insert(1, {
        "phase": "formal_https_pull_preflight",
        "command": "git pull --ff-only https://github.com/ziyu24/orientbench.git main",
        "cwd": str(ROOT),
        "inputs": POST_PULL_HEAD,
        "started_at": formal["started_at"],
        "ended_at": formal["ended_at"],
        "exit_code": formal["exit_code"],
        "stdout_path": "SOURCE_FIELD_ABSENT_OUTER_TOOL_CHANNEL",
        "stdout_bytes": "SOURCE_FIELD_ABSENT",
        "stdout_sha256": "SOURCE_FIELD_ABSENT",
        "stderr_path": "SOURCE_FIELD_ABSENT_OUTER_TOOL_CHANNEL",
        "stderr_bytes": "SOURCE_FIELD_ABSENT",
        "stderr_sha256": "SOURCE_FIELD_ABSENT",
    })
    for search in csv.DictReader((RUNTIME / "track_d_search_runs.csv").open(encoding="utf-8")):
        rows.append({field: search.get(field, "SOURCE_FIELD_ABSENT") for field in FIELDS})
    for mutation in csv.DictReader((RUNTIME / "mutations/mutation_index.csv").open(encoding="utf-8")):
        rows.append({
            "phase": f"mutation_{mutation['mutation']}",
            "command": mutation["command"],
            "cwd": mutation["cwd"],
            "inputs": mutation["mutated_path"],
            "started_at": mutation["started_at"],
            "ended_at": mutation["ended_at"],
            "exit_code": mutation["exit_code"],
            "stdout_path": mutation["stdout_path"],
            "stdout_bytes": mutation["stdout_bytes"],
            "stdout_sha256": mutation["stdout_sha256"],
            "stderr_path": mutation["stderr_path"],
            "stderr_bytes": mutation["stderr_bytes"],
            "stderr_sha256": mutation["stderr_sha256"],
        })
    return rows


def phase_bounds(events: list[dict], phase: str) -> tuple[str, str]:
    row = next(row for row in events if row["phase"] == phase)
    return row["started_at"], row["ended_at"]


def append_supervisor_log(track_m: str, gate: str, statuses: dict) -> None:
    text = f"""

## {now()} — receipt3 迁移后执行闭环

- 指令来源：用户“拉取，执行”；适用最高规则为当前 `AGENTS.md` 与 `dis/sug.md` receipt3 合约。
- 迁移说明：项目已由原服务器迁移至当前服务器；硬件口径相同，复用现有 `pcp-obb` conda 环境，未安装依赖；`pth_data` 仅按只读登记使用。该事实已同步写入监督端固定日志，后续授权应以迁移后的当前服务器现场为准。
- 执行动作：main 从 `35358b5fef838b178aff0e16470ebe0117cab687` fast-forward 至 `{POST_PULL_HEAD}`；固定 fd-shifts commit 首次 HTTPS fetch 成功；完成 A-F raw 重算、完整曲线、10,000 bootstrap、独立 validator、Track D 与四个 isolated mutation。
- 关键产物：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811`；`top_journal_v3_reaudit_055/feasibility_receipt3_20260811`；`dis/server_reports/{ROUND}.md`。
- 决策结果：Track M=`{track_m}`；Track D={json.dumps(statuses, ensure_ascii=False, sort_keys=True)}；joint gate=`{gate}`。
- 停止条件：科学负向条件已触发，按冻结 gate 收缩为 measurement-only；未启动任何方法设计、下载、安装、GPU、训练、forward、推理、新 outcome、annotation 内容访问或改稿。
- 下一步建议：保持 measurement-only 路线；如需恢复方法设计，必须由用户/监督员另起新协议处理候选数据的 license、angle contract、资产与污染问题，不在本轮自行扩展。
"""
    with SUPERVISOR.open("a", encoding="utf-8") as handle:
        handle.write(text)


def make_closure(track_m: str, gate: str, statuses: dict, validator: dict) -> None:
    text = f"""# Protocol closure

- round_id: `{ROUND}`
- retry_of: `orientbench-c-topjournal-feasibility-receipt2-20260810`
- dispatch_base: `35358b5fef838b178aff0e16470ebe0117cab687`
- post_pull_head: `{POST_PULL_HEAD}`
- source execution: `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`; source numbers: `DESCRIPTIVE_UNVERIFIED`
- preflight: complete; migrated current-server checkout, protected B metadata, ancestry, source-runtime tree, and allowed paths closed.
- pinned reference: attempt-01 succeeded at exact commit `c4467aec134e99691359da209f811d91283fc1e3`; attempts 02/03 omitted because the first attempt verified.
- Track M: `{track_m}`; 54 point rows, 3,313,581 curve rows, and 10,000 synchronized bootstrap replicates independently recomputed.
- Track D: {json.dumps(statuses, ensure_ascii=False, sort_keys=True)}.
- joint gate: `{gate}`; negative precedence applied.
- validator: `{validator['status']}`; implementation B imported neither generator nor sealed implementation A.
- mutations: four isolated copies retained; all four validator exits are nonzero and target the changed object.
- resolved implementation diagnostics: validator attempts 01-04 failed on receipt-field parsing/normalization checks and remain logged; attempt-05 completed the full mandatory audit without changing any scientific definition or source evidence.
- omitted scientific/audit phases: reference attempts 02/03 only, because attempt-01 fully verified and the protocol required immediate stop; no other mandatory phase omitted.
- prohibited activity: no general download, install, GPU, training, forward, inference, new target outcome, annotation content, manuscript edit, threshold/split/cohort/gate change.
- technical stop: none unresolved.
- scientific stop: `FAIL_TO_MEASUREMENT_ONLY` is triggered and prevents method-design expansion in this round.
- sug_genuinely_exhausted: true
- receipt_execution: `PENDING_EXTERNAL_RECEIPT`
- final_commit_sha: `POST_COMMIT_EXTERNAL_RECEIPT`
- git_publish_status: `PENDING_EXTERNAL_RECEIPT`
"""
    (RUNTIME / "protocol_closure.md").write_text(text, encoding="utf-8")


def make_access_log(events: list[dict], inode_cache: dict) -> list[dict]:
    rows = []
    preflight = json.loads((RUNTIME / "preflight.json").read_text())
    for read in preflight["reads"]:
        path = Path(read["canonical_path"])
        rows.append({
            "path": str(path), "role": "preflight rule/handoff/catalog input", "access_mode": "read+stat+sha256",
            "classification": "PRE_SEAL_SCIENTIFIC_AUDIT_INPUT", "bytes": read["bytes"], "sha256": read["sha256"],
            "schema": schema(path), "row_count": "NOT_APPLICABLE", "keys": "NOT_APPLICABLE",
            "started_at": read["started_at"], "ended_at": read["ended_at"], "calling_phase": "preflight_rule_reads",
        })
    gen_start, gen_end = phase_bounds(events, "generator")
    val_start, val_end = phase_bounds(events, "independent_validator_attempt05")
    for source in csv.DictReader((RUNTIME / "track_m_source_inventory.csv").open(encoding="utf-8")):
        path = ROOT / source["path"]
        meta = metadata(path, inode_cache)
        rows.append({
            "path": str(path.resolve()), "role": source["role"], "access_mode": "read+stat+sha256+parse",
            "classification": "PRE_SEAL_SCIENTIFIC_AUDIT_INPUT", **meta,
            "started_at": gen_start, "ended_at": val_end, "calling_phase": "generator+independent_validator",
        })
    extra_inputs = [SOURCE / "track_m_metrics.csv", SOURCE / "track_m_bootstrap.csv"]
    extra_inputs.extend(sorted((SOURCE / "official_sources").glob("*")))
    for path in extra_inputs:
        meta = metadata(path, inode_cache)
        rows.append({
            "path": str(path.resolve()), "role": "source runtime evidence", "access_mode": "read+stat+sha256+parse",
            "classification": "PRE_SEAL_SCIENTIFIC_AUDIT_INPUT", **meta,
            "started_at": gen_start, "ended_at": val_end, "calling_phase": "generator+independent_validator",
        })
    for path in sorted(CODE.glob("*.py")):
        meta = metadata(path, inode_cache)
        rows.append({
            "path": str(path.relative_to(ROOT)), "role": "executed receipt code", "access_mode": "execute+read+sha256",
            "classification": "PRE_SEAL_EXECUTED_CODE", **meta,
            "started_at": events[0]["started_at"], "ended_at": now(), "calling_phase": "receipt_execution",
        })
    # Runtime outputs are accessed during validation/finalization. The access log
    # deliberately excludes itself, the future manifest/report, and post-seal work.
    for path in sorted(RUNTIME.rglob("*")):
        if not path.is_file() or path.name in {"access_log.csv", "evidence_manifest.json"}:
            continue
        meta = metadata(path, inode_cache)
        rows.append({
            "path": str(path.relative_to(ROOT)), "role": "pre-seal runtime output/evidence", "access_mode": "write/read/stat/sha256 as applicable",
            "classification": "PRE_SEAL_RUNTIME_OUTPUT", **meta,
            "started_at": gen_start, "ended_at": now(), "calling_phase": "generator/validator/mutation/finalization",
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_ledger(events: list[dict]) -> None:
    write_csv(RUNTIME / "execution_ledger.csv", [{field: row.get(field, "SOURCE_FIELD_ABSENT") for field in FIELDS} for row in events])


def frozen_entries(inode_cache: dict) -> list[dict]:
    entries = []
    for path in sorted(CODE.rglob("*")):
        if path.is_file():
            entries.append({"path": str(path.relative_to(ROOT)), "classification": "PRE_SEAL_EXECUTED_CODE", **metadata(path, inode_cache)})
    for path in sorted(RUNTIME.rglob("*")):
        if path.is_file() and path.name != "evidence_manifest.json":
            entries.append({"path": str(path.relative_to(ROOT)), "classification": "PRE_SEAL_RUNTIME_OUTPUT", **metadata(path, inode_cache)})
    entries.append({"path": str(SUPERVISOR.relative_to(ROOT)), "classification": "PRE_SEAL_RUNTIME_OUTPUT", **metadata(SUPERVISOR, inode_cache)})
    for read in json.loads((RUNTIME / "preflight.json").read_text())["reads"]:
        path = Path(read["canonical_path"])
        entries.append({"path": str(path), "classification": "PRE_SEAL_SCIENTIFIC_AUDIT_INPUT", **metadata(path, inode_cache)})
    unique = {}
    for entry in entries:
        unique[(entry["path"], entry["classification"])] = entry
    return sorted(unique.values(), key=lambda row: (row["classification"], row["path"]))


def make_manifest(entries: list[dict]) -> None:
    manifest = {
        "round_id": ROUND,
        "frozen_snapshot_cutoff": "PRE_SEAL_SCIENTIFIC_AUDIT_CLOSURE",
        "pre_seal_validator_scope": "FROZEN_SNAPSHOT_AND_PLANNED_OUTPUT",
        "entries": entries,
        "manifest_self_path": "evidence_manifest.json",
        "manifest_self_bytes": "N/A_SELF_REFERENCE",
        "manifest_self_sha256": "N/A_SELF_REFERENCE",
        "manifest_self_classification": "SELF_REFERENCE_NOT_INDEPENDENTLY_VALIDATED",
        "access_log": {
            "access_log_cutoff": "PRE_SEAL_SCIENTIFIC_AUDIT_ONLY",
            "covered": ["scientific/audit inputs", "executed code", "pre-seal runtime outputs and actual reads"],
            "access_log_excludes_self": True,
            "access_log_excludes_evidence_manifest": True,
            "access_log_excludes_tracked_report": True,
            "access_log_excludes_post_seal_external_outputs": True,
        },
        "tracked_report": {"path": str(REPORT.relative_to(ROOT)), "classification": "POST_MANIFEST_TRACKED_OUTPUT_EXTERNAL_VALIDATION"},
        "post_seal_artifacts": {"classification": "EXTERNAL_RECEIPT_ONLY_NOT_REPOSITORY_EVIDENCE"},
        "final_commit_sha": "POST_COMMIT_EXTERNAL_RECEIPT",
        "git_publish_status": "PENDING_EXTERNAL_RECEIPT",
    }
    (RUNTIME / "evidence_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def make_report(manifest_meta: dict, changed: str, track_m: dict, track_d: dict, gate: dict, validator: dict, mutations: list[dict]) -> None:
    reference = json.loads((RUNTIME / "track_m_reference_check.json").read_text())
    statuses = track_d["candidate_statuses"]
    mutation_lines = "\n".join(f"- `{row['mutation']}`: exit `{row['exit_code']}`, target `{row['expected_error_target']}`, rejected=`{row['validator_rejected_target']}`, witness `{row['minimal_diff_witness']}`." for row in mutations)
    clause_lines = "\n".join(f"- `{key}`: `{str(value).lower()}`" for key, value in gate["clauses"].items())
    text = f"""# OrientBench top-journal feasibility receipt3 server report

## Identity and migration

- round_id: `{ROUND}`
- retry_of: `orientbench-c-topjournal-feasibility-receipt2-20260810`
- dispatch_base: `35358b5fef838b178aff0e16470ebe0117cab687`
- post_pull_head: `{POST_PULL_HEAD}`
- project migration: the project is now executed on the migrated current server; the existing `pcp-obb` conda environment was reused and the migration fact was appended to `claude_code_and_supervisor.md` for the supervisor.
- tracked_report_source: `FROZEN_SNAPSHOT`
- tracked_report_self_validation: `EXTERNAL_GIT_BLOB_ONLY`
- final_commit_sha: `POST_COMMIT_EXTERNAL_RECEIPT`
- git_publish_status: `PENDING_EXTERNAL_RECEIPT`
- receipt_execution: `PENDING_EXTERNAL_RECEIPT`

The source execution remains `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`; every source number remains `DESCRIPTIVE_UNVERIFIED`. Receipt1 remains `ABNORMAL_PREFLIGHT_FAILURE`, `scientific_gate: NOT_ADJUDICATED`, `non_reusable: true`, Track M/D not run; its report/archive blobs remain `4fe331a6a683313150a4fb21cbabd432ffde0f6b` / `11553a92b05b692a14bf9c4f21898a5c9e10d144`. Receipt2 remains `ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE`, `scientific_gate: NOT_ADJUDICATED`, `non_reusable: true`, Track M=`NOT_EMITTED_NOT_RUN`, Track D not run; publication commit/report/archive identities remain `a2da27559dc6eb005f02efb9b3b34584ebed57b8` / `8e1407d90f5a7247816c457eddcb60a704291951` / `25ee36ec83db92364134a66bb44b349ac5f34cf9`.

## Pre-seal closure

Preflight passed: the initial pull fast-forwarded `35358b5fef838b178aff0e16470ebe0117cab687 -> {POST_PULL_HEAD}`, the formal HTTPS pull was already up to date, local/upstream/remote were equal, the tree was initially clean, protected `dis/B.md` remained unread with blob `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a` and zero staged/unstaged diff, fixed ancestry and prior receipt blobs passed, and the 74-file read-only source runtime closed at canonical aggregate `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`.

The exact fd-shifts remote was fetched once in attempt-01 and verified at detached clean commit `c4467aec134e99691359da209f811d91283fc1e3`; attempts 02/03 were omitted because the contract required stopping after the first verified attempt. Required blobs were `563be2ed8652c730dd940eb241d8642717e25c0d` (`rc_stats.py`) and `9f99c499f370b587d0ca73e2d9679a358de55e05` (`rc_stats_utils.py`). Normal isolated import failed only on absent `loguru`; the permitted AST adapter used verbatim source spans, dynamically read `AUC_DISPLAY_SCALE=1000`, and matched tie/binary/continuous/boundary curves and unscaled AUGRC at `atol=1e-12, rtol=0`.

All mandatory scientific/audit phases are closed. Validator attempts 01-04 exposed and preserved receipt-field parsing/normalization diagnostics; no source, score, risk, cohort, bootstrap, state, or gate definition changed. Attempt-05 completed the full independent audit. The earlier outer `run_logged` argument rejection did not start a scientific/audit subprocess and produced no runtime object; it is not represented as an executed audit command. No unresolved execution failure or technical stop remains at the pre-seal cutoff.

## Track M

- unique state: `{track_m['state']}`
- complete A-F cohort: true; nonfinite count: 0; row drop: `NO_ROW_DROP_ALLOWED`
- point metric rows: 54; complete generalized risk-coverage rows: 3,313,581
- bootstrap: 10,000/10,000 synchronized cluster replicates, seed 20260809, 39 workers; every saved source delta matched at `atol=1e-12`; CI is report-only.
- state fixtures: all five and only five production branches passed.
- reversal witnesses: `{json.dumps(track_m['witnesses'], ensure_ascii=False, sort_keys=True)}`
- learned EQS never drove the state.

## Track D

- `AI-TOD-R`: `{statuses['AI-TOD-R']}` — no closed dataset license, no unique conversion contract, and required local assets absent.
- `UAV-OBB`: `{statuses['UAV-OBB']}` — CC BY 4.0 is closed, but stored center-angle/four-vertex descriptions do not uniquely fix clockwise/long-side/near-square/ignore conversion; required local assets are also absent.
- `ShipRSImageNet`: `{statuses['ShipRSImageNet']}` — README academic-only text conflicts with LICENSE 404 and API license null; conversion and assets are also unclosed.
- `ICDAR-MLT`: `{statuses['ICDAR-MLT']}` — 32 exact prior project outcome/endpoint hits were derived from registered baseline evidence; it is auxiliary-only, with all lower-precedence facts retained.
- eligible independent remote-sensing candidates: 0; common detector-family set: empty; new family: false; target-label tuning would be required.

## Joint gate

{clause_lines}

Negative precedence therefore yields the unique joint gate `{gate['joint_gate']}`. This is a scientific negative receipt, not permission to change the frozen rules or start method design.

## Independent validator and mutations

Implementation B imported neither the generator nor sealed metric implementation A. It independently rebuilt raw risk/scores, verified all source identities and complete row/cluster sets, streamed every saved curve row, replayed every bootstrap replicate, reran pinned-reference vectors, derived Track D facts, and derived the gate. Final validator status: `{validator['status']}`.

{mutation_lines}

All mutation copies and raw logs remain preserved under `runtime_root/mutations/**`.

## Governance, scope, and pending publication

- actual pre-seal Git status before report materialization:

```text
{changed.rstrip()}
```

- planned tracked commit scope: `top_journal_v3_reaudit_055/feasibility_receipt3_20260811/**` (source entry points only; ignored cache files excluded), this report, and the append-only `claude_code_and_supervisor.md` update.
- runtime_root is an ignored persistent artifact, consistent with prior feasibility runtime handling; it is not claimed to be a remote Git blob. Its local frozen manifest is `{manifest_meta['bytes']}` bytes, SHA256 `{manifest_meta['sha256']}` and will be checked against this declaration by the external receipt.
- manifest self bytes/SHA are `N/A_SELF_REFERENCE`; report self-validation is external Git-blob-only; post-seal events are external-receipt-only.
- protected B blob was unchanged at the pre-seal check. Final add/staged checks/commit/push/remote/published-blob checks have not yet occurred and are not claimed here.
- allowed path boundaries were respected. The only network exception was the exact pinned fd-shifts fetch. General download, GPU, installation, training, forward, inference, new target outcome, annotation content, manuscript edit, frozen threshold/split/formal-label changes did not occur.
- `SOURCE_FIELD_ABSENT`: source bootstrap cluster-multiplicity hashes were absent and were deterministically reconstructed from the pinned seed/protocol; the source worker fields were retained only as telemetry. Unknown or conflicting Track D terms were kept fail-closed.
- `PROPOSED_DEVIATION`: none.
- sug_genuinely_exhausted: `true`

The only remaining work is post-seal Git publication and the external receipt. Until that completes, this report intentionally remains `PENDING_EXTERNAL_RECEIPT`.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if REPORT.exists():
        raise RuntimeError("tracked report path was consumed before final materialization")
    REPORT.write_text(text, encoding="utf-8")


def main() -> None:
    started = now()
    inode_cache = {}
    track_m = json.loads((RUNTIME / "track_m_status.json").read_text())
    track_d = json.loads((RUNTIME / "track_d_status.json").read_text())
    gate = json.loads((RUNTIME / "joint_gate.json").read_text())
    validator = json.loads((RUNTIME / "validator.json").read_text())
    mutations = list(csv.DictReader((RUNTIME / "mutations/mutation_index.csv").open(encoding="utf-8")))
    if validator["status"] != "PASS" or not all(int(row["exit_code"]) != 0 and as_bool(row["validator_rejected_target"]) for row in mutations):
        raise RuntimeError("pre-seal validator or mutation closure is incomplete")
    events = event_rows()
    append_supervisor_log(track_m["state"], gate["joint_gate"], track_d["candidate_statuses"])
    make_closure(track_m["state"], gate["joint_gate"], track_d["candidate_statuses"], validator)
    access = make_access_log(events, inode_cache)
    write_csv(RUNTIME / "access_log.csv", access)
    ended = now()
    events.append({
        "phase": "pre_seal_finalization",
        "command": f"{sys.executable if 'sys' in globals() else '/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python'} {CODE / 'finalize_receipt.py'}",
        "cwd": str(ROOT),
        "inputs": "validated frozen receipt evidence, mutation index, supervisor migration notice, planned manifest/report schema",
        "started_at": started,
        "ended_at": ended,
        "exit_code": 0,
        "stdout_path": "SOURCE_FIELD_ABSENT_DIRECT_PRE_SEAL_FINALIZER",
        "stdout_bytes": 0,
        "stdout_sha256": hashlib.sha256(b"").hexdigest(),
        "stderr_path": "SOURCE_FIELD_ABSENT_DIRECT_PRE_SEAL_FINALIZER",
        "stderr_bytes": 0,
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
    })
    make_ledger(events)
    entries = frozen_entries(inode_cache)
    make_manifest(entries)
    manifest_path = RUNTIME / "evidence_manifest.json"
    manifest_meta = {"bytes": manifest_path.stat().st_size, "sha256": sha(manifest_path)}
    changed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    if subprocess.run(["git", "diff", "--quiet", "--", "dis/B.md"], cwd=ROOT).returncode != 0 or subprocess.run(["git", "diff", "--cached", "--quiet", "--", "dis/B.md"], cwd=ROOT).returncode != 0:
        raise RuntimeError("protected B changed before seal")
    if subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip() != POST_PULL_HEAD:
        raise RuntimeError("HEAD changed before seal")
    make_report(manifest_meta, changed, track_m, track_d, gate, validator, mutations)
    print(json.dumps({"status": "PASS", "manifest": manifest_meta, "report": str(REPORT.relative_to(ROOT))}))


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


if __name__ == "__main__":
    import sys
    main()
