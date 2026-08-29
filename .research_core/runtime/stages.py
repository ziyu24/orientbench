from __future__ import annotations

from pathlib import Path

from .storage import write_text_atomic


SURVEY = """# 研究进展调研

## 范围

## 当前进展矩阵

| 方向 | 方法 | 证据 | 局限 | 候选问题 |
| --- | --- | --- | --- | --- |

## 未选候选问题
"""

FOCUS = """# 聚焦问题

## 选定问题

## 选择理由

## 主要反证条件

## 已知风险与下一步
"""

SIMPLE_STAGE_FILES = {
    "tasks": (
        "tasks/README.md",
        "# 任务\n\n仅记录经授权、可恢复的研究任务。\n",
    ),
    "experiments": (
        "experiments/INDEX.yaml",
        "schema_version: 1\nexperiments: []\n",
    ),
    "failures": (
        "failures/REGISTRY.yaml",
        "schema_version: 1\nfailures: []\n",
    ),
    "reviews": (
        "reviews/README.md",
        "# 评审\n\n仅索引正式评审及其处置。\n",
    ),
    "paper": (
        "paper/README.md",
        "# 论文\n\n论文资产仅在研究主张具备证据后初始化。\n",
    ),
}


def initialize(root: Path, stage: str) -> Path:
    mapping = {
        "survey": (Path(root) / "research/SURVEY.md", SURVEY),
        "focus": (Path(root) / "research/FOCUS.md", FOCUS),
    }
    mapping.update(
        {
            name: (Path(root) / relative, content)
            for name, (relative, content) in SIMPLE_STAGE_FILES.items()
        }
    )
    if stage not in mapping:
        raise ValueError("unsupported stage")
    path, content = mapping[stage]
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise FileExistsError(path)
        return path
    if stage == "focus" and not (Path(root) / "research/SURVEY.md").is_file():
        raise ValueError("survey required before focus")
    write_text_atomic(path, content, overwrite=False)
    return path
