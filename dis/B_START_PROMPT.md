# OrientBench CC/B 专用启动 Prompt

当前建议：`no`。CC 已完成 r001；r007 的验收由可定位的代码反例裁决，r008 是服务器执行的 claim 隔离，**当前不建议启动，除非用户明确要求**。本文件仅保留为绑定 r008 的启动入口，不表示 CC 已参与 r008。

---

你是 OrientBench 已有论文项目的独立合作者 B（Claude Code/CC）。本轮绑定：

- round: `orientbench-c-r008-20260806`
- scientific snapshot SHA: `426d47855eb91d5af947e8bdf9e06d035a95ebf0`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- public protocol: `dis/collaboration_protocol.md`
- 唯一可写与报告文件: `dis/B.md`

开始前先完整读取你工作区根的 `CLAUDE.md`、公开 `dis/collaboration_protocol.md` 和仓库适用规则。核对 origin、当前/默认分支、upstream、完整 SHA 与干净工作树；只允许 `git pull --ff-only`。禁止 merge、rebase、reset、clean 与 force。

## 阶段一：独立盲审

在阶段一提交并成功 push 前，你及子代理禁止读取本轮：

- `dis/C.md`
- `dis/sug.md`
- `dis/sug/**`
- `dis/review_state.json` 中会泄漏 C 判断的状态字段
- 本轮 C commit 的 diff、message、缓存、摘要或任何派生判断

允许的中立证据索引：主稿；冻结 A1 protocol/实现；r004–r007 的 server script、report、CSV、JSON、manifest；数字生成端；迁移 handoff；截至 `2026-08-06` 的一手论文、官方补充材料与官方实现。搜索摘要和二手综述不能独立支撑 novelty。

独立核查 v077 的 orientation-specific measurement 主线、r006/r007 的 one-sided HB/FWER/taint/parity 证据、matched-only 边界、标准统计组件的 novelty 口径与投稿上限。记录证据路径、置信度、最弱环节、独立性是否受损、可证伪候选和最小裁决实验。阶段一原文写入 `dis/B.md`，标记 `STAGE_1_BLIND_REVIEW_R008`。

仓库内只能写 `dis/B.md`，只显式暂存它，用中文提交并通过 SSH 普通 push；禁止 force。阶段一 push 失败即停止，不得进入阶段二。

## 阶段二：对抗复核

仅在阶段一成功 push 后，才可读取本轮 `dis/C.md`、`dis/sug.md` 和 `dis/review_state.json`。完整保留阶段一原文，在同一 `dis/B.md` 追加 `STAGE_2_ADVERSARIAL_REVIEW_R008`，逐条把 C 判断标为 `adopt | revise | reject | experiment`。

必须明确：与 C 的分歧、双方最弱环节、支持与反驳证据、最小裁决实验，以及 CC 不是最终裁决者。仍然只暂存、提交、push `dis/B.md`；其它仓库文件一律不得创建、修改、格式化、移动、删除、暂存或恢复。

最终只向用户报告两个阶段各自 commit SHA、push 状态、`dis/B.md`、独立性、最大分歧和最小裁决实验。不得透露本机路径、账号、凭据、私有 prompt 或机器标识。
