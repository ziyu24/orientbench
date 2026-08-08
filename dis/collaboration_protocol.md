# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r014-20260808`
- control parent: `61eb65ea4c56e15829031f79e57773b1a370269f`
- r012 server commit: `d76e3837c43987bfdcf134ceecc5f7ff3ab9f292`
- r012 server report: `dis/server_reports/orientbench-c-r012-20260807.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- planned manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md`
- C: `dis/C.md`
- B only: `dis/B.md`
- B stage 1: `a5a94dffcc4f7c1811720b39aa87a545a10d649c`
- B stage 2 / review head: `b959a09c021ade11241aecd970c90060dbbed84f`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- current unique server report: `dis/server_reports/orientbench-c-r014-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色、所有权与 Git

C 先审固定 SHA；是否调用 CC 由用户决定，CC 不是裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

开始读取所有上级/当前 `AGENTS.md`，核对远端、分支/upstream、完整 SHA 与干净树，只允许 HTTPS fast-forward。各角色仅显式暂存自有/授权文件；禁止 force、merge、rebase、reset、clean与无差别暂存。冲突或失败即停止并如实报告。

## r012 证据的精确含义

- r012 是 `INCOMPLETE_EARLY_STOP`：A0 触发后未执行fit、target label attach、bootstrap、EQS gate或HRSC。
- 科学 trigger 是 `FAIL_PROVENANCE_R012`：FAIR raw只有3,896/4,362 image rows；这不是EQS性能失败，EQS与HRSC均为 `NOT_EVALUATED`。
- 当时没有HRSC不造成FAIR失败；现在HRSC可用也不修复FAIR、不替代Core。
- r012提交的下游脚本是guard/placeholder，不能表述为“完整实现但未运行”。稿件仍有失效UCB、D_audit披露与引用问题。
- r011 fixed-dose只可描述性使用；历史leave-dataset为0/6，不能包装为跨数据集支持。

## 服务器完成语义

服务器进程退出或按规则早停不等于“执行完毕”。

- 最终首行 `执行完毕`：全部无条件任务与实际分支必需任务完成，得到可判定Core结果，并完成稿件、manifest、validator、范围核验、commit和push。Core PASS时HRSC必须实际完成；Core非PASS时按条件记 `NOT_RUN_CORE_NOT_PASS`。
- 最终首行 `未执行完毕`：任何provenance/implementation/environment/resource/protocol问题导致提前停止，Core PASS后HRSC未完成，或稿件/validator/commit/push未完成。

报告必须分开 `execution_completion`、`scientific_verdict`、`last_completed_phase`、`early_stop_trigger`、`unrun_required_phases`、`core_status`、`hrsc_status` 与 `push_status`。来源早停只能是 provenance 失败；只有完整有效统计执行后才能判 EQS 性能 FAIL/INCONCLUSIVE。

## 当前服务器任务

用户授权 r014 作为新证据轮次，不回改 r012。先穷尽查找或用冻结 FAIR/24 config/checkpoint/split/threshold/NMS 做 identity/h/v full forward，闭合4,362-image universe；再按原冻结协议完整执行 Core-6 EQS。

主门：unit support至少4/6，每项 `Delta_NRC>=0.02`、CI lower>0、Holm-6通过；覆盖三数据集与至少两detector families；FAIR必须support；dataset aggregate 3/3通过；SODA按mother scene。只有Core PASS后才执行预指定HRSC2016/LSKNet独立确认。不得换gate、换selector、换split或用HRSC续命。

当前真实级别仍是 strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS依赖r014基础修复与EQS/HRSC证据，CVPR/ICCV尚未达到。新服务器证据出现前 `cc_recommendation=no`。
