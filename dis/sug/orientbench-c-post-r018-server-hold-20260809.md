# OrientBench：r018 后服务器暂停

- status: `NO_ACTIVE_SERVER_TASK`
- last server round: `orientbench-c-r018-20260808`
- last server commit: `8ce84331a14c12a5ac41e46cb354ca712286626e`
- last server report: `dis/server_reports/orientbench-c-r018-20260808.md`
- archived r018 instruction: `dis/sug/orientbench-c-r018-20260808-server-returned.md`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- current decision owner: `C / user`

本文件是暂停标记，不是可执行服务器任务。服务器不得自行创建 r019、修 validator、重跑 bootstrap、训练、推理、重拟合、重评分、改稿或修改任何仓库文件。

## C 对 r018 的最终裁决

- 执行轨迹：服务器确实完成 A–C、生成 10 项产物、单 commit 并 push；不是早停。
- Git/provenance：采纳。r018 为单 commit、精确 10 条授权路径，`dis/B.md` blob 未变；r017 的 47 条 full-record、12 个非自引用 Git blobs、r018 frozen snapshot 与 output hashes 闭合。
- 数值分支：采纳为 `EXPLORATORY_CORE_SUPPORT_R015`。9,000 行三元域完整，support 从 Delta/CI/Holm 重算为 unit 6/6、dataset 3/3，完整冻结 gate 一致；这不是 confirmatory/deployable PASS。
- r018 收据：拒绝 `VALID_STATIC_ADJUDICATION_R018`，正式记为 `PROTOCOL_DRIFT_R018 / FAIL_AUDIT_IMPLEMENTATION_R018`。原因是必做动态验证仍实现错误却签发 VALID。
- 早停/性能：r018 不是早停，也不是 EQS 性能失败。

## 已冻结的 feature 事实

1. r012 冻结契约明确规定：association margin 只有一个候选时为 `1`、无候选时为 `0`。r018 把单候选 expected 错写为 `0`，其该项“偏差”是假阳性。
2. 冻结契约把 doubled-angle axial circular dispersion 与 `u_axis` 列为两个量；实际 sealed feature schema 没有独立 axial-dispersion 字段。该缺项是真实 implementation deviation，不能与 `u_axis` 混成一个微测试。
3. r018 的 w/h+90 测试只比较 `log_pred_ar`，未验证角特征等价；该行为保持 `unknown`。
4. 当前探索性数值来自实际 sealed features/scores，故经验数值不因意图契约缺项而消失；但不得声称已实现完整冻结 feature contract 或由 doubled-angle feature 解释收益。

## 当前科学与投稿状态

- strong-JSTARS potential、尚未 ready。
- TGRS/ISPRS JPRS 的下一判别动作是投稿级贡献、相关工作、可证伪性与实际实现边界攻击，不是继续服务器收据循环。
- HRSC 区间跨零、leave-dataset 0/6、fixed-dose descriptive-only、r014 formal failure 不变；CVPR/ICCV 不成立。
- `cc_recommendation: recommended_now`：贡献与主要证据已冻结，且新暴露的 feature-contract 偏差需要独立投稿级对抗审查。是否启动 CC 由用户决定；当前尚未启动。

## 唯一下一步

状态为 `WAITING_USER_DECISION`：等待用户决定是否启动一次投稿级 CC/B 对抗审查。用户作出决定前，服务器保持暂停，`dis/B.md` 保持 B/CC 独占，任何一方不得用本文件推断出新的执行授权。
