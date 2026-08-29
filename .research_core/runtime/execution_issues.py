"""Append-only B/C reports only for catastrophic SERVER execution errors."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any

import yaml

from . import peer_governance


INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
ISSUE_FILE = re.compile(r"([BC])-([0-9]{3,})\.yaml\Z")
SEVERITIES = {"CATASTROPHIC"}
CATEGORIES = {
    "SCIENTIFIC_ROUTE_INVALIDATION",
    "RESULT_CHAIN_FUNDAMENTALLY_INVALID",
    "UNRECOVERABLE_EXTERNAL_DAMAGE",
}
REQUIRED_ACTIONS = {
    "STOP_AND_REPLAN",
    "USER_DECISION",
}
REPORT_KEYS = {
    "instruction_id",
    "severity",
    "category",
    "summary",
    "evidence_refs",
    "impact",
    "required_action",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    if not (root / ".git").exists() or not (root / "project.yaml").is_file():
        raise ValueError("execution issue reporting requires a project root")
    return root


def _role(root: Path) -> str:
    role = peer_governance.current_worker(root)["role"]
    mapped = {"PEER_B": "B", "PEER_C": "C", "SERVER": "SERVER"}.get(role)
    if mapped is None:
        raise ValueError("unknown execution issue actor")
    return mapped


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"execution issue record is not a plain file: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError("execution issue record must be a mapping")
    return value


def _exclusive_yaml(path: Path, value: dict[str, Any]) -> None:
    payload = yaml.safe_dump(value, allow_unicode=True, sort_keys=False).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ValueError("execution issue directory must be a plain directory")
    with path.open("xb") as handle:
        handle.write(payload)


def _reference(value: str) -> str:
    if type(value) is not str or not value or len(value) > 512 or "\\" in value:
        raise ValueError("invalid execution issue evidence reference")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise ValueError("execution issue evidence reference escapes project")
    return value


def _issue_root(root: Path) -> Path:
    base = root / "coordination/execution-issues"
    if base.is_symlink() or not base.is_dir():
        raise ValueError("execution issue root must be a plain directory")
    return base


def _report_path(root: Path, relative: str) -> Path:
    reference = _reference(relative)
    parts = PurePosixPath(reference).parts
    if (
        len(parts) != 4
        or parts[:2] != ("coordination", "execution-issues")
        or INSTRUCTION_ID.fullmatch(parts[2]) is None
        or ISSUE_FILE.fullmatch(parts[3]) is None
    ):
        raise ValueError("invalid execution issue path")
    path = root.joinpath(*parts)
    expected_parent = _issue_root(root) / parts[2]
    if path.parent.resolve() != expected_parent.resolve():
        raise ValueError("execution issue path escapes project")
    return path


def _reports(root: Path) -> list[Path]:
    base = _issue_root(root)
    paths: list[Path] = []
    for instruction in sorted(base.iterdir()):
        if instruction.name == "README.md":
            continue
        if (
            instruction.is_symlink()
            or not instruction.is_dir()
            or INSTRUCTION_ID.fullmatch(instruction.name) is None
        ):
            raise ValueError("invalid execution issue instruction directory")
        for path in sorted(instruction.iterdir()):
            if path.name.endswith((".notice.yaml", ".ack.yaml", ".resolution.yaml")):
                continue
            if path.is_symlink() or not path.is_file() or ISSUE_FILE.fullmatch(path.name) is None:
                raise ValueError("invalid execution issue record name")
            paths.append(path)
    return paths


def _validate_report(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "issue_id",
        "instruction_id",
        "reported_by",
        "severity",
        "category",
        "summary",
        "evidence_refs",
        "impact",
        "required_action",
        "reported_at",
        "user_notification_required",
    }
    if type(value) is not dict or set(value) != required or value.get("schema_version") != 1:
        raise ValueError("invalid execution issue record")
    match = ISSUE_FILE.fullmatch(f"{value.get('issue_id')}.yaml")
    if (
        match is None
        or value.get("reported_by") != match.group(1)
        or INSTRUCTION_ID.fullmatch(str(value.get("instruction_id"))) is None
        or value.get("severity") not in SEVERITIES
        or value.get("category") not in CATEGORIES
        or value.get("required_action") not in REQUIRED_ACTIONS
        or value.get("user_notification_required") is not True
    ):
        raise ValueError("invalid execution issue identity")
    for key in ("summary", "impact"):
        if type(value.get(key)) is not str or len(value[key].strip()) < 12:
            raise ValueError(f"execution issue {key} is too short")
    refs = value.get("evidence_refs")
    if type(refs) is not list or not refs or any(type(item) is not str for item in refs):
        raise ValueError("execution issue requires evidence references")
    for item in refs:
        _reference(item)
    if type(value.get("reported_at")) is not str or not value["reported_at"]:
        raise ValueError("execution issue timestamp is invalid")
    return value


def report(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    root = _root(root)
    actor = _role(root)
    if actor not in {"B", "C"}:
        raise ValueError("only B or C may report a catastrophic SERVER execution error")
    if type(request) is not dict or set(request) != REPORT_KEYS:
        raise ValueError("invalid execution issue request")
    instruction_id = request["instruction_id"]
    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid execution instruction id")
    if request["severity"] not in SEVERITIES or request["category"] not in CATEGORIES:
        raise ValueError("invalid execution issue classification")
    if request["required_action"] not in REQUIRED_ACTIONS:
        raise ValueError("invalid execution issue required action")
    for key in ("summary", "impact"):
        if type(request[key]) is not str or len(request[key].strip()) < 12:
            raise ValueError(f"execution issue {key} is too short")
    refs = request["evidence_refs"]
    if type(refs) is not list or not refs or any(type(item) is not str for item in refs):
        raise ValueError("execution issue requires evidence references")
    refs = [_reference(item) for item in refs]
    parent = _issue_root(root) / instruction_id
    parent.mkdir(exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("execution issue instruction directory is invalid")
    existing = [
        int(match.group(2))
        for path in parent.iterdir()
        if (match := ISSUE_FILE.fullmatch(path.name)) is not None and match.group(1) == actor
    ]
    sequence = max(existing, default=0) + 1
    issue_id = f"{actor}-{sequence:03d}"
    document = {
        "schema_version": 1,
        "issue_id": issue_id,
        "instruction_id": instruction_id,
        "reported_by": actor,
        "severity": request["severity"],
        "category": request["category"],
        "summary": request["summary"].strip(),
        "evidence_refs": refs,
        "impact": request["impact"].strip(),
        "required_action": request["required_action"],
        "reported_at": _utc_now(),
        "user_notification_required": True,
    }
    path = parent / f"{issue_id}.yaml"
    _exclusive_yaml(path, document)
    relative = path.relative_to(root).as_posix()
    return {
        "status": "CATASTROPHIC_USER_NOTIFICATION_REQUIRED",
        "issue_path": relative,
        "summary": document["summary"],
        "impact": document["impact"],
        "required_action": document["required_action"],
        "next_action": "TELL_USER_IMMEDIATELY_THEN_RECORD_NOTICE",
    }


def _companion(report_path: Path, kind: str) -> Path:
    return report_path.with_name(f"{report_path.stem}.{kind}.yaml")


def _bound_companion(root: Path, report_path: Path, kind: str) -> dict[str, Any] | None:
    path = _companion(report_path, kind)
    if path.is_symlink():
        raise ValueError("execution issue companion must not be a symbolic link")
    if not path.exists():
        return None
    document = _load_yaml(path)
    common = {
        "schema_version",
        "issue_path",
        "issue_sha256",
    }
    specific = {
        "notice": {"notified_by", "summary", "notified_at"},
        "ack": {"acknowledged_by", "response_action", "summary", "acknowledged_at"},
        "resolution": {"resolved_by", "verdict", "summary", "resolved_at"},
    }[kind]
    relative = report_path.relative_to(root).as_posix()
    if (
        set(document) != common | specific
        or document.get("schema_version") != 1
        or document.get("issue_path") != relative
        or document.get("issue_sha256")
        != hashlib.sha256(report_path.read_bytes()).hexdigest()
    ):
        raise ValueError("execution issue companion binding is invalid")
    actor_match = ISSUE_FILE.fullmatch(report_path.name)
    if actor_match is None:
        raise ValueError("execution issue companion report identity is invalid")
    if kind == "notice" and document.get("notified_by") != actor_match.group(1):
        raise ValueError("execution issue notice actor is invalid")
    if kind == "ack" and (
        document.get("acknowledged_by") != "SERVER"
        or document.get("response_action")
        not in {"REQUEST_BC_REPLAN", "STOP_AND_WAIT_USER"}
    ):
        raise ValueError("execution issue acknowledgement is invalid")
    if kind == "resolution" and (
        document.get("resolved_by") not in {"B", "C"}
        or document.get("verdict") not in {"RESOLVED", "SUPERSEDED_BY_NEW_PLAN"}
    ):
        raise ValueError("execution issue resolution is invalid")
    summary = document.get("summary")
    timestamp_key = {
        "notice": "notified_at",
        "ack": "acknowledged_at",
        "resolution": "resolved_at",
    }[kind]
    if (
        type(summary) is not str
        or len(summary.strip()) < 8
        or type(document.get(timestamp_key)) is not str
        or not document[timestamp_key]
    ):
        raise ValueError("execution issue companion content is invalid")
    return document


def record_notice(root: Path, issue_path: str, summary: str) -> dict[str, Any]:
    root = _root(root)
    actor = _role(root)
    path = _report_path(root, issue_path)
    report_value = _validate_report(_load_yaml(path))
    if actor != report_value["reported_by"]:
        raise ValueError("only the reporting peer records the immediate user notice")
    if type(summary) is not str or len(summary.strip()) < 8:
        raise ValueError("user notice summary is required")
    notice = _companion(path, "notice")
    _exclusive_yaml(
        notice,
        {
            "schema_version": 1,
            "issue_path": issue_path,
            "issue_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "notified_by": actor,
            "summary": summary.strip(),
            "notified_at": _utc_now(),
        },
    )
    return {"status": "USER_NOTIFIED", "notice_path": notice.relative_to(root).as_posix()}


def acknowledge(
    root: Path, issue_path: str, response_action: str, summary: str
) -> dict[str, Any]:
    root = _root(root)
    if _role(root) != "SERVER":
        raise ValueError("only SERVER acknowledges an execution issue")
    if response_action not in {"REQUEST_BC_REPLAN", "STOP_AND_WAIT_USER"}:
        raise ValueError("invalid SERVER issue response action")
    if type(summary) is not str or len(summary.strip()) < 8:
        raise ValueError("SERVER acknowledgement summary is required")
    path = _report_path(root, issue_path)
    _validate_report(_load_yaml(path))
    if _bound_companion(root, path, "notice") is None:
        raise ValueError("SERVER cannot acknowledge before immediate user notice")
    ack = _companion(path, "ack")
    _exclusive_yaml(
        ack,
        {
            "schema_version": 1,
            "issue_path": issue_path,
            "issue_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "acknowledged_by": "SERVER",
            "response_action": response_action,
            "summary": summary.strip(),
            "acknowledged_at": _utc_now(),
        },
    )
    return {"status": "ACKNOWLEDGED", "ack_path": ack.relative_to(root).as_posix()}


def resolve(root: Path, issue_path: str, verdict: str, summary: str) -> dict[str, Any]:
    root = _root(root)
    actor = _role(root)
    if actor not in {"B", "C"}:
        raise ValueError("only B or C verifies execution issue resolution")
    if verdict not in {"RESOLVED", "SUPERSEDED_BY_NEW_PLAN"}:
        raise ValueError("invalid execution issue resolution verdict")
    if type(summary) is not str or len(summary.strip()) < 8:
        raise ValueError("execution issue resolution summary is required")
    path = _report_path(root, issue_path)
    _validate_report(_load_yaml(path))
    if _bound_companion(root, path, "ack") is None:
        raise ValueError("B/C cannot resolve before SERVER acknowledgement")
    resolution = _companion(path, "resolution")
    _exclusive_yaml(
        resolution,
        {
            "schema_version": 1,
            "issue_path": issue_path,
            "issue_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "resolved_by": actor,
            "verdict": verdict,
            "summary": summary.strip(),
            "resolved_at": _utc_now(),
        },
    )
    return {"status": verdict, "resolution_path": resolution.relative_to(root).as_posix()}


def list_issues(root: Path, instruction_id: str | None = None) -> list[dict[str, Any]]:
    root = _root(root)
    if instruction_id is not None and INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid execution instruction id")
    result: list[dict[str, Any]] = []
    for path in _reports(root):
        report_value = _validate_report(_load_yaml(path))
        if instruction_id is not None and report_value["instruction_id"] != instruction_id:
            continue
        relative = path.relative_to(root).as_posix()
        noticed = _bound_companion(root, path, "notice") is not None
        acknowledged = _bound_companion(root, path, "ack") is not None
        resolved = _bound_companion(root, path, "resolution") is not None
        result.append(
            {
                **report_value,
                "issue_path": relative,
                "notification_status": "RECORDED" if noticed else "REQUIRED",
                "server_status": "ACKNOWLEDGED" if acknowledged else "PENDING",
                "status": "RESOLVED" if resolved else "OPEN",
            }
        )
    return result


def require_no_unnotified(root: Path) -> None:
    pending = [
        item["issue_path"]
        for item in list_issues(root)
        if item["notification_status"] == "REQUIRED"
    ]
    if pending:
        raise ValueError(
            "B/C must notify the user about SERVER execution errors before further research: "
            + ",".join(pending)
        )


def pending_server_attention(root: Path) -> list[dict[str, Any]]:
    return [item for item in list_issues(root) if item["status"] == "OPEN"]
