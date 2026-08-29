from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Iterator

import yaml

from . import authorization, transactions


STATES = {"LOCKED", "UNLOCKED"}
EVENT = re.compile(r"L([0-9]{6})[.]yaml")
SHA256 = re.compile(r"[0-9a-f]{64}")
STATE_KEYS = {
    "schema_version", "state", "sequence", "last_event", "last_event_sha256",
}
EVENT_KEYS = {
    "schema_version", "event_id", "sequence", "from_state", "to_state",
    "reason", "actor_source", "actor_role", "changed_at", "previous_event_sha256",
    "control_ref", "control_sha256",
}


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True,
        text=True, encoding="utf-8", check=False, shell=False,
    )
    if completed.returncode == 0:
        if Path(completed.stdout.strip()).resolve() == root:
            return root
        raise ValueError("project lock requires the exact Git repository root")
    required = (
        root / "project.yaml",
        root / ".research_core/contract.yaml",
        root / ".research_core/PROJECT_LOCK.yaml",
    )
    event_directory = root / "coordination/project-lock/events"
    if (
        any(path.is_symlink() or not path.is_file() for path in required)
        or event_directory.is_symlink()
        or not event_directory.is_dir()
    ):
        raise ValueError("project lock requires the exact project staging root")
    return root


def _load_yaml(path: Path, label: str, *, max_bytes: int = 64 * 1024) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"plain YAML file required: {label}")
    payload = path.read_bytes()
    if not payload or len(payload) > max_bytes:
        raise ValueError(f"invalid YAML size: {label}")
    try:
        value = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError(f"invalid YAML: {label}") from error
    if type(value) is not dict:
        raise ValueError(f"YAML mapping required: {label}")
    return value


