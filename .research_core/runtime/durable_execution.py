"""Durable r-prefixed instruction runner used by the “拉取，执行” entrypoint."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any

import yaml


INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
GUARD_CAPABILITIES = {
    "LANDLOCK_ABI_1_WRITE_DELETE_ALLOWLIST",
    "NETWORK_NAMESPACE_WHEN_UNDECLARED",
    "AMBIENT_SECRET_ENV_SCRUB",
    "NO_SUDO_REQUIRED",
}
EXECUTION_GUARD_RELATIVE = ".research_core/runtime/execution_guard.py"
STATES = {
    "CLAIMED",
    "RUNNING",
    "REPAIR_REQUIRED",
    "PROJECT_LOCKED",
    "REPORTING",
    "PUSHED",
    "COMPLETE",
    "FAILED",
    "INCOMPLETE",
    "BLOCKED",
    "STOPPED",
}
TERMINAL = {"COMPLETE", "FAILED", "INCOMPLETE", "BLOCKED", "STOPPED"}
ABNORMAL_REVIEW_ACTION = (
    "B/C inspect the published command logs, result previews, and acceptance evidence; "
    "issue the next r-prefixed correction for an ordinary error, or report a "
    "catastrophic scientific-route error to the user"
)
PROJECT_LOCK_BLOCKER = "PROJECT_LOCKED: project operations are stopped until explicit unlock"
EVIDENCE_PREVIEW_BYTES = 65536
JOURNAL_KEYS = {
    "schema_version",
    "instruction_id",
    "dispatch_token",
    "plan_ref",
    "plan_sha256",
    "source_commit",
    "authority_snapshot",
    "authority_sha256",
    "permission_snapshots",
    "placement_receipt",
    "boundary_guard",
    "state",
    "attempt",
    "adaptation_sequence",
    "worker_pid",
    "command_pid",
    "dataset_checkpoint_index",
    "dataset_mounts",
    "checkpoint_index",
    "acceptance_checkpoint_index",
    "heartbeat_at",
    "started_at",
    "deadline_at",
    "finished_at",
    "exit_code",
    "failure_reason",
    "recovery_action",
    "terminal_message",
    "result_branch",
    "result_commit",
    "remote_commit",
    "stop_requested",
    "supervision_required",
    "supervision_status",
    "bc_review_required",
    "bc_review_reason",
    "bc_review_status",
    "bc_review_receipt",
    "bc_review_sha256",
    "bc_review_observed_state",
    "bc_reviewed_journal_sha256",
    "bc_correction_instruction_id",
}
DATASET_MOUNT_KEYS = {
    "schema_version",
    "owner_id",
    "route_index",
    "method",
    "dataset_id",
    "version",
    "digest",
    "source_node_id",
    "target_node_id",
    "target_root",
    "status",
}
_DETACHED_WORKERS: list[subprocess.Popen] = []


class _DatasetPreparationControl(RuntimeError):
    def __init__(self, state: str, reason: str):
        super().__init__(reason)
        self.state = state
        self.reason = reason


class _PublicationControl(RuntimeError):
    def __init__(self, state: str, reason: str):
        super().__init__(reason)
        self.state = state
        self.reason = reason


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _process_group_options() -> dict[str, Any]:
    if os.name == "nt":
        return {
            "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        }
    return {"start_new_session": True}


def _terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    """Stop the guard and every command process it started."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()


def _runtime_module(name: str):
    runtime_root = Path(__file__).resolve().parent
    package_name = f"cqc_durable_runtime_{hashlib.sha256(str(runtime_root).encode()).hexdigest()[:16]}"
    if package_name not in sys.modules:
        specification = importlib.util.spec_from_file_location(
            package_name,
            runtime_root / "__init__.py",
            submodule_search_locations=[str(runtime_root)],
        )
        if specification is None or specification.loader is None:
            raise ValueError("research runtime package is unavailable")
        package = importlib.util.module_from_spec(specification)
        sys.modules[package_name] = package
        specification.loader.exec_module(package)
    qualified = f"{package_name}.{name}"
    if qualified in sys.modules:
        return sys.modules[qualified]
    path = runtime_root / f"{name}.py"
    specification = importlib.util.spec_from_file_location(qualified, path)
    if specification is None or specification.loader is None:
        raise ValueError(f"research runtime is unavailable: {name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[qualified] = module
    specification.loader.exec_module(module)
    return module


def _git(
    root: Path,
    *arguments: str,
    check: bool = True,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            shell=False,
            timeout=timeout,
            env=environment,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"Git execution operation timed out: {arguments[0]}") from error
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"Git execution operation failed: {detail}")
    return completed


def _require_https_origin(root: Path) -> str:
    url = _git(root, "remote", "get-url", "--push", "origin").stdout.strip()
    if re.fullmatch(r"https://[^\s]+", url, flags=re.IGNORECASE) is None:
        raise ValueError("production origin push URL must use HTTPS")
    return url


def _exact_root(root: Path) -> Path:
    root = Path(root).resolve()
    completed = _git(root, "rev-parse", "--show-toplevel")
    if Path(completed.stdout.strip()).resolve() != root:
        raise ValueError("pull-execute requires the exact repository root")
    return root


def _require_server(root: Path) -> None:
    if _runtime_module("peer_governance").current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER may claim or run numeric instructions")


def _git_directory(root: Path) -> Path:
    value = _git(root, "rev-parse", "--git-dir").stdout.strip()
    path = Path(value)
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def _journal_directory(root: Path, instruction_id: str) -> Path:
    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid r-prefixed instruction id")
    return _git_directory(root) / "cqc-execution" / instruction_id


def _journal_path(root: Path, instruction_id: str) -> Path:
    return _journal_directory(root, instruction_id) / "JOURNAL.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"plain YAML file required: {path.name}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise ValueError(f"YAML mapping required: {path.name}")
    return document


def _exclusive_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, document: dict[str, Any]) -> None:
    payload = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _stream_binding(path: Path, key: str, value: str) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    head_limit = EVIDENCE_PREVIEW_BYTES // 2
    tail_limit = EVIDENCE_PREVIEW_BYTES - head_limit
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    truncated = size > EVIDENCE_PREVIEW_BYTES
    with path.open("rb") as handle:
        if not truncated:
            captured = handle.read(EVIDENCE_PREVIEW_BYTES)
            preview = captured.decode("utf-8", errors="replace")
            preview_bytes = len(captured)
        else:
            head = handle.read(head_limit)
            handle.seek(-tail_limit, os.SEEK_END)
            tail = handle.read(tail_limit)
            preview = (
                head.decode("utf-8", errors="replace")
                + "\n...<CQC_EVIDENCE_PREVIEW_TRUNCATED>...\n"
                + tail.decode("utf-8", errors="replace")
            )
            preview_bytes = len(head) + len(tail)
    return {
        key: value,
        "size_bytes": size,
        "sha256": digest.hexdigest(),
        "preview_utf8": preview,
        "preview_bytes": preview_bytes,
        "preview_truncated": truncated,
    }


def load_journal(root: Path, instruction_id: str) -> dict[str, Any]:
    root = _exact_root(root)
    document = _load_yaml(_journal_path(root, instruction_id))
    # Compatibility for v1.11 journals claimed before W0026. New claims always
    # persist both fields; old nonterminal work remains recoverable.
    document.setdefault("dispatch_token", hashlib.sha256(
        f"LEGACY\0{instruction_id}".encode("utf-8")
    ).hexdigest())
    document.setdefault("dataset_mounts", [])
    document.setdefault("permission_snapshots", {})
    if (
        set(document) != JOURNAL_KEYS
        or type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
        or document.get("instruction_id") != instruction_id
        or type(document.get("dispatch_token")) is not str
        or SHA256.fullmatch(document["dispatch_token"]) is None
        or document.get("state") not in STATES
        or type(document.get("attempt")) is not int
        or document["attempt"] < 0
        or type(document.get("checkpoint_index")) is not int
        or document["checkpoint_index"] < 0
        or type(document.get("dataset_checkpoint_index")) is not int
        or document["dataset_checkpoint_index"] < 0
        or type(document.get("plan_ref")) is not str
        or type(document.get("plan_sha256")) is not str
        or SHA256.fullmatch(document["plan_sha256"]) is None
        or type(document.get("source_commit")) is not str
        or GIT_OID.fullmatch(document["source_commit"]) is None
        or type(document.get("authority_snapshot")) is not dict
        or type(document.get("authority_sha256")) is not str
        or SHA256.fullmatch(document["authority_sha256"]) is None
        or type(document.get("permission_snapshots")) is not dict
        or any(
            permission not in {"external_write", "resource_expansion", "publish"}
            or type(snapshot) is not dict
            for permission, snapshot in document.get("permission_snapshots", {}).items()
        )
        or type(document.get("placement_receipt")) is not dict
        or type(document.get("boundary_guard")) is not dict
        or type(document.get("dataset_mounts")) is not list
        or any(
            type(item) is not dict
            or set(item) != DATASET_MOUNT_KEYS
            or item.get("schema_version") != 1
            or item.get("owner_id") != instruction_id
            or type(item.get("route_index")) is not int
            or item["route_index"] < 0
            or item.get("method") != "READONLY_SHARD_STREAM"
            or item.get("status") not in {"ACTIVE", "RELEASED"}
            for item in document.get("dataset_mounts", [])
        )
        or type(document.get("adaptation_sequence")) is not int
        or document["adaptation_sequence"] < 0
        or type(document.get("acceptance_checkpoint_index")) is not int
        or document["acceptance_checkpoint_index"] < 0
        or type(document.get("deadline_at")) is not str
        or not document["deadline_at"]
        or type(document.get("stop_requested")) is not bool
        or type(document.get("supervision_required")) is not bool
        or document.get("supervision_status") not in {"ACTIVE", "TERMINAL"}
        or type(document.get("bc_review_required")) is not bool
        or (
            document["bc_review_required"]
            and (
                type(document.get("bc_review_reason")) is not str
                or not document["bc_review_reason"]
            )
        )
        or (
            not document["bc_review_required"]
            and document.get("bc_review_reason") is not None
        )
        or (
            document["bc_review_required"]
            and (
                document.get("bc_review_status") != "REQUIRED"
                or document.get("bc_review_receipt") is not None
                or document.get("bc_review_sha256") is not None
                or document.get("bc_review_observed_state") is not None
                or document.get("bc_reviewed_journal_sha256") is not None
                or document.get("bc_correction_instruction_id") is not None
            )
        )
        or (
            not document["bc_review_required"]
            and document.get("bc_review_status") == "NOT_REQUIRED"
            and (
                document.get("bc_review_receipt") is not None
                or document.get("bc_review_sha256") is not None
                or document.get("bc_review_observed_state") is not None
                or document.get("bc_reviewed_journal_sha256") is not None
                or document.get("bc_correction_instruction_id") is not None
            )
        )
        or (
            not document["bc_review_required"]
            and document.get("bc_review_status") != "NOT_REQUIRED"
            and (
                document.get("bc_review_status") not in {
                    "NEXT_R_CORRECTION_REQUIRED",
                    "VERIFIED_CORRECT",
                    "CATASTROPHIC_REPORT_REQUIRED",
                }
                or type(document.get("bc_review_receipt")) is not str
                or not document["bc_review_receipt"]
                or type(document.get("bc_review_sha256")) is not str
                or SHA256.fullmatch(document["bc_review_sha256"]) is None
                or document.get("bc_review_observed_state") not in STATES
                or type(document.get("bc_reviewed_journal_sha256")) is not str
                or SHA256.fullmatch(document["bc_reviewed_journal_sha256"]) is None
                or (
                    document.get("bc_correction_instruction_id") is not None
                    and (
                        document.get("bc_review_status")
                        != "NEXT_R_CORRECTION_REQUIRED"
                        or type(document["bc_correction_instruction_id"]) is not str
                        or INSTRUCTION_ID.fullmatch(
                            document["bc_correction_instruction_id"]
                        )
                        is None
                    )
                )
            )
        )
    ):
        raise ValueError("invalid durable execution journal")
    routes = document["placement_receipt"].get("dataset_routes", [])
    if (
        type(routes) is not list
        or document["dataset_checkpoint_index"] > len(routes)
        or any(type(route) is not dict for route in routes)
    ):
        raise ValueError("invalid durable dataset preparation checkpoint")
    if not document["bc_review_required"] and document["bc_review_status"] != "NOT_REQUIRED":
        pure = PurePosixPath(document["bc_review_receipt"])
        if (
            pure.is_absolute()
            or ".." in pure.parts
            or len(pure.parts) != 5
            or pure.parts[:3] != ("coordination", "instructions", instruction_id)
            or pure.parts[3] != "reviews"
        ):
            raise ValueError("invalid B/C review receipt binding")
        receipt = root.joinpath(*pure.parts)
        if (
            receipt.is_symlink()
            or not receipt.is_file()
            or hashlib.sha256(receipt.read_bytes()).hexdigest()
            != document["bc_review_sha256"]
        ):
            raise ValueError("B/C review receipt changed")
    return document


