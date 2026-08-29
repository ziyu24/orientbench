from __future__ import annotations

from pathlib import Path

from .peer_governance import current_worker
from .storage import write_text_atomic


def _author(root: Path) -> str:
    worker = current_worker(root)
    if worker["role"] == "SERVER":
        raise ValueError("SERVER cannot author scientific recommendations")
    return f"{worker['worker_id']} / {worker['role']}"


def append_recommendation(
    root: Path,
    *,
    summary: str,
    rationale: str,
    uncertainty: str,
    evidence: list[str],
    alternatives: list[str] | None = None,
    review_roles: list[str] | None = None,
    unresolved_conflicts: list[str] | None = None,
) -> str:
    path = Path(root) / "coordination/RESEARCH_LOG.md"
    text = path.read_text(encoding="utf-8")
    number = text.count("\n## LOG") + 1
    entry = (
        f"\n## LOG{number:04d} · PEER_RECOMMENDATION\n\n"
        f"- 作者：{_author(root)}\n"
        f"- 建议：{summary}\n"
        f"- 理由：{rationale}\n"
        f"- 不确定性：{uncertainty}\n"
        f"- 备选方案：{', '.join(alternatives or []) if alternatives else '无'}\n"
        f"- 证据引用：{', '.join(evidence) if evidence else '无'}\n"
        f"- 审查角色：{', '.join(review_roles) if review_roles else '无'}\n"
        f"- 未解决冲突：{'; '.join(unresolved_conflicts) if unresolved_conflicts else '无'}\n"
    )
    write_text_atomic(path, text.rstrip() + "\n" + entry, overwrite=True)
    return f"LOG{number:04d}"


def append_event(root: Path, *, event_type: str, summary: str, source_refs: list[str]) -> str:
    path = Path(root) / "coordination/RESEARCH_LOG.md"
    text = path.read_text(encoding="utf-8")
    number = text.count("\n## LOG") + 1
    entry = (
        f"\n## LOG{number:04d} · {event_type}\n\n"
        f"- 作者：{_author(root)}\n"
        f"- 摘要：{summary}\n"
        f"- 来源引用：{', '.join(source_refs) if source_refs else '无'}\n"
    )
    write_text_atomic(path, text.rstrip() + "\n" + entry, overwrite=True)
    return f"LOG{number:04d}"
