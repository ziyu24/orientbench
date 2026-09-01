# 当前状态

- 阶段：`R002_EVIDENCE_CLOSEOUT_REPAIR_REQUIRED`。
- 阻塞项：r002 尚无正式 `coordination/executions/r002/RESULT.yaml`，当前独立验证器没有重算完整 G1，且 FAIR1M-D 的 corrected universe 被额外改变。
- 唯一下一步：SERVER 在现有 r002 计划内做同编号、无 GPU、correction-only 的证据闭环修复；不得绕过缺失的执行回执新开 r003。
- 当前正式科学状态：`INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE`；方法方向判断为 `KILL_GR_EQS_METHOD_PENDING_INDEPENDENT_CLOSEOUT`。闭环前不得接受正式 KILL，也不得进入 HRSC/RSAR 或 G2。
- 已确认 r002 缺陷：原实现对匹配后的 rbox 直接比较 raw theta，未在 `w<h` 时进行长边 `+90°` canonicalization。修复后 A-F 的 standalone Risk@90 分别为 0.142542、0.154831、0.171654、0.195031、0.162476、0.175884，回到 r014 的 0.138474、0.153111、0.169814、0.191893、0.160119、0.174050 同一量级；这确认 canonicalization 是十倍漂移的主因，但不能声称解释了全部逐行差异。
- 修正 G1 的实质结果为负：DIOR-R 最大 `delta_NRC=0.01413<0.02` 且 C 近零；SODA-A/F 为负；三个数据集的风险非劣合取均未通过。18 组修正结果全部选择 `lambda=0`，因此冻结公式下 fusion score 与 raw score 恒等，AP75 增益为零，不可能达到正增益门。
- 已纳入 Git 的 compact evidence 包含 316,927 条 audit risk rows、950,781 条 compact scores 和恰好 180,000 条 bootstrap replicates；64 项 artifact manifest 的 Git blob bytes/SHA-256 全部匹配。按生产行序重排后，18 组点估计和全部 bootstrap CI 可从这些证据复现。
- 当前 `independent_verification: PASS` 不可接受：验证器只重算六个 standalone 指标并检查行数，没有逐行验证 canonical risk、18 组 GR-EQS 指标、180,000 个 bootstrap/CI/gate、`lambda=0` 的 fusion/raw 排序与 AP 恒等，也会覆盖传入的正式 result/manifest。
- 当前四格实际为 0/4：三个 r014-data cell 因 r014 raw/matched-fullval 资产缺失而不可运行；可用的 r002-code/r002-data cell 也只引用旧摘要。r014 资产缺失阻塞历史四格归因，但不阻塞对冻结 GR-EQS 方法去留的最终负裁决。
- FAIR1M-D 从原 r002 的 15,199 rows/1,231 clusters 变为 corrected 的 15,148/1,222；审计代码新增了原生产路径没有的 `difficulty != 0` 过滤。SERVER 必须恢复原 r002 D universe，并只修风险语义，不得缩减 cohort。
- SERVER 同编号修复必须：补齐可逐项审计的 code provenance；让 validator 只读且独立复算 manifest、逐行风险、18 组指标、全部 bootstrap/CI/gate；真实执行 r002/r002 cell；恢复 D universe；验证全部 `lambda=0` 时 fusion/raw score、排序与 AP 恒等；生成正式 RESULT/SUPERVISION 并更新远端状态。r014 三格若资产确实不存在，继续如实标记 unavailable，禁止填补或伪造。
- r001 复核：geometry theta 中位 0.2425237894 rad（13.8956°）超过 0.05 rad（2.8648°）门，足以关闭 CMR；shuffle_class/shuffle_box 比较了不受 foreign q 影响的条件似然字段，二者作废但不改变 geometry 负结论。
- 期刊水平：中科院 2025 地球科学大类二区 JSTARS 对标，尚非 TGRS。
- 状态来源：权威 HTTPS 远端 `main` 的 `88cdc3c5e345c77a69f9eccdc9c15ee4204e1160`、r001/r002/r014 生产代码与已提交证据、B 的独立行级与 bootstrap 复算、`coordination/STATE.yaml`。
