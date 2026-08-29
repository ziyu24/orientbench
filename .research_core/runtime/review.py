from __future__ import annotations

from pathlib import Path

from .context import _read_project_file


REQUIRED_FIELDS = (
    "name",
    "failure_mode",
    "question",
    "evidence_scope",
    "stop_condition",
)
TRIGGERS = (
    "SELECT",
    "FREEZE",
    "INTERPRET",
    "RESOURCE",
    "SUBMIT",
    "PUBLISH",
    "选择",
    "冻结",
    "解释",
    "扩大",
    "资源",
    "主张",
    "投稿",
    "发布",
)


def recommendation(task: str, state: dict) -> str | None:
    combined = f"{task} {state.get('next_action', '')}"
    if any(token in combined for token in TRIGGERS) or bool(state.get("risks")):
        return "TASK_ADAPTIVE_REVIEW_RECOMMENDED"
    return None


def context_bundle(
    root: Path,
    *,
    task: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    if not task.strip():
        raise ValueError("task 不得为空")
    evidence = [
        {"path": relative, "content": _read_project_file(Path(root).resolve(), relative)}
        for relative in evidence_refs or []
    ]
    return {
        "composition_rules": {
            "role_count": "usually_2_to_4_not_fixed",
            "required_fields": list(REQUIRED_FIELDS),
            "separate_passes_do_not_prove_independence": True,
        },
        "task": task,
        "evidence": evidence,
    }


def parse_role(value: str) -> dict[str, str]:
    parts = value.split("|")
    if len(parts) != len(REQUIRED_FIELDS) or any(not part.strip() for part in parts):
        raise ValueError("review-role 必须包含五个非空字段并以 | 分隔")
    return dict(zip(REQUIRED_FIELDS, (part.strip() for part in parts)))
