---
schema_version: 2
plan_id: b-r026-dota-external-confirmation-20260813
dispatch_id: orientbench-b-r026-dota-external-confirmation-20260813
initiator: B
base_sha: a3f058d6e9ecff6bd5bb0e65186549f16beb364d
supersedes: b-r024-dota-external-replication-20260813
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13 路线一授权与『抓紧向前推进』指示；r025 为用户最高授权诊断，本轮将其正式化（dis/B.md §11-§12）"
scientific_snapshot:
  primary: a3f058d6e9ecff6bd5bb0e65186549f16beb364d
  confirmation_target: "r025 诊断信号：DOTA 上 AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen(DIOR-source) / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION"
  frozen_delta_table_blob: 757be607730b4fd9e1c5bbd28dfb94ae01201b14
  normative_risk_endpoint_semantics_blob: 2b0458690c68f6a11587ff4c578d12cecb901698
  normative_predicate_semantics_blob: e483c5a905545161faa8be2dddc02ca5ef4ae562
  normative_feature_transform_blob: bbafd08ae778ac45f40f8073f1a3a0b32ab94605
  r025_raw_layer_reference_blob: f6d4b9958da301042008ad475dbccaf03ba5aee8
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r026-dota-external-confirmation-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库可读；DOTA-v1.0 val 原料、r019 identity predictions 与 tile GT 转换、Core 冻结 features/scores 按正文规则使用
write_set:
  - outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/**
  - top_journal_v3_reaudit_055/dota_external_confirmation_r026_20260813/**
  - dis/server_reports/orientbench-b-r026-dota-external-confirmation-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 1, gpu_hours_max: 4, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["DOTA-v1.0-val", "existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/
      - top_journal_v3_reaudit_055/dota_external_confirmation_r026_20260813/
      - dis/server_reports/orientbench-b-r026-dota-external-confirmation-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 32212254720
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - outputs/persistent_artifacts
gates:
  - gate_id: G1
    rule: 预注册外部确认四态（正文）；CONFIRMED_EXTERNAL / CONFIRMED_EXTERNAL_STRONG / NOT_CONFIRMED / INCONCLUSIVE_EXTERNAL 均属正常完整执行。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - AP parity 复核失败（任一 unit 与官方期望绝对差 > 0.002）。
  - GT 完整性检查失败（正文 GT 规则两分支均不成立）。
  - A/B 两实现 matched 集合身份或数值超容差不一致且无法定位解释。
  - 在 DOTA 上拟合或调整任何探针系数；使用预注册 β 之外的探针进入判据。
  - 训练模型；写入越出 write_set；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r026 DOTA 外部确认（B 发起，r025 诊断的正式化）

## 一句话

把 r025 的用户授权诊断升级为正式证据：同 seed、同原料、同 DIOR-source 冻结探针，补齐 r025 缺失的**完整判据层**（ε/CI/centered-p/Holm/swap/witness），双独立实现 + comparator + validator + mutations。raw 层预期精确复现 r025；witness 标志以本轮正式判据为准。

## 冻结科学协议

**探针（字面预注册，禁止任何拟合/调整/替换）**：
```text
linear_source_frozen = β·[1, logit_score, log_pred_ar, half_log_pred_area]
β = [-0.23342829, 0.00830977, 0.02817757, 0.00753967]   # r014 DIOR A/B/C 精确恢复系数（r024 报告表）
raw_confidence = detection_score
```
特征变换（logit/log/clip 边界）以 r019 密封特征实现为规范（blob `bbafd08a…`），A/B 各自独立实现并在报告披露实际边界；DIOR-source 选择理由预注册：复现目标源自 DIOR，检验的就是 DIOR→DOTA 迁移。**敏感性（纯描述、非 gate、不产生 witness）**：FAIR1M-source 与 SODA-A-source β 变体（r024 报告表）各出一张 dataset 级点估计+CI 表。

**总体/匹配/风险**：DOTA-v1.0 val 全 5297 tiles / 458 mothers（零 eligible 保留；集合与 r019 密封 SHA 核对：mothers `5b97f439…`、tiles `c3191815…`）。r019 identity predictions 复用，AP parity 门（orcnn 0.7061/0.4517，rtmdet 0.7161/0.4868，容差 0.002）；预测缺失或 parity 失败才允许 GPU 重推（≤4 GPU 时）。匹配：tile 级、逐类、score 降序贪心（平分按索引）、取未匹配同类 GT 中最高 rIoU 且 ≥0.5，ignore GT 排除（与 r025 实现一致，报告披露）。风险与全 AR 域语义以主研究 `independent_b.py`（blob `2b045869…`）为规范：long-side canonical 角、180° 周期、`r_geo=clip(e_can/max(δ0.75(AR),1°),0,3)/3`、冻结 delta 表（blob `757be607…`）finite-grid/`numpy.interp`/inverse-tail。

**GT 规则（两分支，报告披露走哪支）**：优先从 DOTA val 原始 annfiles 重建 tile GT；不可得则用 r019 持久化 `dota_gt_fresh.pkl`，但必须通过完整性门：5297 tiles、GT 总数 55804、逐类计数表进报告、bytes/SHA 记录、来源披露（r019 prelabel 阶段转换）。两分支均不成立 → kill。

**假设族与判据（执行前冻结，与主研究逐字一致）**：unit 族 = {orcnn, rtmdet} × {AUGRC, Risk@70} 共 4 条；dataset 族 = DOTA equal-unit × 2 endpoints 共 2 条；分别 Holm。唯一 contrast = `linear_source_frozen − raw_confidence`；唯一 ablation = `NORMALIZED_ALL_AR`（主域 AR≥2.1）；唯一方向 = `RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`。witness 谓词全量执行（规范 blob `e483c5a9…`）：`Delta_main_CI_low>ε_main` 且 `Delta_ablation_CI_high<−ε_ablation`；`ε_AUGRC=max(5e-4, 0.02·max(|M_probe|,|M_raw|))`、`ε_Risk=max(1e-3, …)` 按各 cohort 一次计算；centered-p `(1+count(|DoD_b−DoD̂|≥|DoD̂|))/10001`，Holm<0.05；DoD 95% percentile CI 排零；`|DoD|≥ε_main+ε_ablation`；**Risk@70 witness 必须检验 swap**：whole-tie accepted set 定义与主研究相同，`swap_main_.70≥0.05` 且 `swap_ablation_.70≥0.05`；AUGRC 无 swap 门。bootstrap：mother cluster、seed=20260813、replicates 0..9999、`RandomState(seed)` 逐 replicate `randint+bincount`，两 unit 共用 multiplicity。

**预注册四态与论文映射**：
- `CONFIRMED_EXTERNAL`：AUGRC dataset witness + ≥1 AUGRC unit witness（完整判据）→ 跨数据集测量有效性主张正式成立（DIOR formal + DOTA formal、≥2 检测器族、2 数据集），**JPRS 主稿主张**。
- `CONFIRMED_EXTERNAL_STRONG`：上者 + Risk@70 dataset witness（含 swap）→ 同上，主张更强。
- `NOT_CONFIRMED`：完整执行、两 endpoint 均无 dataset witness → r025 信号定性为判据不达标，论文按 JSTARS-scope，DOTA 效应作描述性报告。
- `INCONCLUSIVE_EXTERNAL`：其余完整执行情形（如仅 unit witness、或 dataset 仅一 endpoint 且非 AUGRC）→ 论文主张取 DIOR formal + DOTA 部分外部支持的中间档，投稿目标由 B/C+用户裁定。
- `NOT_ADJUDICATED`：kill 触发。
无论何态，全部效应量、CI、swap 值、两域点估计、敏感性表全量进报告。

**预注册期望**：raw 层（matched 集合、point 指标、16 列 bootstrap 数组）应与 r025 runtime（`run_b5`）精确一致（同 seed/原料/管线，参考 blob `f6d4b995…`）；不一致必须逐项解释。witness 层无预期约束——r025 报告的 witness 表不构成本轮判据的先验。

## 执行结构（务实）

1. STARTED 单文件 commit+push。
2. A/B 两套独立实现（不共享代码、不互读输出）：原料层（GT、匹配、风险、点指标、bootstrap）+ **完整判据层**（ε/CI/p/Holm/swap/witness/四态）。
3. Comparator：matched 身份精确一致、数值 atol=1e-10、witness/四态精确一致。
4. 独立 validator：从 A 输出重算点端点、Holm、centered-p、全部 witness 谓词（含 swap）。
5. 与 r025 raw 层比对：一致性表进报告。
6. 语义 mutation ≥4：GT theta 篡改、tile→mother 篡改、AR 门 2.1→1.0、swap 门 0.05→0、报告 token 篡改（任选≥4，pristine 0/mutated 非 0）。
7. 报告（模板 schema 2，含四态、全部数表、敏感性表、偏差清单、资源），结果 commit+push，两行回执。

务实规则同 r023/r024：可审计 ff-only 同步即可；配置照实记录；不要求 strace/tracer/postseal；操作者知晓 r025 结果非污染；未预料情况默认继续+披露，仅 kill 清单停。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull verdict；ACCEPTED/KILLED 需双方一致。C 对 r023 的 verdict 与对本轮的 critique 一并欢迎。
