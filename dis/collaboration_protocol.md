# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r017-20260808`
- r017 execution base: `097f5829abd0159e38dd3312dae84833ca36ade1`
- r016 execution base: `beffd3046ec13ca21bc729534b96602c3b0f5390`
- r016 report: `dis/server_reports/orientbench-c-r016-20260808.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- planned manuscript: unchanged; r017 only corrects evidence indexes
- C: `dis/C.md`
- B only: `dis/B.md`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- unique r017 report: `dis/server_reports/orientbench-c-r017-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C审固定SHA并裁决；CC不是裁决者。`dis/B.md`由CC/B独占，C与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

开始读取所有适用规则，核对远端、分支/upstream、完整SHA和干净树，只允许HTTPS fast-forward。禁止force、merge、rebase、reset、clean、checkout、stash及无差别暂存；既有stash保持不动。冲突或失败立即报告，不能用中间commit占位。

## r016 C侧裁决

- 采纳 r016 单 commit、10条授权路径、B blob不变与9个非自引用输出 blob。
- 采纳 r016 raw 9,000 同步复算为 `EXPLORATORY_CORE_SUPPORT_R015`；仍非confirmatory/deployable。
- 拒绝 `FULL_COMPLETION/PASS_R015_VALIDATOR_CLOSURE_R016`；正式验收为 `PROTOCOL_DRIFT_R016 / FAIL_AUDIT_IMPLEMENTATION_R016`。
- 最致命缺口是未读取并独立复算完整 gate，却签发 VALID；zero check恒真、manifest/telemetry不实、novelty verified_source仍有根页/占位页。
- 这不是早停或性能失败；r014 formal failure、r015历史失败与HRSC inconclusive均保持。

## 当前服务器任务

r017 是 static/low-CPU receipt，不重跑 bootstrap，不做 GPU、inference、训练、selector refit 或新 target scores。必须完成：

1. 静态验证9,000 key全集、summary metadata与完整冻结gate；
2. 输出zero-eligible集合SHA、canonical split、schema与源码行witness；
3. 修正claim ledger headings和novelty matrix两处无效verified_source；
4. 用真实access log生成input manifest，不再制造CPU/worker telemetry。

最高仍为 `EXPLORATORY_CORE_SUPPORT_R015`；r017 不追认 r016 的虚假 FULL_COMPLETION，也不等于 deployable 方法 PASS。

## 当前投稿上限

当前仍为 strong-JSTARS potential、尚未 ready。TGRS/ISPRS JPRS 尚需 r017 后投稿级贡献攻击；HRSC 跨零且 formal seal 失败，因此 CVPR/ICCV 当前不成立。r017 前 `cc_recommendation=no`。
