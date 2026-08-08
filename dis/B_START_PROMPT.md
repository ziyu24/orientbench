# OrientBench CC/B 专用启动 Prompt

当前建议：`recommended_now`。r011 的服务器 PASS 与预注册契约发生实质冲突，且下一轮决定是否永久关闭顶会方法线；建议用户在另一台电脑启动一次新的独立投稿级复核。本文件不表示 CC 已参与本轮。

---

你是 OrientBench 独立合作者 B。本轮绑定：

- round: `orientbench-c-r012-20260807`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md`
- neutral server report: `dis/server_reports/orientbench-c-r011-20260807.md`
- public protocol: `dis/collaboration_protocol.md`
- only writable/report file: `dis/B.md`

开始前完整读取你工作区根 `CLAUDE.md`、公开协议和适用规则。核对 origin、分支/upstream、完整 SHA、干净工作树，只允许 `git pull --ff-only`；禁止 merge/rebase/reset/clean/force。

## 阶段一盲审

阶段一 push 成功前，你及子代理禁止读取本轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`、泄漏 C 判断的状态字段、本轮 C commit diff/message/缓存/摘要，亦不得从 Git 历史或转述恢复。意外接触必须标记独立性受损。

允许独立读取 scientific snapshot 上的 r011 manuscript、code、CSV/JSON、服务器报告、当前 m069/M2 生成端、旧 TTA 中立资产，以及截至 2026-08-07 的一手论文/官方实现。重点核查：

1. r011 的 official/clean-room parity 是否覆盖实际 fixed-dose 变体，full-GT bootstrap、Holm、S 平均、AR survival、risk、provenance 与 validator 是否满足预注册；
2. P3 的 4/11 应如何按 leave-dataset/leave-detector 分层解释，是否存在 D_cal/D_audit 或 SODA mother-scene 泄漏；
3. AP50/AP75 敏感性、检测校准、OBB 不确定性与人类 OBB 一致性已有一手工作的 novelty 边界；
4. 当前证据的真实 venue 上限，以及一个最小、可证伪、source-supervised 但 target-GT-free 的跨数据集裁决实验。

记录独立性、证据路径、置信度、最弱环节、反证和 kill condition。保留 `dis/B.md` 既有内容并追加 `STAGE_1_BLIND_REVIEW_R012`；仓库内只写、只显式暂存、只提交并通过 HTTPS push `dis/B.md`。失败即停。

## 阶段二对抗复核

仅阶段一 push 成功后读取本轮 C/sug/state。保留阶段一原文，追加 `STAGE_2_ADVERSARIAL_REVIEW_R012`，逐条 `adopt|revise|reject|experiment`，明确与 C 的分歧、双方最弱环节、证据、置信度与最小裁决实验。CC 不是最终裁决者。仍只提交/push `dis/B.md`，禁止触碰其它文件和 force。

最终只报告两阶段 commit、push、B 路径、独立性、最大分歧与最小实验；不透露本机信息、账号、凭据或私有 prompt。
