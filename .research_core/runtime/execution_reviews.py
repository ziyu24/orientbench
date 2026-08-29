"""Append-only B/C review receipts for SERVER execution outcomes."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

import yaml

from . import durable_execution, peer_governance, research_execution


INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
REVIEW_FILE = re.compile(r"([BC])-([0-9]{3,})\.yaml\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
VERDICTS = {
    "ISSUE_NEXT_R_CORRECTION",
    "VERIFIED_CORRECT",
    "CATASTROPHIC_REPORT_REQUIRED",
}
ABNORMAL_STATES = {"FAILED", "INCOMPLETE", "BLOCKED", "STOPPED"}
REVIEW_KEYS = {
    "schema_version",
    "review_id",
    "instruction_id",
    "reviewed_by",
    "observed_state",
    "journal_sha256",
    "verdict",
    "summary",
    "evidence",
    "reviewed_at",
}
ABNORMAL_EVIDENCE_KEYS = {
    "schema_version",
    "instruction_id",
    "terminal_journal_sha256",
    "terminal_journal",
    "command_logs",
    "result_files",
    "recorded_at",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    if Path(durable_execution._git(root, "rev-parse", "--show-toplevel").stdout.strip()).resolve() != root:
        raise ValueError("execution review requires the exact project root")
    return root


def _actor(root: Path) -> str:
    role = peer_governance.current_worker(root)["role"]
    actor = {"PEER_B": "B", "PEER_C": "C"}.get(role)
    if actor is None:
        raise ValueError("only B or C may record an execution review")
    return actor


def _safe_evidence_path(instruction_id: str, value: str) -> tuple[str, tuple[str, ...]]:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("invalid execution-review evidence path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValueError("execution-review evidence escapes project")
    parts = pure.parts
    allowed = (
        parts[:3] == ("coordination", "instructions", instruction_id)
        or parts[:3] == ("coordination", "executions", instruction_id)
        or parts[:2] == ("runs", instruction_id)
    )
    if not allowed:
        raise ValueError("execution-review evidence is not bound to the instruction")
    return pure.as_posix(), parts


def _evidence(root: Path, instruction_id: str, values: list[str]) -> list[dict[str, Any]]:
    if (
        type(values) is not list
        or not values
        or len(values) != len(set(values))
        or any(type(value) is not str for value in values)
    ):
        raise ValueError("execution review requires unique evidence paths")
    result = []
    for value in values:
        relative, parts = _safe_evidence_path(instruction_id, value)
        path = root.joinpath(*parts)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"execution-review evidence is missing: {relative}")
        result.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return result


def _materialize_execution_evidence(
    root: Path, instruction_id: str, values: list[str]
) -> None:
    """Fetch missing execution YAML from the plan's verified result branch."""

    missing = []
    for value in values:
        relative, parts = _safe_evidence_path(instruction_id, value)
        path = root.joinpath(*parts)
        if path.is_symlink():
            raise ValueError("execution-review evidence cannot be a symbolic link")
        if not path.is_file():
            missing.append((relative, path))
    if not missing:
        return
    try:
        branch = research_execution.load_server_plan(root, instruction_id)["result_branch"]
    except ValueError:
        shown = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", f"refs/heads/exec/{instruction_id}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            check=False, shell=False,
        )
        branch = (
            f"exec/{instruction_id}"
            if shown.returncode == 0 and shown.stdout.strip()
            else "main"
        )
    remote_ref = f"refs/remotes/origin/{branch}"
    completed = subprocess.run(
        [
            "git",
            "fetch",
            "origin",
            f"refs/heads/{branch}:{remote_ref}",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"cannot fetch SERVER execution evidence: {detail}")
    for relative, path in missing:
        shown = subprocess.run(
            ["git", "show", f"{remote_ref}:{relative}"],
            cwd=root,
            capture_output=True,
            check=False,
            shell=False,
        )
        if shown.returncode != 0:
            raise ValueError(f"execution evidence is absent from {branch}: {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.is_symlink() or path.exists():
            raise ValueError("execution-review evidence destination is unsafe")
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(shown.stdout)
            handle.flush()
            os.fsync(handle.fileno())


def _state_from_evidence(
    root: Path,
    instruction_id: str,
    verdict: str,
    evidence: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    paths = {item["path"] for item in evidence}
    if verdict == "VERIFIED_CORRECT":
        required = f"coordination/executions/{instruction_id}/RESULT.yaml"
        if required not in paths:
            raise ValueError("VERIFIED_CORRECT requires the exact execution RESULT.yaml")
        result = yaml.safe_load((root / required).read_text(encoding="utf-8"))
        if (
            type(result) is not dict
            or result.get("instruction_id") != instruction_id
            or result.get("status") != "SUCCEEDED"
            or type(result.get("checkpoint_index")) is not int
            or type(result.get("acceptance_checkpoint_index")) is not int
        ):
            raise ValueError("VERIFIED_CORRECT result evidence is invalid")
        plan = research_execution.load_server_plan(root, instruction_id)
        if (
            plan["execution_followup"]["mode"] != "CORRECT_PREVIOUS_EXECUTION"
            or result.get("plan_sha256")
            != hashlib.sha256(
                (
                    root
                    / "coordination/instructions"
                    / instruction_id
                    / "SERVER_PLAN.yaml"
                ).read_bytes()
            ).hexdigest()
        ):
            raise ValueError("VERIFIED_CORRECT result does not bind the correction plan")
        payload = (root / required).read_bytes()
        return {
            "state": "COMPLETE",
            "plan_sha256": result["plan_sha256"],
            "checkpoint_index": result["checkpoint_index"],
            "acceptance_checkpoint_index": result["acceptance_checkpoint_index"],
        }, hashlib.sha256(payload).hexdigest()
    candidates = [
        path
        for path in paths
        if re.fullmatch(
            rf"coordination/executions/{re.escape(instruction_id)}/ABNORMAL-[0-9]{{3,}}\.yaml",
            path,
        )
    ]
    if len(candidates) != 1:
        raise ValueError("abnormal execution review requires one exact ABNORMAL evidence bundle")
    required = candidates[0]
    abnormal = yaml.safe_load((root / required).read_text(encoding="utf-8"))
    journal = abnormal.get("terminal_journal") if type(abnormal) is dict else None
    if (
        type(abnormal) is not dict
        or set(abnormal) != ABNORMAL_EVIDENCE_KEYS
        or abnormal.get("schema_version") != 1
        or abnormal.get("instruction_id") != instruction_id
        or type(journal) is not dict
        or set(journal) != durable_execution.JOURNAL_KEYS
        or journal.get("instruction_id") != instruction_id
        or journal.get("state") not in ABNORMAL_STATES
        or journal.get("bc_review_required") is not True
        or journal.get("bc_review_status") != "REQUIRED"
        or journal.get("bc_review_receipt") is not None
        or journal.get("bc_review_sha256") is not None
        or SHA256.fullmatch(str(journal.get("plan_sha256"))) is None
        or type(abnormal.get("command_logs")) is not list
        or type(abnormal.get("result_files")) is not list
    ):
        raise ValueError("abnormal execution evidence does not match the terminal journal")
    journal_payload = yaml.safe_dump(
        journal, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    journal_sha256 = hashlib.sha256(journal_payload).hexdigest()
    if abnormal.get("terminal_journal_sha256") != journal_sha256:
        raise ValueError("abnormal terminal journal snapshot changed")
    for collection, identity_key in ((abnormal["command_logs"], "name"), (abnormal["result_files"], "path")):
        identities = set()
        for item in collection:
            if (
                type(item) is not dict
                or set(item)
                != {
                    identity_key,
                    "size_bytes",
                    "sha256",
                    "preview_utf8",
                    "preview_bytes",
                    "preview_truncated",
                }
                or type(item.get(identity_key)) is not str
                or not item[identity_key]
                or item[identity_key] in identities
                or type(item.get("size_bytes")) is not int
                or item["size_bytes"] < 0
                or SHA256.fullmatch(str(item.get("sha256"))) is None
                or type(item.get("preview_utf8")) is not str
                or type(item.get("preview_bytes")) is not int
                or item["preview_bytes"] < 0
                or item["preview_bytes"] > durable_execution.EVIDENCE_PREVIEW_BYTES
                or item["preview_bytes"] > item["size_bytes"]
                or type(item.get("preview_truncated")) is not bool
                or item["preview_truncated"]
                != (item["size_bytes"] > durable_execution.EVIDENCE_PREVIEW_BYTES)
            ):
                raise ValueError("abnormal execution file binding is invalid")
            identities.add(item[identity_key])
    plan = research_execution.load_server_plan(root, instruction_id)
    plan_path = root / "coordination/instructions" / instruction_id / "SERVER_PLAN.yaml"
    if (
        hashlib.sha256(plan_path.read_bytes()).hexdigest() != journal["plan_sha256"]
        or plan["instruction_id"] != instruction_id
    ):
        raise ValueError("abnormal evidence does not bind the prior SERVER plan")
    return journal, journal_sha256


def _review_directory(root: Path, instruction_id: str) -> Path:
    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid execution-review instruction id")
    parent = root / "coordination/instructions" / instruction_id
    plan = parent / "SERVER_PLAN.yaml"
    if parent.is_symlink() or not parent.is_dir() or plan.is_symlink() or not plan.is_file():
        raise ValueError("execution review requires the prior SERVER plan")
    directory = parent / "reviews"
    directory.mkdir(exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("execution-review directory is invalid")
    return directory


def _validate(document: dict[str, Any]) -> dict[str, Any]:
    if (
        type(document) is not dict
        or set(document) != REVIEW_KEYS
        or document.get("schema_version") != 1
        or INSTRUCTION_ID.fullmatch(str(document.get("instruction_id"))) is None
        or REVIEW_FILE.fullmatch(f'{document.get("review_id")}.yaml') is None
        or document.get("reviewed_by") not in {"B", "C"}
        or not str(document["review_id"]).startswith(f'{document["reviewed_by"]}-')
        or document.get("observed_state") not in durable_execution.STATES
        or SHA256.fullmatch(str(document.get("journal_sha256"))) is None
        or document.get("verdict") not in VERDICTS
        or type(document.get("summary")) is not str
        or len(document["summary"].strip()) < 12
        or type(document.get("reviewed_at")) is not str
        or not document["reviewed_at"]
        or type(document.get("evidence")) is not list
        or not document["evidence"]
    ):
        raise ValueError("invalid execution-review receipt")
    paths: set[str] = set()
    for item in document["evidence"]:
        if (
            type(item) is not dict
            or set(item) != {"path", "size_bytes", "sha256"}
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] < 0
            or SHA256.fullmatch(str(item.get("sha256"))) is None
        ):
            raise ValueError("invalid execution-review evidence binding")
        relative, _ = _safe_evidence_path(document["instruction_id"], item.get("path"))
        if relative in paths:
            raise ValueError("duplicate execution-review evidence binding")
        paths.add(relative)
    return document


def load_review(root: Path, relative: str, expected_sha256: str | None = None) -> dict[str, Any]:
    root = _root(root)
    if type(relative) is not str or "\\" in relative:
        raise ValueError("invalid execution-review receipt path")
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or len(pure.parts) != 5
        or pure.parts[:2] != ("coordination", "instructions")
        or INSTRUCTION_ID.fullmatch(pure.parts[2]) is None
        or pure.parts[3] != "reviews"
        or REVIEW_FILE.fullmatch(pure.parts[4]) is None
    ):
        raise ValueError("invalid execution-review receipt path")
    path = root.joinpath(*pure.parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("execution-review receipt is missing")
    payload = path.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError("execution-review receipt changed")
    document = yaml.safe_load(payload)
    document = _validate(document)
    if document["instruction_id"] != pure.parts[2] or f'{document["review_id"]}.yaml' != pure.parts[4]:
        raise ValueError("execution-review receipt identity changed")
    for item in document["evidence"]:
        _, parts = _safe_evidence_path(document["instruction_id"], item["path"])
        evidence_path = root.joinpath(*parts)
        if (
            evidence_path.is_symlink()
            or not evidence_path.is_file()
            or evidence_path.stat().st_size != item["size_bytes"]
            or hashlib.sha256(evidence_path.read_bytes()).hexdigest() != item["sha256"]
        ):
            raise ValueError("execution-review evidence changed")
    state, state_sha256 = _state_from_evidence(
        root,
        document["instruction_id"],
        document["verdict"],
        document["evidence"],
    )
    if (
        state["state"] != document["observed_state"]
        or state_sha256 != document["journal_sha256"]
    ):
        raise ValueError("execution-review receipt is not bound to its execution evidence")
    return document


def record(
    root: Path,
    *,
    instruction_id: str,
    verdict: str,
    summary: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    root = _root(root)
    actor = _actor(root)
    if verdict not in VERDICTS:
        raise ValueError("invalid execution-review verdict")
    if type(summary) is not str or len(summary.strip()) < 12:
        raise ValueError("execution-review summary is too short")
    _materialize_execution_evidence(root, instruction_id, evidence_refs)
    evidence = _evidence(root, instruction_id, evidence_refs)
    state, journal_sha256 = _state_from_evidence(
        root, instruction_id, verdict, evidence
    )
    directory = _review_directory(root, instruction_id)
    existing = [
        int(match.group(2))
        for path in directory.iterdir()
        if (match := REVIEW_FILE.fullmatch(path.name)) is not None and match.group(1) == actor
    ]
    review_id = f"{actor}-{max(existing, default=0) + 1:03d}"
    document = {
        "schema_version": 1,
        "review_id": review_id,
        "instruction_id": instruction_id,
        "reviewed_by": actor,
        "observed_state": state["state"],
        "journal_sha256": journal_sha256,
        "verdict": verdict,
        "summary": summary.strip(),
        "evidence": evidence,
        "reviewed_at": _utc_now(),
    }
    path = directory / f"{review_id}.yaml"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    relative = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    status = {
        "ISSUE_NEXT_R_CORRECTION": "NEXT_R_CORRECTION_REQUIRED",
        "VERIFIED_CORRECT": "VERIFIED_CORRECT",
        "CATASTROPHIC_REPORT_REQUIRED": "CATASTROPHIC_REPORT_REQUIRED",
    }[verdict]
    return {
        "status": status,
        "review_path": relative,
        "review_sha256": digest,
        "instruction_id": instruction_id,
        "verdict": verdict,
    }
