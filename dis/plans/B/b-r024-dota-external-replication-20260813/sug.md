---
schema_version: 2
plan_id: b-r024-dota-external-replication-20260813
dispatch_id: orientbench-b-r024-dota-external-replication-20260813
initiator: B
base_sha: f584c17071c2e4b1c7391b387f2d167a071b38c0
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13：『授权路线一，抓紧推进』——预注册外部复现研究，含必要时的 GPU inference 与官方 checkpoint 获取（dis/B.md §11）"
scientific_snapshot:
  primary: f584c17071c2e4b1c7391b387f2d167a071b38c0
  replication_target: "r023 正式结果：AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION（DIOR-only，INCONCLUSIVE_MIXED）"
  frozen_delta_table: top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json
  frozen_delta_table_blob: 757be607730b4fd9e1c5bbd28dfb94ae01201b14
  r019_matcher_semantic_reference_blob: 47e7cf4c3612f5fc09535260547f7ba7be594410
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r024-dota-external-replication-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库可读；DOTA-v1.0 val 图像/标注、r019 既有预测产物、Core A-F 冻结 features/scores（outputs/persistent_artifacts/**）按下文分支规则使用
write_set:
  - outputs/persistent_artifacts/orientbench_dota_external_replication_r024_20260813/**
  - top_journal_v3_reaudit_055/dota_external_replication_r024_20260813/**
  - dis/server_reports/orientbench-b-r024-dota-external-replication-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 1, gpu_hours_max: 10, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["DOTA-v1.0-val", "existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_dota_external_replication_r024_20260813/
      - top_journal_v3_reaudit_055/dota_external_replication_r024_20260813/
      - dis/server_reports/orientbench-b-r024-dota-external-replication-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 32212254720
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
      - 官方 mmrotate model zoo checkpoint URL（仅在本地 checkpoint 缺失且需要新 forward 时，逐条记录 URL 与 SHA-256）
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - outputs/persistent_artifacts
gates:
  - gate_id: G1
    rule: 预注册外部复现四态（见正文）；REPLICATED / NOT_REPLICATED / INCONCLUSIVE_EXTERNAL 均属正常完整执行，服务器只报告。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 官方 AP parity 复核失败（任一 unit 与官方期望 AP50/AP75 绝对差 > 0.002）且无法通过重新 forward 修复。
  - 线性探针恢复失败（正文 P 步骤两分支均不成立）——此时以 NOT_ADJUDICATED_PROBE_PROVENANCE 停止并如实报告，不得改用任何替代探针。
  - A/B 两套实现 matched 集合身份或任一数值超容差不一致。
  - 使用任何 r023/r020/recovery 的 DIOR/FAIR1M/SODA 结果数字作为 DOTA 计算输入；读取 DOTA 之外的新目标数据。
  - 训练任何模型；写入越出 write_set；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r024 DOTA 外部复现（B 发起，预注册确认性研究）

## 一句话

在 DOTA-v1.0 val（与 DIOR/FAIR1M/SODA 独立的外部 OBB 数据）上，用**完全相同的冻结机器**检验 r023 已正式确立的 DIOR AR-domain 签名是否跨数据集复现。复现 → 跨数据集测量有效性贡献（JPRS 主张）；不复现 → 效应定性为 DIOR 特有（JSTARS-scope caveat）。本计划在看到任何 DOTA 结果**之前**冻结全部假设、方向、族、判据与论文映射。

## 冻结科学协议

**总体**：DOTA-v1.0 val 全部 5297 tiles（排除 DOTA-2.0 增补），458 mother scenes 为 cluster universe（零 eligible 的 mother 保留）。tile→mother 由 tile 文件名源图映射，A/B 独立重建并核对（参考 r019 的 458/5297 与集合 SHA：mothers `5b97f439…`，tiles `c3191815…`；不一致须披露解释）。

**单位**：`DOTA/orcnn`（Oriented R-CNN）与 `DOTA/rtmdet`（RTMDet）两个 unit，检测器族与 Core B/C、F 同族。官方 parity 门：每 unit 预测集必须复核 AP50/AP75 与官方期望（orcnn 0.7061/0.4517，rtmdet 0.7161/0.4868）绝对差 ≤0.002。

**匹配**：tile 级、逐类、按 score 降序贪心把预测配到未匹配 GT，rIoU≥0.5 的 TP 对进入总体（语义与 r019 密封 matcher 一致，参考 blob `47e7cf4c…`；由 A/B 各自独立实现，matched 集合身份必须精确一致）。**不施加任何 GT AR 掩码**——全 AR 域进入基表。

**风险**：与主研究逐字相同——预测与 GT 均 long-side canonicalize，角差按 180° 周期，`AR=max(gt_w,gt_h)/min(gt_w,gt_h)`，`r_geo=clip(e_can/max(delta_0.75(AR),1°),0,3)/3`，delta 表用 Git 冻结的 `m4_delta_theta_075_frozen.json`（blob `757be607…`），同一 finite-grid/`numpy.interp`/inverse-tail 实现。

**探针 P（关键预注册）**：`raw_confidence = detection_score`；`linear_source_frozen` 必须是 r014 冻结线性函数本身，按以下唯一决策树取得，禁止任何重拟合或替代：
- P1：在仓库与 outputs 的 r014 产物中找到显式系数/定义工件 → 在全部六个 Core unit 的冻结 scores 列上复算验证（max abs 残差 ≤1e-8）→ 采用。
- P2：找不到工件 → 精确恢复：对每个 Core unit，用其 features/scores 全表把 `score_ar_size_linear` 列对候选设计矩阵（`{detection_score, logit_score} × {pred_ar, log_pred_ar} × {pred_area, log_pred_area, half_log_pred_area}` + 截距）做最小二乘精确求解；要求存在唯一候选在**全部六个 unit** 上 max abs 残差 ≤1e-8 **且六组系数一致（成对差 ≤1e-6）**→ 该全局冻结函数用于 DOTA（对 DOTA 预测的同名量应用同一变换与系数）。
- P1/P2 均不成立（含六 unit 系数不一致）→ `NOT_ADJUDICATED_PROBE_PROVENANCE` 停止。恢复出的定义、系数、逐 unit 残差全部写入报告。

**假设族**（在任何 DOTA 标注被打开前冻结）：contrast 唯一 = `linear_source_frozen − raw_confidence`；ablation 唯一 = `NORMALIZED_ALL_AR`（主域 AR≥2.1 vs 全 AR）；endpoints = `AUGRC`、`Risk@70`（Risk@90 在 r023 无 dataset witness，预注册排除）。unit 族 = 2 units × 2 endpoints = 4 条，dataset 族 = 2 条（等权 unit 聚合），两族分别 Holm。方向唯一 = `RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`。

**推断**：mother-scene cluster bootstrap，`seed=20260813`，replicates 0..9999，`RandomState(seed)` 逐 replicate `randint+bincount` multiplicity，同数据集内共用；witness 谓词与主研究逐字相同（`Delta_main_CI_low>ε_main` 且 `Delta_ablation_CI_high<−ε_ablation`；centered-p `(1+count(|DoD_b−DoD̂|≥|DoD̂|))/10001` Holm<0.05；DoD 95% CI 排零；`|DoD|≥ε_main+ε_ablation`；Risk@70 两 cohort swap≥0.05；AUGRC 无 swap 门；ε 公式同主研究）。

**预注册四态与论文映射**（执行前锁死，事后不得重划）：
- `REPLICATED`：AUGRC dataset witness 成立且 ≥1 个 AUGRC unit witness。→ 跨数据集（DIOR+DOTA、两检测器族）测量有效性主张成立，投 **ISPRS JPRS**；Risk@70 dataset witness 同时成立记为 `REPLICATED_STRONG`。
- `NOT_REPLICATED`：完整执行且两 endpoint 均无 dataset witness。→ 效应定性 DIOR 特有，论文按 **JSTARS-scope** 收口，DOTA 负结果如实并入；不再签发新复现轮，除非用户另行授权。
- `INCONCLUSIVE_EXTERNAL`：其余完整执行情形（如仅 unit witness、或仅 Risk@70 dataset witness）。→ 按 JSTARS-scope 收口并如实报告部分信号；同样不自动续命。
- `NOT_ADJUDICATED`：kill 清单触发。
效应量、CI、两域点估计无论何态均全量报告（供论文使用，非判据）。

## 数据与模型来源（分支规则，报告披露走了哪支）

- 优先复用 r019 已存在的**原始预测/推理产物**（不是其分析数字）：条件是官方 AP parity 复核通过 + 产物 bytes/SHA 记录。r019 的分析结论已作废，本轮一律不读其风险/匹配/统计结果。
- 原始预测缺失或 parity 不过 → 用本地（或官方 model zoo 下载并记录 SHA 的）checkpoint 对 DOTA val 重新 inference（GPU ≤10 小时帽内），再过 parity 门。
- DOTA 标注（val GT）为公开集，直接读取；禁止读取任何其它新目标数据。

## 执行结构（务实，r023 风格）

1. STARTED 单文件 commit+push。
2. 探针 P 步骤（只碰 Core 冻结 features/scores，尚不碰 DOTA 标注）；结果写 runtime。
3. 数据分支：获得两 unit 预测 + parity 门。
4. A/B 两套独立实现（不共享代码、不互读输出）：各自完成 tile→mother、匹配、canonical 角/AR/风险、eligibility、point 端点、4+2 假设、10k bootstrap、Holm、witness、四态。先 B 后 A 或并行皆可，照实记录。
5. Comparator：matched 集合身份精确一致；数值 atol=1e-10；witness/状态精确一致。
6. 独立 validator：重算 point 端点、Holm、centered-p、witness 谓词（r023 风格）。
7. 语义 mutation（≥4 项，照 recovery 风格：GT theta 篡改、tile→mother 篡改、AR 门 2.1→1.0、报告 token 篡改；pristine 0 / mutated 非 0）。
8. 报告（模板 schema 2）：P 步骤全记录、分支与 parity、四态、全部效应量/CI、偏差列表、资源；结果 commit+push；两行回执。

## 务实规则

同 r023：任何可审计 ff-only HTTPS 同步皆可；CPU/GPU 配置照实记录；不要求 strace/tracer/duty-cycle/postseal receipt；操作者知晓 r023/recovery 历史结果非污染（本计划正文即含复现目标）；遇到未预料情况默认"继续 + 报告披露"，只有 kill 清单才停。**唯一额外纪律：任何 DOTA GT 的打开必须发生在第 2 步探针冻结完成之后，打开时间与文件清单写入报告。**

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull verdict；ACCEPTED/KILLED 需双方一致。