def _update(root: Path, instruction_id: str, **changes: Any) -> dict[str, Any]:
    with _runtime_module("transactions").journal(root, instruction_id):
        document = load_journal(root, instruction_id)
        if not set(changes).issubset(JOURNAL_KEYS - {"schema_version", "instruction_id"}):
            raise ValueError("invalid journal transition fields")
        document.update(changes)
        _atomic_yaml(_journal_path(root, instruction_id), document)
        return document


def _release_dataset_mounts(
    root: Path, instruction_id: str, *, reset_checkpoint: bool = True
) -> str | None:
    """Release profile-46 subset leases; reject stale pre-v2 remote mounts."""

    del reset_checkpoint
    if not _journal_path(root, instruction_id).is_file():
        return None
    journal = load_journal(root, instruction_id)
    if journal["dataset_mounts"]:
        return "legacy remote dataset mount requires explicit operator cleanup"
    try:
        from cqc_fabric import local_execution

        local_execution.release_preflight(journal["placement_receipt"])
    except (OSError, ValueError) as error:
        return f"local dataset subset lease cleanup failed: {error}"
    return None


def _terminal(
    root: Path,
    instruction_id: str,
    *,
    state: str,
    reason: str,
    recovery_action: str,
    exit_code: int | None,
) -> dict[str, Any]:
    with _runtime_module("transactions").journal(root, instruction_id):
        return _terminal_locked(
            root,
            instruction_id,
            state=state,
            reason=reason,
            recovery_action=recovery_action,
            exit_code=exit_code,
        )


def _terminal_locked(
    root: Path,
    instruction_id: str,
    *,
    state: str,
    reason: str,
    recovery_action: str,
    exit_code: int | None,
) -> dict[str, Any]:
    if state not in TERMINAL - {"COMPLETE"}:
        raise ValueError("invalid abnormal terminal state")
    cleanup_error = _release_dataset_mounts(root, instruction_id)
    if cleanup_error is not None:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"{reason}; {cleanup_error}",
            exit_code=exit_code,
            cleanup_mounts=False,
        )
    current = load_journal(root, instruction_id)
    terminal = {
        **current,
        "state": state,
        "command_pid": None,
        "worker_pid": None,
        "heartbeat_at": _utc_now(),
        "finished_at": _utc_now(),
        "exit_code": exit_code,
        "failure_reason": reason,
        # An abnormal terminal state is immutable. This field describes the
        # next B/C governance action; it never authorizes same-r recovery.
        "recovery_action": recovery_action,
        "terminal_message": f"未正常执行完：{reason}",
        "supervision_status": "TERMINAL",
        "bc_review_required": True,
        "bc_review_reason": (
            "B_OR_C_MUST_REVIEW_COMMAND_LOG_RESULT_AND_ACCEPTANCE_THEN_"
            "ISSUE_DIRECT_NEXT_R_CORRECTION_IF_ORDINARY"
        ),
        "bc_review_status": "REQUIRED",
        "bc_review_receipt": None,
        "bc_review_sha256": None,
        "bc_review_observed_state": None,
        "bc_reviewed_journal_sha256": None,
        "bc_correction_instruction_id": None,
    }
    # Evidence is frozen first. If it cannot be produced, the on-disk journal
    # remains nonterminal and the worker can retry instead of deadlocking review.
    _write_abnormal_evidence(root, instruction_id, terminal)
    _atomic_yaml(_journal_path(root, instruction_id), terminal)
    # Publication failure does not destroy the local terminal evidence. SERVER
    # can idempotently retry it with execution publish-abnormal.
    try:
        publish_abnormal(root, instruction_id)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return load_journal(root, instruction_id)


def _engineering_pause(
    root: Path,
    instruction_id: str,
    *,
    reason: str,
    exit_code: int | None,
    cleanup_mounts: bool = True,
) -> dict[str, Any]:
    """Pause a repairable engineering failure without consuming a new r number."""

    reset_local_cache = False
    if cleanup_mounts:
        if _journal_path(root, instruction_id).is_file():
            reset_local_cache = (
                load_journal(root, instruction_id)
                .get("placement_receipt", {})
                .get("server_profile")
                == "46"
            )
        cleanup_error = _release_dataset_mounts(root, instruction_id)
        if cleanup_error is not None:
            reason = f"{reason}; {cleanup_error}"
    return _update(
        root,
        instruction_id,
        state="REPAIR_REQUIRED",
        command_pid=None,
        worker_pid=None,
        heartbeat_at=_utc_now(),
        finished_at=None,
        exit_code=exit_code,
        failure_reason=reason,
        recovery_action=(
            "SERVER inspects logs, existing files, environments, official/project "
            "configuration and checkpoints; records a CONTINUE_AND_LOG adaptation; "
            "then recovers this same r-prefixed instruction"
        ),
        terminal_message=None,
        supervision_status="ACTIVE",
        bc_review_required=False,
        bc_review_reason=None,
        bc_review_status="NOT_REQUIRED",
        **(
            {"placement_receipt": {}, "dataset_checkpoint_index": 0}
            if reset_local_cache
            else {}
        ),
    )


def _project_lock_pause(
    root: Path,
    instruction_id: str,
    *,
    reason: str = PROJECT_LOCK_BLOCKER,
) -> dict[str, Any]:
    """Pause an in-flight instruction without consuming it or requiring B/C review."""

    reset_local_cache = (
        load_journal(root, instruction_id)
        .get("placement_receipt", {})
        .get("server_profile")
        == "46"
    )
    cleanup_error = _release_dataset_mounts(root, instruction_id)
    if cleanup_error is not None:
        reason = f"{reason}; {cleanup_error}"
    return _update(
        root,
        instruction_id,
        state="PROJECT_LOCKED",
        command_pid=None,
        worker_pid=None,
        heartbeat_at=_utc_now(),
        finished_at=None,
        exit_code=None,
        failure_reason=reason,
        recovery_action=(
            "unlock the project, synchronize main, then recover this same instruction"
        ),
        terminal_message=None,
        supervision_status="ACTIVE",
        bc_review_required=False,
        bc_review_reason=None,
        bc_review_status="NOT_REQUIRED",
        **(
            {"placement_receipt": {}, "dataset_checkpoint_index": 0}
            if reset_local_cache
            else {}
        ),
    )


