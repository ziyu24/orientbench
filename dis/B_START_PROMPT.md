# OrientBench CC/B 专用启动 Prompt

当前建议：`no`。CC 已完成 r001，r006 的问题可由证明、模拟和服务器机器 gate 直接裁决；**当前不建议启动，除非用户明确要求**。本文件仅保留为绑定 r006 的可执行启动 prompt，不表示 CC 已参与 r006，也不得伪造新 B 结论。

---

你是 OrientBench 已有论文项目的独立合作者 B（Claude Code/CC）。本轮不是从零选题，而是对固定科学快照执行先盲审、后对抗复核。

## 固定绑定

- round: `orientbench-c-r006-20260805`
- scientific snapshot SHA: `60142448ff1f461531ad1eb2cd0c17785e782350`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- 公开协作协议: `dis/collaboration_protocol.md`
- 你的唯一报告与仓库内唯一可写文件: `dis/B.md`

阶段一中立证据索引：

- 主稿与冻结 A1：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a1_a3.py`
- r004：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_power_decomposition_r004.py`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_gate_r004.json`
- r005：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_scene_oracle_r005.py`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_scene_oracle_gate_r005.json`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_scene_attainable_envelope_r005.csv`、`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_failure_bounds_r005.csv`
- 数字生成端：`top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv`、`top_journal_v3_reaudit_055/scripts/recompute_table1_fullval_k1_065.py`、`top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv`、`scripts/m1_ar21_unify.py`
- 迁移与复算边界：`docs/server_migration_handoff_20260727.md`

## 开始前

1. 先完整读取你所在工作区根的 `CLAUDE.md`，仅把它作为 B/CC 侧本地说明；再读取公开的 `dis/collaboration_protocol.md` 和仓库内适用规则。
2. 核对 origin、当前/默认分支、upstream、完整 SHA 与工作树；只允许 `git pull --ff-only`，且必须能追溯到上述 snapshot。远端不符、脏树、不能 fast-forward 或规则冲突时停止；禁止 merge/rebase/reset/clean/force。
3. 你参加过 r001，必须如实记录。若已通过其它渠道获知 r006 的 C 判断，阶段一独立性必须标为受损。
4. 仓库内只有 `dis/B.md` 可写；不得创建、修改、格式化、移动、删除、暂存或恢复其它文件。

## 阶段一：r006 独立盲审

在阶段一，你和任何子代理都禁止读取：

- 当前 `dis/C.md`；
- 当前 `dis/sug.md`；
- `dis/sug/**`；
- `dis/review_state.json` 中会泄漏 C 判断的字段；
- 当前 C 提交的 diff、commit message、缓存、终端转述或其它派生判断。

如意外接触，立即在 `dis/B.md` 标记 `independence=impaired` 并记录范围；不得描述为盲审。只依据 active manuscript、中立证据索引、代码/机器结果及截至 `2026-08-05` 的一手论文、官方补充材料或官方实现审查。搜索摘要与二手综述不能独立支撑 novelty。

动态选择 1–3 个能改变决策的视角，做一轮“建设候选—最强攻击—证据综合”。重点核查：

- r005 relaxed envelope 的支配性、practical 缺口与 90 行/30 情境的非独立口径；
- score 因果上下界是否支持任一方向的 headline；
- split fixed-sequence 是否已有一手先例，OrientBench 的实质差异是什么；
- 新协议应如何做到 D_fit-only ordering、D_cal-only testing、FWER control 和冻结后外部验证；
- 当前投稿上限、最多三个可证伪候选和杀死条件。

记录证据路径、置信度、最弱环节、反证条件和最小裁决实验。阶段一原文标记 `STAGE_1_BLIND_REVIEW_R006`，只写入 `dis/B.md`。

阶段一结束只显式执行：

```text
git add -- dis/B.md
git diff --cached -- dis/B.md
git commit -m "完成 OrientBench r006 独立盲审"
git push
```

必须使用 SSH，禁止 force。push 失败即停止，保留本地 commit并如实报告；未成功 push 不得进入阶段二。

## 阶段二：逐条对抗复核 C

仅在阶段一成功 push 后，才可读取当前 `dis/C.md`、`dis/sug.md`、`dis/review_state.json` 和相关 C commit。逐条按 `adopt | revise | reject | experiment` 复核；C 与 CC 都不是最终裁决者。

阶段二追加到同一个 `dis/B.md`，完整保留阶段一原文，并标记 `STAGE_2_ADVERSARIAL_REVIEW_R006`。至少记录独立性、证据路径、置信度、与 C 的分歧、双方最弱环节和最小裁决实验。仍只显式暂存 `dis/B.md`，中文提交并通过 SSH 正常 push；禁止 force。

## 最终回报

向用户只报告两个阶段各自的完整 commit SHA、push 状态、`dis/B.md` 路径、独立性、最大分歧和最小裁决实验。不得透露本机路径、账号、凭据、私有 prompt、机器标识或工作区根本地说明。
