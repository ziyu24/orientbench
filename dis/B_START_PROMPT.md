# OrientBench CC/B 专用启动 Prompt

当前建议：`no`。r010 的实现错误已有直接代码反例；当前先执行 r011，**不建议启动，除非用户明确要求**。本文件只保留绑定 r011 的入口，不表示 CC 已参与。

---

你是 OrientBench 独立合作者 B。本轮绑定：

- round: `orientbench-c-r011-20260807`
- scientific snapshot: `c62ea3514e98f76baf557c22a5dd0ef812d84ee0`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md`
- neutral server report: `dis/server_reports/orientbench-c-r010-20260806.md`
- public protocol: `dis/collaboration_protocol.md`
- only writable/report file: `dis/B.md`

开始前完整读取你工作区根 `CLAUDE.md`、公开协议和适用规则。核对 origin、分支/upstream、完整 SHA、干净工作树，只允许 `git pull --ff-only`；禁止 merge/rebase/reset/clean/force。

## 阶段一盲审

阶段一 push 成功前，你及子代理禁止读取本轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`、泄漏 C 判断的状态字段、本轮 C commit diff/message/缓存/摘要，亦不得从 Git 历史或转述恢复。意外接触必须标记独立性受损。

允许 v080、r010 code/CSV/JSON/report、当前 m069/M2 生成端、旧 P3 中立资产及截至2026-08-07的一手论文/官方实现。独立核查 evaluator、full-GT bootstrap、S/D、AR survival、provenance，以及 P1+P3 的 supervision/leakage/deployability边界。记录证据路径、置信度、最弱环节、反证和最小实验。原文写入 `dis/B.md`，标记 `STAGE_1_BLIND_REVIEW_R011`；只暂存/中文提交/HTTPS push该文件。失败即停。

## 阶段二对抗复核

仅阶段一 push成功后读取本轮 C/sug/state。保留阶段一原文，追加 `STAGE_2_ADVERSARIAL_REVIEW_R011`，逐条 `adopt|revise|reject|experiment`，明确分歧、双方最弱环节、证据、置信度与最小裁决实验。CC不是最终裁决者。仍只提交/push `dis/B.md`，禁止触碰其它文件和force。

最终只报告两阶段commit、push、B路径、独立性、最大分歧与最小实验，不透露本机信息、账号、凭据或私有prompt。
