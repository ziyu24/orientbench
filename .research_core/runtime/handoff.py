from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess

import yaml

from .context import read_project_file, select_context
from .peer_governance import current_worker, load_dispatch, validate_plan
from .state import validate_state
from .workstreams import checkpoint_paths


INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
HANDOFF_ID = re.compile(r"H([0-9]{6})[.]yaml\Z")
ROLES = {"B", "C", "SERVER"}


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True,
        text=True, encoding="utf-8", check=False, shell=False,
    )
    if completed.returncode != 0 or Path(completed.stdout.strip()).resolve() != root:
        raise ValueError("Git handoff requires the exact repository root")
    return root


def _git(root: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
    try:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, capture_output=True, text=True,
            encoding="utf-8", check=False, shell=False, timeout=30,
            env=environment,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("Git handoff command timed out") from error
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "Git handoff command failed")
    return completed.stdout.strip()


def _role(root: Path) -> str:
    role = current_worker(root, allow_host_default=False)["role"]
    normalized = {"PEER_B": "B", "PEER_C": "C", "SERVER": "SERVER"}.get(role)
    if normalized is None:
        raise ValueError("Git handoff requires a bound B, C, or SERVER role")
    return normalized


def _exclusive_yaml(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError("handoff directory must not be a symlink")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def record_requirement(
    root: Path,
    *,
    to_role: str,
    summary: str,
    related_instruction_id: str | None,
) -> dict[str, object]:
    """Append a role-owned requirement that must be committed before handoff."""

    root = _root(root)
    from_role = _role(root)
    target = str(to_role).upper()
    if target not in ROLES or target == from_role:
        raise ValueError("handoff target must be a different B, C, or SERVER role")
    if type(summary) is not str or len(summary.strip()) < 12 or "\x00" in summary:
        raise ValueError("handoff summary must contain at least 12 characters")
    if related_instruction_id is not None and (
        type(related_instruction_id) is not str
        or INSTRUCTION_ID.fullmatch(related_instruction_id) is None
    ):
        raise ValueError("handoff instruction id is invalid")
    directory = root / "coordination" / "handoffs" / from_role
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("role handoff directory is unavailable")
    paths = sorted(path for path in directory.iterdir() if HANDOFF_ID.fullmatch(path.name))
    expected = list(range(1, len(paths) + 1))
    actual = [int(HANDOFF_ID.fullmatch(path.name).group(1)) for path in paths]
    if actual != expected:
        raise ValueError("role handoff sequence is not contiguous")
    sequence = len(paths) + 1
    handoff_id = f"H{sequence:06d}"
    document: dict[str, object] = {
        "schema_version": 1,
        "handoff_id": handoff_id,
        "from_role": from_role,
        "to_role": target,
        "summary": summary.strip(),
        "related_instruction_id": related_instruction_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    path = directory / f"{handoff_id}.yaml"
    _exclusive_yaml(path, document)
    return {**document, "path": path.relative_to(root).as_posix()}


def verify_git_finalization(
    root: Path, *, allow_local_test_remote: bool = False
) -> dict[str, object]:
    """Fail until the role worktree is clean and its legal branch is on origin."""

    root = _root(root)
    role = _role(root)
    status = _git(root, "status", "--porcelain=v1")
    if status:
        raise ValueError("Git handoff blocked by uncommitted or dirty project content")
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if role in {"B", "C"} and branch != "main":
        raise ValueError("B/C must integrate completed work and requirements into main")
    if role == "SERVER" and branch != "main" and re.fullmatch(r"exec/r[0-9]{3,}", branch) is None:
        raise ValueError("SERVER completion must use main or a short-lived exec/rNNN")
    origin = _git(root, "remote", "get-url", "origin")
    push_origin = _git(root, "remote", "get-url", "--push", "origin")
    if (
        (not origin.startswith("https://") or not push_origin.startswith("https://"))
        and not allow_local_test_remote
    ):
        raise ValueError("Git handoff production origin must use HTTPS")
    local_commit = _git(root, "rev-parse", "HEAD")
    remote_output = _git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    lines = [line.split() for line in remote_output.splitlines() if line.strip()]
    if len(lines) != 1 or len(lines[0]) != 2:
        raise ValueError("Git handoff branch is unpushed or remote ref is unavailable")
    remote_commit = lines[0][0]
    if remote_commit != local_commit:
        raise ValueError("Git handoff is unpushed or remote ref does not match local HEAD")
    return {
        "status": "GIT_FINALIZED",
        "role": role,
        "branch": branch,
        "local_commit": local_commit,
        "remote_commit": remote_commit,
        "origin": origin,
        "push_origin": push_origin,
    }


def resume_bundle(root: Path, *, evidence_refs: list[str] | None = None) -> dict[str, object]:
    root = Path(root).resolve()
    errors = validate_state(root)
    if errors:
        raise ValueError("; ".join(errors))
    worker = current_worker(root)
    files = select_context(root, evidence_refs=evidence_refs)
    state = __import__("yaml").safe_load(files["coordination/STATE.yaml"])
    if state.get("active_workstream") is not None:
        for path in checkpoint_paths(root, state["active_workstream"]):
            relative = path.relative_to(root).as_posix()
            files[relative] = read_project_file(root, relative)
    active = load_dispatch(root)["active"]
    if active is not None:
        validate_plan(root, active["plan_path"])
        files[active["plan_path"]] = read_project_file(root, active["plan_path"])
    return {
        "worker_id": worker["worker_id"],
        "role": worker["role"],
        "authority": "coordination/DISPATCH.yaml",
        "files": dict(sorted(files.items())),
    }
