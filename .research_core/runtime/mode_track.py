"""One-way work-track activation without rewriting project creation identity."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
from typing import Any

import yaml


TARGET_FILES = {
    "PAPER_REPRODUCTION": {
        "research/REPRODUCTION.md": (
            "# 论文复现轨道\n\n"
            "只记录论文来源、官方代码/配置、数据子集、验收指标和差异。\n"
        ),
    },
    "CHAT_HANDOFF": {
        "research/HANDOFF.md": (
            "# 聊天交接轨道\n\n"
            "只记录已确认事实、待验证事项、来源和唯一下一步。\n"
        ),
        "research/raw/README.md": (
            "# 原始交接材料\n\n原始材料不是证据；使用前必须核验。\n"
        ),
    },
}
REQUEST_ID = re.compile(r"MT[0-9]{4,}\Z")


def _mode_path(root: Path) -> Path:
    root = Path(root).resolve()
    path = root / ".research_core/mode.yaml"
    if (
        (root / ".research_core").is_symlink()
        or path.is_symlink()
        or not path.is_file()
    ):
        raise ValueError("project mode record is missing")
    return path


def _new_overlay_path(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    path = root.joinpath(*Path(relative).parts)
    for parent in (path.parent, *path.parents):
        if parent == root:
            break
        if parent.exists() and parent.is_symlink():
            raise ValueError(f"track overlay parent is a symbolic link: {relative}")
    resolved = path.resolve(strict=False)
    if root not in resolved.parents:
        raise ValueError(f"track overlay escapes project: {relative}")
    return path


def _load(root: Path) -> dict[str, Any]:
    document = yaml.safe_load(_mode_path(root).read_text(encoding="utf-8"))
    if (
        type(document) is not dict
        or document.get("mode") != "NEW_RESEARCH"
        or document.get("origin_mode") != "NEW_RESEARCH"
        or document.get("active_track") != "NEW_RESEARCH"
        or document.get("allowed_next_tracks")
        != ["PAPER_REPRODUCTION", "CHAT_HANDOFF"]
        or document.get("reverse_transition_allowed") is not False
    ):
        raise ValueError("only an untransitioned NEW_RESEARCH project can change track")
    project = yaml.safe_load((Path(root) / "project.yaml").read_text(encoding="utf-8"))
    if type(project) is not dict or project.get("mode") != "NEW_RESEARCH":
        raise ValueError("immutable project creation mode is not NEW_RESEARCH")
    return document


def _digest(document: dict[str, Any]) -> str:
    payload = {key: value for key, value in document.items() if key != "preview_digest"}
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def preview(root: Path, target: str, *, request_id: str) -> dict[str, Any]:
    root = Path(root).resolve()
    mode = _load(root)
    if target not in TARGET_FILES:
        raise ValueError("target track must be PAPER_REPRODUCTION or CHAT_HANDOFF")
    if type(request_id) is not str or REQUEST_ID.fullmatch(request_id) is None:
        raise ValueError("track request id must use MTdddd")
    for relative in TARGET_FILES[target]:
        if _new_overlay_path(root, relative).exists():
            raise ValueError(f"track overlay already exists: {relative}")
    project = yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
    result = {
        "schema_version": 1,
        "project_id": project.get("project_id"),
        "request_id": request_id,
        "origin_mode": mode["origin_mode"],
        "from_track": mode["active_track"],
        "to_track": target,
        "created_paths": sorted(TARGET_FILES[target]),
        "updated_path": ".research_core/mode.yaml",
        "registry_identity_changes": False,
        "reverse_transition_allowed": False,
        "required_confirmation": "批准创建",
    }
    result["preview_digest"] = _digest(result)
    return result


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text if text.endswith("\n") else text + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply(
    root: Path,
    target: str,
    *,
    request_id: str,
    preview_digest: str,
    confirmation: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if confirmation != "批准创建":
        raise ValueError("track activation requires exact confirmation: 批准创建")
    expected = preview(root, target, request_id=request_id)
    if preview_digest != expected["preview_digest"]:
        raise ValueError("track preview digest changed; preview again")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    if status.returncode != 0 or status.stdout:
        raise ValueError("track activation requires a clean project worktree")
    mode = _load(root)
    mode["active_track"] = target
    mode["allowed_next_tracks"] = []
    # Create new overlay files first, then atomically publish the mode change.
    created: list[Path] = []
    try:
        for relative, content in TARGET_FILES[target].items():
            path = _new_overlay_path(root, relative)
            if path.exists():
                raise ValueError(f"track overlay already exists: {relative}")
            _atomic_text(path, content)
            created.append(path)
        _atomic_text(
            _mode_path(root),
            yaml.safe_dump(mode, allow_unicode=True, sort_keys=False),
        )
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return {
        "status": "TRACK_ACTIVATED",
        "origin_mode": "NEW_RESEARCH",
        "active_track": target,
        "created_paths": expected["created_paths"],
        "registry_identity_changes": False,
    }
