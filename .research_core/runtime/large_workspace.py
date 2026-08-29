"""Rebuildable large-workspace lifecycle below one mode-selected project root."""

from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any

import yaml


LEAN_LIMIT_BYTES = 100 * 1024 * 1024
PROFILE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
STATE_KEYS = {
    "schema_version",
    "project_id",
    "profile",
    "project_root",
    "workspace_root",
    "source_commit",
    "lean_limit_bytes",
    "disposable_and_rebuildable",
    "state",
    "artifacts",
    "updated_at",
}
STATE_ARTIFACT_KEYS = {"manifest_path", "manifest_sha256", "artifact_id", "output"}
STATE_OUTPUT_KEYS = {"path", "size_bytes", "sha256"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"large-workspace Git operation failed: {detail}")
    return completed.stdout.strip()


def _exact_root(root: Path) -> Path:
    root = Path(root).resolve()
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("large workspace requires the exact project root")
    return root


def _require_server(root: Path) -> None:
    from . import peer_governance

    if peer_governance.current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER manages the materialized large workspace")


def _plain_ancestor_chain(path: Path, stop: Path) -> None:
    current = path
    while True:
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            raise ValueError(f"large-workspace path is not a plain directory: {current}")
        if current == stop:
            return
        if stop not in current.parents:
            raise ValueError("large-workspace path escapes its fixed root")
        current = current.parent


def project_shm_root(
    root: Path,
    *,
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
    create: bool = False,
) -> Path:
    """Replace the leading home path with /dev/shm, preserving every component."""

    root = Path(root).resolve()
    home = Path.home().resolve() if home is None else Path(home).resolve()
    shm_root = Path(shm_root).resolve()
    if root == home or home not in root.parents:
        raise ValueError("project must be a proper descendant of the current home")
    if shm_root == home or str(shm_root) == shm_root.anchor:
        raise ValueError("invalid shared-memory root")
    relative = root.relative_to(home)
    # The host convention is literal leading-home replacement:
    # ~/zy/study/P -> /dev/shm/zy/study/P and
    # ~/cqc/study/P -> /dev/shm/cqc/study/P. The SSH login account can differ
    # from the logical zy/cqc project root and must not be inserted again.
    target = shm_root.joinpath(*relative.parts)
    _plain_ancestor_chain(target, shm_root)
    if create:
        target.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or not target.is_dir():
            raise ValueError("shared-memory project mirror is not a plain directory")
    return target


