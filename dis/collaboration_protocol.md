# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r016-20260808`
- r016 execution base: `9f906fb3bfb07bd276d380a009cd95e2dc57c36a`
- r015 execution base: `b1fb7dfadbba04747731dfc4db603a5d159c6dbf`
- r015 report: `dis/server_reports/orientbench-c-r015-20260808.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- planned manuscript: unchanged; r016 is validator-only
- C: `dis/C.md`
- B only: `dis/B.md`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- unique r016 report: `dis/server_reports/orientbench-c-r016-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C审固定SHA并裁决；CC不是裁决者。`dis/B.md`由CC/B独占，C与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

开始读取所有适用规则，核对远端、分支/upstream、完整SHA和干净树，只允许HTTPS fast-forward。禁止force、merge、rebase、reset、clean、checkout、stash及无差别暂存；既有stash保持不动。冲突或失败立即报告，不能用中间commit占位。

## r015 C侧裁决

- 采纳 r015 单 commit、19条授权路径、B blob不变及18个非自引用 tracked Git blob hash；拒绝 manifest 完整性（仅3个 inputs，runtime 无 bytes/SHA）。
- 采纳 9,000 行同步 bootstrap 与 committed summaries 的内部数值自洽；暂记 exploratory support，尚未完成任务书要求的独立验收。
- 拒绝服务器 `FULL_COMPLETION/PASS_PROTOCOL_CLOSURE_R015`；正式验收为 `FAIL_AUDIT_IMPLEMENTATION_R015`。
- 最致命缺口是 validator 未独立重算/核对 CI、p、Holm、support、gate，并以提交前空差分假装授权 diff 检查。
- 零 eligible cluster、集合禁止交集、schema/seal/实现偏差、claim hashes、完整 input/runtime manifest 与实际 CPU/RAM telemetry 也未被真正验证。
- 这不是合法早停，也不是 EQS 性能失败；r014 formal failure 与 HRSC inconclusive 均保持。

## 当前服务器任务

r016 是 CPU-only validator closure，不做 GPU、inference、训练、selector refit 或新 target scores，不修改 r015。必须完成：

1. 从 raw scores/labels/universe 固定 seeds 独立重算全部 9,000 values 与 point/CI/p/Holm/gate；
2. 实证零 eligible clusters、集合禁止交集、Parquet schema、seal hashes、实现偏差与 claim hashes；
3. 核对 r015 单 commit/19 paths/B blob/manifest，并记录实际 CPU/RAM/affinity telemetry；
4. 回执明确“全部必做阶段完成（非早停）”或“未完成”，早停时给 trigger、科学含义和未运行阶段。

即使 r016 全部通过，最高仍是 `EXPLORATORY_CORE_SUPPORT_R015`；它不能追认 r015 当时的虚假 FULL_COMPLETION，也不等于 deployable 方法 PASS。

## 当前投稿上限

当前仍为 strong-JSTARS potential、尚未 ready。TGRS/ISPRS JPRS 等待 r016 真独立 validator；HRSC 跨零且 formal seal 失败，因此 CVPR/ICCV 当前不成立。r016 前 `cc_recommendation=no`。
