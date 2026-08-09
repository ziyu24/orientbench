---
round_id: orientbench-c-topjournal-feasibility-dispatch-20260809
control_base: f2aeeb2edd177f6eb62c390042ea74068316570d
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
review_mode: post_r019_protocol_implementation_timelock_audit
evidence_cutoff: 2026-08-09
r019_formal_status: INVALIDATED_R019
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
tgrs_status: CONDITIONAL_ON_METHOD_UPGRADE
cc_recommendation: no
cc_status: completed
---

# OrientBench C：r019 失效裁决与顶刊可行性分流

## 结论

`r019` 的计算确实到达两个 DOTA target 单元并完成 10,000 次 mother-scene cluster bootstrap；它不是 efficacy early-stop，也不能被改写成“因为效果不佳而提前停止”。但其前瞻身份所依赖的协议、实现和时间锁均没有形成可复核闭环，所以正式状态只能是：

```text
INVALIDATED_R019_PROTOCOL_DRIFT_FAIL_IMPLEMENTATION_FAIL_TIMELOCK
```

这不是可采信的科学 `PASS`、正式科学 `FAIL` 或 `INCONCLUSIVE`。所有 r019 数字均为 `INVALIDATED_DESCRIPTIVE_ONLY`，只能用于说明失效实现的表现，不能进入论文的确认性证据、总体显著性家族或 venue gate。

当前唯一可辩护路线是 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`。TGRS 仅在未来取得真正的方法升级及新的干净前瞻证据后才恢复为候选，即 `CONDITIONAL_ON_METHOD_UPGRADE`；当前证据不支持 CVPR/ICCV 等顶会路线。learned EQS 已从主贡献移除，角色固定为 `APPENDIX_FAILED_MIGRATION_ONLY`。

## 证据锁

- control/review base：`f2aeeb2edd177f6eb62c390042ea74068316570d`。
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`。
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；本轮仅核验 blob/diff 元数据，C 不读取或触碰其内容。
- active manuscript 仍为 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`；本轮不改稿。
- r019 报告为 `dis/server_reports/orientbench-c-r019-20260809.md`，但报告中的 headline verdict 不覆盖本次协议/实现/时间锁审计。
- 当前服务器唯一活动指令为 `dis/sug.md`；唯一未来报告为 `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`，runtime 为 `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`。

## r019 决定性失效 witness

| 审计面 | 决定性 witness | 裁决 |
|---|---|---|
| prior-outcome 与硬前提 | prior-outcome search 和若干 hard preconditions 被硬编码为通过，或没有保存足以独立证明“未发现/满足”的命令、范围、退出码、命中裁决与哈希 | `PROTOCOL_DRIFT_R019` |
| validator 与 mutation | validator 消费生成端结果或 gate 状态；所谓 mutation 没有对独立原始输入执行真实字节/cluster/prior-hit/manifest 变异，因而不能证明 verifier 会拒绝伪证据 | `FAIL_IMPLEMENTATION_R019` |
| zero-label-access | `target_label_access_before_seal: 0` 没有由完整访问账本和 fail-closed witness 独立证明 | `FAIL_TIMELOCK_R019` |
| postseal 边界 | label reveal 后使用的 runtime adapter 未在 prelabel seal 中封存；首次标签访问时间又在重试路径中被覆盖，无法证明所有 outcome-sensitive 执行都发生在不可回改的 seal 之后 | `FAIL_TIMELOCK_R019` |
| provenance 闭合 | manifest、evidence manifest、execution ledger、实际访问日志和产物哈希不能互相闭合；报告断言无法回溯为完整可验证事件序列 | `FAIL_IMPLEMENTATION_R019` |

因此，r019 暴露的是协议执行、validator 实现与时间锁证据失效，不是一个可以据此判断 selector efficacy 的正式科学失败。事后修补脚本、补写 ledger 或重放 DOTA 都不能恢复原来的前瞻身份。

## 失效数字的描述性边界

r019 的 learned EQS 相对冻结 linear score 在失效实现中呈正向对比：ORCNN、RTMDet-M 与等权 aggregate 的 `delta_linear_eqs` 分别约为 `0.0844`、`0.0500` 和 `0.0672`，报告区间为正。与此同时，standalone guard 明确为负：两个 unit 与 aggregate 分别约为 `-0.0159`、`-0.0352` 和 `-0.0256`。

两组结果必须一起报告，且只能标为 `INVALIDATED_DESCRIPTIVE_ONLY`：正向 learned-vs-linear 对比不构成 PASS，负向 standalone guard 也不构成正式科学 FAIL。它们至多进入附录的 failed-migration audit，不能驱动新的 gate、主贡献或投稿上限。

## 投稿与贡献裁决

主论文保留并强化 measurement/diagnostic 主线：geometry-equivalence-aware、angle-specific、scene-aware 的 OBB orientation reliability 协议，使用 scene/mother-scene 统计单位、AUGRC、完整 risk–coverage 与固定 coverage 工作点。不得把 TTA uncertainty、angle quality、selective prediction 或 cross-detector reliability 重新包装为概念首创。

learned EQS、r015 与 r019 只保留为开发史、失败迁移和负面实现审计。若未来 feasibility gate 不能证明密封旧资产上的稳健候选以及两个 pristine 遥感 OBB 数据集共享至少三个 detector family，则直接按 ISPRS JPRS measurement/diagnostic 写作；不得降低门槛来维持方法路线。

## 唯一下一步

新的无 GPU feasibility gate 是唯一下一步：Track M 只审计已消费、byte-exact 且 provenance 闭合的旧资产；Track D 只做候选数据集资产、许可、角度合约与 prior-outcome 的无 outcome 审计。服务器权限固定为：GPU、下载、训练、推理和新 target outcome 全部不授权。

这一步不是 r019 修复或新实验，也不预先占用 r020。禁止用 DOTA、HRSC、Core-6、同一数据集的新 detector 或其它旧资产救场；禁止换 gate、换 cluster、换指标或重跑来恢复前瞻身份；禁止重复调用 CC。即使得到 `PASS_TO_METHOD_DESIGN`，也只允许未来另写协议并再次取得用户批准，不授权下载、训练、推理、label access 或方法实验。

## 决策台账

| 项目 | 当前决策 | 允许的下一项证据动作 |
|---|---|---|
| r019 执行量 | `COMPUTATION_REACHED_TARGET_AND_10000_BOOTSTRAP` | 仅保留可审计历史，不重跑恢复身份 |
| r019 正式结论 | `INVALIDATED_R019_PROTOCOL_DRIFT_FAIL_IMPLEMENTATION_FAIL_TIMELOCK` | 数字仅作 `INVALIDATED_DESCRIPTIVE_ONLY` |
| learned EQS | `APPENDIX_FAILED_MIGRATION_ONLY` | 不再作为候选获胜或主贡献驱动 |
| 当前路线 | `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC` | 先完成无 GPU feasibility gate |
| TGRS | `CONDITIONAL_ON_METHOD_UPGRADE` | 只在未来新协议、新用户批准和干净前瞻证据后重审 |
| 顶会 | `NOT_SUPPORTED` | 不以 feasibility 或旧结果重开 |
| CC | completed；`cc_recommendation: no` | 用户未来明确重新授权前不启动新一轮 |
