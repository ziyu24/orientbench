# OrientBench 服务器任务：B3/B4 统计重审与 B5 可执行重门控

- round: `orientbench-c-r001-20260805`
- scientific snapshot: `9d9cdae1847f9c82e841f6f8b2692389cf9d9d79`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r001-20260805.md`
- 当前结论边界: A=`A_MEASUREMENT_ONLY`；B5 的 bounded mechanism 可作为待核验假设，不能直接放行 B6。

## 1. 科学问题

现有 B3/B4 报告的候选 NRC 点差在 matched-instance universe 上计算，但 cluster bootstrap 先把 score 与 risk 聚合成 image/mother-scene means，再对这些均值计算 NRC。需要回答：当 cluster resampling 通过 multiplicity weights 作用到原始实例、从而保持实例级 NRC estimand 后，候选比较、外部确认和 B5 verdict 是否仍成立？

本轮只修复统计证据链与可执行 gate；不运行 B6/B7，不修改 A 主稿，不把机制干预包装成 ranking-only/AP-invariant 方法。

## 2. 前置完整性门

执行任何计算前：

1. 核对当前代码基线包含 scientific snapshot `9d9cdae1847f9c82e841f6f8b2692389cf9d9d79`，并在报告中记录实际 HEAD；若已有新提交，只允许它们是本轮协作资产或经记录的服务器实现提交，必须给出 ancestry。
2. 按 [`docs/server_migration_handoff_20260727.md`](../docs/server_migration_handoff_20260727.md) 核对服务器工作区、10 个 split CSV、275 个迁移资产、B3/B4 frozen dumps、三份 B4 checkpoint manifest 及其 SHA-256。不得重新训练或静默替换缺失资产。
3. `configs/thresholds.yaml` 必须按 raw bytes 得到 SHA-256 `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`。若仅因 checkout 换行导致哈希不同，先报告并停止；不得重写冻结文件来“匹配”哈希。
4. 复核冻结协议：[`b1_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b1_protocol_frozen.json)、[`b4_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b4_protocol_frozen.json) 与 G0 的正确 weighted-cluster 实现。

任何一项失败都早停为 `inconclusive`，不得继续生成看似完整的 verdict。

## 3. 固定协议

1. 宇宙、mask、endpoint、score 方向、stable tie order、seed 和 800 次配对 resample 均沿用冻结 B1/B4 协议；连续角误差与 geometry-normalized severe event 分开。
2. 点估计与每个 bootstrap replicate 必须是同一个 matched-instance NRC estimand。抽到某 cluster `k` 次时，将该 cluster 内所有实例赋 multiplicity weight `k`；不得先对 score 或 risk 做 cluster mean 后再计算 NRC。
3. candidate 与 phase_mod/detection_score 使用相同 cluster resample ID，报告 paired delta、2.5%/97.5% 分位数、Monte Carlo seed、cluster 数、instance 数和 resample-ID hash。
4. B3 按冻结 image cluster；B4 按冻结 mother_scene cluster。若代码或协议显示单位不同，停止并在报告中列冲突，不自行改口径。
5. ranking-only 候选保持 prediction identity、boxes、classes、NMS 与 AP；phase-vector 干预改变角度时明确标为 mechanism-only，NMS 未重跑则不声称 AP invariance。
6. B5 状态必须由机器可检查条件从健康表、身份审计、外部重复和修正 bootstrap 输出推导；禁止在输出代码中直接写死 H1--H4 或 final verdict。
7. 原有冻结 B1--B5 报告不覆盖、不删除。所有重审产物采用本轮专用文件名。

## 4. 实现自由度与授权写入

可在以下范围内新增或修改服务器代码/证据：

- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/`：新增本轮重审脚本及测试；如确需抽取公用函数，可最小修改 `run_b3_real_interventions.py` / `run_b4_b5_analysis.py`，但必须保持旧冻结输出不被覆盖。
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/`：只新增下列本轮产物。
- `dis/server_reports/orientbench-c-r001-20260805.md`：唯一服务器叙述报告。

允许实现采用加权 stable sort、按 multiplicity 展开或经逐行等价测试证明的优化。禁止修改数据、split、checkpoint、冻结 JSON、A 主稿、现有冻结 CSV，以及 `dis/B.md`。

## 5. 必须生成的证据产物

1. `b3_candidate_cluster_bootstrap_reaudit_r001.csv`
2. `b4_candidate_external_bootstrap_reaudit_r001.csv`
3. `b5_gate_reaudit_r001.csv`
4. `b3_b4_estimand_equivalence_tests_r001.csv`
5. `b3_b4_reaudit_manifest_r001.json`
6. `dis/server_reports/orientbench-c-r001-20260805.md`

manifest 至少记录输入/输出相对路径、raw SHA-256、行数/schema、scientific snapshot、实际代码 SHA、命令、seed、replicates、cluster unit、instance universe hash 和 resample-ID hash。报告必须列出旧实现与新实现的逐项差异，以及 B3 `58` 行中旧实例点差落在旧区间外的 `39` 行、B4 `24` 行中的 `4` 行是否被独立复现。

## 6. Pass / fail / inconclusive gate

- `PASS_STATISTICAL_REGATE`：前置完整性全过；测试证明 bootstrap 与点估计为同一实例级 estimand；全部产物可从命令重生成且哈希稳定；B5 verdict 由条件计算而非硬编码。该状态只表示可以重新评估是否运行 B6，不等于候选有效。
- `FAIL_CANDIDATE_GATE`：完整性和实现均通过，但修正后的预注册比较不能支持候选，或任何 ranking-only 身份/AP 条件失败。停止 B6，并将候选降级/杀死。
- `INCONCLUSIVE_ASSET_OR_PROTOCOL`：资产/哈希/协议单位不完整或冲突、无法保持相同 estimand、重算不稳定。停止，不生成科学成功结论。

早停顺序：完整性失败 → estimand 等价测试失败 → 身份边界失败 → 重算候选 gate 失败。没有新证据时停止，不增加事后 score、seed、阈值或 endpoint。

## 7. 服务器最终回复格式

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r001-20260805.md`。
