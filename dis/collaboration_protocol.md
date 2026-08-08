# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r013-20260808`
- scientific evidence snapshot: `d76e3837c43987bfdcf134ceecc5f7ff3ab9f292`
- r012 execution base: `ebf8c27eb4ff9c225be920454b7a5f013fbc5099`
- r012 server report: `dis/server_reports/orientbench-c-r012-20260807.md`
- current manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- planned manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r013.md`
- C: `dis/C.md`
- B only: `dis/B.md`
- B stage 1: `a5a94dffcc4f7c1811720b39aa87a545a10d649c`
- B stage 2 / review head: `b959a09c021ade11241aecd970c90060dbbed84f`
- protected B blob: `3181a862137918f1dd41677893937c12b3c39c28`
- current server instruction: `dis/sug.md`
- current unique server report: `dis/server_reports/orientbench-c-r013-20260808.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色与所有权

C 先审固定 SHA；是否调用 CC 由用户决定，CC 不是裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

本轮 CC 已在 r012 服务器执行前完成。严格独立性仍为 `strict_blind_independence=false / minor_redundant_exposure`。r012 服务器新证据已由 C 审核；当前不重复启动 CC，先完成直接可判定的 r013 稿件事实修订。修订通过后是否进行投稿前对抗审查由用户决定。

## r012 证据裁决

- `FAIL_PROVENANCE_R012` 被 C 采纳：FAIR1M r011 三视图 raw 仅3,896/4,362 image rows，m069完整 raw dump未持久化，Core方法门在 A0 合法停止。
- r012 没有产生 EQS fit、target label attach、bootstrap、NRC收益或HRSC确认，禁止把来源失败解释为性能失败或成功。
- r012 非 PASS 按预注册关闭当前 EQS/顶会方法线；不得重跑同门、换候选、改最小效应或用旧TTA续命。
- 服务器包总体记为 `protocol_drift`：稿件仍保留无效UCB、遗漏D_audit披露、PSC与DIOR-R引用错误；三个下游脚本仅为guard而非完整实现。
- r011 fixed-dose仍只可描述性使用；历史leave-dataset为0/6，不能包装为跨数据集支持。

## 当前服务器任务

r013只做 manuscript-only foundation repair。不得训练、推理、复算统计、加载新目标标签、修改任何历史科学资产或重新评价EQS。PASS只表示事实链和文本门通过，不表示TGRS/CVPR/ICCV-ready。

## Git

开始核对远端、分支/upstream、完整 SHA 与干净树，只允许 fast-forward。各角色仅显式暂存自有/授权文件；禁止 force、merge、rebase、reset、clean、无差别暂存。冲突或失败即停止并如实报告。