def _write_abnormal_evidence(
    root: Path, instruction_id: str, journal: dict[str, Any]
) -> str:
    """Freeze the terminal journal and available command logs inside the project."""

    journal_payload = yaml.safe_dump(
        journal, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    logs = []
    log_root = _journal_directory(root, instruction_id) / "logs"
    if log_root.exists():
        if log_root.is_symlink() or not log_root.is_dir():
            raise ValueError("durable execution log root is invalid")
        for path in sorted(log_root.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise ValueError("durable execution log evidence is invalid")
            logs.append(_stream_binding(path, "name", path.name))
    results = []
    plan = _plan_for_journal(root, journal)
    for relative in plan["expected_results"]:
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink():
            raise ValueError("abnormal result evidence cannot be a symbolic link")
        if not path.is_file():
            continue
        results.append(_stream_binding(path, "path", relative))
    document = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "terminal_journal_sha256": hashlib.sha256(journal_payload).hexdigest(),
        "terminal_journal": journal,
        "command_logs": logs,
        "result_files": results,
        "recorded_at": _utc_now(),
    }
    relative = (
        Path("coordination/executions")
        / instruction_id
        / f'ABNORMAL-{journal["attempt"]:03d}.yaml'
    )
    path = root / relative
    if path.parent.exists() and (path.parent.is_symlink() or not path.parent.is_dir()):
        raise ValueError("abnormal execution evidence root is invalid")
    _atomic_yaml(path, document)
    return relative.as_posix()


def publish_abnormal(root: Path, instruction_id: str) -> dict[str, Any]:
    """Idempotently publish a terminal evidence bundle on exec/<rNNN>."""

    root = _exact_root(root)
    _require_server(root)
    _require_https_origin(root)
    journal = load_journal(root, instruction_id)
    if journal["state"] not in TERMINAL - {"COMPLETE"}:
        raise ValueError("only abnormal terminal evidence can be published")
    relative = (
        Path("coordination/executions")
        / instruction_id
        / f'ABNORMAL-{journal["attempt"]:03d}.yaml'
    ).as_posix()
    branch = f"exec/{instruction_id}"
    original = _git(root, "branch", "--show-current").stdout.strip()
    if not original:
        raise ValueError("abnormal publication requires a named Git branch")
    try:
        exists = (
            _git(
                root,
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/heads/{branch}",
                check=False,
            ).returncode
            == 0
        )
        if original != branch:
            if exists:
                _git(root, "switch", branch)
            else:
                _git(root, "switch", "-c", branch)
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink() or not path.is_file():
            raise ValueError("abnormal terminal evidence is missing")
        _git(root, "add", "--", relative)
        if _git(root, "diff", "--cached", "--quiet", "--", relative, check=False).returncode != 0:
            _git(
                root,
                "commit",
                "--only",
                "-m",
                f"execution {instruction_id}: publish abnormal evidence",
                "--",
                relative,
            )
        commit = _git(root, "rev-parse", "HEAD").stdout.strip()
        _git(root, "push", "origin", f"{branch}:{branch}")
        remote = _git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}").stdout.strip()
        remote_commit = remote.split()[0] if remote else ""
        if remote_commit != commit:
            raise ValueError("abnormal evidence remote ref does not match local commit")
        return {
            "status": "ABNORMAL_EVIDENCE_PUBLISHED",
            "instruction_id": instruction_id,
            "evidence_ref": relative,
            "result_branch": branch,
            "result_commit": commit,
            "remote_commit": remote_commit,
        }
    finally:
        current = _git(root, "branch", "--show-current", check=False).stdout.strip()
        if original and current and current != original:
            _git(root, "switch", original, check=False)


def _plan_path(root: Path, instruction_id: str) -> Path:
    return root / "coordination/instructions" / instruction_id / "SERVER_PLAN.yaml"


def _ready_candidates(root: Path) -> list[str]:
    parent = root / "coordination/instructions"
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("r-prefixed instruction root is unavailable")
    candidates = []
    for item in parent.iterdir():
        if not item.is_dir() or INSTRUCTION_ID.fullmatch(item.name) is None:
            continue
        plan = item / "SERVER_PLAN.yaml"
        if not plan.is_file() or plan.is_symlink():
            continue
        document = _load_yaml(plan)
        if document.get("instruction_id") != item.name or document.get("status") != "READY":
            raise ValueError(f"invalid READY instruction: {item.name}")
        if not _journal_path(root, item.name).exists():
            candidates.append(item.name)
    return sorted(candidates, key=lambda value: int(value[1:]))


def _master_recovery_candidates(root: Path) -> list[dict[str, Any]]:
    base = _git_directory(root) / "cqc-execution"
    if not base.exists():
        return []
    if base.is_symlink() or not base.is_dir():
        raise ValueError("durable execution journal root is invalid")
    result = []
    for directory in base.iterdir():
        if directory.is_symlink() or not directory.is_dir() or INSTRUCTION_ID.fullmatch(directory.name) is None:
            continue
        journal = load_journal(root, directory.name)
        if (
            journal["state"] in {
                "CLAIMED", "RUNNING", "REPAIR_REQUIRED", "PROJECT_LOCKED",
                "REPORTING", "PUSHED",
            }
            and not journal["bc_review_required"]
            and not _pid_alive(journal["worker_pid"])
        ):
            result.append(journal)
    return sorted(result, key=lambda item: int(item["instruction_id"][1:]), reverse=True)


def _review_gate_candidates(root: Path) -> list[dict[str, Any]]:
    base = _git_directory(root) / "cqc-execution"
    if not base.exists():
        return []
    if base.is_symlink() or not base.is_dir():
        raise ValueError("durable execution journal root is invalid")
    result = []
    for directory in base.iterdir():
        if directory.is_symlink() or not directory.is_dir() or INSTRUCTION_ID.fullmatch(directory.name) is None:
            continue
        journal = load_journal(root, directory.name)
        if (
            not _pid_alive(journal["worker_pid"])
            and (
                journal["bc_review_required"]
                or (
                    journal["bc_review_status"] == "NEXT_R_CORRECTION_REQUIRED"
                    and journal["bc_correction_instruction_id"] is None
                )
                or journal["bc_review_status"] == "CATASTROPHIC_REPORT_REQUIRED"
            )
        ):
            result.append(journal)
    return sorted(result, key=lambda item: int(item["instruction_id"][1:]), reverse=True)


def _permission_snapshots(
    root: Path, plan: dict[str, Any], *, online: bool
) -> dict[str, dict[str, Any]]:
    state = _load_yaml(root / "coordination/STATE.yaml")
    permissions = state.get("permissions")
    if type(permissions) is not dict:
        raise ValueError("project permissions are invalid")
    missing = [
        permission
        for permission in plan.get("required_permissions", [])
        if permissions.get(permission) is not True
    ]
    if missing:
        raise ValueError(f"required permissions are false: {','.join(missing)}")
    authorizations = state.get("permission_authorizations")
    snapshot_items: list[tuple[str, dict[str, Any]]] = []
    for permission in plan.get("required_permissions", []):
        if permission not in {"external_write", "resource_expansion", "publish"}:
            continue
        authorization = (
            authorizations.get(permission) if type(authorizations) is dict else None
        )
        if type(authorization) is not dict:
            raise ValueError(
                f"required permission lacks user authorization: {permission}"
            )
        snapshot = _runtime_module("authorization").permission_snapshot(
            root,
            permission=permission,
            authorization_ref=authorization.get("ref"),
            authorization_sha256=authorization.get("sha256"),
            plan=plan,
            online=online,
        )
        snapshot_items.append((permission, snapshot))
    return dict(snapshot_items)


def _permissions_blocker(
    root: Path,
    plan: dict[str, Any],
    *,
    expected_snapshots: dict[str, Any] | None = None,
    online: bool = False,
) -> str | None:
    try:
        snapshots = _permission_snapshots(root, plan, online=online)
    except (OSError, UnicodeError, ValueError) as error:
        mode = "online" if online else "local"
        return f"{mode} permission snapshot is invalid: {error}"
    if expected_snapshots is not None and snapshots != expected_snapshots:
        return "local permission snapshot changed after task claim"
    return None


