"""Explicit, Git-recoverable project maintenance for research_core v1.5.0."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

import yaml


TERMINAL_STATES = {"KILLED", "INCONCLUSIVE", "SUPERSEDED", "FAILED", "ABANDONED"}
EXPLICIT_PHRASES = ("整理项目", "清理项目冗余", "项目瘦身")
PROTECTED_PREFIXES = (
    "artifacts",
    "paper",
    "research",
    "runs",
    ".research_core",
    "tools",
    "coordination/maintenance",
    "coordination/governance",
    "coordination/controls",
    "coordination/directives",
    "coordination/notices",
    "coordination/STATE.yaml",
    "coordination/NOW.md",
    "coordination/DISPATCH.yaml",
)
ALLOWED_PREFIXES = (
    "dis/plans/B",
    "dis/plans/C",
    "dis/opinions/B",
    "dis/opinions/C",
    "dis/reports",
    "coordination/dialogues",
    "coordination/deviations",
    "coordination/dispatch/archive",
    "coordination/executions",
    "coordination/supervision",
    "coordination/user-directives",
)
REQUEST_KEYS = {"schema_version", "cleanup_id", "as_of", "user_instruction", "items"}
ITEM_KEYS = {"path", "terminal_status", "terminal_at", "reason"}
ID = re.compile(r"M[0-9]{4}\Z")
GIT_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
RECENT_LIMIT = 10
MAX_ITEMS = 100
MAX_FILE_BYTES = 1024 * 1024
REQUEST_RELATIVE = "coordination/maintenance/REQUEST.yaml"
PREVIEW_RELATIVE = "coordination/maintenance/PREVIEW.yaml"


def _load_yaml(path: Path) -> dict:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return document


def _atomic_yaml(path: Path, document: dict) -> None:
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


def _exclusive_yaml(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
        stream.flush()
        os.fsync(stream.fileno())


def _git(root: Path, *arguments: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"git command failed: {detail}")
    return completed.stdout.strip()


def _safe_relative(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("invalid maintenance path")
    path = PurePosixPath(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise ValueError("invalid maintenance path")
    return path.as_posix()


def _under(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(prefix + "/")


def _parse_time(value: object, label: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError(f"invalid {label}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"invalid {label}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"invalid {label}")
    return parsed.astimezone(timezone.utc)


def _plain_path(root: Path, relative: str) -> Path:
    current = root
    for component in PurePosixPath(relative).parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("maintenance path must not contain symlinks")
    resolved = current.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError("maintenance path escaped project root")
    return current


def _load_index(root: Path) -> dict:
    document = _load_yaml(root / "coordination/maintenance/INDEX.yaml")
    if set(document) != {
        "schema_version",
        "recent",
        "buckets",
        "total_batches",
        "total_items",
    }:
        raise ValueError("invalid maintenance index")
    if document["schema_version"] != 1:
        raise ValueError("invalid maintenance index schema")
    if type(document["recent"]) is not list or len(document["recent"]) > RECENT_LIMIT:
        raise ValueError("maintenance recent index is not bounded")
    if type(document["buckets"]) is not list:
        raise ValueError("invalid maintenance buckets")
    if type(document["total_batches"]) is not int or type(document["total_items"]) is not int:
        raise ValueError("invalid maintenance totals")
    return document


def _active_dispatch(root: Path) -> bool:
    dispatch = _load_yaml(root / "coordination/DISPATCH.yaml")
    return dispatch.get("active") is not None


def _tracked_files(root: Path, relative: str) -> list[str]:
    output = _git(root, "ls-files", "--", relative)
    files = [line for line in output.splitlines() if line]
    if not files:
        raise ValueError("maintenance candidate must be tracked by Git")
    return files


def _has_external_reference(root: Path, candidate: str, candidate_files: set[str]) -> bool:
    for relative in _git(root, "ls-files").splitlines():
        if not relative or relative in candidate_files:
            continue
        if _under(relative, "coordination/maintenance"):
            continue
        path = root / relative
        if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if candidate in text:
            return True
    return False


def _validate_request(root: Path, request: dict) -> tuple[datetime, list[dict]]:
    if set(request) != REQUEST_KEYS or request.get("schema_version") != 1:
        raise ValueError("invalid maintenance request schema")
    cleanup_id = request.get("cleanup_id")
    if type(cleanup_id) is not str or ID.fullmatch(cleanup_id) is None:
        raise ValueError("invalid cleanup id")
    instruction = request.get("user_instruction")
    if type(instruction) is not str or not any(
        phrase in instruction for phrase in EXPLICIT_PHRASES
    ):
        raise ValueError("explicit cleanup request is required")
    as_of = _parse_time(request.get("as_of"), "maintenance as_of")
    items = request.get("items")
    if type(items) is not list or not items or len(items) > MAX_ITEMS:
        raise ValueError("invalid maintenance items")
    flattened: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not dict or set(item) != ITEM_KEYS:
            raise ValueError("invalid maintenance item schema")
        relative = _safe_relative(item["path"])
        if any(_under(relative, prefix) for prefix in PROTECTED_PREFIXES):
            raise ValueError("protected project content cannot be maintained")
        allowed = next(
            (prefix for prefix in ALLOWED_PREFIXES if _under(relative, prefix)),
            None,
        )
        if allowed is None or relative == allowed:
            raise ValueError("maintenance path is outside allowed history roots")
        status = item["terminal_status"]
        if status not in TERMINAL_STATES:
            raise ValueError("maintenance item requires a terminal status")
        terminal_at = _parse_time(item["terminal_at"], "terminal_at")
        if (as_of - terminal_at).total_seconds() < 30 * 24 * 60 * 60:
            raise ValueError("maintenance item must be terminal for at least 30 days")
        reason = item["reason"]
        if type(reason) is not str or not reason.strip() or len(reason) > 240:
            raise ValueError("invalid maintenance reason")
        candidate = _plain_path(root, relative)
        if not candidate.exists():
            raise ValueError("maintenance candidate is missing")
        files = _tracked_files(root, relative)
        file_set = set(files)
        if _has_external_reference(root, relative, file_set):
            raise ValueError("maintenance candidate is still referenced")
        for file_relative in files:
            if file_relative in seen:
                raise ValueError("overlapping maintenance candidates")
            seen.add(file_relative)
            path = _plain_path(root, file_relative)
            if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("maintenance only accepts bounded regular files")
            flattened.append(
                {
                    "path": file_relative,
                    "terminal_status": status,
                    "terminal_at": item["terminal_at"],
                    "reason": reason.strip(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return as_of, flattened


def preview(root: Path, request_path: Path) -> Path:
    root = Path(root).resolve(strict=True)
    request_path = Path(request_path).resolve(strict=True)
    if not request_path.is_relative_to(root):
        raise ValueError("maintenance request must be inside the project")
    if request_path.relative_to(root).as_posix() != REQUEST_RELATIVE:
        raise ValueError("maintenance request must use the canonical project path")
    if _active_dispatch(root):
        raise ValueError("project maintenance is blocked by an active dispatch")
    request = _load_yaml(request_path)
    as_of, items = _validate_request(root, request)
    source_sha = _git(root, "rev-parse", "HEAD")
    relative_request = request_path.relative_to(root).as_posix()
    document = {
        "schema_version": 1,
        "cleanup_id": request["cleanup_id"],
        "as_of": request["as_of"],
        "source_sha": source_sha,
        "request_path": relative_request,
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "user_instruction": request["user_instruction"],
        "bucket": as_of.strftime("%Y-%m"),
        "items": items,
    }
    path = root / PREVIEW_RELATIVE
    _atomic_yaml(path, document)
    return path


def _assert_clean_for_apply(root: Path, allowed: set[str]) -> None:
    for line in _git(root, "status", "--porcelain").splitlines():
        relative = line[3:].replace("\\", "/")
        if " -> " in relative:
            relative = relative.split(" -> ", 1)[1]
        if relative not in allowed:
            raise ValueError("maintenance apply requires a clean worktree")


def _remove_empty_parents(root: Path, path: Path) -> None:
    stop_roots = {root / prefix for prefix in ALLOWED_PREFIXES}
    current = path.parent
    while current not in stop_roots and current != root:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def apply(root: Path, preview_path: Path, *, explicit_user_request: bool) -> Path:
    if explicit_user_request is not True:
        raise ValueError("explicit user request confirmation is required")
    root = Path(root).resolve(strict=True)
    preview_path = Path(preview_path).resolve(strict=True)
    if not preview_path.is_relative_to(root):
        raise ValueError("maintenance preview must be inside the project")
    if preview_path.relative_to(root).as_posix() != PREVIEW_RELATIVE:
        raise ValueError("maintenance preview must use the canonical project path")
    document = _load_yaml(preview_path)
    required = {
        "schema_version",
        "cleanup_id",
        "as_of",
        "source_sha",
        "request_path",
        "request_sha256",
        "user_instruction",
        "bucket",
        "items",
    }
    if set(document) != required or document.get("schema_version") != 1:
        raise ValueError("invalid maintenance preview")
    source_sha = document["source_sha"]
    if type(source_sha) is not str or GIT_SHA.fullmatch(source_sha) is None:
        raise ValueError("invalid maintenance source SHA")
    if _git(root, "rev-parse", "HEAD") != source_sha:
        raise ValueError("maintenance preview HEAD has changed")
    request_path = root / _safe_relative(document["request_path"])
    if not request_path.is_file() or hashlib.sha256(request_path.read_bytes()).hexdigest() != document["request_sha256"]:
        raise ValueError("maintenance request changed after preview")
    _assert_clean_for_apply(
        root,
        {request_path.relative_to(root).as_posix(), preview_path.relative_to(root).as_posix()},
    )
    if _active_dispatch(root):
        raise ValueError("project maintenance is blocked by an active dispatch")
    request = _load_yaml(request_path)
    request_as_of, current_items = _validate_request(root, request)
    expected_binding = {
        "cleanup_id": request["cleanup_id"],
        "as_of": request["as_of"],
        "source_sha": source_sha,
        "request_path": REQUEST_RELATIVE,
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "user_instruction": request["user_instruction"],
        "bucket": request_as_of.strftime("%Y-%m"),
        "items": current_items,
    }
    if any(document[key] != value for key, value in expected_binding.items()):
        raise ValueError("maintenance preview binding mismatch")
    cleanup_id = document["cleanup_id"]
    bucket = document["bucket"]
    batch_path = root / f"coordination/maintenance/archive/{bucket}/{cleanup_id}.yaml"
    if batch_path.exists():
        raise FileExistsError("maintenance batch already exists")
    batch_items = []
    backups: dict[Path, bytes] = {}
    for item in document["items"]:
        path = root / item["path"]
        backups[path] = path.read_bytes()
        batch_items.append(
            {
                **item,
                "source_sha": source_sha,
                "restore_command": f"git show {source_sha}:{item['path']}",
            }
        )
    batch = {
        "schema_version": 1,
        "cleanup_id": cleanup_id,
        "applied_at": document["as_of"],
        "source_sha": source_sha,
        "user_instruction": document["user_instruction"],
        "items": batch_items,
    }
    index_path = root / "coordination/maintenance/INDEX.yaml"
    old_index = _load_index(root)
    recent_entry = {
        "cleanup_id": cleanup_id,
        "bucket": bucket,
        "batch_path": batch_path.relative_to(root).as_posix(),
        "source_sha": source_sha,
        "item_count": len(batch_items),
        "summary": "已建立可恢复索引并移出活动树",
    }
    buckets = [dict(item) for item in old_index["buckets"]]
    bucket_entry = next((item for item in buckets if item.get("bucket") == bucket), None)
    if bucket_entry is None:
        buckets.append({"bucket": bucket, "batch_count": 1})
    else:
        bucket_entry["batch_count"] = int(bucket_entry.get("batch_count", 0)) + 1
    updated_index = {
        "schema_version": 1,
        "recent": [*old_index["recent"], recent_entry][-RECENT_LIMIT:],
        "buckets": buckets,
        "total_batches": old_index["total_batches"] + 1,
        "total_items": old_index["total_items"] + len(batch_items),
    }
    _exclusive_yaml(batch_path, batch)
    try:
        _atomic_yaml(index_path, updated_index)
        for path in backups:
            path.unlink()
            _remove_empty_parents(root, path)
    except BaseException:
        for path, payload in backups.items():
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
        _atomic_yaml(index_path, old_index)
        batch_path.unlink(missing_ok=True)
        raise
    request_path.unlink(missing_ok=True)
    preview_path.unlink(missing_ok=True)
    return batch_path


def compact_view(root: Path, *, recent: int = RECENT_LIMIT) -> dict:
    if type(recent) is not int or recent < 0 or recent > RECENT_LIMIT:
        raise ValueError(f"recent must be between 0 and {RECENT_LIMIT}")
    index = _load_index(Path(root).resolve(strict=True))
    return {
        "recent": index["recent"][-recent:] if recent else [],
        "history_count": index["total_batches"],
        "item_count": index["total_items"],
        "buckets": index["buckets"],
        "history_detail_command": "maintenance show --id CLEANUP_ID",
    }


def show(root: Path, cleanup_id: str) -> dict:
    if type(cleanup_id) is not str or ID.fullmatch(cleanup_id) is None:
        raise ValueError("invalid cleanup id")
    matches = list(
        (Path(root).resolve(strict=True) / "coordination/maintenance/archive").glob(
            f"*/{cleanup_id}.yaml"
        )
    )
    if len(matches) != 1:
        raise ValueError("maintenance batch not found")
    return _load_yaml(matches[0])