def _atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError("project lock parent must not be a symlink")
    payload = yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _exclusive_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError("project lock event parent must not be a symlink")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(document, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


@contextmanager
def _operation_lock(root: Path) -> Iterator[None]:
    with transactions.project_control(root):
        yield


def _validate_state(value: dict[str, Any]) -> dict[str, Any]:
    if (
        set(value) != STATE_KEYS
        or value.get("schema_version") != 1
        or value.get("state") not in STATES
        or type(value.get("sequence")) is not int
        or value["sequence"] < 0
    ):
        raise ValueError("invalid project lock state")
    if value["sequence"] == 0:
        if value["last_event"] is not None or value["last_event_sha256"] is not None:
            raise ValueError("initial project lock state must not bind an event")
    elif (
        value["last_event"] != f"coordination/project-lock/events/L{value['sequence']:06d}.yaml"
        or type(value["last_event_sha256"]) is not str
        or SHA256.fullmatch(value["last_event_sha256"]) is None
    ):
        raise ValueError("project lock state event binding is invalid")
    return value


def _events(root: Path) -> list[tuple[Path, dict[str, Any], str]]:
    directory = root / "coordination/project-lock/events"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("project lock event directory is invalid")
    result: list[tuple[Path, dict[str, Any], str]] = []
    previous_digest: str | None = None
    previous_state = "UNLOCKED"
    paths = sorted(path for path in directory.iterdir() if EVENT.fullmatch(path.name))
    for sequence, path in enumerate(paths, start=1):
        match = EVENT.fullmatch(path.name)
        assert match is not None
        value = _load_yaml(path, path.relative_to(root).as_posix())
        if (
            int(match.group(1)) != sequence
            or set(value) != EVENT_KEYS
            or value.get("schema_version") != 1
            or value.get("event_id") != f"L{sequence:06d}"
            or value.get("sequence") != sequence
            or value.get("from_state") != previous_state
            or value.get("to_state") not in STATES
            or value["to_state"] == previous_state
            or type(value.get("reason")) is not str
            or len(value["reason"].strip()) < 12
            or value.get("actor_source") not in {"FACTORY", "PROJECT"}
            or value.get("actor_role") not in {"FACTORY", "B", "C", "SERVER", "UNBOUND"}
            or type(value.get("changed_at")) is not str
            or not value["changed_at"].endswith("Z")
            or value.get("previous_event_sha256") != previous_digest
            or (
                value["to_state"] == "UNLOCKED"
                and (
                    type(value.get("control_ref")) is not str
                    or type(value.get("control_sha256")) is not str
                    or SHA256.fullmatch(value["control_sha256"]) is None
                )
            )
            or (
                value["to_state"] == "LOCKED"
                and (
                    value.get("control_ref") is not None
                    or value.get("control_sha256") is not None
                )
            )
        ):
            raise ValueError(f"invalid project lock event: {path.name}")
        if value["to_state"] == "UNLOCKED":
            authorization.unlock_snapshot(
                root,
                authorization_ref=value["control_ref"],
                authorization_sha256=value["control_sha256"],
                lock_sequence=sequence,
                online=False,
            )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result.append((path, value, digest))
        previous_digest = digest
        previous_state = value["to_state"]
    return result


def _state_from_event(path: Path, event: dict[str, Any], digest: str, root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "state": event["to_state"],
        "sequence": event["sequence"],
        "last_event": path.relative_to(root).as_posix(),
        "last_event_sha256": digest,
    }


def _load_unlocked(root: Path, *, recover: bool) -> dict[str, Any]:
    path = root / ".research_core/PROJECT_LOCK.yaml"
    current = _validate_state(_load_yaml(path, ".research_core/PROJECT_LOCK.yaml"))
    events = _events(root)
    if len(events) == current["sequence"]:
        if events:
            expected = _state_from_event(*events[-1], root)
            if current != expected:
                raise ValueError("project lock state does not match its event chain")
        elif current != {
            "schema_version": 1, "state": "UNLOCKED", "sequence": 0,
            "last_event": None, "last_event_sha256": None,
        }:
            raise ValueError("initial project lock state is not canonical")
        return current
    if recover and len(events) == current["sequence"] + 1:
        event_path, event, digest = events[-1]
        if event["from_state"] != current["state"]:
            raise ValueError("pending project lock event does not extend current state")
        recovered = _state_from_event(event_path, event, digest, root)
        _atomic_yaml(path, recovered)
        return recovered
    raise ValueError("project lock state and event chain diverged")


def load(root: Path) -> dict[str, Any]:
    root = _root(root)
    with _operation_lock(root):
        return _load_unlocked(root, recover=True)


def claim_snapshot(root: Path) -> dict[str, Any]:
    """Online-check only the current unlock before a SERVER claim or recovery."""

    root = _root(root)
    with _operation_lock(root):
        current = _load_unlocked(root, recover=True)
        if current["state"] == "LOCKED":
            raise ValueError("PROJECT_LOCKED: project operations are stopped")
        control = None
        if current["sequence"]:
            event = _load_yaml(
                root.joinpath(*Path(current["last_event"]).parts),
                current["last_event"],
            )
            control = authorization.unlock_snapshot(
                root,
                authorization_ref=event["control_ref"],
                authorization_sha256=event["control_sha256"],
                lock_sequence=current["sequence"],
                online=True,
            )
        return {
            "schema_version": 1,
            "state": current["state"],
            "sequence": current["sequence"],
            "last_event_sha256": current["last_event_sha256"],
            "unlock_control": control,
        }


def _actor_role(root: Path) -> str:
    try:
        from . import peer_governance

        role = peer_governance.current_worker(root, allow_host_default=False)["role"]
    except ValueError:
        return "UNBOUND"
    return {"PEER_B": "B", "PEER_C": "C", "SERVER": "SERVER"}.get(role, "UNBOUND")


def set_state(
    root: Path,
    *,
    state: str,
    reason: str,
    authorization_ref: str | None = None,
    authorization_sha256: str | None = None,
) -> dict[str, Any]:
    for attempt in range(4):
        try:
            return _set_state_once(
                root,
                state=state,
                reason=reason,
                authorization_ref=authorization_ref,
                authorization_sha256=authorization_sha256,
            )
        except authorization.ConcurrentControlTransaction:
            if attempt == 3:
                raise
    raise RuntimeError("project lock transaction retry loop is invalid")


def _set_state_once(
    root: Path,
    *,
    state: str,
    reason: str,
    authorization_ref: str | None = None,
    authorization_sha256: str | None = None,
) -> dict[str, Any]:
    root = _root(root)
    target = str(state).upper()
    if target not in STATES:
        raise ValueError("invalid project lock transition")
    if type(reason) is not str or len(reason.strip()) < 12 or "\x00" in reason:
        raise ValueError("project lock reason must contain at least 12 characters")
    with _operation_lock(root):
        if target == "UNLOCKED":
            authorization.synchronize_authority_main(root)
        current = _load_unlocked(root, recover=True)
        if current["state"] == target:
            return {**current, "changed": False}
        sequence = current["sequence"] + 1
        actor_role = _actor_role(root)
        control = None
        if target == "UNLOCKED":
            control = authorization.validate_unlock_authorization(
                root,
                authorization_ref=authorization_ref,
                authorization_sha256=authorization_sha256,
                lock_sequence=sequence,
            )
        event = {
            "schema_version": 1,
            "event_id": f"L{sequence:06d}",
            "sequence": sequence,
            "from_state": current["state"],
            "to_state": target,
            "reason": reason.strip(),
            "actor_source": "PROJECT",
            "actor_role": actor_role,
            "changed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "previous_event_sha256": current["last_event_sha256"],
            "control_ref": control["ref"] if control is not None else None,
            "control_sha256": control["sha256"] if control is not None else None,
        }
        event_path = root / f"coordination/project-lock/events/L{sequence:06d}.yaml"
        event_payload = yaml.safe_dump(
            event, allow_unicode=True, sort_keys=False
        ).encode("utf-8")
        digest = hashlib.sha256(event_payload).hexdigest()
        updated = _state_from_event(event_path, event, digest, root)
        state_path = root / ".research_core/PROJECT_LOCK.yaml"
        before_sha256 = hashlib.sha256(state_path.read_bytes()).hexdigest()
        updated_payload = yaml.safe_dump(
            updated, allow_unicode=True, sort_keys=False
        ).encode("utf-8")
        relative_event = event_path.relative_to(root).as_posix()
        expected_files = {
            ".research_core/PROJECT_LOCK.yaml": before_sha256,
            relative_event: None,
        }
        updated_files = {
            ".research_core/PROJECT_LOCK.yaml": updated_payload,
            relative_event: event_payload,
        }
        if control is not None:
            authorization.consume_control(
                root,
                control,
                purpose=f"PROJECT_UNLOCK:L{sequence:06d}",
                before_state_sha256=before_sha256,
                expected_files=expected_files,
                updated_files=updated_files,
            )
        else:
            # LOCKED is an immediate fail-safe and must work during network loss.
            # The shared advisory lock linearizes the local transition; normal
            # role finalization later publishes the append-only event to main.
            _exclusive_yaml(event_path, event)
            _atomic_yaml(state_path, updated)
        if _load_unlocked(root, recover=False) != updated:
            raise ValueError("project lock transaction was not adopted locally")
        return {**updated, "changed": True}


def require_operation(root: Path, *, command: str, action: str | None = None, key: str | None = None, value: str | None = None) -> None:
    current = load(root)
    if current["state"] == "UNLOCKED":
        return
    allowed = (
        command in {"help", "validate-project", "self-test"}
        or (command == "status" and action == "check")
        or (command == "project-lock" and action in {"status", "unlock"})
        or (command == "dispatch" and action == "claim-status")
        or (command == "handoff" and action == "verify")
        or (command == "config" and action == "show")
        or (
            command == "config" and action == "set" and key == "project.lock"
            and str(value).upper() == "UNLOCKED"
        )
    )
    if not allowed:
        raise ValueError(
            "PROJECT_LOCKED: project operations are stopped; only help, read-only status, "
            "validation, lock status and explicit unlock are allowed"
        )