def _document_sha256(document: dict[str, Any]) -> str:
    payload = yaml.safe_dump(
        document, allow_unicode=True, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _local_git_setting(root: Path, key: str, *, required: bool = True) -> str | None:
    completed = _git(root, "config", "--local", "--get", key, check=False)
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        if required:
            raise ValueError(f"host-local setting is missing: {key}")
        return None
    return value


def _placement_preflight(
    root: Path,
    plan: dict[str, Any],
    instruction_id: str,
) -> dict[str, Any]:
    try:
        from cqc_fabric import local_execution
    except ImportError as error:
        raise ValueError("host-global cqc-fabric 2.1 is unavailable") from error
    configured_profile = _local_git_setting(
        root, "cqc.server-profile", required=False
    )
    dataset_root = _local_git_setting(root, "cqc.dataset-root", required=False)
    project = _load_yaml(root / "project.yaml")
    return local_execution.preflight(
        root,
        project_id=project.get("project_id"),
        instruction_id=instruction_id,
        datasets=plan["datasets"],
        gpu_count=plan["resources"]["gpu_count"],
        gpu_memory_mib=plan["resources"]["gpu_memory_mib"],
        configured_profile=configured_profile,
        dataset_root=dataset_root,
    )

def _execution_guard(root: Path) -> tuple[list[str], dict[str, Any]]:
    path = root / EXECUTION_GUARD_RELATIVE
    if path.is_symlink() or not path.is_file():
        raise ValueError("source-commit-bound execution guard is missing")
    contract = _load_yaml(root / ".research_core/contract.yaml")
    # The contract owns durable-execution settings under its policy block.
    # Accept the former top-level position only for older migrated contracts.
    expected = contract.get("execution_guard_sha256")
    if expected is None:
        expected = contract.get("durable_execution_policy", {}).get(
            "execution_guard_sha256"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if type(expected) is not str or SHA256.fullmatch(expected) is None or actual != expected:
        raise ValueError("source-commit-bound execution guard digest changed")
    prefix = [sys.executable, "-I", "-B", str(path)]
    completed = subprocess.run(
        [*prefix, "--probe"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        raise ValueError("no-sudo execution guard is unavailable on this node")
    try:
        probe = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValueError("execution guard probe is invalid") from error
    if (
        type(probe) is not dict
        or probe.get("available") is not True
        or set(probe.get("capabilities", [])) != GUARD_CAPABILITIES
        or type(probe.get("landlock_abi")) is not int
        or probe["landlock_abi"] < 1
        or probe.get("network_namespace") is not True
    ):
        raise ValueError("execution guard capability probe failed")
    receipt = {
        "schema_version": 4,
        "trust_source": "PLAN_SOURCE_COMMIT_BOUND_COOPERATIVE_AGENT",
        "implementation_path": EXECUTION_GUARD_RELATIVE,
        "implementation_sha256": actual,
        "landlock_abi": probe["landlock_abi"],
        "network_namespace": True,
        "capabilities": sorted(GUARD_CAPABILITIES),
    }
    return prefix, receipt


def _repo_write_roots(root: Path, plan: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for relative in plan["execution_scope"]["repo_write_roots"]:
        candidate = root.joinpath(*PurePosixPath(relative).parts)
        unresolved = candidate.absolute()
        for parent in (unresolved, *unresolved.parents):
            if parent == root.parent:
                break
            if parent.exists() and parent.is_symlink():
                raise ValueError("repository write root contains a symbolic link")
        resolved = candidate.resolve(strict=False)
        if resolved != root and root not in resolved.parents:
            raise ValueError("repository write root escapes project")
        candidate.mkdir(parents=True, exist_ok=True)
        if candidate.is_symlink() or not candidate.is_dir():
            raise ValueError("repository write root must be a plain directory")
        paths.append(str(candidate.resolve()))
    return paths


def _host_write_roots(root: Path, plan: dict[str, Any]) -> list[str]:
    scopes = plan["execution_scope"]["host_write_scopes"]
    if not scopes:
        return []
    mirror = _runtime_module("large_workspace").project_shm_root(root, create=True)
    return [str(mirror)]


def _guarded_command(
    root: Path,
    instruction_id: str,
    journal: dict[str, Any],
    plan: dict[str, Any],
    command: list[str],
    label: str,
) -> list[str]:
    prefix, receipt = _execution_guard(root)
    if receipt != journal["boundary_guard"]:
        raise ValueError("host-local execution guard changed after claim")
    request_path = _journal_directory(root, instruction_id) / "GUARD-REQUEST.json"
    request = {
        "schema_version": 2,
        "instruction_id": instruction_id,
        "label": label,
        "repository_root": str(root),
        "plan_sha256": journal["plan_sha256"],
        "authority_sha256": journal["authority_sha256"],
        "placement": journal["placement_receipt"],
        "resources": plan["resources"],
        "datasets": plan["datasets"],
        "execution_scope": plan["execution_scope"],
        "resolved_repo_write_roots": _repo_write_roots(root, plan),
        "resolved_host_write_roots": _host_write_roots(root, plan),
        "required_permissions": plan["required_permissions"],
        "hard_boundaries": plan["hard_boundaries"],
        "command": command,
    }
    _atomic_json(request_path, request)
    return [*prefix, "--request", str(request_path), "--", *command]


def _adaptation_sequence(root: Path, instruction_id: str) -> int:
    parent = root / "coordination/instructions" / instruction_id / "deviations"
    if not parent.exists():
        return 0
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("invalid MASTER adaptation directory")
    sequences = [
        int(path.stem)
        for path in parent.glob("[0-9][0-9][0-9].yaml")
        if path.is_file() and not path.is_symlink() and path.stem.isdecimal()
    ]
    if sequences and sorted(sequences) != list(range(1, max(sequences) + 1)):
        raise ValueError("invalid MASTER adaptation sequence")
    return max(sequences, default=0)


def _adaptation_changed_paths(root: Path, instruction_id: str) -> list[str]:
    parent = root / "coordination/instructions" / instruction_id / "deviations"
    if not parent.exists():
        return []
    paths: list[str] = []
    for event_path in sorted(parent.glob("[0-9][0-9][0-9].yaml")):
        event = _load_yaml(event_path)
        changed = event.get("changed_paths", [])
        if (
            type(changed) is not list
            or any(type(item) is not str or not item for item in changed)
        ):
            raise ValueError("invalid MASTER engineering changed paths")
        for relative in changed:
            candidate = PurePosixPath(relative)
            if candidate.is_absolute() or ".." in candidate.parts or candidate.parts[0] == ".git":
                raise ValueError("invalid MASTER engineering changed path")
            if relative not in paths:
                paths.append(relative)
    return paths


def _runtime_blocker(
    root: Path, plan: dict[str, Any], journal: dict[str, Any]
) -> str | None:
    try:
        lock_state = _runtime_module("project_lock").load(root)["state"]
    except (OSError, UnicodeError, ValueError) as error:
        return f"project operation lock is invalid: {error}"
    if lock_state == "LOCKED":
        return PROJECT_LOCK_BLOCKER
    current_authority = _runtime_module("research_execution").load_authority(root)
    if (
        current_authority != journal["authority_snapshot"]
        or _document_sha256(current_authority) != journal["authority_sha256"]
        or plan.get("authority_snapshot") != journal["authority_snapshot"]
    ):
        return "SERVER authority snapshot changed or was revoked"
    blocker = _permissions_blocker(
        root,
        plan,
        expected_snapshots=journal["permission_snapshots"],
        online=False,
    )
    if blocker is not None:
        return blocker
    try:
        from cqc_fabric import local_execution

        current_profile = local_execution.detect_profile(
            root,
            _local_git_setting(root, "cqc.server-profile", required=False),
        )
    except (ImportError, ValueError) as error:
        return str(error)
    if journal["placement_receipt"].get("server_profile") != current_profile:
        return "local server profile no longer matches the execution receipt"
    try:
        _, guard = _execution_guard(root)
    except (OSError, ValueError) as error:
        return str(error)
    if guard != journal["boundary_guard"]:
        return "host-local execution guard changed or lost required capabilities"
    return None


def _run_reporting_process(
    root: Path,
    instruction_id: str,
    plan: dict[str, Any],
    arguments: list[str],
    *,
    timeout_seconds: float,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    """Run one publication step with heartbeat, STOP, lock and deadline control."""

    if (
        type(arguments) is not list
        or not arguments
        or any(type(value) is not str or not value for value in arguments)
        or type(timeout_seconds) not in {int, float}
        or timeout_seconds <= 0
    ):
        raise ValueError("invalid reporting subprocess request")
    environment = dict(os.environ)
    environment.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
    with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(
        mode="w+b"
    ) as stderr_file:
        process = subprocess.Popen(
            arguments,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            shell=False,
            env=environment,
            **_process_group_options(),
        )
        _update(
            root,
            instruction_id,
            command_pid=process.pid,
            heartbeat_at=_utc_now(),
        )
        started = time.monotonic()
        last_heartbeat = started
        control: _PublicationControl | None = None
        while process.poll() is None:
            now = time.monotonic()
            latest = load_journal(root, instruction_id)
            if latest["stop_requested"]:
                control = _PublicationControl(
                    "STOPPED", "USER_STOP requested during result publication"
                )
            else:
                blocker = _runtime_blocker(root, plan, latest)
                if blocker == PROJECT_LOCK_BLOCKER:
                    control = _PublicationControl("PROJECT_LOCKED", blocker)
                elif blocker is not None:
                    control = _PublicationControl("BLOCKED", blocker)
                elif _deadline_exceeded(latest):
                    control = _PublicationControl(
                        "REPAIR_REQUIRED",
                        "declared max_hours budget exhausted during result publication",
                    )
                elif now - started >= float(timeout_seconds):
                    control = _PublicationControl(
                        "REPAIR_REQUIRED",
                        f"result publication step timed out after {timeout_seconds:g} seconds",
                    )
            if control is not None:
                _terminate_process_tree(process)
                break
            if now - last_heartbeat >= 0.5:
                _update(root, instruction_id, heartbeat_at=_utc_now())
                last_heartbeat = now
            time.sleep(0.05)
        returncode = process.wait()
        _update(
            root,
            instruction_id,
            command_pid=None,
            heartbeat_at=_utc_now(),
        )
        if control is not None:
            raise control
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout_bytes = stdout_file.read()
        stderr_bytes = stderr_file.read()
    stdout: Any = stdout_bytes.decode("utf-8", errors="replace") if text else stdout_bytes
    stderr: Any = stderr_bytes.decode("utf-8", errors="replace") if text else stderr_bytes
    return subprocess.CompletedProcess(arguments, returncode, stdout=stdout, stderr=stderr)


def _reporting_git(
    root: Path,
    instruction_id: str,
    plan: dict[str, Any],
    *arguments: str,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    completed = _run_reporting_process(
        root,
        instruction_id,
        plan,
        ["git", *arguments],
        timeout_seconds=300,
        text=text,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr or completed.stdout
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise ValueError(f"Git result publication failed: {str(detail).strip()}")
    return completed


def _require_reporting_https_origin(
    root: Path, instruction_id: str, plan: dict[str, Any]
) -> str:
    url = _reporting_git(
        root, instruction_id, plan, "remote", "get-url", "--push", "origin"
    ).stdout.strip()
    if re.fullmatch(r"https://[^\s]+", url, flags=re.IGNORECASE) is None:
        raise ValueError("production origin push URL must use HTTPS")
    return url


def _deadline_exceeded(journal: dict[str, Any]) -> bool:
    value = journal.get("deadline_at")
    if type(value) is not str:
        return True
    try:
        deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) >= deadline


def _repairable_claim_preflight(reason: str) -> bool:
    lowered = reason.casefold()
    return (
        reason.startswith("claim-time control verification incomplete:")
        or reason.startswith("host-local setting is missing:")
        or reason.startswith("host-global cqc-fabric 2.1 is unavailable")
        or "no such file or directory" in lowered
        or "cannot find the file" in lowered
        or "cannot find path" in lowered
        or "execution guard digest changed" in lowered
    )


def _local_dispatch_identity(instruction_id: str, payload: bytes) -> str:
    return hashlib.sha256(
        b"LOCAL\0" + instruction_id.encode("utf-8") + b"\0" + payload
    ).hexdigest()


def _claim(
    root: Path,
    instruction_id: str,
    *,
    dispatch_token: str | None = None,
) -> dict[str, Any]:
    with _runtime_module("transactions").project_control(root):
        control_sync_blocker = None
        try:
            _runtime_module("authorization").synchronize_authority_main(root)
        except (OSError, UnicodeError, ValueError) as error:
            control_sync_blocker = (
                f"claim-time control verification incomplete: {error}"
            )
        _runtime_module("project_lock").require_operation(
            root, command="dispatch", action="pull-execute"
        )
        return _claim_locked(
            root,
            instruction_id,
            dispatch_token=dispatch_token,
            control_sync_blocker=control_sync_blocker,
        )


def _claim_locked(
    root: Path,
    instruction_id: str,
    *,
    dispatch_token: str | None = None,
    control_sync_blocker: str | None = None,
) -> dict[str, Any]:
    plan_path = _plan_path(root, instruction_id)
    plan = _runtime_module("research_execution").load_server_plan(
        root, instruction_id
    )
    payload = plan_path.read_bytes()
    if dispatch_token is None:
        dispatch_token = _local_dispatch_identity(instruction_id, payload)
    if type(dispatch_token) is not str or SHA256.fullmatch(dispatch_token) is None:
        raise ValueError("invalid local dispatch token")
    relative = plan_path.relative_to(root).as_posix()
    _apply_local_correction_receipt(root, instruction_id, plan)
    research = _runtime_module("research_execution")
    current_authority = research.load_authority(root)
    authority_blocker = (
        None
        if plan.get("authority_snapshot") == current_authority
        else "SERVER authority changed after the plan was issued"
    )
    permission_snapshots: dict[str, dict[str, Any]] = {}
    claim_verification_blocker = control_sync_blocker
    if claim_verification_blocker is None:
        try:
            _runtime_module("project_lock").claim_snapshot(root)
            permission_snapshots = _permission_snapshots(root, plan, online=True)
        except (OSError, UnicodeError, ValueError) as error:
            claim_verification_blocker = (
                f"claim-time control verification incomplete: {error}"
            )
    placement_receipt: dict[str, Any] = {}
    placement_blocker = None
    try:
        placement_receipt = _placement_preflight(
            root,
            plan,
            instruction_id,
        )
    except (OSError, ValueError) as error:
        placement_blocker = str(error)
    boundary_guard: dict[str, Any] = {}
    guard_blocker = None
    try:
        _, boundary_guard = _execution_guard(root)
    except (OSError, ValueError) as error:
        guard_blocker = str(error)
    now = datetime.now(timezone.utc)
    document = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "dispatch_token": dispatch_token,
        "plan_ref": relative,
        "plan_sha256": hashlib.sha256(payload).hexdigest(),
        "source_commit": _git(root, "rev-parse", "HEAD").stdout.strip(),
        "authority_snapshot": plan["authority_snapshot"],
        "authority_sha256": _document_sha256(plan["authority_snapshot"]),
        "permission_snapshots": permission_snapshots,
        "placement_receipt": placement_receipt,
        "boundary_guard": boundary_guard,
        "state": "CLAIMED",
        "attempt": 0,
        "adaptation_sequence": _adaptation_sequence(root, instruction_id),
        "worker_pid": None,
        "command_pid": None,
        "dataset_checkpoint_index": 0,
        "dataset_mounts": [],
        "checkpoint_index": 0,
        "acceptance_checkpoint_index": 0,
        "heartbeat_at": _utc_now(),
        "started_at": None,
        "deadline_at": (now + timedelta(hours=float(plan["resources"]["max_hours"]))).isoformat().replace("+00:00", "Z"),
        "finished_at": None,
        "exit_code": None,
        "failure_reason": None,
        "recovery_action": "start durable worker",
        "terminal_message": None,
        "result_branch": plan["result_branch"],
        "result_commit": None,
        "remote_commit": None,
        "stop_requested": False,
        "supervision_required": bool(
            plan["resources"]["gpu_count"]
            or plan["resources"]["max_hours"] > 0.5
        ),
        "supervision_status": "ACTIVE",
        "bc_review_required": False,
        "bc_review_reason": None,
        "bc_review_status": "NOT_REQUIRED",
        "bc_review_receipt": None,
        "bc_review_sha256": None,
        "bc_review_observed_state": None,
        "bc_reviewed_journal_sha256": None,
        "bc_correction_instruction_id": None,
    }
    with _runtime_module("transactions").journal(root, instruction_id):
        _exclusive_yaml(_journal_path(root, instruction_id), document)
    blocker = authority_blocker
    if blocker is not None:
        return _terminal(
            root,
            instruction_id,
            state="BLOCKED",
            reason=blocker,
            recovery_action=ABNORMAL_REVIEW_ACTION,
            exit_code=None,
        )
    preflight_blocker = (
        claim_verification_blocker or placement_blocker or guard_blocker
    )
    if preflight_blocker is not None:
        if _repairable_claim_preflight(preflight_blocker):
            return _engineering_pause(
                root,
                instruction_id,
                reason=f"repairable claim preflight: {preflight_blocker}",
                exit_code=None,
            )
        return _terminal(
            root,
            instruction_id,
            state="BLOCKED",
            reason=preflight_blocker,
            recovery_action=ABNORMAL_REVIEW_ACTION,
            exit_code=None,
        )
    return document


def _apply_local_correction_receipt(
    root: Path, instruction_id: str, plan: dict[str, Any]
) -> None:
    followup = plan["execution_followup"]
    if followup["mode"] != "CORRECT_PREVIOUS_EXECUTION":
        return
    prior_id = followup["prior_instruction_id"]
    path = _journal_path(root, prior_id)
    if not path.exists():
        return
    journal = load_journal(root, prior_id)
    if journal["bc_correction_instruction_id"] == instruction_id:
        return
    if journal["bc_review_required"] is not True or journal["bc_review_status"] != "REQUIRED":
        raise ValueError("local prior execution journal cannot accept this correction")
    payload = path.read_bytes()
    review = _runtime_module("execution_reviews").load_review(
        root,
        followup["review_receipt"],
        expected_sha256=followup["review_sha256"],
    )
    if (
        review["instruction_id"] != prior_id
        or review["verdict"] != "ISSUE_NEXT_R_CORRECTION"
        or review["observed_state"] != journal["state"]
        or review["journal_sha256"] != hashlib.sha256(payload).hexdigest()
    ):
        raise ValueError("B/C correction receipt does not match the local terminal journal")
    _update(
        root,
        prior_id,
        bc_review_required=False,
        bc_review_reason=None,
        bc_review_status="NEXT_R_CORRECTION_REQUIRED",
        bc_review_receipt=followup["review_receipt"],
        bc_review_sha256=followup["review_sha256"],
        bc_review_observed_state=review["observed_state"],
        bc_reviewed_journal_sha256=review["journal_sha256"],
        bc_correction_instruction_id=instruction_id,
    )


def _launch(root: Path, instruction_id: str) -> None:
    arguments = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(root),
        instruction_id,
    ]
    options: dict[str, Any] = {
        "cwd": root,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        options["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        )
    else:
        options["start_new_session"] = True
    _DETACHED_WORKERS.append(subprocess.Popen(arguments, **options))


def dispatch_intent(root: Path) -> dict[str, Any]:
    """Synchronize this project host and identify its one local instruction."""

    root = _exact_root(root)
    _require_server(root)
    _runtime_module("project_lock").require_operation(
        root, command="dispatch", action="pull-execute"
    )
    if _git(root, "branch", "--show-current").stdout.strip() != "main":
        raise ValueError("local dispatch intent requires branch main")
    if _git(root, "status", "--porcelain", "--untracked-files=all").stdout:
        raise ValueError("local dispatch intent requires a clean worktree")
    _require_https_origin(root)
    _git(root, "pull", "--ff-only", "origin", "main")
    candidates = _ready_candidates(root)
    if len(candidates) != 1:
        raise ValueError(
            f"local dispatch requires exactly one ready instruction; found {len(candidates)}"
        )
    plan = _runtime_module("research_execution").load_server_plan(
        root, candidates[0]
    )
    return {
        "instruction_id": candidates[0],
        "source_commit": _git(root, "rev-parse", "HEAD").stdout.strip(),
        "execution_summary": plan["execution_summary"],
    }


def claim_status(
    root: Path, instruction_id: str, dispatch_token: str
) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    if (
        type(instruction_id) is not str
        or INSTRUCTION_ID.fullmatch(instruction_id) is None
        or type(dispatch_token) is not str
        or SHA256.fullmatch(dispatch_token) is None
    ):
        raise ValueError("invalid claim-status identity")
    path = _journal_path(root, instruction_id)
    if not path.exists():
        return {"status": "UNCLAIMED", "instruction_id": instruction_id}
    journal = load_journal(root, instruction_id)
    if journal["dispatch_token"] != dispatch_token:
        return {
            "status": "TOKEN_CONFLICT",
            "instruction_id": instruction_id,
            "state": journal["state"],
        }
    return {
        "status": "CLAIMED_MATCH",
        "instruction_id": instruction_id,
        "state": journal["state"],
    }


def pull_and_execute(
    root: Path,
    *,
    launch: bool = True,
) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    _runtime_module("project_lock").require_operation(
        root, command="dispatch", action="pull-execute"
    )
    if _git(root, "branch", "--show-current").stdout.strip() != "main":
        raise ValueError("pull-execute requires branch main")
    if _git(root, "status", "--porcelain", "--untracked-files=all").stdout:
        raise ValueError("pull-execute requires a clean worktree")
    _require_https_origin(root)
    _git(root, "pull", "--ff-only", "origin", "main")
    open_issues = _runtime_module("execution_issues").pending_server_attention(root)
    if open_issues:
        return {
            "status": "ATTENTION_REQUIRED",
            "reason": "B_OR_C_REPORTED_CATASTROPHIC_SERVER_EXECUTION_ERROR",
            "issues": open_issues,
            "next_action": "ACKNOWLEDGE_AND_REPAIR_OR_REQUEST_REPLAN",
        }
    candidates = _ready_candidates(root)
    if not candidates:
        review_gates = _review_gate_candidates(root)
        if review_gates:
            journal = review_gates[0]
            return {
                "status": (
                    "BC_REVIEW_REQUIRED"
                    if journal["bc_review_required"]
                    else journal["bc_review_status"]
                ),
                "instruction_id": journal["instruction_id"],
                "failure_reason": journal["failure_reason"],
                "user_notification_required": (
                    journal["bc_review_status"] == "CATASTROPHIC_REPORT_REQUIRED"
                ),
                "next_action": (
                    "B_OR_C_RECORDS_REVIEW_BEFORE_ANY_SERVER_RECOVERY"
                    if journal["bc_review_required"]
                    else "WAIT_FOR_B_OR_C_TO_ISSUE_THE_NEXT_R_CORRECTION"
                ),
            }
        recoverable = _master_recovery_candidates(root)
        if recoverable:
            journal = recoverable[0]
            return {
                "status": "AUTONOMOUS_MASTER_RECOVERY_REQUIRED",
                "instruction_id": journal["instruction_id"],
                "failure_reason": journal["failure_reason"],
                "recovery_action": journal["recovery_action"],
                "user_notification_required": False,
                "next_action": (
                    "SERVER_INSPECTS_EXISTING_FILES_ENVIRONMENTS_DATA_AND_LOGS_THEN_"
                    "RESUMES_THE_NONTERMINAL_INSTRUCTION_FROM_ITS_LAST_CHECKPOINT"
                ),
                "forbidden_response": "DO_NOT_ASK_BC_OR_USER_ABOUT_REPAIRABLE_ENGINEERING_DETAILS",
            }
        raise ValueError("zero ready r-prefixed instructions and no recoverable execution")
    if len(candidates) != 1:
        raise ValueError(
            f"multiple ready r-prefixed instructions ({len(candidates)}); cannot select a unique execution"
        )
    instruction_id = candidates[0]
    journal = _claim(root, instruction_id)
    if launch and journal["state"] == "CLAIMED":
        _launch(root, instruction_id)
        # The detached worker may already have advanced the state.
        journal = load_journal(root, instruction_id)
    return journal


def _plan_for_journal(root: Path, journal: dict[str, Any]) -> dict[str, Any]:
    path = root.joinpath(*PurePosixPath(journal["plan_ref"]).parts)
    if (
        path.is_symlink()
        or not path.is_file()
        or hashlib.sha256(path.read_bytes()).hexdigest() != journal["plan_sha256"]
    ):
        raise ValueError("claimed SERVER plan changed")
    if _git(
        root,
        "merge-base",
        "--is-ancestor",
        journal["source_commit"],
        "HEAD",
        check=False,
    ).returncode != 0:
        raise ValueError("execution checkout no longer contains the claimed source commit")
    plan = _runtime_module("research_execution").load_server_plan(
        root, journal["instruction_id"]
    )
    if _git(
        root,
        "merge-base",
        "--is-ancestor",
        plan["source_commit"],
        journal["source_commit"],
        check=False,
    ).returncode != 0:
        raise ValueError("claimed execution commit does not contain the planned source commit")
    return plan


def _result_files(root: Path, plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    files = []
    missing = []
    for relative in plan["expected_results"]:
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.exists():
            missing.append(relative)
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"result is not a plain file: {relative}")
        payload = path.read_bytes()
        if not payload:
            raise ValueError(f"result is empty and cannot satisfy acceptance: {relative}")
        files.append(
            {
                "path": relative,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return files, missing


def completion_receipt(root: Path, instruction_id: str) -> dict[str, Any]:
    """Return machine evidence for completion; a journal message alone is insufficient."""

    root = _exact_root(root)
    _require_server(root)
    journal = load_journal(root, instruction_id)
    if journal["state"] != "COMPLETE":
        return {
            "state": journal["state"],
            "instruction_id": instruction_id,
            "failure_reason": journal["failure_reason"],
            "terminal_message": journal["terminal_message"],
        }
    plan = _plan_for_journal(root, journal)
    if (
        journal["dataset_checkpoint_index"]
        != len(journal["placement_receipt"].get("dataset_routes", []))
        or journal["acceptance_checkpoint_index"] != len(plan["acceptance_argv"])
        or not plan["acceptance_argv"]
        or journal["result_commit"] != journal["remote_commit"]
        or GIT_OID.fullmatch(str(journal["result_commit"])) is None
    ):
        raise ValueError("COMPLETE journal lacks machine acceptance or remote verification")
    report_relative = f"coordination/executions/{instruction_id}/RESULT.yaml"
    completed = _git(
        root,
        "show",
        f'{journal["result_commit"]}:{report_relative}',
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("completed result report is absent from the verified result commit")
    try:
        report = yaml.safe_load(completed.stdout)
    except yaml.YAMLError as error:
        raise ValueError("completed result report is invalid") from error
    files = report.get("result_files") if type(report) is dict else None
    if (
        type(report) is not dict
        or report.get("instruction_id") != instruction_id
        or report.get("status") != "SUCCEEDED"
        or report.get("bc_scientific_assessment_required") is not True
        or report.get("acceptance_checkpoint_index") != len(plan["acceptance_argv"])
        or type(files) is not list
        or not files
        or any(
            type(item) is not dict
            or type(item.get("path")) is not str
            or not item["path"]
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] <= 0
            or type(item.get("sha256")) is not str
            or SHA256.fullmatch(item["sha256"]) is None
            for item in files
        )
    ):
        raise ValueError("completed result report lacks nonempty digest-bound results")
    if [item["path"] for item in files] != plan["expected_results"]:
        raise ValueError("completed result report does not cover the planned result set")
    for item in files:
        blob = subprocess.run(
            ["git", "show", f'{journal["result_commit"]}:{item["path"]}'],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
        )
        if (
            blob.returncode != 0
            or len(blob.stdout) != item["size_bytes"]
            or hashlib.sha256(blob.stdout).hexdigest() != item["sha256"]
        ):
            raise ValueError("completed result blob does not match its frozen digest")
    return {
        "state": "COMPLETE",
        "instruction_id": instruction_id,
        "terminal_message": "执行完毕：机器验收、非空结果和远端提交均已核验",
        "scientific_assessment_status": "B_C_OR_EXPLICIT_DOCTORAL_REQUIRED",
        "next_action": (
            "B_C_OR_EXPLICIT_DOCTORAL_ASSESSES_VENUE_LEVEL_AND_TGRS_GAP"
        ),
        "result_commit": journal["result_commit"],
        "remote_commit": journal["remote_commit"],
        "acceptance_checkpoint_index": journal["acceptance_checkpoint_index"],
        "acceptance_command_count": len(plan["acceptance_argv"]),
        "result_files": files,
    }


def _write_success_report(
    root: Path,
    instruction_id: str,
    journal: dict[str, Any],
    files: list[dict[str, Any]],
) -> Path:
    path = root / "coordination/executions" / instruction_id / "RESULT.yaml"
    stable = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "status": "SUCCEEDED",
        "plan_ref": journal["plan_ref"],
        "plan_sha256": journal["plan_sha256"],
        "source_commit": journal["source_commit"],
        "dataset_checkpoint_index": journal["dataset_checkpoint_index"],
        "checkpoint_index": journal["checkpoint_index"],
        "acceptance_checkpoint_index": journal["acceptance_checkpoint_index"],
        "result_files": files,
        "bc_verification_required": (
            _plan_for_journal(root, journal)["execution_followup"]["mode"]
            == "CORRECT_PREVIOUS_EXECUTION"
        ),
        "bc_scientific_assessment_required": True,
        "message": "实验进程已完成，结果提交等待或已经过远端验证",
    }
    if path.exists():
        existing = _load_yaml(path)
        if (
            type(existing.get("completed_at")) is not str
            or not existing["completed_at"]
            or {key: value for key, value in existing.items() if key != "completed_at"}
            != stable
        ):
            raise ValueError("execution result report already exists with different content")
    else:
        document = {**stable, "completed_at": _utc_now()}
        _exclusive_yaml(path, document)
    return path


def _publish(
    root: Path,
    instruction_id: str,
    plan: dict[str, Any],
    journal: dict[str, Any],
) -> tuple[str, str]:
    _require_reporting_https_origin(root, instruction_id, plan)
    branch = plan["result_branch"]
    current = _reporting_git(
        root, instruction_id, plan, "branch", "--show-current"
    ).stdout.strip()
    exists = (
        _reporting_git(
            root,
            instruction_id,
            plan,
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
            check=False,
        ).returncode
        == 0
    )
    if current != branch:
        if exists:
            _reporting_git(root, instruction_id, plan, "switch", branch)
        else:
            _reporting_git(root, instruction_id, plan, "switch", "-c", branch)
    deviation_root = root / "coordination/instructions" / instruction_id / "deviations"
    deviation_paths = (
        [path.relative_to(root).as_posix() for path in sorted(deviation_root.glob("*.yaml"))]
        if deviation_root.is_dir() and not deviation_root.is_symlink()
        else []
    )
    result_and_adaptation_paths = [
        *plan["expected_results"],
        *_adaptation_changed_paths(root, instruction_id),
        *deviation_paths,
    ]
    _reporting_git(
        root, instruction_id, plan, "add", "--", *result_and_adaptation_paths
    )
    staged_files = []
    for relative in plan["expected_results"]:
        completed = _reporting_git(
            root,
            instruction_id,
            plan,
            "show",
            f":{relative}",
            check=False,
            text=False,
        )
        if completed.returncode != 0:
            raise ValueError(f"cannot read staged result blob: {relative}")
        staged_files.append(
            {
                "path": relative,
                "size_bytes": len(completed.stdout),
                "sha256": hashlib.sha256(completed.stdout).hexdigest(),
            }
        )
    report = _write_success_report(root, instruction_id, journal, staged_files)
    _reporting_git(
        root,
        instruction_id,
        plan,
        "add",
        "--",
        report.relative_to(root).as_posix(),
    )
    staged = _reporting_git(
        root, instruction_id, plan, "diff", "--cached", "--quiet", check=False
    ).returncode
    if staged == 1:
        _reporting_git(
            root, instruction_id, plan, "commit", "-m", f"exec: complete {instruction_id}"
        )
    elif staged != 0:
        raise ValueError("cannot inspect staged execution results")
    commit = _reporting_git(
        root, instruction_id, plan, "rev-parse", "HEAD"
    ).stdout.strip()
    if journal.get("result_commit") not in {None, commit}:
        raise ValueError("publication checkpoint commit changed")
    journal = _update(
        root,
        instruction_id,
        result_commit=commit,
        heartbeat_at=_utc_now(),
    )
    if journal.get("remote_commit") is None:
        _reporting_git(root, instruction_id, plan, "push", "-u", "origin", branch)
        journal = _update(
            root,
            instruction_id,
            state="PUSHED",
            heartbeat_at=_utc_now(),
        )
    remote_line = _reporting_git(
        root,
        instruction_id,
        plan,
        "ls-remote",
        "--heads",
        "origin",
        f"refs/heads/{branch}",
    ).stdout.strip()
    parts = remote_line.split()
    if len(parts) != 2 or parts[1] != f"refs/heads/{branch}":
        raise ValueError("result branch remote ref is missing")
    remote = parts[0]
    if remote != commit:
        raise ValueError("result branch remote commit verification failed")
    _update(
        root,
        instruction_id,
        state="PUSHED",
        result_commit=commit,
        remote_commit=remote,
        heartbeat_at=_utc_now(),
    )
    if branch != "main":
        _reporting_git(root, instruction_id, plan, "switch", "main")
    return commit, remote


def _prepare_datasets(
    root: Path,
    instruction_id: str,
    plan: dict[str, Any],
    journal: dict[str, Any],
    log_root: Path,
) -> tuple[dict[str, Any], bool]:
    """Recheck local official data availability without identity or digest validation."""

    routes = journal["placement_receipt"].get("dataset_routes", [])
    if not routes:
        return journal, True
    for route in routes:
        if (
            type(route) is not dict
            or route.get("status") not in {
                "OFFICIAL_LOCAL_AVAILABLE", "COPIED", "CACHE_HIT"
            }
            or type(route.get("local_path")) is not str
        ):
            raise ValueError("invalid local dataset availability receipt")
        path = Path(route["local_path"])
        try:
            available = path.is_dir() and next(path.iterdir(), None) is not None
        except OSError:
            available = False
        if not available:
            return (
                _terminal(
                    root,
                    instruction_id,
                    state="BLOCKED",
                    reason=f"local official dataset became unavailable: {route.get('dataset_id')}",
                    recovery_action=ABNORMAL_REVIEW_ACTION,
                    exit_code=None,
                ),
                False,
            )
    journal = _update(
        root,
        instruction_id,
        dataset_checkpoint_index=len(routes),
        heartbeat_at=_utc_now(),
        recovery_action="resume from the last local command checkpoint",
    )
    return journal, True

def _local_command_environment(journal: dict[str, Any]) -> dict[str, str]:
    try:
        from cqc_fabric import local_execution
    except ImportError as error:
        raise ValueError("host-global cqc-fabric 2.1 is unavailable") from error
    return local_execution.execution_environment(journal["placement_receipt"])


def run_claimed(root: Path, instruction_id: str) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    journal = load_journal(root, instruction_id)
    if journal["state"] in TERMINAL:
        return journal
    if journal["state"] == "PROJECT_LOCKED":
        return journal
    if journal["state"] not in {"CLAIMED", "RUNNING", "REPORTING", "PUSHED"}:
        raise ValueError("instruction is not recoverable")
    if any(item["status"] == "ACTIVE" for item in journal["dataset_mounts"]):
        cleanup_error = _release_dataset_mounts(root, instruction_id)
        if cleanup_error is not None:
            return _engineering_pause(
                root,
                instruction_id,
                reason=(
                    "repairable stale readonly dataset mount cleanup failed: "
                    f"{cleanup_error}"
                ),
                exit_code=None,
                cleanup_mounts=False,
            )
        journal = load_journal(root, instruction_id)
    plan = _plan_for_journal(root, journal)
    blocker = _runtime_blocker(root, plan, journal)
    if blocker is not None:
        if blocker == PROJECT_LOCK_BLOCKER:
            return _project_lock_pause(root, instruction_id)
        return _terminal(
            root,
            instruction_id,
            state="BLOCKED",
            reason=blocker,
            recovery_action=ABNORMAL_REVIEW_ACTION,
            exit_code=None,
        )
    journal = _update(
        root,
        instruction_id,
        state="RUNNING",
        attempt=journal["attempt"] + 1,
        worker_pid=os.getpid(),
        heartbeat_at=_utc_now(),
        started_at=journal["started_at"] or _utc_now(),
        adaptation_sequence=_adaptation_sequence(root, instruction_id),
        failure_reason=None,
        recovery_action="resume from the last dataset or command checkpoint",
        supervision_status="ACTIVE",
    )
    log_root = _journal_directory(root, instruction_id) / "logs"
    log_root.mkdir(exist_ok=True)
    journal, prepared = _prepare_datasets(
        root, instruction_id, plan, journal, log_root
    )
    if not prepared:
        return journal
    for index, command in enumerate(plan["argv"]):
        if index < journal["checkpoint_index"]:
            continue
        stdout_path = log_root / f"{index + 1:03d}.stdout.log"
        stderr_path = log_root / f"{index + 1:03d}.stderr.log"
        with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
            process = subprocess.Popen(
                _guarded_command(
                    root, instruction_id, journal, plan, command, f"command-{index + 1}"
                ),
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                env=_local_command_environment(journal),
                shell=False,
                **_process_group_options(),
            )
            journal = _update(
                root,
                instruction_id,
                command_pid=process.pid,
                heartbeat_at=_utc_now(),
            )
            while process.poll() is None:
                latest = load_journal(root, instruction_id)
                if latest["stop_requested"]:
                    _terminate_process_tree(process)
                    return _terminal(
                        root,
                        instruction_id,
                        state="STOPPED",
                        reason="USER_STOP requested during command execution",
                        recovery_action=ABNORMAL_REVIEW_ACTION,
                        exit_code=process.returncode,
                    )
                blocker = _runtime_blocker(root, plan, latest)
                if blocker is not None or _deadline_exceeded(latest):
                    _terminate_process_tree(process)
                    if blocker == PROJECT_LOCK_BLOCKER:
                        return _project_lock_pause(root, instruction_id)
                    reason = blocker or "declared max_hours execution budget exhausted"
                    return _terminal(
                        root,
                        instruction_id,
                        state="BLOCKED",
                        reason=reason,
                        recovery_action=ABNORMAL_REVIEW_ACTION,
                        exit_code=process.returncode,
                    )
                _update(root, instruction_id, heartbeat_at=_utc_now())
                time.sleep(0.1)
        code = process.returncode
        if code != 0:
            tail = stderr_path.read_bytes()[-65536:].decode("utf-8", errors="replace")
            reason = (
                f"actual OOM at command {index + 1} with exit code {code}"
                if "out of memory" in tail.casefold()
                else f"command {index + 1} exited with exit code {code}"
            )
            return _engineering_pause(
                root,
                instruction_id,
                reason=f"repairable engineering failure: {reason}",
                exit_code=code,
            )
        journal = _update(
            root,
            instruction_id,
            command_pid=None,
            checkpoint_index=index + 1,
            heartbeat_at=_utc_now(),
        )
    try:
        files, missing = _result_files(root, plan)
    except ValueError as error:
        return _engineering_pause(
            root, instruction_id, reason=f"repairable result validation: {error}", exit_code=0
        )
    if missing:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"repairable missing declared results: {','.join(missing)}",
            exit_code=0,
        )
    for index, command in enumerate(plan["acceptance_argv"]):
        if index < journal["acceptance_checkpoint_index"]:
            continue
        latest = load_journal(root, instruction_id)
        blocker = _runtime_blocker(root, plan, latest)
        if blocker is not None or _deadline_exceeded(latest):
            if blocker == PROJECT_LOCK_BLOCKER:
                return _project_lock_pause(root, instruction_id)
            return _terminal(
                root,
                instruction_id,
                state="BLOCKED",
                reason=blocker or "declared max_hours execution budget exhausted",
                recovery_action=ABNORMAL_REVIEW_ACTION,
                exit_code=None,
            )
        stdout_path = log_root / f"acceptance-{index + 1:03d}.stdout.log"
        stderr_path = log_root / f"acceptance-{index + 1:03d}.stderr.log"
        with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
            process = subprocess.Popen(
                _guarded_command(
                    root,
                    instruction_id,
                    latest,
                    plan,
                    command,
                    f"acceptance-{index + 1}",
                ),
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                env=_local_command_environment(journal),
                shell=False,
                **_process_group_options(),
            )
            _update(
                root,
                instruction_id,
                command_pid=process.pid,
                heartbeat_at=_utc_now(),
            )
            while process.poll() is None:
                latest = load_journal(root, instruction_id)
                if latest["stop_requested"]:
                    _terminate_process_tree(process)
                    return _terminal(
                        root,
                        instruction_id,
                        state="STOPPED",
                        reason="USER_STOP requested during acceptance verification",
                        recovery_action=ABNORMAL_REVIEW_ACTION,
                        exit_code=process.returncode,
                    )
                blocker = _runtime_blocker(root, plan, latest)
                if blocker is not None or _deadline_exceeded(latest):
                    _terminate_process_tree(process)
                    if blocker == PROJECT_LOCK_BLOCKER:
                        return _project_lock_pause(root, instruction_id)
                    return _terminal(
                        root,
                        instruction_id,
                        state="BLOCKED",
                        reason=blocker or "declared max_hours execution budget exhausted",
                        recovery_action=ABNORMAL_REVIEW_ACTION,
                        exit_code=process.returncode,
                    )
                _update(root, instruction_id, heartbeat_at=_utc_now())
                time.sleep(0.1)
        if process.returncode != 0:
            tail = stderr_path.read_bytes()[-65536:].decode("utf-8", errors="replace")
            detail = tail.strip() or f"exit code {process.returncode}"
            return _engineering_pause(
                root,
                instruction_id,
                reason=f"repairable acceptance command {index + 1} failed: {detail}",
                exit_code=process.returncode,
            )
        journal = _update(
            root,
            instruction_id,
            command_pid=None,
            acceptance_checkpoint_index=index + 1,
            heartbeat_at=_utc_now(),
        )
    try:
        files, missing = _result_files(root, plan)
    except ValueError as error:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"repairable post-acceptance result validation failed: {error}",
            exit_code=0,
        )
    if missing:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"repairable post-acceptance results are missing: {','.join(missing)}",
            exit_code=0,
        )
    latest = load_journal(root, instruction_id)
    blocker = _runtime_blocker(root, plan, latest)
    if blocker is not None:
        if blocker == PROJECT_LOCK_BLOCKER:
            return _project_lock_pause(root, instruction_id)
        return _terminal(
            root,
            instruction_id,
            state="BLOCKED",
            reason=blocker,
            recovery_action=ABNORMAL_REVIEW_ACTION,
            exit_code=0,
        )
    cleanup_error = _release_dataset_mounts(
        root, instruction_id, reset_checkpoint=False
    )
    if cleanup_error is not None:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"repairable pre-publication dataset cleanup failed: {cleanup_error}",
            exit_code=0,
            cleanup_mounts=False,
        )
    journal = _update(
        root,
        instruction_id,
        state="REPORTING",
        command_pid=None,
        worker_pid=os.getpid(),
        heartbeat_at=_utc_now(),
        exit_code=0,
        recovery_action="publish and verify the r-prefixed result branch",
    )
    try:
        commit, remote = _publish(root, instruction_id, plan, journal)
        _update(
            root,
            instruction_id,
            state="PUSHED",
            result_commit=commit,
            remote_commit=remote,
            heartbeat_at=_utc_now(),
        )
    except _PublicationControl as control:
        if control.state == "PROJECT_LOCKED":
            return _project_lock_pause(root, instruction_id, reason=control.reason)
        if control.state == "REPAIR_REQUIRED":
            return _engineering_pause(
                root,
                instruction_id,
                reason=control.reason,
                exit_code=0,
            )
        return _terminal(
            root,
            instruction_id,
            state=control.state,
            reason=control.reason,
            recovery_action=(
                "none" if control.state == "STOPPED" else ABNORMAL_REVIEW_ACTION
            ),
            exit_code=None,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return _engineering_pause(
            root,
            instruction_id,
            reason=f"repairable result publication or remote verification failed: {error}",
            exit_code=0,
        )
    # COMPLETE and request_stop share this exact journal lock as their
    # linearization boundary. If STOP committed first, publication may already
    # have produced a remote result, but SERVER must not report execution
    # completion. If COMPLETE committed first, request_stop only reads and
    # returns the immutable terminal journal.
    with _runtime_module("transactions").journal(root, instruction_id):
        latest = load_journal(root, instruction_id)
        if latest["stop_requested"]:
            return _terminal_locked(
                root,
                instruction_id,
                state="STOPPED",
                reason=(
                    "USER_STOP acknowledged before final completion; "
                    "the result branch may already have been published"
                ),
                recovery_action="none",
                exit_code=0,
            )
        return _update(
            root,
            instruction_id,
            state="COMPLETE",
            worker_pid=None,
            command_pid=None,
            heartbeat_at=_utc_now(),
            finished_at=_utc_now(),
            failure_reason=None,
            recovery_action="none",
            terminal_message="执行完毕：机器验收、非空结果和远端提交均已核验",
            supervision_status="TERMINAL",
            bc_review_required=(
                plan["execution_followup"]["mode"] == "CORRECT_PREVIOUS_EXECUTION"
            ),
            bc_review_reason=(
                "B_OR_C_MUST_VERIFY_CORRECTED_EXECUTION"
                if plan["execution_followup"]["mode"] == "CORRECT_PREVIOUS_EXECUTION"
                else None
            ),
            bc_review_status=(
                "REQUIRED"
                if plan["execution_followup"]["mode"] == "CORRECT_PREVIOUS_EXECUTION"
                else "NOT_REQUIRED"
            ),
            bc_review_receipt=None,
            bc_review_sha256=None,
            bc_review_observed_state=None,
            bc_reviewed_journal_sha256=None,
            bc_correction_instruction_id=None,
        )


def _pid_alive(pid: int | None) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def recover(root: Path, instruction_id: str, *, launch: bool = True) -> dict[str, Any]:
    root = _exact_root(root)
    with _runtime_module("transactions").project_control(root):
        return _recover_locked(root, instruction_id, launch=launch)


def _recover_locked(
    root: Path, instruction_id: str, *, launch: bool = True
) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    journal = load_journal(root, instruction_id)
    if journal["state"] in {"COMPLETE", "STOPPED"}:
        return journal
    if (
        journal["state"] == "PROJECT_LOCKED"
        and _runtime_module("project_lock").load(root)["state"] == "LOCKED"
    ):
        return journal
    if _pid_alive(journal["worker_pid"]):
        return journal
    # A claim-time guard-resolution error is an ordinary local framework
    # adaptation, even if an older runtime persisted it as BLOCKED.  Restore
    # the same instruction to the documented nonterminal repair path before
    # imposing the B/C abnormal-terminal review requirement.
    if (
        journal["state"] == "BLOCKED"
        and _repairable_claim_preflight(str(journal.get("failure_reason", "")))
    ):
        journal = _engineering_pause(
            root,
            instruction_id,
            reason=(
                "repairable legacy claim preflight: "
                f"{journal.get('failure_reason')}"
            ),
            exit_code=None,
        )
    if journal["bc_review_required"]:
        raise ValueError("B or C must record an execution review before SERVER recovery")
    if journal["state"] in {"FAILED", "INCOMPLETE", "BLOCKED"}:
        raise ValueError(
            "abnormal terminal execution requires B/C review and a direct next-r correction"
        )
    plan = _plan_for_journal(root, journal)
    try:
        _runtime_module("project_lock").claim_snapshot(root)
        refreshed_permissions = _permission_snapshots(root, plan, online=True)
    except (OSError, UnicodeError, ValueError) as error:
        return _update(
            root,
            instruction_id,
            heartbeat_at=_utc_now(),
            failure_reason=f"claim-time control verification incomplete: {error}",
            recovery_action="retry this same instruction when control verification is available",
        )
    if refreshed_permissions != journal.get("permission_snapshots", {}):
        journal = _update(
            root,
            instruction_id,
            permission_snapshots=refreshed_permissions,
            heartbeat_at=_utc_now(),
        )
    if journal["state"] == "BLOCKED":
        if not journal["placement_receipt"]:
            try:
                receipt = _placement_preflight(root, plan, instruction_id)
            except (OSError, ValueError):
                return journal
            journal = _update(root, instruction_id, placement_receipt=receipt)
        if not journal["boundary_guard"]:
            try:
                _, guard = _execution_guard(root)
            except (OSError, ValueError):
                return journal
            journal = _update(root, instruction_id, boundary_guard=guard)
        if _runtime_blocker(root, plan, journal) is not None:
            return journal
    current_adaptation = _adaptation_sequence(root, instruction_id)
    claim_verification_wait = (
        journal["state"] == "REPAIR_REQUIRED"
        and "claim-time control verification incomplete:"
        in str(journal.get("failure_reason"))
    )
    if (
        journal["state"] == "REPAIR_REQUIRED"
        and not claim_verification_wait
        and current_adaptation <= journal["adaptation_sequence"]
    ):
        raise ValueError(
            "SERVER must inspect and record a CONTINUE_AND_LOG engineering adaptation "
            "before recovering this same r-prefixed instruction"
        )
    if journal["state"] == "REPAIR_REQUIRED" and journal.get("placement_receipt") == {}:
        try:
            receipt = _placement_preflight(root, plan, instruction_id)
        except (OSError, ValueError) as error:
            return _update(
                root,
                instruction_id,
                heartbeat_at=_utc_now(),
                failure_reason=f"repairable claim preflight remains incomplete: {error}",
            )
        journal = _update(root, instruction_id, placement_receipt=receipt)
    if journal["state"] == "REPAIR_REQUIRED" and journal.get("boundary_guard") == {}:
        try:
            _, guard = _execution_guard(root)
        except (OSError, ValueError) as error:
            return _update(
                root,
                instruction_id,
                heartbeat_at=_utc_now(),
                failure_reason=f"repairable claim guard remains incomplete: {error}",
            )
        journal = _update(root, instruction_id, boundary_guard=guard)
    checkpoint_index = journal["checkpoint_index"]
    acceptance_checkpoint_index = journal["acceptance_checkpoint_index"]
    if journal["state"] == "REPAIR_REQUIRED" and not claim_verification_wait:
        if checkpoint_index >= len(plan["argv"]):
            checkpoint_index = max(0, checkpoint_index - 1)
        acceptance_checkpoint_index = 0
    deadline_at = journal.get("deadline_at")
    if journal["state"] == "PROJECT_LOCKED":
        try:
            paused_at = datetime.fromisoformat(
                journal["heartbeat_at"].replace("Z", "+00:00")
            )
            previous_deadline = datetime.fromisoformat(
                str(deadline_at).replace("Z", "+00:00")
            )
        except (AttributeError, ValueError) as error:
            raise ValueError("project-lock pause timestamps are invalid") from error
        deadline_at = (
            previous_deadline + (datetime.now(timezone.utc) - paused_at)
        ).isoformat().replace("+00:00", "Z")
    journal = _update(
        root,
        instruction_id,
        state="CLAIMED",
        worker_pid=None,
        command_pid=None,
        heartbeat_at=_utc_now(),
        failure_reason=(
            "claim-time controls verified; resuming the same instruction"
            if claim_verification_wait
            else "repair adaptation recorded; resuming the same instruction"
            if journal["state"] == "REPAIR_REQUIRED"
            else "project unlocked; resuming the same instruction"
            if journal["state"] == "PROJECT_LOCKED"
            else "previous durable worker is no longer alive"
        ),
        recovery_action="resume this same r-prefixed instruction from its safe checkpoint",
        finished_at=None,
        exit_code=None,
        terminal_message=None,
        adaptation_sequence=current_adaptation,
        checkpoint_index=checkpoint_index,
        acceptance_checkpoint_index=acceptance_checkpoint_index,
        **({"deadline_at": deadline_at} if deadline_at is not None else {}),
        supervision_status="ACTIVE",
    )
    if launch:
        _launch(root, instruction_id)
        journal = load_journal(root, instruction_id)
    return journal


def request_stop(root: Path, instruction_id: str) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    with _runtime_module("transactions").journal(root, instruction_id):
        journal = load_journal(root, instruction_id)
        if journal["state"] in TERMINAL:
            return journal
        return _update(
            root,
            instruction_id,
            stop_requested=True,
            heartbeat_at=_utc_now(),
            recovery_action="durable worker will stop at the next heartbeat",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=2, metavar=("ROOT", "INSTRUCTION"))
    arguments = parser.parse_args(argv)
    if arguments.worker is None:
        parser.error("--worker is required")
    root, instruction_id = arguments.worker
    try:
        result = run_claimed(Path(root), instruction_id)
    except BaseException as error:
        try:
            _engineering_pause(
                Path(root),
                instruction_id,
                reason=f"repairable durable worker crash: {type(error).__name__}: {error}",
                exit_code=None,
            )
        except BaseException:
            pass
        return 2
    return 0 if result["state"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
