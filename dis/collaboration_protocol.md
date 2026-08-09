# OrientBench 最小跨机器协作协议

## 当前锚点

- state：`READY_FOR_SERVER_FEASIBILITY_GATE`
- round：`orientbench-c-topjournal-feasibility-20260809`
- control/review base：`f2aeeb2edd177f6eb62c390042ea74068316570d`
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- active instruction：`dis/sug.md`
- unique future report：`dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
- runtime root：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`
- CC：`COMPLETED`；`cc_recommendation: no`

跨机器共享只通过仓库，不写账号、机器标识、凭据、本地绝对路径或 C 侧私有规则。两个 SHA 的职责不同：control/review base 固定本次 C 侧派发基线；scientific data cutoff 固定已审计科学证据的最晚提交，二者不得互换。

## 当前科学状态

`r019` 的计算到达两个 target 单元并完成 10,000 次 bootstrap，但 prior-outcome/hard-precondition witness、独立 validator 与真实 mutation、zero-label-access、postseal adapter/首次标签访问时间以及 manifest/ledger 闭环均失效。其正式判定为 `INVALIDATED_R019_PROTOCOL_DRIFT_FAIL_IMPLEMENTATION_FAIL_TIMELOCK`；数字只能是 `INVALIDATED_DESCRIPTIVE_ONLY`，不是科学 PASS、正式科学 FAIL 或 INCONCLUSIVE。

失效实现中的 learned EQS 相对 linear 对比为正，standalone guard 为负；两者都只能作 appendix failed-migration 描述，不能驱动 gate。当前路线固定为 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`，TGRS 为 `CONDITIONAL_ON_FUTURE_METHOD_UPGRADE`，顶会为 `NOT_SUPPORTED`。

不得用 DOTA、HRSC、Core-6、同一数据集的新 detector 或其它旧结果救场；不得修复/重跑 r019 来恢复前瞻身份，不得启用 r020 或替换 gate，不得重复调用 CC。

## 角色与所有权

C 负责冻结科学问题、状态映射和 joint gate；服务器只执行 `dis/sug.md`，按唯一报告回传证据；服务器回报后仍由 C 审计证据并裁决。CC/B 不是最终裁决者，本轮 CC 已完成且关闭。

`dis/B.md` 由 CC/B 独占。C 与服务器均不得创建、读取内容、修改、格式化、移动、删除、暂存、恢复或提交；只可核验其普通/staged diff 为零及 blob 等于上列值。

服务器只可写：

1. `top_journal_v3_reaudit_055/feasibility_gate_20260809/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
4. `claude_code_and_supervisor.md`，仅 append-only

服务器不得修改 C/review state/本协议/B start/主稿/旧报告/旧 runtime 或其它科学资产。当前权限必须逐项解释为：

```yaml
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
```

不得使用 GPU、下载数据或模型、安装依赖、训练、运行 forward/inference、打开候选 target 标签计算 outcome，或用 target 标签调参。Track M 仅可重算已消费且 byte-exact/provenance 闭合的旧资产；Track D 仅可做官方来源、许可、角度合约、本地 stat 和真实 prior-outcome 搜索。

## Joint gate

- `PASS_TO_METHOD_DESIGN`：当且仅当 Track M=`ROBUST_CANDIDATE`，至少两个相互独立的遥感 OBB 候选为 `ELIGIBLE_CANDIDATE`，二者共享同一组至少三个 detector family、其中至少一个 family 未参与旧 Core 开发，并且未来不需要 target-label tuning。
- `FAIL_TO_MEASUREMENT_ONLY`：Track M 为 `METRIC_REVERSAL`、`BASELINE_DOMINATED` 或 `SENSITIVITY_UNSTABLE`；或少于两个遥感候选合格；或共同三-family 集合不存在；或许可/角度合约不闭合；或必须 target-label tuning。
- `INCONCLUSIVE_FEASIBILITY`：仅在 Track M=`INSUFFICIENT_ASSETS` 且 Track D 没有独立触发 `FAIL_TO_MEASUREMENT_ONLY` 时成立；默认仍走 measurement-only，不授权方法研究。

`PASS_TO_METHOD_DESIGN` 只授权未来起草新的前瞻协议，并再次请求用户明确批准；它不授权下载、训练、推理、label access、新 outcome 或任何方法实验。

## 完成语义与报告

- `FULL_COMPLETION`：Track M、Track D 四候选、generator、独立 validator、四项真实 mutation、所有可判定 gate 和必需证据均按完整 `dis/sug.md` 穷尽。缺资产、污染、metric reversal、baseline domination、角度不兼容、license 阻塞或其它负面可行性发现仍可属于完整执行。
- `EARLY_STOP_TECHNICAL`：只允许仓库/规则冲突、受保护文件异常、runtime collision、访问控制或 executable-audit failure 触发；必须列出已完成与未执行阶段及准确原因。
- `FAILED_EXECUTION`：非允许技术早停的执行错误，或结果/证据无法由 validator 复核；不得包装为科学负结果。

唯一报告必须逐项写出 `all_contract_work_finished`、`technical_early_stop`、`execution_failed`、completed/omitted phases 及原因，并用 `sug_genuinely_exhausted: true|false` 明确回答整份 `dis/sug.md` 是否真正穷尽。只有全部合同工作、唯一 result commit、HTTPS push 和 post-push external receipt 完成，服务器才可回复 `执行完毕`；否则必须回复 `未执行完毕`。
