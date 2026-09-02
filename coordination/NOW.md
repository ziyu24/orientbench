# 当前状态

- 阶段：`R002_FAILED_ACCEPTANCE_B_REVIEWED`。
- 权威发布：HTTPS 远端 `main` 与 `exec/r002-evidence-closeout-repair-final` 均为 `8236d149b02268135485f1076bb6c0fdd3c74a55`。
- 机器结果：`coordination/executions/r002/RESULT.yaml` 与 `coordination/supervision/r002/SUPERVISION.yaml` 均记录 `FAILED_ACCEPTANCE`；正式科学状态为 `INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE`。不得把该轮包装成通过验收的 KILL。
- 决定性阻塞：FAIR1M-D 原 r002 cohort 为 15,199 rows/1,231 clusters，corrected cohort 为 15,148/1,222。恢复出的 4,362 个 annotation 文件与公开 digest 完全一致，但历史 label 多出的 51 个 D_audit matches 无法由存续 GT geometry/runtime conversion 重放，冻结 universe/no-shrink 条件未满足。
- 验证进展：新 validator 只读核对 64 项 manifest、逐行已存 long-axis 的 le90/risk、18 个 G1 cells、提交的 bootstrap CI，以及全部 `lambda=0` 时 fusion/raw score 恒等；正式报告为 `ok=false`。
- 仍存证据限制：validator 没有从 raw pred/GT geometry 独立重建 long-axis 与 `delta_0.75`，也没有从 risk rows、scores、cluster draws 重放 180,000 个 bootstrap replicates；四格仍未闭合，r002/r002 cell 也只有旧摘要。因此不能接受正式 `KILL_GR_EQS_METHOD`。
- 方法方向判断：GR-EQS 负向冻结。修正 G1 中 DIOR-R 最大 `delta_NRC=0.01413<0.02` 且 C 近零，SODA-A/F 为负，三个数据集风险非劣合取均未通过；18 组均为 `lambda=0`，fusion 与 raw 排序相同、AP 增益为零。FAIR1M-D 的 51 行冲突不提供可逆转这些独立负门的正向证据，但该判断不是正式 r002 KILL 回执。
- G2 权限：不授权；禁止 HRSC/RSAR、训练、推理和新实验。
- 唯一下一步：B/C 在独立后续回合选择新的 TGRS 级科学假设；在新计划获批前保持无活动 workstream，本轮不再向 SERVER 下发 r002 修复命令，也不自动执行新路线。
- r001 复核：geometry theta 中位 0.2425237894 rad（13.8956°）超过 0.05 rad（2.8648°）门，足以关闭 CMR；shuffle_class/shuffle_box 比较了不受 foreign q 影响的条件似然字段，二者作废但不改变 geometry 负结论。
- 期刊水平：中科院 2025 地球科学大类二区 JSTARS 对标，尚非 TGRS。
- 状态来源：权威远端 `main@8236d149b02268135485f1076bb6c0fdd3c74a55`、正式 r002 RESULT/VALIDATION/SUPERVISION、FAIR1M recovery receipt、已提交 compact evidence 与 B 的只读复核。
