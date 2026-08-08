# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r015-20260808`
- r015 execution base: `b60dee50cefd8dee055bef166d2165b22c4490a8`
- r014 intermediate commit: `e0b91ea83974ce6259149df02f1705e8f5421c39`
- r014 report: `dis/server_reports/orientbench-c-r014-20260808.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md`
- planned manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- C: `dis/C.md`
- B only: `dis/B.md`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- unique r015 report: `dis/server_reports/orientbench-c-r015-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C审固定SHA并裁决；CC不是裁决者。`dis/B.md`由CC/B独占，C与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

开始读取所有适用规则，核对远端、分支/upstream、完整SHA和干净树，只允许HTTPS fast-forward。禁止force、merge、rebase、reset、clean、checkout、stash及无差别暂存；既有stash保持不动。冲突或失败立即报告，不能用中间commit占位。

## r014 C侧裁决

- 采纳FAIR修复：4,362/4,362 images、78,644 GT、488,194 identity predictions及official AP parity。
- 采纳HRSC实际结果为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`，不得换单元续命。
- 拒绝服务器 `FULL_COMPLETION/PASS_DEPLOYABLE_EQS_R014`；正式裁决为 `protocol_drift / FAIL_PROTOCOL_R014`。
- 最致命缺口是prelabel seal仅含features/models/scores，未含protocol与全部执行代码；代码最终Git身份晚于target运行，不能事后恢复confirmatory seal。
- dataset aggregates使用不同unit seeds后按列平均，不是同dataset共享cluster multiplicity；3/3 formal aggregate无效。
- validator消费CSV/JSON多于从raw独立重算；r014稿仍让2016 RICNN承担DIOR来源。
- r014数值不是性能FAIL，只能暂记strong exploratory positive candidate。

## 当前服务器任务

r015是CPU-only协议闭合，不做GPU、inference、训练、selector refit或新target scores。只读r014 runtime，完成：

1. Git/代码/prelabel seal/label access法证；
2. 从完整D_audit image/mother universe进行同dataset共享cluster multiplicity的1,000次同步bootstrap；
3. 独立集合泄漏、feature实现和动态validator；
4. 新建r015稿，将Core降为exploratory，保留HRSC不确定，并修正DIOR基础论文与AOPG/DIOR-R一手来源。

即使重算数字满足旧阈值，最高只能是 `EXPLORATORY_CORE_SUPPORT_R015`；审计成功状态 `PASS_PROTOCOL_CLOSURE_R015`只表示证据与稿件闭合，不等于deployable方法PASS。

## 当前投稿上限

当前仍为strong-JSTARS potential、尚未ready。TGRS/ISPRS JPRS在r015同步重算和稿件降级后重评；HRSC跨零且formal seal失败，因此CVPR/ICCV当前不成立。新证据出现前 `cc_recommendation=no`。
