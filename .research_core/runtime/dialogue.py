from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

import yaml


DIALOGUE_ID = re.compile(r"([BC])D[0-9]{4}\Z")
EVENT_ID = re.compile(r"([BC])[0-9]{4}\Z")
DIRECTIVE_ID = re.compile(r"U([BC])[0-9]{4}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ROLE_WORKERS = {
    "peer-b-primary": "B",
    "peer-c-primary": "C",
}
TRIGGERS = {"NORMAL", "CRITICAL", "UNCERTAIN"}
EVENT_KINDS = {"MESSAGE", "PROPOSAL", "CRITIQUE", "CONCLUSION"}
DIRECTIVE_ACTIONS = {
    "DISPATCH_AFTER_DIALOGUE",
    "CRITIQUE_INHERIT_AND_REPLACE",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_relative(value: str, label: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError(f"invalid {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"invalid {label}")
    return path.as_posix()


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(data) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return data


def _atomic_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _exclusive_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _current_role(root: Path) -> str:
    from . import peer_governance

    identity = peer_governance.current_worker(root)
    role = {"PEER_B": "B", "PEER_C": "C"}.get(identity["role"])
    if role is None:
        raise ValueError("a bound peer worker is required")
    return role


def _validate_string_list(value: object, label: str) -> list[str]:
    if (
        type(value) is not list
        or not value
        or any(type(item) is not str or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"invalid {label}")
    return value


def _dialogue_path(root: Path, dialogue_id: str) -> Path:
    match = DIALOGUE_ID.fullmatch(str(dialogue_id))
    if match is None:
        raise ValueError("invalid dialogue identity")
    root = Path(root).resolve()
    path = root / "coordination/dialogues" / dialogue_id
    if path.parent.resolve() != (root / "coordination/dialogues").resolve():
        raise ValueError("dialogue path escapes project")
    return path


def open_dialogue(
    root: Path,
    dialogue_id: str,
    topic: str,
    trigger: str,
    conflict_set: list[str],
) -> Path:
    root = Path(root).resolve()
    role = _current_role(root)
    match = DIALOGUE_ID.fullmatch(str(dialogue_id))
    if match is None or match.group(1) != role:
        raise ValueError("worker does not own dialogue identity")
    if type(topic) is not str or not topic.strip() or "\x00" in topic:
        raise ValueError("dialogue topic is required")
    if trigger not in TRIGGERS:
        raise ValueError("invalid dialogue trigger")
    conflicts = _validate_string_list(conflict_set, "dialogue conflict_set")
    directory = _dialogue_path(root, dialogue_id)
    directory.mkdir(parents=False, exist_ok=False)
    try:
        return _exclusive_yaml(
            directory / "SESSION.yaml",
            {
                "schema_version": 1,
                "dialogue_id": dialogue_id,
                "opened_by": role,
                "topic": topic.strip(),
                "trigger": trigger,
                "conflict_set": conflicts,
                "created_at": _utc_now(),
            },
        )
    except BaseException:
        try:
            directory.rmdir()
        except OSError:
            pass
        raise


def _validate_session(path: Path) -> dict:
    document = _load_yaml(path)
    if set(document) != {
        "schema_version", "dialogue_id", "opened_by", "topic", "trigger",
        "conflict_set", "created_at",
    } or document["schema_version"] != 1:
        raise ValueError("invalid dialogue session")
    match = DIALOGUE_ID.fullmatch(str(document["dialogue_id"]))
    if match is None or document["opened_by"] != match.group(1):
        raise ValueError("dialogue owner mismatch")
    if document["trigger"] not in TRIGGERS:
        raise ValueError("invalid dialogue trigger")
    _validate_string_list(document["conflict_set"], "dialogue conflict_set")
    if type(document["topic"]) is not str or not document["topic"].strip():
        raise ValueError("invalid dialogue topic")
    if type(document["created_at"]) is not str or not document["created_at"]:
        raise ValueError("invalid dialogue timestamp")
    return document


def _validate_event(path: Path, dialogue_id: str, role: str) -> dict:
    document = _load_yaml(path)
    if set(document) != {
        "schema_version", "event_id", "dialogue_id", "author_role", "kind",
        "message", "created_at",
    } or document["schema_version"] != 1:
        raise ValueError("invalid dialogue event")
    match = EVENT_ID.fullmatch(str(document["event_id"]))
    if (
        match is None
        or match.group(1) != role
        or document["author_role"] != role
        or document["dialogue_id"] != dialogue_id
        or document["kind"] not in EVENT_KINDS
        or type(document["message"]) is not str
        or not document["message"].strip()
    ):
        raise ValueError("dialogue event identity mismatch")
    return document


def load_dialogue(root: Path, dialogue_id: str) -> dict:
    directory = _dialogue_path(Path(root).resolve(), dialogue_id)
    session = _validate_session(directory / "SESSION.yaml")
    events: list[dict] = []
    for role in ("B", "C"):
        event_root = directory / "events" / role
        if not event_root.exists():
            continue
        for path in sorted(event_root.glob("*.yaml")):
            if path.is_symlink() or not path.is_file():
                raise ValueError("dialogue event must be a plain file")
            events.append(_validate_event(path, dialogue_id, role))
    return {"session": session, "events": events}


def post_event(
    root: Path,
    dialogue_id: str,
    event_id: str,
    kind: str,
    message: str,
) -> Path:
    root = Path(root).resolve()
    role = _current_role(root)
    current = load_dialogue(root, dialogue_id)
    match = EVENT_ID.fullmatch(str(event_id))
    if match is None or match.group(1) != role:
        raise ValueError("worker does not own dialogue event")
    if kind not in EVENT_KINDS:
        raise ValueError("invalid dialogue event kind")
    if type(message) is not str or not message.strip() or "\x00" in message:
        raise ValueError("dialogue message is required")
    if kind == "CONCLUSION" and current["session"]["trigger"] in {
        "CRITICAL", "UNCERTAIN"
    }:
        contributors = {event["author_role"] for event in current["events"]}
        if contributors != {"B", "C"}:
            raise ValueError("critical dialogue requires both peer contributions")
    path = (
        _dialogue_path(root, dialogue_id)
        / "events"
        / role
        / f"{event_id}.yaml"
    )
    return _exclusive_yaml(
        path,
        {
            "schema_version": 1,
            "event_id": event_id,
            "dialogue_id": dialogue_id,
            "author_role": role,
            "kind": kind,
            "message": message.strip(),
            "created_at": _utc_now(),
        },
    )


def _directive_path(root: Path, relative: str) -> Path:
    relative = _safe_relative(relative, "user directive")
    match = re.fullmatch(
        r"coordination/directives/([BC])/(U[BC][0-9]{4})\.yaml", relative
    )
    if match is None or match.group(2)[1] != match.group(1):
        raise ValueError("user directive path is not role-owned")
    root = Path(root).resolve()
    path = root.joinpath(*PurePosixPath(relative).parts)
    if path.parent.resolve() != (root / "coordination/directives" / match.group(1)).resolve():
        raise ValueError("user directive path escapes project")
    return path


def validate_user_directive(root: Path, relative: str) -> dict:
    path = _directive_path(Path(root).resolve(), relative)
    document = _load_yaml(path)
    if set(document) != {
        "schema_version", "directive_id", "designated_role", "action",
        "user_instruction", "dialogue_id", "prior_plan_path",
        "prior_plan_sha256", "created_at",
    } or document["schema_version"] != 1:
        raise ValueError("invalid user directive")
    match = DIRECTIVE_ID.fullmatch(str(document["directive_id"]))
    if match is None or match.group(1) != document["designated_role"]:
        raise ValueError("user directive role mismatch")
    expected = f"coordination/directives/{match.group(1)}/{document['directive_id']}.yaml"
    if relative != expected or document["action"] not in DIRECTIVE_ACTIONS:
        raise ValueError("invalid user directive identity")
    if type(document["user_instruction"]) is not str or not document["user_instruction"].strip():
        raise ValueError("user directive text is required")
    if document["action"] == "DISPATCH_AFTER_DIALOGUE":
        if DIALOGUE_ID.fullmatch(str(document["dialogue_id"])) is None:
            raise ValueError("dialogue directive requires a dialogue")
        if document["prior_plan_path"] is not None or document["prior_plan_sha256"] is not None:
            raise ValueError("dialogue directive cannot bind a prior plan")
    else:
        _safe_relative(document["prior_plan_path"], "prior plan path")
        if SHA256.fullmatch(str(document["prior_plan_sha256"])) is None:
            raise ValueError("replacement directive requires prior plan SHA256")
        if document["dialogue_id"] is not None:
            _dialogue_path(Path(root).resolve(), document["dialogue_id"])
    return document


def _matching_dialogue_directives(root: Path, dialogue_id: str) -> list[dict]:
    matches: list[dict] = []
    for role in ("B", "C"):
        directory = Path(root) / "coordination/directives" / role
        if not directory.exists():
            continue
        for path in sorted(directory.glob("U*.yaml")):
            relative = path.relative_to(root).as_posix()
            document = validate_user_directive(root, relative)
            if (
                document["action"] == "DISPATCH_AFTER_DIALOGUE"
                and document["dialogue_id"] == dialogue_id
            ):
                matches.append(document)
    return matches


def dialogue_status(root: Path, dialogue_id: str) -> dict:
    current = load_dialogue(root, dialogue_id)
    session = current["session"]
    conclusions = [event for event in current["events"] if event["kind"] == "CONCLUSION"]
    if not conclusions:
        status = "OPEN"
    elif session["trigger"] == "NORMAL":
        status = "CLOSED"
    elif _matching_dialogue_directives(Path(root).resolve(), dialogue_id):
        status = "DESIGNATED"
    else:
        status = "USER_DESIGNATION_REQUIRED"
    return {
        "dialogue_id": dialogue_id,
        "trigger": session["trigger"],
        "conflict_set": session["conflict_set"],
        "status": status,
        "events": current["events"],
    }


def record_user_directive(
    root: Path,
    directive_id: str,
    *,
    designated_role: str,
    action: str,
    user_instruction: str,
    dialogue_id: str | None = None,
    prior_plan_path: str | None = None,
    prior_plan_sha256: str | None = None,
) -> Path:
    root = Path(root).resolve()
    role = _current_role(root)
    match = DIRECTIVE_ID.fullmatch(str(directive_id))
    if match is None or match.group(1) != role or designated_role != role:
        raise ValueError("only the user-designated peer may record this directive")
    if action not in DIRECTIVE_ACTIONS:
        raise ValueError("invalid user directive action")
    if type(user_instruction) is not str or not user_instruction.strip() or "\x00" in user_instruction:
        raise ValueError("user directive text is required")
    if action == "DISPATCH_AFTER_DIALOGUE":
        if dialogue_id is None:
            raise ValueError("dialogue directive requires a dialogue")
        status = dialogue_status(root, dialogue_id)
        if status["status"] != "USER_DESIGNATION_REQUIRED":
            raise ValueError("dialogue is not awaiting user designation")
        prior_plan_path = None
        prior_plan_sha256 = None
    else:
        if prior_plan_path is None or prior_plan_sha256 is None:
            raise ValueError("replacement directive requires the active plan")
        prior_plan_path = _safe_relative(prior_plan_path, "prior plan path")
        if SHA256.fullmatch(prior_plan_sha256) is None:
            raise ValueError("invalid prior plan SHA256")
        if dialogue_id is not None:
            _dialogue_path(root, dialogue_id)
    relative = f"coordination/directives/{role}/{directive_id}.yaml"
    path = _directive_path(root, relative)
    document = {
        "schema_version": 1,
        "directive_id": directive_id,
        "designated_role": role,
        "action": action,
        "user_instruction": user_instruction.strip(),
        "dialogue_id": dialogue_id,
        "prior_plan_path": prior_plan_path,
        "prior_plan_sha256": prior_plan_sha256,
        "created_at": _utc_now(),
    }
    _exclusive_yaml(path, document)
    validate_user_directive(root, relative)
    return path


def relevant_dialogues(root: Path, conflict_set: list[str]) -> list[dict]:
    root = Path(root).resolve()
    conflicts = set(conflict_set)
    directory = root / "coordination/dialogues"
    relevant: list[dict] = []
    if not directory.exists():
        return relevant
    for session in sorted(directory.glob("[BC]D[0-9][0-9][0-9][0-9]/SESSION.yaml")):
        status = dialogue_status(root, session.parent.name)
        if (
            status["trigger"] in {"CRITICAL", "UNCERTAIN"}
            and conflicts.intersection(status["conflict_set"])
        ):
            relevant.append(status)
    return relevant


def unresolved_dialogues(root: Path, conflict_set: list[str]) -> list[dict]:
    return [
        status
        for status in relevant_dialogues(root, conflict_set)
        if status["status"] in {"OPEN", "USER_DESIGNATION_REQUIRED"}
    ]


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"git dialogue sync failed: {detail}")
    return completed


def sync_dialogue(root: Path) -> dict:
    root = Path(root).resolve()
    top = _git(root, "rev-parse", "--show-toplevel").stdout.strip()
    if Path(top).resolve() != root:
        raise ValueError("dialogue sync requires the exact repository root")
    if _git(root, "branch", "--show-current").stdout.strip() != "main":
        raise ValueError("dialogue sync requires branch main")
    if _git(root, "status", "--porcelain").stdout:
        raise ValueError("dialogue sync requires a clean worktree")
    _git(root, "fetch", "origin", "main")
    local = _git(root, "rev-parse", "HEAD").stdout.strip()
    remote = _git(root, "rev-parse", "origin/main").stdout.strip()
    if local == remote:
        return {"status": "SYNCED", "head": local}
    local_is_ancestor = _git(
        root, "merge-base", "--is-ancestor", local, remote, check=False
    ).returncode == 0
    remote_is_ancestor = _git(
        root, "merge-base", "--is-ancestor", remote, local, check=False
    ).returncode == 0
    if local_is_ancestor:
        _git(root, "merge", "--ff-only", "origin/main")
        return {"status": "UPDATED", "head": remote}
    if remote_is_ancestor:
        return {"status": "AHEAD", "head": local, "remote": remote}
    raise ValueError("local main and origin/main diverged; dialogue sync stopped")
