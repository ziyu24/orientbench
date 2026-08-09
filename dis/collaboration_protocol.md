# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r018-20260808`
- r018 execution base: `b349dcbd44685eae66bdabbdf7a795493ccdc08e`
- r017 execution base: `942a5a2cb7e78e8b8ef9d447a6bcd449c590c017`
- r017 report: `dis/server_reports/orientbench-c-r017-20260808.md`
- archived r017 instruction: `dis/sug/orientbench-c-r017-20260808-server-returned.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- planned manuscript: unchanged；r018 禁止改稿
- C: `dis/C.md`
- B only: `dis/B.md`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- unique r018 report: `dis/server_reports/orientbench-c-r018-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C 审固定 SHA 并裁决；CC 不是最终裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

开始读取所有适用规则，核对 HTTPS 远端、分支/upstream、完整 SHA、工作树和 index，只允许 fast-forward。禁止 force、merge、rebase、reset、clean、checkout、stash 及无差别暂存；既有 stash 保持不动。冲突或失败立即报告，不能用中间 commit 占位。

## r017 C 侧裁决

- r017 的脚本、产物、commit 和 push 确实完成；它不是早停，也不是 EQS 性能失败。
- 采纳单 commit、13 条授权路径、B blob 不变、12 个非自引用输出和 tracked input blobs。
- 采纳当前表内 unit 6/6、dataset 3/3 为 `EXPLORATORY_CORE_SUPPORT_R015`；仍非 confirmatory/deployable。
- 采纳 claim/novelty/稿件边界索引；不改正文和科学数字。
- 拒绝 `FULL_COMPLETION/PASS_STATIC_RECEIPT_R017`；正式状态为 `PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`。
- 决定性缺口是三元 key 未验、support/gate 不独立、source metadata 冒充已比较、feature sentinel witness 自相矛盾，以及 manifest wrapper bypass 后只比较路径。

## 当前服务器任务

r018 是终结型 static/low-CPU adjudication：

1. 验证 `(level,key,dataset,replicate)` 全域，并从 Delta/CI/Holm 重新判 support 与完整 gate；缺失的 r016 summary metadata 必须写 `SOURCE_FIELD_ABSENT`，不能硬补。
2. 保存 canonical set/intersection count+SHA；以可执行微测试核对 sentinel、w/h+90°、0/90、tie-break 等 feature contract，并做逐文件 schema/seal witness。
3. 把 r017 manifest 当普通输入，逐条全字段核对 access records；从 Git blob 核对 r017 范围与输出。
4. 明确区分 r018 是否完整执行、r017 历史负裁决、探索性数值采纳和早停意义。负验证结果也可以在全部阶段完成时诚实回报 `执行完毕`。

禁止重跑 bootstrap、GPU、训练、推理、refit、新 scores、改稿、换 gate 或覆盖历史。r018 成功 token 只表示裁决收据有效；服务器不得自行生成 r019。

## 当前投稿上限与 CC

当前仍为 strong-JSTARS potential、尚未 ready。TGRS/ISPRS JPRS 尚需 r018 后的一次投稿级贡献攻击；HRSC 跨零、leave-dataset 0/6、formal seal 失败使 CVPR/ICCV 不成立。

`cc_recommendation: no`。r018 是有明确反证条件的本地静态修复；在新服务器证据出现前不重复调用 CC。
