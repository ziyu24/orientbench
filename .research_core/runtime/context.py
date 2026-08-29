from __future__ import annotations

from pathlib import Path, PurePosixPath


def read_project_file(root: Path, relative: str) -> str:
    root = Path(root).resolve()
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
        raise ValueError("context reference escapes project")
    path = root.joinpath(*posix.parts)
    if not path.is_file() or root not in path.resolve().parents:
        raise ValueError(f"context reference missing or unsafe: {relative}")
    return path.read_text(encoding="utf-8")


def select_context(root: Path, *, evidence_refs: list[str] | None = None) -> dict[str, str]:
    selected = {}
    for relative in (
        "project.yaml",
        "coordination/NOW.md",
        "coordination/STATE.yaml",
        "coordination/DISPATCH.yaml",
        "coordination/governance/WORKERS.yaml",
        "coordination/governance/ROLE_CONTRACT.md",
    ):
        selected[relative] = read_project_file(root, relative)
    for relative in evidence_refs or []:
        selected[relative] = read_project_file(root, relative)
    return selected


_read_project_file = read_project_file
