# OrientBench 最小跨机器协作协议

## 当前锚点

- state: `READY_FOR_CC_STAGE_1`
- CC round: `orientbench-cc-post-r018-20260809`
- user authorization: `true` (`2026-08-09`)
- CC review base: `48a770327919aaf3270f802962501689a969653d`
- evidence cutoff: `8ce84331a14c12a5ac41e46cb354ca712286626e`
- r018 control parent: `40679c9e3a5a94de61f4e078e1fad437b2b461b7`
- r018 report: `dis/server_reports/orientbench-c-r018-20260808.md`
- archived r018 instruction: `dis/sug/orientbench-c-r018-20260808-server-returned.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- C: `dis/C.md`
- B only: `dis/B.md`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- server status: `NO_ACTIVE_SERVER_TASK`
- server hold marker: `dis/sug.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C 审固定 SHA 并裁决；CC 不是最终裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只能写被有效 `dis/sug.md` 明确授权的路径；当前 hold 文件不提供任何写入授权。

开始前读取所有适用规则，核对 HTTPS 远端、分支/upstream、完整 SHA、工作树和 index，只允许 fast-forward。禁止 force、merge、rebase、reset、clean、checkout、stash 及无差别暂存；冲突或失败立即报告。

## r018 C 侧裁决

- 执行轨迹采纳：Phase A–C、10 项产物、单 commit 与 push 完成；不是早停或性能失败。
- Git/provenance 采纳：r017 full records/Git blobs、r018 snapshot/output hashes 和 B blob 全部闭合。
- 数值采纳为实际 sealed implementation 的 `EXPLORATORY_CORE_SUPPORT_R015`：unit 6/6、dataset 3/3；仍非 confirmatory/deployable。
- 拒绝 `VALID_STATIC_ADJUDICATION_R018`；正式状态为 `PROTOCOL_DRIFT_R018 / FAIL_AUDIT_IMPLEMENTATION_R018`。
- 冻结 single-candidate margin 应为 1，r018 的 expected=0 是假偏差；真实偏差是 sealed schema 缺少独立 doubled-angle axial dispersion；w/h+90 角等价仍 unknown。
- claim/novelty/稿件边界的当前内容经独立复核可采纳。

## 当前服务器与投稿状态

服务器暂停，不得自行创建 r019、修 validator、重跑实验或改稿。机械收据循环结束。

当前为 strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS 转入投稿级贡献/相关工作/实际实现边界攻击。HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、r014 formal failure 不变；CVPR/ICCV 不成立。

## CC 状态

用户已明确授权，当前为 `READY_FOR_CC_STAGE_1`。唯一启动入口是 `dis/B_START_PROMPT.md`，唯一可写路径是 `dis/B.md`；C、服务器及其他角色继续不得触碰 `dis/B.md`。

阶段一先完成投稿级独立盲审，在形成完整文本和判断前禁读当前 C、review state、collaboration protocol、sug、server reports 与这些材料的 Git 历史；冻结文字后才可为追加保护读取既有 B，并必须披露任何先验 exposure。阶段一单独 commit 且成功推送后，阶段二才可读取 C，逐条以 `adopt | revise | reject | experiment` 对抗复核，再以第二个只含 `dis/B.md` 的 commit 推送。CC 不是最终裁决者。

负面科学裁决、venue 降级或“贡献不成立”均可为 `FULL_COMPLETION`，不是早停。只有必做阶段未做完、证据/仓库状态不安全或 push 未完成时才可报 `EARLY_STOP/FAILED`，并必须列明完成项、停止点和未完成项。

服务器仍为 `NO_ACTIVE_SERVER_TASK`，不得自行创建 r019，也不得把 CC 碰撞改造成新的 validator 或训练轮次。