def project_materialization_root(
    root: Path,
    *,
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
    create: bool = False,
) -> Path:
    """Use only the project home root or its deterministic /dev/shm mirror.

    The host-global storage planner selects the tier.  Its choice is recorded
    only in worktree-local Git config so real host paths never enter commits.
    """

    root = Path(root).resolve()
    mirror = project_shm_root(root, home=home, shm_root=shm_root, create=False)
    completed = subprocess.run(
        ["git", "config", "--local", "--get", "cqc.large-workspace-root"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    configured = completed.stdout.strip()
    selected = Path(configured).resolve() if completed.returncode == 0 and configured else mirror
    if selected not in {root, mirror}:
        raise ValueError("large workspace root must be project home or its deterministic shm mirror")
    stop = root if selected == root else Path(shm_root).resolve()
    _plain_ancestor_chain(selected, stop)
    if create:
        selected.mkdir(parents=True, exist_ok=True)
        if selected.is_symlink() or not selected.is_dir():
            raise ValueError("large-workspace project root is not a plain directory")
    return selected


def _profile_root(
    root: Path,
    profile: str,
    *,
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
    create: bool = False,
) -> Path:
    if type(profile) is not str or PROFILE.fullmatch(profile) is None:
        raise ValueError("invalid large-workspace profile")
    materialization_root = project_materialization_root(
        root, home=home, shm_root=shm_root, create=create
    )
    parent = materialization_root / "large-workspaces"
    target = parent / profile
    _plain_ancestor_chain(target, materialization_root)
    if create:
        parent.mkdir(exist_ok=True)
        target.mkdir(exist_ok=True)
        if parent.is_symlink() or target.is_symlink():
            raise ValueError("large-workspace profile cannot use symbolic links")
    return target


def _tree_usage(path: Path, *, stop_after: int | None = None) -> int:
    total = 0
    pending = [Path(path)]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except FileNotFoundError:
            continue
        for entry in entries:
            if current == path and entry.name == ".git":
                continue
            if entry.is_symlink():
                total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                pending.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                total += entry.stat(follow_symlinks=False).st_size
            else:
                raise ValueError(f"unsupported project filesystem entry: {entry.path}")
            if stop_after is not None and total > stop_after:
                return total
    return total


def _legacy_incremental_usage(root: Path, source_head: str) -> int:
    if GIT_OID.fullmatch(source_head) is None:
        raise ValueError("legacy migration source head is invalid")
    _git(root, "cat-file", "-e", f"{source_head}^{{commit}}")
    baseline = set(
        item for item in _git(
            root, "ls-tree", "-r", "--name-only", "-z", source_head
        ).split("\0") if item
    )
    changed = set(
        item for item in _git(
            root, "diff", "--name-only", "-z", source_head, "--"
        ).split("\0") if item
    )
    total = 0
    pending = [root]
    while pending:
        current = pending.pop()
        for entry in os.scandir(current):
            if current == root and entry.name == ".git":
                continue
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            if entry.is_symlink():
                if relative not in baseline or relative in changed:
                    total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                pending.append(path)
            elif entry.is_file(follow_symlinks=False):
                if relative not in baseline or relative in changed:
                    total += entry.stat(follow_symlinks=False).st_size
            else:
                raise ValueError(f"unsupported project filesystem entry: {entry.path}")
            if total > LEAN_LIMIT_BYTES:
                return total
    return total


def lean_usage(root: Path) -> dict[str, int | bool]:
    root = Path(root).resolve()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("large workspace requires a plain project root")
    # Factory staging is deliberately validated before ``git init`` so a
    # failed generated-project self-test cannot leave repository state behind.
    # Once .git exists, retain the stronger exact-worktree-root check.
    if os.path.lexists(root / ".git"):
        root = _exact_root(root)
    source_head = None
    project_path = root / "project.yaml"
    if project_path.is_file() and not project_path.is_symlink():
        try:
            project = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError):
            project = None
        migration = project.get("migration") if type(project) is dict else None
        if (
            type(migration) is dict
            and migration.get("profile") == "IN_PLACE_HISTORY_PRESERVING"
        ):
            source_head = migration.get("source_head")
    size = (
        _legacy_incremental_usage(root, source_head)
        if source_head is not None and os.path.lexists(root / ".git")
        else _tree_usage(root, stop_after=LEAN_LIMIT_BYTES)
    )
    return {
        "size_bytes": size,
        "limit_bytes": LEAN_LIMIT_BYTES,
        "within_limit": size <= LEAN_LIMIT_BYTES,
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"plain YAML file required: {path}")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("large-workspace YAML is too large")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError("large-workspace YAML must be a mapping")
    return value


def _atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(document, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_manifest(root: Path, relative: str) -> tuple[str, Path, dict[str, Any]]:
    if type(relative) is not str or "\\" in relative:
        raise ValueError("invalid artifact manifest reference")
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or len(pure.parts) != 3
        or pure.parts[:2] != ("artifacts", "manifests")
        or pure.suffix != ".yaml"
    ):
        raise ValueError("artifact manifest must use artifacts/manifests/<id>.yaml")
    path = root.joinpath(*pure.parts)
    document = _load_yaml(path)
    try:
        from cqc_fabric.artifacts import validate_manifest

        document = validate_manifest(document)
    except (ImportError, ValueError) as error:
        raise ValueError("invalid centralized rebuildable artifact manifest") from error
    required = {
        "schema_version",
        "artifact_id",
        "kind",
        "location",
        "size_bytes",
        "sha256",
        "provenance",
        "rebuild",
        "rebuildable",
        "status",
        "deletion_note",
    }
    if set(document) != required or document.get("schema_version") != 1:
        raise ValueError("invalid rebuildable artifact manifest")
    if document.get("rebuildable") is not True:
        raise ValueError("large-workspace artifact must be rebuildable")
    rebuild = document.get("rebuild")
    if (
        type(rebuild) is not dict
        or rebuild.get("inputs_available") is not True
        or type(rebuild.get("steps")) is not list
        or not rebuild["steps"]
    ):
        raise ValueError("large-workspace rebuild inputs and steps are required")
    for command in rebuild["steps"]:
        if (
            type(command) is not list
            or not command
            or any(type(argument) is not str or not argument for argument in command)
        ):
            raise ValueError("artifact rebuild steps must be structured argv")
    location = document.get("location")
    output = PurePosixPath(str(location.get("relative_path", ""))) if type(location) is dict else PurePosixPath()
    if (
        output.is_absolute()
        or not output.parts
        or ".." in output.parts
        or "." in output.parts
        or output.parts[0] in {"_runtime", ".cqc-workspace.yaml"}
    ):
        raise ValueError("artifact output must be relative to the dedicated large workspace")
    if (
        type(document.get("size_bytes")) is not int
        or document["size_bytes"] < 0
        or type(document.get("sha256")) is not str
        or SHA256.fullmatch(document["sha256"]) is None
    ):
        raise ValueError("invalid artifact size or digest")
    return pure.as_posix(), path, document


def _state(path: Path) -> dict[str, Any]:
    document = _load_yaml(path / ".cqc-workspace.yaml")
    if (
        set(document) != STATE_KEYS
        or document.get("schema_version") != 1
        or document.get("disposable_and_rebuildable") is not True
        or document.get("state") not in {"PREPARED", "EXPANDING", "EXPANDED", "INCOMPLETE"}
        or type(document.get("project_id")) is not str
        or not document["project_id"]
        or type(document.get("profile")) is not str
        or PROFILE.fullmatch(document["profile"]) is None
        or type(document.get("project_root")) is not str
        or type(document.get("workspace_root")) is not str
        or type(document.get("source_commit")) is not str
        or GIT_OID.fullmatch(document["source_commit"]) is None
        or document.get("lean_limit_bytes") != LEAN_LIMIT_BYTES
        or type(document.get("updated_at")) is not str
        or not document["updated_at"]
        or type(document.get("artifacts")) is not list
    ):
        raise ValueError("invalid large-workspace state")
    manifests: set[str] = set()
    outputs: set[str] = set()
    artifact_ids: set[str] = set()
    for item in document["artifacts"]:
        if type(item) is not dict or set(item) != STATE_ARTIFACT_KEYS:
            raise ValueError("invalid large-workspace artifact state")
        output = item.get("output")
        if (
            type(item.get("manifest_path")) is not str
            or type(item.get("manifest_sha256")) is not str
            or SHA256.fullmatch(item["manifest_sha256"]) is None
            or type(item.get("artifact_id")) is not str
            or not item["artifact_id"]
            or type(output) is not dict
            or set(output) != STATE_OUTPUT_KEYS
            or type(output.get("path")) is not str
            or type(output.get("size_bytes")) is not int
            or output["size_bytes"] < 0
            or type(output.get("sha256")) is not str
            or SHA256.fullmatch(output["sha256"]) is None
        ):
            raise ValueError("invalid large-workspace artifact state")
        pure = PurePosixPath(output["path"])
        if pure.is_absolute() or not pure.parts or ".." in pure.parts or "." in pure.parts:
            raise ValueError("invalid large-workspace artifact output")
        if (
            item["manifest_path"] in manifests
            or output["path"] in outputs
            or item["artifact_id"] in artifact_ids
        ):
            raise ValueError("duplicate large-workspace artifact state")
        manifests.add(item["manifest_path"])
        outputs.add(output["path"])
        artifact_ids.add(item["artifact_id"])
    return document


def _validate_state_identity(root: Path, target: Path, state: dict[str, Any]) -> None:
    project = _load_yaml(root / "project.yaml")
    if (
        state["project_id"] != project.get("project_id")
        or state["profile"] != target.name
        or state["project_root"] != str(root)
        or state["workspace_root"] != str(target)
        or _git(root, "cat-file", "-e", f'{state["source_commit"]}^{{commit}}') != ""
    ):
        raise ValueError("large-workspace identity or source commit changed")


@contextmanager
def _profile_lock(parent: Path, profile: str):
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("large-workspace lock parent is invalid")
    lock_path = parent / f".{profile}.lock"
    handle = lock_path.open("a+b")
    locked = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        yield
    except OSError as error:
        raise ValueError("large-workspace profile is already locked") from error
    finally:
        try:
            if locked:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _prepare(
    root: Path,
    profile: str,
    *,
    home: Path | None,
    shm_root: Path,
) -> tuple[Path, dict[str, Any]]:
    usage = lean_usage(root)
    if usage["within_limit"] is not True:
        raise ValueError("lean project exceeds the 100 MiB working-tree limit")
    target = _profile_root(root, profile, home=home, shm_root=shm_root, create=True)
    state_path = target / ".cqc-workspace.yaml"
    if state_path.exists():
        return target, _state(target)
    project = _load_yaml(root / "project.yaml")
    source = _git(root, "rev-parse", "HEAD")
    if GIT_OID.fullmatch(source) is None:
        raise ValueError("large workspace requires an exact source commit")
    document = {
        "schema_version": 1,
        "project_id": project.get("project_id"),
        "profile": profile,
        "project_root": str(root),
        "workspace_root": str(target),
        "source_commit": source,
        "lean_limit_bytes": LEAN_LIMIT_BYTES,
        "disposable_and_rebuildable": True,
        "state": "PREPARED",
        "artifacts": [],
        "updated_at": _utc_now(),
    }
    _atomic_yaml(state_path, document)
    return target, document


def _verified_output(target: Path, document: dict[str, Any]) -> dict[str, Any] | None:
    output = PurePosixPath(document["location"]["relative_path"])
    path = target.joinpath(*output.parts)
    if path.is_symlink() or not path.is_file():
        return None
    resolved = path.resolve(strict=True)
    if target.resolve() not in resolved.parents:
        raise ValueError("artifact output escapes the dedicated large workspace")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    if size != document["size_bytes"] or digest.hexdigest() != document["sha256"]:
        return None
    return {"path": output.as_posix(), "size_bytes": size, "sha256": digest.hexdigest()}


def expand(
    root: Path,
    *,
    profile: str,
    manifests: list[str],
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    if type(manifests) is not list or not manifests or len(manifests) != len(set(manifests)):
        raise ValueError("one or more unique artifact manifests are required")
    target = _profile_root(
        root, profile, home=home, shm_root=shm_root, create=False
    )
    selected = [_safe_manifest(root, relative) for relative in manifests]
    with _profile_lock(target.parent, profile):
        return _expand_locked(
            root,
            profile=profile,
            selected=selected,
            home=home,
            shm_root=shm_root,
        )


def _expand_locked(
    root: Path,
    *,
    profile: str,
    selected: list[tuple[str, Path, dict[str, Any]]],
    home: Path | None,
    shm_root: Path,
) -> dict[str, Any]:
    target, state = _prepare(root, profile, home=home, shm_root=shm_root)
    _validate_state_identity(root, target, state)
    state_path = target / ".cqc-workspace.yaml"
    existing = {item["manifest_path"]: item for item in state["artifacts"]}
    state["state"] = "EXPANDING"
    state["updated_at"] = _utc_now()
    _atomic_yaml(state_path, state)
    try:
        for relative, path, document in selected:
            manifest_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            verified = _verified_output(target, document)
            if verified is None:
                raise ValueError(
                    "artifact output is missing or invalid; execute every manifest rebuild "
                    f"step as a guarded SERVER_PLAN command before workspace expand: {relative}"
                )
            existing[relative] = {
                "manifest_path": relative,
                "manifest_sha256": manifest_sha,
                "artifact_id": document["artifact_id"],
                "output": verified,
            }
            state["artifacts"] = [existing[key] for key in sorted(existing)]
            state["updated_at"] = _utc_now()
            _atomic_yaml(state_path, state)
    except BaseException:
        state["state"] = "INCOMPLETE"
        state["updated_at"] = _utc_now()
        _atomic_yaml(state_path, state)
        raise
    state["state"] = "EXPANDED"
    state["updated_at"] = _utc_now()
    _atomic_yaml(state_path, state)
    return status(root, profile=profile, home=home, shm_root=shm_root)


def status(
    root: Path,
    *,
    profile: str,
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
) -> dict[str, Any]:
    root = _exact_root(root)
    target = _profile_root(root, profile, home=home, shm_root=shm_root)
    usage = lean_usage(root)
    if not target.exists():
        return {
            "profile": profile,
            "state": "COMPACT",
            "project_root": str(root),
            "workspace_root": str(target),
            "lean": usage,
            "materialized_bytes": 0,
        }
    state = _state(target)
    _validate_state_identity(root, target, state)
    return {
        "profile": profile,
        "state": state["state"],
        "project_root": str(root),
        "workspace_root": str(target),
        "lean": usage,
        "materialized_bytes": _tree_usage(target),
        "artifacts": state["artifacts"],
    }


def compact(
    root: Path,
    *,
    profile: str,
    home: Path | None = None,
    shm_root: Path = Path("/dev/shm"),
) -> dict[str, Any]:
    root = _exact_root(root)
    _require_server(root)
    target = _profile_root(root, profile, home=home, shm_root=shm_root)
    if not target.exists():
        return status(root, profile=profile, home=home, shm_root=shm_root)
    with _profile_lock(target.parent, profile):
        _compact_locked(root, target)
    return status(root, profile=profile, home=home, shm_root=shm_root)


def _compact_locked(root: Path, target: Path) -> None:
    state = _state(target)
    _validate_state_identity(root, target, state)
    if state["state"] != "EXPANDED" or not state["artifacts"]:
        raise ValueError("only a fully expanded, manifest-closed workspace may be compacted")
    registered_files: set[str] = set()
    registered_directories: set[str] = {"_runtime"}
    for item in state["artifacts"]:
        relative, path, document = _safe_manifest(root, item["manifest_path"])
        if relative != item["manifest_path"]:
            raise ValueError("large-workspace manifest identity changed")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["manifest_sha256"]:
            raise ValueError("large-workspace manifest changed before compaction")
        if document["rebuild"]["inputs_available"] is not True:
            raise ValueError("large-workspace artifact is no longer rebuildable")
        verified = _verified_output(target, document)
        if (
            verified is None
            or verified != item["output"]
            or document["artifact_id"] != item["artifact_id"]
        ):
            raise ValueError("large-workspace artifact changed before compaction")
        registered_files.add(verified["path"])
        parts = PurePosixPath(verified["path"]).parts[:-1]
        for index in range(1, len(parts) + 1):
            registered_directories.add(PurePosixPath(*parts[:index]).as_posix())
    pending = [target]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            entries = list(entries)
        for entry in entries:
            relative = Path(entry.path).relative_to(target).as_posix()
            if entry.is_symlink():
                raise ValueError(f"symbolic link blocks workspace compaction: {relative}")
            if entry.is_dir(follow_symlinks=False):
                if relative == "_runtime" or relative.startswith("_runtime/"):
                    continue
                if relative not in registered_directories:
                    raise ValueError(
                        f"unregistered directory blocks workspace compaction: {relative}"
                    )
                pending.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                if relative == ".cqc-workspace.yaml" or relative.startswith("_runtime/"):
                    continue
                if relative not in registered_files:
                    raise ValueError(
                        f"unregistered file blocks workspace compaction: {relative}"
                    )
            else:
                raise ValueError(f"unsupported path blocks workspace compaction: {relative}")
    parent = target.parent
    descriptor, raw = tempfile.mkstemp(prefix=f".{target.name}-compact-", dir=parent)
    os.close(descriptor)
    tombstone = Path(raw)
    tombstone.unlink()
    os.replace(target, tombstone)
    shutil.rmtree(tombstone)
