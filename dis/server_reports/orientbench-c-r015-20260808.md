execution_completion: FULL_COMPLETION
audit_verdict: PASS_PROTOCOL_CLOSURE_R015
r014_formal_verdict: FAIL_PROTOCOL_R014
r015_numeric_status: EXPLORATORY_CORE_SUPPORT_R015
hrsc_status: INCONCLUSIVE_INDEPENDENT_HRSC_R014
last_completed_phase: E_validator_and_final_commit
early_stop_trigger: NONE
unrun_required_phases: []
push_status: PUSHED

# r015 协议闭合报告

## 执行边界

本轮为 CPU-only 只读闭合：未训练、未做 detector forward、未重建 TTA、未重拟合 selector、未产生新 target score，且 r014 runtime 保持只读。所有新增结果均来自 r014 sealed scores、原始 matched labels、冻结 image universe 与 SODA tile-to-mother 映射。

## 法证裁决

独立审计确认 r014 的 prelabel seal 仅登记 feature、model 与 score 文件，未登记 protocol 或五个执行脚本。`ac7a524 -> e0b91ea -> b60dee5` 父链显示 r014 实现脚本在后一个提交才进入版本库；两个提交也不满足原单提交契约。最终 manifest 的哈希一致性只能证明最终文件存在，不能回填揭盲前封存。结论固定为 `FAIL_PROTOCOL_R014_UNRECOVERABLE_PRELABEL_SEAL`，r014 正式状态为 `FAIL_PROTOCOL_R014`。

源数据函数在按 D_cal/D_audit role 过滤前读取完整 matched label 文件。逐 outer target 的物理读取顺序、集合交集、schema 和 r012 特征契约检查均写入 r015 审计表；物理读取与拟合使用被明确区分。未据此重写或重新评分。

## 同步总体重算

完整 audit cluster universe 为 DIOR-R 5,900 images、FAIR1M-v1.0 2,142 images、SODA-A 576 mother scenes；同数据集 units 的集合完全一致，且总体包含零 eligible matched row 的簇。每个数据集以固定随机状态执行 1,000 次同步有放回抽样，unit 差值为 `NRC(linear)-NRC(EQS)`，数据集聚合在每次抽样中对 unit 等权。

| 数据集 | Delta NRC | 同步 95% CI | Holm p | 数值状态 |
|---|---:|---:|---:|---|
| DIOR-R | 0.1733 | [0.1458, 0.2020] | 0.0030 | exploratory |
| FAIR1M-v1.0 | 0.2436 | [0.2048, 0.2848] | 0.0030 | exploratory |
| SODA-A | 0.1645 | [0.1062, 0.2300] | 0.0030 | exploratory |

六个 unit 的同步区间均为正，满足冻结的数值支持门，但同一 target audit 已揭盲，故状态只能为 `EXPLORATORY_CORE_SUPPORT_R015`，不是部署性或独立验证结论。HRSC 保持 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`，Delta NRC=0.060167，95% CI=[-0.014323, 0.143800]。

## 稿件与验证

r015 稿件已将 EQS 部分降为 exploratory post-audit evidence，采用同步区间并修正 DIOR/DIOR-R 与 PSC 引用；不再使用 r014 的不一致数据集聚合区间。独立 validator 从 raw score、label、universe 和固定随机数重新生成 9,000 个值并逐值比对输出，检查最终 token 为 `VALID_PROTOCOL_CLOSURE_R015`。该 token 只证明协议闭合，不证明 deployable selector。

## Git

本轮只修改 r015 明确授权的 19 条路径；r014 及更早产物、冻结数据、split、threshold 与 `dis/B.md` 未改。
