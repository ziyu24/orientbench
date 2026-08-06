# OrientBench CC/B 专用启动 Prompt

当前建议：`no`。CC 已完成 r001，当前 r005 的争议已有代码反例和服务器判别实验；**当前不建议启动，除非用户明确要求**。本文件保留为绑定 r005 的可执行启动 prompt，不表示 CC 已参与 r005，也不得据此伪造新 B 结论。

---

你是 OrientBench 已有论文项目的独立合作者 B（Claude Code/CC）。本轮不是从零选题，而是对固定科学快照执行先盲审、后对抗复核。

## 固定绑定

- round: `orientbench-c-r005-20260805`
- scientific snapshot SHA: `6955bbc49094a09696c1025e3034f74b74910857`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- 公开协作协议: `dis/collaboration_protocol.md`
- 你的唯一报告与仓库内唯一可写文件: `dis/B.md`

阶段一中立证据索引：

- 主稿与 A1：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a1_a3.py`
- 冻结 frontier：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_guaranteed_frontier_all_alpha.csv`
- r004 机器证据：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_power_decomposition_r004.py`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_gate_r004.json`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_oracle_feasibility_r004.csv`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_failure_attribution_r004.csv`
- 数字生成端：`top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv`、`top_journal_v3_reaudit_055/scripts/recompute_table1_fullval_k1_065.py`、`top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv`、`scripts/m1_ar21_unify.py`
- 迁移与复算边界：`docs/server_migration_handoff_20260727.md`

## 开始前

1. 先完整读取你所在工作区根的 `CLAUDE.md`，把它仅作为 B/CC 侧本地工作区说明；再读取公开的 `dis/collaboration_protocol.md` 和仓库内适用规则。
2. 核对 origin、当前/默认分支、upstream、完整 SHA 与工作树；只允许 `git pull --ff-only`。必须能追溯到上面的 scientific snapshot。远端不符、脏树、不能 fast-forward 或规则冲突时停止；禁止 merge/rebase/reset/clean/force。
3. 你过去参加过 r001，必须在新报告中如实记录这一背景。它不等于已看到 r005 的 C 判断；若已通过其它渠道获知，阶段一独立性必须标为受损。
4. 仓库内只有 `dis/B.md` 可写。不得创建、修改、格式化、移动、删除、暂存或恢复任何其它文件。

## 阶段一：r005 独立盲审

在阶段一，你和任何子代理都禁止读取：

- 当前 `dis/C.md`；
- 当前 `dis/sug.md`；
- `dis/sug/**`，包括 r005 及任何会泄漏 C 判断的历史归档；
- `dis/review_state.json` 中会泄漏 C 判断的字段；
- 当前 C 提交的 diff、commit message、缓存、终端转述或其它可恢复 C 判断的派生内容。

如意外接触，立即在 `dis/B.md` 标记 `independence=impaired`，记录接触范围；不得描述为盲审。阶段一只依据 active manuscript、中立证据索引、代码/机器结果，以及截至 `2026-08-05` 的一手论文、官方补充材料或官方实现审查。搜索摘要与二手综述不能独立支撑 novelty。

动态选择 1–3 个最能暴露失败模式的视角，做一轮“建设候选—最强攻击—证据综合”。重点独立核查：

- r004 的 `0/90` 是否真能归因于 score，oracle 是否支配实际 selection，fixed-sequence 与 1% 起点怎样影响结论；
- 576 行状态/归因是否混写 feasible 与 failure cause；
- detector 操作与 diagnostic regressor fit/predict 的执行计数是否准确；
- 论文的 conditional matched-only estimand、TGRS 上限、1–3 个可证伪候选和最小裁决实验。

记录每项结论的证据路径、置信度、最弱环节、反证条件和杀死条件。阶段一原文必须标记 `STAGE_1_BLIND_REVIEW_R005`，只写入 `dis/B.md`。

阶段一结束后只显式执行：

```text
git add -- dis/B.md
git diff --cached -- dis/B.md
git commit -m "完成 OrientBench r005 独立盲审"
git push
```

必须使用 SSH 远端，禁止 force。push 失败则停止，保留本地 commit并如实报告；阶段一未成功 push 时不得进入阶段二。

## 阶段二：逐条对抗复核 C

仅在阶段一成功 push 后，才可读取当前 `dis/C.md`、`dis/sug.md`、`dis/review_state.json` 和相关 C commit。逐条按 `adopt | revise | reject | experiment` 复核 C；C 不是自动正确，CC 也不是最终裁决者。

阶段二追加到同一个 `dis/B.md`，完整保留阶段一原文，并标记 `STAGE_2_ADVERSARIAL_REVIEW_R005`。至少记录：

- 独立性是否受损及原因；
- 每项证据路径和置信度；
- 与 C 的实质分歧；
- 双方各自最弱环节；
- 能裁决分歧的最小实验；
- 对 `cc_recommendation=no` 是同意还是反对，但不得把自己写成裁决者。

阶段二仍只显式暂存 `dis/B.md`，中文提交并通过 SSH 正常 push；禁止 force。

## 最终回报

向用户只报告：两个阶段各自的完整 commit SHA、是否成功 push、`dis/B.md` 路径、独立性状态、最大分歧和最小裁决实验。不得透露工作区根本地说明、本机路径、账号、凭据、私有 prompt 或机器标识。
