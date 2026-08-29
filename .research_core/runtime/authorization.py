"""Shared validation for user-controlled permission and project-unlock events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

import yaml


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
SENSITIVE_PERMISSIONS = {"external_write", "resource_expansion", "publish"}
ROLES = {"B", "C"}
CONTROL_ID = re.compile(r"uc-[0-9a-f]{32}\Z")
PERMISSION_EVENT_KEYS = {
    "schema_version",
    "project_id",
    "permission",
    "instruction_id",
    "plan_ref",
    "plan_sha256",
    "scope",
    "scope_sha256",
    "expires_at",
    "issued_by_role",
    "user_control",
    "control_id",
}
UNLOCK_EVENT_KEYS = {
    "schema_version",
    "project_id",
    "action",
    "lock_sequence",
    "expires_at",
    "issued_by_role",
    "user_control",
    "control_id",
}
CONSUMPTION_KEYS = {
    "schema_version",
    "control_id",
    "purpose",
    "authorization_ref",
    "authorization_sha256",
    "authorization_blob_oid",
    "repository_authority_sha256",
    "remote_main_parent",
    "before_state_sha256",
    "consumed_at",
}

STRUCTURAL_GIT_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_INDEX_FILE",
}


class ConcurrentControlTransaction(ValueError):
    """Authoritative main advanced normally; caller may synchronize and retry."""


def _portable_yaml_bytes(payload: bytes) -> bytes:
    """Use one digest/content identity across LF and CRLF Git worktrees."""

    return payload.replace(b"\r\n", b"\n")


def _canonical_sha256(value: Any) -> str:
    payload = yaml.safe_dump(
        value, allow_unicode=True, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _project_id(root: Path) -> str:
    path = root / "project.yaml"
    if path.is_symlink() or not path.is_file():
        raise ValueError("project identity document is unavailable")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    value = document.get("project_id") if type(document) is dict else None
    if type(value) is not str or not value:
        raise ValueError("project identity is invalid")
    return value


def _future_expiry(value: Any) -> str:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("authorization expiry is invalid")
    try:
        expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("authorization expiry is invalid") from error
    now = datetime.now(timezone.utc)
    if expiry <= now or expiry > now + timedelta(hours=24):
        raise ValueError("authorization is expired or exceeds the 24-hour control window")
    return value


def _load_event(
    root: Path,
    *,
    authorization_ref: Any,
    authorization_sha256: Any,
) -> tuple[dict[str, Any], str, str, bytes]:
    if (
        type(authorization_ref) is not str
        or type(authorization_sha256) is not str
        or SHA256.fullmatch(authorization_sha256) is None
    ):
        raise ValueError("digest-bound user authorization is required")
    pure = PurePosixPath(authorization_ref)
    if (
        pure.is_absolute()
        or "." in pure.parts
        or ".." in pure.parts
        or len(pure.parts) < 4
        or pure.parts[:2] != ("coordination", "controls")
        or pure.parts[2] not in ROLES
    ):
        raise ValueError("user authorization ref is invalid")
    path = root.joinpath(*pure.parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("user authorization event is missing")
    payload = path.read_bytes()
    if (
        not payload
        or len(payload) > 64 * 1024
        or hashlib.sha256(_portable_yaml_bytes(payload)).hexdigest()
        != authorization_sha256
    ):
        raise ValueError("user authorization event changed")
    try:
        document = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError("user authorization event must be plain UTF-8 YAML") from error
    if type(document) is not dict:
        raise ValueError("user authorization event must be a mapping")
    relative = pure.as_posix()
    return document, relative, pure.parts[2], payload


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key.startswith("GIT_CONFIG_") or key in STRUCTURAL_GIT_ENV:
            environment.pop(key, None)
    environment.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
    return environment


def _git(root: Path, arguments: list[str], *, timeout: int = 30) -> str:
    try:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, capture_output=True, text=True,
            encoding="utf-8", check=False, shell=False, timeout=timeout,
            env=_git_environment(),
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("external user-control remote main verification timed out") from error
    if completed.returncode != 0:
        raise ValueError(
            completed.stderr.strip()
            or "external user-control remote main verification failed"
        )
    return completed.stdout.strip()


def _canonical_repository_url(value: Any) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError("repository authority URL is invalid")
    if value.startswith("https://"):
        base = value.rstrip("/")
        if not base.endswith(".git"):
            base += ".git"
        return base
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("repository authority URL must be absolute")
    return str(path.resolve())


def _authoritative_repository(root: Path) -> tuple[str, str]:
    """Read the immutable authority URL from the repository's only root commit."""

    root = Path(root).resolve()
    identities = _git(
        root,
        ["log", "--reverse", "--format=%H", "--diff-filter=A", "--", "project.yaml"],
    ).splitlines()
    if len(identities) != 1 or GIT_OID.fullmatch(identities[0]) is None:
        raise ValueError("repository authority identity commit is ambiguous")
    payload = _git(root, ["show", f"{identities[0]}:project.yaml"]).encode("utf-8")
    if not payload or len(payload) > 64 * 1024:
        raise ValueError("repository authority project identity is invalid")
    try:
        document = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError("repository authority project identity is invalid") from error
    project_id = document.get("project_id") if type(document) is dict else None
    repository = document.get("repository_name") if type(document) is dict else None
    migration = document.get("migration") if type(document) is dict else None
    source_head = migration.get("source_head") if type(migration) is dict else None
    if (
        type(project_id) is not str
        or not project_id
        or type(repository) is not str
        or not repository
        or type(document.get("repository_authority_url")) is not str
        or type(migration) is not dict
        or migration.get("profile") != "IN_PLACE_HISTORY_PRESERVING"
        or type(source_head) is not str
        or GIT_OID.fullmatch(source_head) is None
        or _git(root, ["rev-parse", f"{identities[0]}^"]) != source_head
    ):
        raise ValueError("repository authority project identity is invalid")
    authority_url = _canonical_repository_url(document["repository_authority_url"])
    rewrites = subprocess.run(
        ["git", "config", "--get-regexp", r"^url\..*"], cwd=root,
        capture_output=True, text=True, encoding="utf-8", check=False,
        shell=False, timeout=30, env=_git_environment(),
    )
    if rewrites.returncode not in {0, 1}:
        raise ValueError("repository authority Git configuration is unavailable")
    if rewrites.returncode == 0 and rewrites.stdout.strip():
        raise ValueError("repository authority forbids Git URL rewrite configuration")
    fetch_url = _canonical_repository_url(
        _git(root, ["remote", "get-url", "origin"])
    )
    push_url = _canonical_repository_url(
        _git(root, ["remote", "get-url", "--push", "origin"])
    )
    if fetch_url != authority_url or push_url != authority_url:
        raise ValueError("origin does not match the root-commit repository authority")
    return authority_url, hashlib.sha256(authority_url.encode("utf-8")).hexdigest()


