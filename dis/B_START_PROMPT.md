# OrientBench CC/B 专用启动 Prompt

当前建议：`no`。CC 已完成历史轮次；r009 的关键分歧已有代码、统计和主稿反例，当前应先由 Luna-high 执行 r010，**当前不建议启动，除非用户明确要求**。本文件仅保留为绑定 r010 的启动入口，不表示 CC 已参与 r010。

---

你是 OrientBench 已有论文项目的独立合作者 B（Claude Code/CC）。本轮绑定：

- round: `orientbench-c-r010-20260806`
- scientific snapshot SHA: `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md`
- neutral r009 server evidence: `dis/server_reports/orientbench-c-r009-20260806.md`
- public protocol: `dis/collaboration_protocol.md`
- 唯一可写与报告文件: `dis/B.md`

开始前完整读取你工作区根 `CLAUDE.md`、公开 `dis/collaboration_protocol.md` 和仓库适用规则。核对 origin、当前/默认分支、upstream、完整 SHA 与干净工作树，只允许 `git pull --ff-only`；禁止 merge/rebase/reset/clean/force。

## 阶段一：独立盲审

在阶段一提交并成功 push 前，你及子代理禁止读取本轮：

- `dis/C.md`
- `dis/sug.md`
- `dis/sug/**`
- `dis/review_state.json` 中会泄漏 C 判断的字段
- 本轮 C commit 的 diff、message、缓存、摘要或任何派生判断

不得通过 Git 历史、搜索、转述或子代理恢复禁读内容。若意外接触，必须在报告中标记独立性受损。

允许的中立证据：v079；r009 的代码、CSV/JSON、manifest 和服务器报告；其数字生成端；冻结 A1/A4 协议；截至 `2026-08-06` 的一手论文、官方补充材料或官方实现。搜索摘要和二手综述不能独立支撑 novelty。

盲审 r009 是否真的完成 independent evaluator、paired AP bootstrap、三轨 risk/survival、baseline-cohort AR mechanism、claim ledger 和主稿闭环；检查 v079 的 formal quarantine、fixed-dose 主线、post-NMS/GT-directed/symmetric 边界与投稿上限。记录证据路径、置信度、最弱环节、反证、独立性、可证伪候选和最小裁决实验。阶段一原文写入 `dis/B.md`，标记 `STAGE_1_BLIND_REVIEW_R010`。

仓库内唯一可写 `dis/B.md`；只显式暂存它，用中文 commit，通过 SSH 普通 push。阶段一 push 失败即停止，不得进入阶段二。

## 阶段二：对抗复核

仅在阶段一 push 成功后，才可读取本轮 `dis/C.md`、`dis/sug.md` 和 `dis/review_state.json`。完整保留阶段一原文，在同一文件追加 `STAGE_2_ADVERSARIAL_REVIEW_R010`，逐条把 C 判断标为 `adopt|revise|reject|experiment`。

必须记录：与 C 的分歧、双方最弱环节、支持/反驳路径、置信度、独立性是否受损，以及最小裁决实验；明确 CC 不是最终裁决者。仍只暂存、提交、push `dis/B.md`，禁止触碰其它文件，禁止 force。

最终只向用户报告两个阶段各自 commit SHA、push 状态、`dis/B.md`、独立性、最大分歧和最小裁决实验，不得透露本机路径、账号、凭据、私有 prompt 或机器标识。
