# OrientBench 最小跨机器协作协议

## 当前锚点

- state: `READY_FOR_SERVER_R019`
- evidence/head: `f53bb670dea92dca9c0056e20c0cd338d0e52c14`
- scientific data cutoff: `8ce84331a14c12a5ac41e46cb354ca712286626e`
- CC round: `orientbench-cc-post-r018-20260809`
- CC stage 1: `ce6e894377fa881f897c9c2952076461fba2df34`
- CC stage 2: `f53bb670dea92dca9c0056e20c0cd338d0e52c14`
- CC status: `COMPLETED / strict_blind_independence=false`
- protected B blob: `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- server round: `orientbench-c-r019-20260809`
- server instruction: `dis/sug.md`
- unique server report: `dis/server_reports/orientbench-c-r019-20260809.md`

跨机器共享只通过仓库，不写账号、机器标识、凭据、本地绝对路径或 C 侧私有规则。

## 角色与所有权

C 固定科学问题和 gate，并在服务器回报后裁决；CC 不是最终裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。r019 期间其 blob 必须保持上列值。

服务器只可写 `dis/sug.md` 明列的 r019 路径。活动稿、C、review state、collaboration protocol、B start、r014-r018、threshold、split、旧 runtime 和其它项目资产均只读。开始前核对 HTTPS 远端、main、完整 HEAD、upstream、index 和工作树，只允许 fast-forward；禁止 merge/rebase/reset/clean/checkout/stash/force。

## CC 验收

两阶段仓库产物完整，均只改 B；阶段一 exposure 已披露，故可作有效对抗审查但不称严格盲审。新服务器证据出现前 `cc_recommendation: no`，不得重复碰撞。

## r019 双落锁

r019 是 corrected `EQS-RC-R019` 在 DOTA-v1.0 一个数据集、两个 detector-family 单元上的前瞻 endpoint evaluation，不是 r012 HRSC 独立确认替补，也不是两个数据集确认。

服务器必须先在完全不读取 DOTA GT/旧 matched labels 的情况下完成代码、production 微测、source-only fit、DOTA raw/features/scores、mother map、bootstrap draws 与 manifest，并以 prelabel commit 推送远端。只有远端确认该 commit 后，才允许 label attach、统计和第二个 final commit。prelabel 字节不得回改。

负面科学结果不是早停。只有 label reveal 前的 provenance、prior-outcome、mother-map、实现测试或 prelabel push 等硬失败可触发 `EARLY_STOP`；source LODO/盲态功效只作诊断，没有早停或改 gate 权力。一旦揭盲，必须完成两个 unit、aggregate、validator、报告与 push。不得用 HRSC、tile bootstrap、legacy selector 或新数据集救场，不得创建 r020 换 gate 续命。

## 投稿解释

当前 strong-JSTARS potential、尚未 ready，TGRS/ISPRS JPRS conditional。r019 PASS 只显著增强 strong-journal 证据，不自动保证顶刊或重开 CVPR/ICCV；FAIL/INCONCLUSIVE 后停止服务器实验并转 measurement/diagnostic 稿。