def _require_remote_main_blob(
    root: Path, relative: str, payload: bytes
) -> tuple[str, str]:
    """Return the stable blob identity currently published on external main."""

    root = Path(root).resolve()
    control_ref = "refs/cqc/user-control/main"
    authority_url, authority_sha256 = _authoritative_repository(root)
    try:
        _git(
            root,
            ["fetch", "--no-tags", authority_url, f"refs/heads/main:{control_ref}"],
        )
    except ValueError as error:
        raise ValueError(
            "external user-control remote main verification failed"
        ) from error
    try:
        remote_payload = subprocess.run(
            ["git", "show", f"{control_ref}:{relative}"],
            cwd=root, capture_output=True, check=False, shell=False, timeout=30,
            env=_git_environment(),
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("external user-control remote main blob read timed out") from error
    if (
        remote_payload.returncode != 0
        or _portable_yaml_bytes(remote_payload.stdout) != _portable_yaml_bytes(payload)
    ):
        raise ValueError(
            "external user-control credential is absent from remote main or changed"
        )
    blob_oid = _git(root, ["rev-parse", f"{control_ref}:{relative}"])
    if GIT_OID.fullmatch(blob_oid) is None:
        raise ValueError("external user-control remote main blob identity is invalid")
    return blob_oid, authority_sha256


def _adopt_authority_commit(root: Path, commit: str) -> None:
    """Fast-forward the current worktree without discarding unrelated edits."""

    root = Path(root).resolve()
    current = _git(root, ["rev-parse", "HEAD"])
    if current == commit:
        return
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", current, commit], cwd=root,
        capture_output=True, text=True, encoding="utf-8", check=False,
        shell=False, timeout=30, env=_git_environment(),
    )
    if ancestor.returncode != 0:
        raise ValueError("local project history diverged from authoritative main")
    try:
        _git(root, ["reset", "--keep", commit])
    except ValueError as error:
        raise ValueError(
            "local edits conflict with the authoritative control transaction"
        ) from error


