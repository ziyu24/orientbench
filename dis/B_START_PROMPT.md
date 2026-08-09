# OrientBench CC/B 专用启动状态

- `round_id: orientbench-cc-post-r018-20260809`
- `user_authorized: true`
- `authorization_date: 2026-08-09`
- `launch_state: READY_FOR_CC_STAGE_1`
- `review_base_sha: 48a770327919aaf3270f802962501689a969653d`
- `scientific_evidence_cutoff: 8ce84331a14c12a5ac41e46cb354ca712286626e`
- `paper_entry: top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- `only_writable_path: dis/B.md`
- `server_status: NO_ACTIVE_SERVER_TASK`

这是仓库内 CC/B 阶段合约，不是历史 r012 指令的延续，也不把 CC 设为最终裁决者。用户已明确授权本轮投稿级碰撞；CC 拉取当前 HTTPS `main` 后立即按下列两阶段执行，不再等待 C 或用户重复确认。

## 0. 启动与所有权门

1. 完整读取 CC 所在工作区的上级/当前 `AGENTS.md`、本地 `CLAUDE.md` 与本文件；核对 HTTPS 远端、`main`、upstream、完整 HEAD、index 和工作树。已存在仓库只允许 fast-forward；冲突、脏树、远端或所有权不符即停止并如实报告。
2. CC/B 只可追加 `dis/B.md`。不得修改、暂存、恢复或提交任何其他路径；不得运行训练、bootstrap、服务器任务、稿件改写或 validator 修复。
3. 本轮必须保留现有 `dis/B.md` 历史内容。新内容使用本文件指定的唯一阶段标题追加，不得覆盖或回写历史阶段。
4. 科学结论为负、venue 降级或贡献被杀死，仍可构成 `FULL_COMPLETION`；只有必做阶段未完成、证据不可访问、工作树/远端不安全或 push 未完成时，才可报 `EARLY_STOP` 或 `FAILED`，并须说明停止点和已完成/未完成项。

## 1. 阶段一：投稿级独立盲审

### 1.1 盲审隔离

形成阶段一完整文本前，只读以下材料：适用规则、本文件、当前主稿、主稿引用的一手论文，以及仓库中 `dis/` 之外的代码、配置、数据索引和科学产物。阶段一 commit 成功推送前，禁止读取：

- `dis/C.md`
- `dis/review_state.json`
- `dis/collaboration_protocol.md`
- `dis/sug.md` 与 `dis/sug/**`
- `dis/server_reports/**`
- Git 历史中上述 C/服务器材料的旧版本

形成阶段一文本时也不得读取既有 `dis/B.md` 内容。先在当前会话内完成并冻结阶段一文字；仅在追加落盘前读取 `dis/B.md` 以保护既有内容，且不得因看到历史 B 内容而修改已冻结的阶段一判断。若当前 CC 会话在本轮开始前已接触任何禁读材料或当前 C 结论，仍继续完成，但必须将 `strict_blind_independence: false` 并逐项披露 exposure；不得伪装独立。

### 1.2 审查目标

最多采用三个真正改变结论的视角，直接攻击：

1. 去掉 deployability、HRSC 独立确认和未实现 doubled-angle axial feature 后，稿件还剩下什么不可替代的科学贡献；是否只是治理流程或已有 calibration/selective-prediction 的重包装。
2. 当前实际 sealed implementation、探索性 6/6 unit + 3/3 dataset、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only 与稿件措辞是否一致；哪些 claim 会被审稿人一击否决。
3. 最近一手工作、可证伪性、负迁移、外部不确定性和读者价值是否足以支撑 TGRS/ISPRS JPRS；给出 strong-JSTARS、TGRS/ISPRS JPRS、CVPR/ICCV 的真实上限，不为目标 venue 反向包装。

每个实质发现必须保存：严重度、原始证据路径/行号或一手来源、结论、置信度、最弱环节、反证条件，以及是否需要实验。不得伪造首创；没有证据时写 unknown。阶段一必须明确回答：

- 最致命问题是什么；
- 当前主稿是否可投、可投何处；
- TGRS/ISPRS JPRS 的最小充分修正或最小杀死条件；
- 是否存在一个真正能改变 venue 的唯一后续证据，还是应停止实验并转写。

### 1.3 阶段一落盘门

将冻结文本追加到 `dis/B.md`，标题必须恰为：

`# CC_POST_R018_STAGE_1_BLIND_REVIEW`

标题下记录 `round_id`、`review_base_sha`、`scientific_evidence_cutoff`、`strict_blind_independence`、`prior_material_exposure` 与实际读取材料清单。只显式暂存 `dis/B.md`，单独中文 commit，并通过 HTTPS 推送 `main`。阶段一 commit 未成功推送，阶段二绝对不得开始。

## 2. 阶段二：读取 C 后的对抗复核

阶段一推送成功后，重新核对 HEAD/远端/工作树，再读取当前 `dis/C.md`、`dis/review_state.json`、`dis/collaboration_protocol.md`、相关 r018 报告与必要科学证据。阶段一原文逐字保留，不得回改。

逐条覆盖 C 的所有实质结论，至少包括 r018 完成语义、receipt/protocol drift、探索性 6/6 + 3/3 的证据资格、single-candidate margin、缺失 axial feature、w/h+90 unknown、稿件/novelty 边界和 venue ceiling。每条只可归为 `adopt | revise | reject | experiment`，并给独立证据、置信度和反证条件；同时列出 B 独有发现、C 独有发现、双方收敛项与残余分歧。

将阶段二追加到 `dis/B.md`，标题必须恰为：

`# CC_POST_R018_STAGE_2_ADVERSARIAL_RECONCILIATION`

只显式暂存 `dis/B.md`，第二个独立中文 commit，并通过 HTTPS 推送 `main`。不得捎带修改其他文件。

## 3. CC 最终回报字段

完成后向用户一次性报告：

- `task_execution: FULL_COMPLETION | EARLY_STOP | FAILED`
- 阶段一、阶段二完整 commit SHA 与各自 push 状态
- `strict_blind_independence` 及 exposure
- 是否真的完成本文件全部必做项；若没有，准确列出未完成项
- 最致命问题、真实 venue ceiling、唯一下一步

负面科学裁决不是早停。不得把“脚本/阅读结束”冒充“两阶段合约全部完成”，也不得自行新建服务器 r019。
