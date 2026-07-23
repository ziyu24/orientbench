#!/usr/bin/env python3
"""Verify reduced-scope Chinese paper package for supervisor 054."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "top_journal_v3" / "docs"

PAPER = DOCS / "orientation_reliability_reduced_scope_paper_zh.md"
LATEST = DOCS / "codex_latest_report.md"

REQUIRED_DOCS = [
    DOCS / "final_reduced_scope_paper_plan_054.md",
    PAPER,
    DOCS / "negative_results_and_boundaries_054.md",
    DOCS / "conformal_risk_control_main_claim_054.md",
    DOCS / "final_claim_ledger_reduced_scope_054.md",
    LATEST,
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode not in (0, 1):
        fail(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def require_all(text: str, terms: list[str], label: str) -> None:
    missing = [term for term in terms if term not in text]
    if missing:
        fail(f"{label} missing: " + ", ".join(missing))


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_DOCS if not p.exists()]
    if missing:
        fail("missing required docs: " + ", ".join(missing))

    paper = PAPER.read_text(encoding="utf-8")
    all_054 = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in REQUIRED_DOCS)

    require_all(
        paper,
        [
            "# Orientation Reliability：面向旋转目标检测的朝向可靠性基准与风险控制",
            "## 摘要",
            "## 关键词",
            "## 1. 引言",
            "## 2. 相关工作",
            "## 3. 问题定义与指标",
            "## 4. 数据与实验协议",
            "## 5. P1：构造性解耦实验",
            "## 6. P2：Conformal Orientation Risk Control",
            "## 7. P3：PSC 机制测试",
            "## 8. P4：强不确定性基线",
            "## 9. P5：下游任务",
            "## 10. 讨论",
            "## 11. 局限性",
            "## 12. 结论",
        ],
        "paper structure",
    )

    require_all(paper, [f"图{i}" for i in range(1, 9)], "figure placeholders")
    require_all(paper, [f"表{i}" for i in range(1, 9)], "table placeholders")
    require_all(paper, ["附录 A", "附录 B", "附录 C", "附录 D", "附录 E", "附录 F", "附录 G"], "appendices")

    require_all(all_054, ["P1 partial", "P2 pass", "P3/P4 partial", "P5 fail"], "decision language")
    require_all(all_054, ["within-cell conformal orientation risk control", "frozen D_cal / D_audit"], "P2 main claim")
    require_all(all_054, ["P3 partial", "P4 partial", "P5 fail"], "negative result language")

    forbidden_positive = [
        "broader top-tier ready",
        "P3 method success",
        "PSC mechanism proven",
        "downstream utility proven",
        "NRC strictly independent",
        "full project complete",
        "detector SOTA",
        "DOTA SOTA",
        "CVPR ready",
        "TPAMI ready",
    ]
    lower_text = all_054.lower()
    for phrase in forbidden_positive:
        if phrase.lower() in lower_text:
            fail(f"forbidden positive phrase present: {phrase}")

    latest = LATEST.read_text(encoding="utf-8")
    if latest.count("👇👇👇👇👇👇") != 1 or latest.count("👆👆👆👆👆👆") != 1:
        fail("codex_latest_report does not have exactly one entry/exit wrapper")
    require_all(latest, ["054 完成", "中文论文路径", "收缩版定位", "verification/test/git"], "latest report")

    protected = git_lines(["diff", "--name-only", "--", "thresholds.yaml", "configs/thresholds.yaml"])
    protected += [p for p in git_lines(["diff", "--name-only"]) if "D_cal" in p or "D_audit" in p]
    if protected:
        fail("protected files modified: " + ", ".join(protected))

    tracked_big: list[str] = []
    for chunk in git_lines(["ls-files", "-z"]):
        for name in chunk.split("\0"):
            if not name:
                continue
            path = ROOT / name
            if path.exists() and path.is_file() and path.stat().st_size > 100_000_000:
                tracked_big.append(name)
    if tracked_big:
        fail("tracked big files detected: " + ", ".join(tracked_big[:10]))

    print("PASS verify_reduced_scope_paper_054")


if __name__ == "__main__":
    main()