def synchronize_authority_main(root: Path) -> str:
    """Fetch and locally adopt current root-pinned main before a state mutation."""

    root = Path(root).resolve()
    authority_url, _ = _authoritative_repository(root)
    control_ref = "refs/cqc/user-control/main"
    _git(
        root,
        ["fetch", "--no-tags", authority_url, f"refs/heads/main:{control_ref}"],
    )
    commit = _git(root, ["rev-parse", control_ref])
    if GIT_OID.fullmatch(commit) is None:
        raise ValueError("authoritative main commit is invalid")
    _adopt_authority_commit(root, commit)
    return commit


def _consumption_path(root: Path, control_id: str) -> Path:
    return Path(root) / "coordination" / "controls" / "consumed" / f"{control_id}.yaml"


def _load_consumption(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("external user-control credential has not been consumed")
    payload = path.read_bytes()
    if not payload or len(payload) > 64 * 1024:
        raise ValueError("external user-control consumption receipt is invalid")
    try:
        document = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError("external user-control consumption receipt is invalid") from error
    if type(document) is not dict or set(document) != CONSUMPTION_KEYS:
        raise ValueError("external user-control consumption receipt is invalid")
    return document, payload


def require_consumed_control(
    root: Path,
    authorization: dict[str, Any],
    *,
    purpose: str,
    online: bool,
) -> tuple[dict[str, Any], bytes]:
    """Validate the local receipt and optionally its remote one-time claim."""

    event = authorization["event"]
    path = _consumption_path(Path(root), event["control_id"])
    document, payload = _load_consumption(path)
    expected_blob = authorization.get("authorization_blob_oid")
    if (
        document.get("schema_version") != 1
        or document.get("control_id") != event["control_id"]
        or document.get("purpose") != purpose
        or document.get("authorization_ref") != authorization["ref"]
        or document.get("authorization_sha256") != authorization["sha256"]
        or type(document.get("authorization_blob_oid")) is not str
        or GIT_OID.fullmatch(document["authorization_blob_oid"]) is None
        or type(document.get("repository_authority_sha256")) is not str
        or SHA256.fullmatch(document["repository_authority_sha256"]) is None
        or type(document.get("remote_main_parent")) is not str
        or GIT_OID.fullmatch(document["remote_main_parent"]) is None
        or (
            expected_blob is not None
            and document["authorization_blob_oid"] != expected_blob
        )
        or (
            authorization.get("repository_authority_sha256") is not None
            and document["repository_authority_sha256"]
            != authorization["repository_authority_sha256"]
        )
        or type(document.get("before_state_sha256")) is not str
        or SHA256.fullmatch(document["before_state_sha256"]) is None
        or type(document.get("consumed_at")) is not str
        or not document["consumed_at"].endswith("Z")
    ):
        raise ValueError("external user-control consumption receipt does not match")
    try:
        consumed = datetime.fromisoformat(
            document["consumed_at"].replace("Z", "+00:00")
        )
        expiry = datetime.fromisoformat(event["expires_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("external user-control consumption time is invalid") from error
    if consumed > expiry:
        raise ValueError("external user-control was consumed after expiry")
    if online:
        _require_remote_consumption(Path(root), document)
    return document, payload


def _remote_consumption_from_history(
    root: Path, main_ref: str, control_id: str
) -> tuple[dict[str, Any], str] | None:
    relative = f"coordination/controls/consumed/{control_id}.yaml"
    additions = _git(
        root,
        ["log", "--format=%H", "--diff-filter=A", main_ref, "--", relative],
    ).splitlines()
    if not additions:
        return None
    if len(additions) != 1 or GIT_OID.fullmatch(additions[0]) is None:
        raise ValueError("external user-control consumption history is not append-only")
    commit = additions[0]
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=root,
        capture_output=True, check=False, shell=False, timeout=30,
        env=_git_environment(),
    )
    try:
        remote_document = yaml.safe_load(completed.stdout.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError(
            "external user-control remote consumption receipt is invalid"
        ) from error
    if (
        completed.returncode != 0
        or type(remote_document) is not dict
        or set(remote_document) != CONSUMPTION_KEYS
        or _git(root, ["rev-parse", f"{commit}^"])
        != remote_document.get("remote_main_parent")
    ):
        raise ValueError("external user-control remote consumption receipt is invalid")
    current_payload = _remote_file(root, main_ref, relative)
    if current_payload is None or yaml.safe_load(
        current_payload.decode("utf-8")
    ) != remote_document:
        raise ValueError("external user-control consumption history was deleted or changed")
    return remote_document, commit


def _require_remote_consumption(root: Path, document: dict[str, Any]) -> None:
    authority_url, authority_sha256 = _authoritative_repository(root)
    if document["repository_authority_sha256"] != authority_sha256:
        raise ValueError("external user-control repository authority changed")
    main_ref = "refs/cqc/user-control/main"
    try:
        _git(
            root,
            ["fetch", "--no-tags", authority_url, f"refs/heads/main:{main_ref}"],
        )
        remote = _remote_consumption_from_history(
            root, main_ref, document["control_id"]
        )
    except ValueError as error:
        raise ValueError(
            "external user-control remote consumption receipt is unavailable"
        ) from error
    if remote is None or remote[0] != document:
        raise ValueError("external user-control remote consumption receipt changed")


def consume_control(
    root: Path,
    authorization: dict[str, Any],
    *,
    purpose: str,
    before_state_sha256: str,
    expected_files: dict[str, str | None] | None = None,
    updated_files: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    if (
        type(purpose) is not str
        or not purpose
        or type(before_state_sha256) is not str
        or SHA256.fullmatch(before_state_sha256) is None
    ):
        raise ValueError("external user-control consumption request is invalid")
    event = authorization["event"]
    path = _consumption_path(Path(root), event["control_id"])
    document = {
        "schema_version": 1,
        "control_id": event["control_id"],
        "purpose": purpose,
        "authorization_ref": authorization["ref"],
        "authorization_sha256": authorization["sha256"],
        "authorization_blob_oid": authorization["authorization_blob_oid"],
        "repository_authority_sha256": authorization[
            "repository_authority_sha256"
        ],
        "before_state_sha256": before_state_sha256,
        "consumed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    document, ledger_commit = _claim_remote_consumption(
        Path(root),
        document,
        authorization,
        expected_files=expected_files or {},
        updated_files=updated_files or {},
    )
    _adopt_authority_commit(Path(root), ledger_commit)
    existing, _ = _load_consumption(path)
    if existing != document:
        raise ValueError("local user-control receipt does not match authoritative main")
    return existing


def _run_git_input(
    root: Path, arguments: list[str], *, payload: str, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=root, input=payload, capture_output=True,
        text=True, encoding="utf-8", check=False, shell=False, timeout=30,
        env=environment,
    )


def _transaction_relative(value: str) -> str:
    pure = PurePosixPath(value)
    if (
        type(value) is not str
        or not value
        or "\\" in value
        or pure.is_absolute()
        or ".." in pure.parts
        or pure.as_posix() != value
    ):
        raise ValueError("control transaction path is invalid")
    return value


def _remote_file(root: Path, commit: str, relative: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=root,
        capture_output=True, check=False, shell=False, timeout=30,
        env=_git_environment(),
    )
    if completed.returncode == 0:
        return completed.stdout
    missing = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{relative}"], cwd=root,
        capture_output=True, check=False, shell=False, timeout=30,
        env=_git_environment(),
    )
    if missing.returncode != 0:
        return None
    raise ValueError("authoritative control transaction file is unreadable")


def _validate_transaction_files(
    root: Path,
    parent: str,
    expected_files: dict[str, str | None],
    updated_files: dict[str, bytes],
) -> dict[str, bytes]:
    if set(expected_files) != set(updated_files):
        raise ValueError("control transaction file closure does not match")
    updates: dict[str, bytes] = {}
    for raw_relative, payload in updated_files.items():
        relative = _transaction_relative(raw_relative)
        expected = expected_files[raw_relative]
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) > 1024 * 1024
            or (expected is not None and (type(expected) is not str or SHA256.fullmatch(expected) is None))
        ):
            raise ValueError("control transaction file identity is invalid")
        current = _remote_file(root, parent, relative)
        if expected is None:
            if current is not None:
                raise ValueError("control transaction expected an absent file")
        elif current is None or hashlib.sha256(current).hexdigest() != expected:
            raise ValueError("authoritative project state changed before transaction")
        updates[relative] = payload
    return updates


def _build_transaction_commit(
    root: Path,
    parent: str,
    updates: dict[str, bytes],
    *,
    message: str,
) -> str:
    environment = {
        **_git_environment(),
        "GIT_AUTHOR_NAME": "cqc control transaction",
        "GIT_AUTHOR_EMAIL": "cqc-control@example.invalid",
        "GIT_COMMITTER_NAME": "cqc control transaction",
        "GIT_COMMITTER_EMAIL": "cqc-control@example.invalid",
    }
    descriptor, index_name = tempfile.mkstemp(prefix="cqc-control-index-")
    os.close(descriptor)
    Path(index_name).unlink(missing_ok=True)
    environment["GIT_INDEX_FILE"] = index_name
    try:
        read_tree = _run_git_input(
            root, ["read-tree", parent], payload="", environment=environment
        )
        if read_tree.returncode != 0:
            raise ValueError("control transaction cannot read authoritative tree")
        for relative, payload in sorted(updates.items()):
            blob = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"], cwd=root,
                input=payload, capture_output=True, check=False, shell=False,
                timeout=30, env=environment,
            )
            blob_oid = blob.stdout.decode("ascii", errors="strict").strip()
            if blob.returncode != 0 or GIT_OID.fullmatch(blob_oid) is None:
                raise ValueError("control transaction blob creation failed")
            indexed = _run_git_input(
                root,
                ["update-index", "--add", "--cacheinfo", "100644", blob_oid, relative],
                payload="",
                environment=environment,
            )
            if indexed.returncode != 0:
                raise ValueError("control transaction index update failed")
        tree = _run_git_input(
            root, ["write-tree"], payload="", environment=environment
        )
        tree_oid = tree.stdout.strip()
        if tree.returncode != 0 or GIT_OID.fullmatch(tree_oid) is None:
            raise ValueError("control transaction tree creation failed")
        commit = _run_git_input(
            root,
            ["commit-tree", tree_oid, "-p", parent],
            payload=message.rstrip() + "\n",
            environment=environment,
        )
        commit_oid = commit.stdout.strip()
        if commit.returncode != 0 or GIT_OID.fullmatch(commit_oid) is None:
            raise ValueError("control transaction commit creation failed")
        return commit_oid
    finally:
        Path(index_name).unlink(missing_ok=True)


