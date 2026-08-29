from __future__ import annotations

from pathlib import Path
import re


WORKSTREAM_ID = re.compile(r"W[0-9]{4}\Z")
CHECKPOINT_FILES = ("STATE.yaml", "RESUME.md", "evidence.md", "decisions.md")


def checkpoint_paths(root: Path, workstream_id: str) -> list[Path]:
    if WORKSTREAM_ID.fullmatch(workstream_id) is None:
        raise ValueError("active_workstream 必须为 Wdddd")
    base = Path(root) / "coordination/workstreams" / workstream_id
    return [base / name for name in CHECKPOINT_FILES]


def checkpoint_errors(root: Path, workstream_id: str | None) -> list[str]:
    if workstream_id is None:
        return []
    if type(workstream_id) is not str:
        return ["active_workstream 必须为 null 或 Wdddd"]
    try:
        paths = checkpoint_paths(root, workstream_id)
    except ValueError as error:
        return [str(error)]
    return [
        f"工作流检查点缺失: {path.relative_to(root).as_posix()}"
        for path in paths
        if not path.is_file()
    ]