def _push_main_transaction(
    root: Path, authority_url: str, parent: str, commit: str
) -> bool:
    pushed = subprocess.run(
        [
            "git", "push", "--porcelain",
            f"--force-with-lease=refs/heads/main:{parent}",
            authority_url,
            f"{commit}:refs/heads/main",
        ],
        cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
        shell=False, timeout=30, env=_git_environment(),
    )
    return pushed.returncode == 0


def _require_local_parent(root: Path, parent: str) -> None:
    if _git(root, ["rev-parse", "HEAD"]) != parent:
        raise ValueError(
            "local main changed before the control transaction; synchronize and retry"
        )


def commit_project_transition(
    root: Path,
    *,
    purpose: str,
    expected_files: dict[str, str | None],
    updated_files: dict[str, bytes],
) -> str:
    """CAS ordinary project-control files onto root-pinned protected main."""

    root = Path(root).resolve()
    authority_url, _ = _authoritative_repository(root)
    main_ref = "refs/cqc/user-control/main"
    _git(root, ["fetch", "--no-tags", authority_url, f"refs/heads/main:{main_ref}"])
    parent = _git(root, ["rev-parse", main_ref])
    _require_local_parent(root, parent)
    updates = _validate_transaction_files(
        root, parent, expected_files, updated_files
    )
    commit = _build_transaction_commit(
        root, parent, updates, message=f"control: {purpose}"
    )
    if not _push_main_transaction(root, authority_url, parent, commit):
        raise ConcurrentControlTransaction(
            "authoritative main changed during project-control transaction"
        )
    _git(root, ["update-ref", main_ref, commit, parent])
    _adopt_authority_commit(root, commit)
    return commit


def _claim_remote_consumption(
    root: Path,
    document: dict[str, Any],
    authorization: dict[str, Any],
    *,
    expected_files: dict[str, str | None],
    updated_files: dict[str, bytes],
) -> tuple[dict[str, Any], str]:
    """CAS receipt and state transition onto protected main in one commit."""

    authority_url, authority_sha256 = _authoritative_repository(root)
    if document["repository_authority_sha256"] != authority_sha256:
        raise ValueError("external user-control repository authority changed")
    blob_oid, refreshed_authority = _require_remote_main_blob(
        root, authorization["ref"], authorization["event_payload"]
    )
    if (
        blob_oid != document["authorization_blob_oid"]
        or refreshed_authority != document["repository_authority_sha256"]
    ):
        raise ValueError("external user-control changed before consumption")
    _future_expiry(authorization["event"].get("expires_at"))
    main_ref = "refs/cqc/user-control/main"
    parent = _git(root, ["rev-parse", main_ref])
    existing = _remote_consumption_from_history(
        root, main_ref, document["control_id"]
    )
    if existing is not None:
        comparable = CONSUMPTION_KEYS - {"consumed_at", "remote_main_parent"}
        if any(existing[0].get(key) != document.get(key) for key in comparable):
            raise ValueError("external user-control credential was already consumed")
        return existing[0], parent
    _require_local_parent(root, parent)
    updates = _validate_transaction_files(
        root, parent, expected_files, updated_files
    )
    claimed = {**document, "remote_main_parent": parent}
    receipt_relative = (
        f"coordination/controls/consumed/{document['control_id']}.yaml"
    )
    if receipt_relative in updates or _remote_file(root, parent, receipt_relative) is not None:
        raise ValueError("external user-control consumption receipt already exists")
    receipt_payload = yaml.safe_dump(
        claimed, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    updates[receipt_relative] = receipt_payload
    commit = _build_transaction_commit(
        root,
        parent,
        updates,
        message=f"control: consume {document['control_id']} for {document['purpose']}",
    )
    if _push_main_transaction(root, authority_url, parent, commit):
        _git(root, ["update-ref", main_ref, commit, parent])
        return claimed, commit
    _git(root, ["fetch", "--no-tags", authority_url, f"refs/heads/main:{main_ref}"])
    current = _git(root, ["rev-parse", main_ref])
    remote = _remote_consumption_from_history(
        root, main_ref, document["control_id"]
    )
    if remote is not None:
        comparable = CONSUMPTION_KEYS - {"consumed_at", "remote_main_parent"}
        if all(remote[0].get(key) == document.get(key) for key in comparable):
            return remote[0], current
        raise ValueError("external user-control credential was already consumed")
    current_event = _remote_file(root, current, authorization["ref"])
    if current_event is not None and _portable_yaml_bytes(
        current_event
    ) == _portable_yaml_bytes(authorization["event_payload"]):
        raise ConcurrentControlTransaction(
            "authoritative main advanced during control consumption"
        )
    raise ValueError(
        "authoritative main changed or revoked the control before consumption"
    )


def permission_scope(plan: dict[str, Any]) -> dict[str, Any]:
    """Bind authorization to the concrete result, resource and publication scope."""

    return {
        "expected_results": plan.get("expected_results"),
        "resources": plan.get("resources"),
        "result_branch": plan.get("result_branch"),
    }


def _permission_authorization(
    root: Path,
    *,
    permission: str,
    authorization_ref: Any,
    authorization_sha256: Any,
    plan: dict[str, Any] | None = None,
    require_issuer_role: str | None = None,
    online: bool = False,
    check_current_expiry: bool = False,
) -> dict[str, Any]:
    if permission not in SENSITIVE_PERMISSIONS:
        raise ValueError("permission is not a sensitive configurable permission")
    document, relative, path_role, event_payload = _load_event(
        Path(root),
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
    )
    if (
        set(document) != PERMISSION_EVENT_KEYS
        or document.get("schema_version") != 1
        or document.get("project_id") != _project_id(Path(root))
        or document.get("permission") != permission
        or document.get("issued_by_role") != path_role
        or document.get("issued_by_role") not in ROLES
        or document.get("user_control")
        != f"用户明确启用项目权限 permission.{permission}"
        or type(document.get("control_id")) is not str
        or CONTROL_ID.fullmatch(document["control_id"]) is None
        or type(document.get("instruction_id")) is not str
        or INSTRUCTION_ID.fullmatch(document["instruction_id"]) is None
    ):
        raise ValueError("permission authorization event identity is invalid")
    if require_issuer_role is not None and document["issued_by_role"] != require_issuer_role:
        raise ValueError("permission authorization issuer does not match the current B/C role")
    if check_current_expiry:
        _future_expiry(document.get("expires_at"))
    expected_ref = (
        f"coordination/instructions/{document['instruction_id']}/SERVER_PLAN.yaml"
    )
    if document.get("plan_ref") != expected_ref:
        raise ValueError("permission authorization plan ref is invalid")
    plan_path = Path(root).joinpath(*PurePosixPath(expected_ref).parts)
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ValueError("permission authorization plan is missing")
    payload = plan_path.read_bytes()
    if (
        type(document.get("plan_sha256")) is not str
        or SHA256.fullmatch(document["plan_sha256"]) is None
        or hashlib.sha256(payload).hexdigest() != document["plan_sha256"]
    ):
        raise ValueError("permission authorization plan changed")
    try:
        bound_plan = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as error:
        raise ValueError("permission authorization plan is invalid") from error
    if (
        type(bound_plan) is not dict
        or bound_plan.get("instruction_id") != document["instruction_id"]
        or permission not in bound_plan.get("required_permissions", [])
    ):
        raise ValueError("permission authorization is not required by the bound plan")
    expected_scope = permission_scope(bound_plan)
    if (
        document.get("scope") != expected_scope
        or type(document.get("scope_sha256")) is not str
        or SHA256.fullmatch(document["scope_sha256"]) is None
        or _canonical_sha256(expected_scope) != document["scope_sha256"]
    ):
        raise ValueError("permission authorization scope changed")
    if plan is not None and (
        plan.get("instruction_id") != bound_plan.get("instruction_id")
        or permission_scope(plan) != expected_scope
        or permission not in plan.get("required_permissions", [])
    ):
        raise ValueError("permission authorization does not cover this execution plan")
    result = {
        "ref": relative,
        "sha256": authorization_sha256,
        "event": document,
        "event_payload": event_payload,
    }
    if online:
        (
            result["authorization_blob_oid"],
            result["repository_authority_sha256"],
        ) = _require_remote_main_blob(Path(root), relative, event_payload)
    return result


def validate_permission_authorization(
    root: Path,
    *,
    permission: str,
    authorization_ref: Any,
    authorization_sha256: Any,
    plan: dict[str, Any] | None = None,
    require_issuer_role: str | None = None,
    require_consumed: bool = False,
) -> dict[str, Any]:
    """Online verification used only while changing sensitive state."""

    result = _permission_authorization(
        root,
        permission=permission,
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
        plan=plan,
        require_issuer_role=require_issuer_role,
        online=True,
        check_current_expiry=True,
    )
    if require_consumed:
        require_consumed_control(
            root,
            result,
            purpose=f"PERMISSION_ENABLE:{permission}",
            online=True,
        )
    return result


def permission_snapshot(
    root: Path,
    *,
    permission: str,
    authorization_ref: Any,
    authorization_sha256: Any,
    plan: dict[str, Any] | None,
    online: bool,
) -> dict[str, Any]:
    """Freeze or locally recheck one consumed, plan-bound permission."""

    result = _permission_authorization(
        root,
        permission=permission,
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
        plan=plan,
        online=online,
        check_current_expiry=online,
    )
    receipt, payload = require_consumed_control(
        root,
        result,
        purpose=f"PERMISSION_ENABLE:{permission}",
        online=online,
    )
    return {
        "schema_version": 1,
        "permission": permission,
        "control_id": result["event"]["control_id"],
        "purpose": receipt["purpose"],
        "authorization_ref": result["ref"],
        "authorization_sha256": result["sha256"],
        "authorization_blob_oid": receipt["authorization_blob_oid"],
        "repository_authority_sha256": receipt[
            "repository_authority_sha256"
        ],
        "consumption_sha256": hashlib.sha256(payload).hexdigest(),
        "plan_sha256": result["event"]["plan_sha256"],
        "scope_sha256": result["event"]["scope_sha256"],
    }


def _unlock_authorization(
    root: Path,
    *,
    authorization_ref: Any,
    authorization_sha256: Any,
    lock_sequence: int,
    require_issuer_role: str | None = None,
    online: bool = False,
    check_current_expiry: bool = False,
) -> dict[str, Any]:
    document, relative, path_role, event_payload = _load_event(
        Path(root),
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
    )
    if (
        set(document) != UNLOCK_EVENT_KEYS
        or document.get("schema_version") != 1
        or document.get("project_id") != _project_id(Path(root))
        or document.get("action") != "PROJECT_UNLOCK"
        or document.get("lock_sequence") != lock_sequence
        or document.get("issued_by_role") != path_role
        or document.get("issued_by_role") not in ROLES
        or type(document.get("control_id")) is not str
        or CONTROL_ID.fullmatch(document["control_id"]) is None
        or document.get("user_control") != "用户明确解锁项目"
    ):
        raise ValueError("project unlock authorization event identity is invalid")
    if check_current_expiry:
        _future_expiry(document.get("expires_at"))
    if require_issuer_role is not None and document["issued_by_role"] != require_issuer_role:
        raise ValueError("project unlock authorization issuer does not match")
    result = {
        "ref": relative,
        "sha256": authorization_sha256,
        "event": document,
        "event_payload": event_payload,
    }
    if online:
        (
            result["authorization_blob_oid"],
            result["repository_authority_sha256"],
        ) = _require_remote_main_blob(Path(root), relative, event_payload)
    return result


def validate_unlock_authorization(
    root: Path,
    *,
    authorization_ref: Any,
    authorization_sha256: Any,
    lock_sequence: int,
    require_issuer_role: str | None = None,
    require_consumed: bool = False,
) -> dict[str, Any]:
    """Online verification used only while applying an unlock transition."""

    result = _unlock_authorization(
        root,
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
        lock_sequence=lock_sequence,
        require_issuer_role=require_issuer_role,
        online=True,
        check_current_expiry=True,
    )
    if require_consumed:
        require_consumed_control(
            root,
            result,
            purpose=f"PROJECT_UNLOCK:L{lock_sequence:06d}",
            online=True,
        )
    return result


def unlock_snapshot(
    root: Path,
    *,
    authorization_ref: Any,
    authorization_sha256: Any,
    lock_sequence: int,
    online: bool,
) -> dict[str, Any]:
    """Recheck a completed unlock without reapplying its expired time window."""

    result = _unlock_authorization(
        root,
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
        lock_sequence=lock_sequence,
        online=online,
        check_current_expiry=False,
    )
    receipt, payload = require_consumed_control(
        root,
        result,
        purpose=f"PROJECT_UNLOCK:L{lock_sequence:06d}",
        online=online,
    )
    return {
        "schema_version": 1,
        "control_id": result["event"]["control_id"],
        "purpose": receipt["purpose"],
        "authorization_ref": result["ref"],
        "authorization_sha256": result["sha256"],
        "authorization_blob_oid": receipt["authorization_blob_oid"],
        "repository_authority_sha256": receipt[
            "repository_authority_sha256"
        ],
        "consumption_sha256": hashlib.sha256(payload).hexdigest(),
        "lock_sequence": lock_sequence,
    }
