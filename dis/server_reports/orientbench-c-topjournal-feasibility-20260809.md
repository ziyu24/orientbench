# OrientBench 顶刊可行性审计服务器报告

## 1. 固定身份与完成分类

```text
round_id: orientbench-c-topjournal-feasibility-20260809
control_base: f2aeeb2edd177f6eb62c390042ea74068316570d
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
status: READY_FOR_SERVER_EXECUTION
server_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
runtime_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
cc_recommendation: no
completion_class: FULL_COMPLETION
all_contract_work_finished: true
technical_early_stop: false
technical_early_stop_reason: none
execution_failed: false
execution_failure_reason: none
sug_genuinely_exhausted: true
final_commit_sha=POST_COMMIT_EXTERNAL_RECEIPT
git_publish_status=PENDING_EXTERNAL_RECEIPT
```

本轮完整穷尽 Track M、Track D、独立 validator、四项真实 mutation、证据封存和联合 gate。负面科学结果与缺失资产按合约属于完整审计结果，不是技术早停。`r019` 保持 `INVALIDATED_R019 / PROTOCOL_DRIFT_R019 / FAIL_IMPLEMENTATION_R019 / FAIL_TIMELOCK_R019`；其数字只允许作 `INVALIDATED_R019_DESCRIPTIVE_ONLY`，本轮未恢复、修复或续跑。

## 2. 启动预检与执行边界

- 起始 HEAD 与远端 `main`：`cb84b950ec5b94d89d0b13327a529e5712885111`。
- 分支：`main`；upstream：`origin/main`；显式 HTTPS fast-forward pull 已完成。
- 起始 index/worktree：干净；runtime_root：启动前不存在。
- `dis/B.md` blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`，与固定值一致，未进入 diff 或 staging。
- 规则读取：`AGENTS.md` 13,862 bytes，SHA256 `421b83ddd8b326f187753795be0682974e9b99bdbeb9b0369b7f1b31fd7a4034`；`pth_data/readme.md` 89,032 bytes，SHA256 `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c`；活动合约与协作协议的字节数和哈希见 `preflight.json`。
- 实际资源：未使用 GPU；未下载数据集或模型；未训练、推理、安装包、读取新目标标注或生成新目标域 outcome。官方网页、README、license 文本仅用于 Track D 法证。
- 科学协议偏差：无。两次 generator 工程异常分别为入口环境导入路径和计算后 ledger 变量名；均发生在 gate 封存前，修复没有改变数据、score、risk、cluster、bootstrap 或状态映射。失败日志被保留，随后完整复算和独立验证通过。

完整命令、cwd、输入、时间、退出码及日志 SHA256 位于 `execution_ledger.csv`。39 个 bootstrap worker 的 child CPU、RSS 和 affinity 位于 `resource_telemetry.csv/json`。

## 3. Track M：密封测量资产

Core A-F 的 row-level risk、固定 score、row key、cluster universe、字节数和 SHA256 均已盘点。DIOR-R/FAIR1M 使用 image cluster，SODA-A 使用 original mother-scene cluster；zero-eligible cluster 保留。连续 severity 严格使用：

```text
risk_cap3 = clip(angle_error / max(delta_theta_0.75(GT_AR), 1 degree), 0, 3)
residual = risk_cap3 / 3
```

AUGRC 使用包含原点的 unique-threshold generalized-risk/coverage 梯形积分，同分组整体进入。两个固定 toy vector 均在 `atol=1e-12, rtol=0` 下通过。dataset aggregate 先逐 evaluation unit 计算，再等权平均。

### 3.1 数据集聚合结果

| Dataset | Score | AUGRC | AURC | NRC | Risk@70 | Risk@90 |
|---|---|---:|---:|---:|---:|---:|
| DIOR-R | raw_confidence | 0.022527 | 0.038353 | 0.497940 | 0.045554 | 0.053362 |
| DIOR-R | linear_source_frozen | 0.023960 | 0.044758 | 0.644747 | 0.048073 | 0.053273 |
| DIOR-R | tta_angle | 0.021641 | 0.038742 | 0.504218 | 0.043150 | 0.051031 |
| DIOR-R | tta_localization | 0.022142 | 0.037808 | 0.485081 | 0.044361 | 0.052575 |
| DIOR-R | S0 | 0.021180 | 0.035719 | 0.432114 | 0.042696 | 0.051361 |
| FAIR1M | raw_confidence | 0.031327 | 0.061436 | 0.900808 | 0.062763 | 0.064289 |
| FAIR1M | linear_source_frozen | 0.031811 | 0.062856 | 0.934088 | 0.063348 | 0.064557 |
| FAIR1M | tta_angle | 0.028222 | 0.051904 | 0.677398 | 0.057609 | 0.061796 |
| FAIR1M | tta_localization | 0.030981 | 0.059511 | 0.855704 | 0.062411 | 0.064409 |
| FAIR1M | S0 | 0.029249 | 0.054583 | 0.740174 | 0.058972 | 0.063059 |
| SODA-A | raw_confidence | 0.027008 | 0.051883 | 0.805310 | 0.054062 | 0.056955 |
| SODA-A | linear_source_frozen | 0.026979 | 0.052375 | 0.818604 | 0.053793 | 0.056695 |
| SODA-A | tta_angle | 0.025177 | 0.046706 | 0.664333 | 0.050820 | 0.054925 |
| SODA-A | tta_localization | 0.026145 | 0.048980 | 0.726761 | 0.052572 | 0.056595 |
| SODA-A | S0 | 0.025226 | 0.046610 | 0.662821 | 0.050850 | 0.055570 |

`learned_EQS` 仅作为 descriptive comparator，未驱动候选状态；其完整指标保留在 `track_m_metrics.csv`。

### 3.2 状态证据

Track M 唯一状态为 **`METRIC_REVERSAL`**：

- DIOR-R：S0 的 NRC/AURC 优于 `tta_angle`，但 Risk@90 为 0.051361，高于 `tta_angle` 的 0.051031。
- SODA-A：S0 的 NRC/AURC 略优于 `tta_angle`，但 AUGRC、Risk@70、Risk@90 均更差。
- `tta_angle` 还在 FAIR1M 和 SODA-A 的 AUGRC 上低于 S0；因 `METRIC_REVERSAL` precedence 更高，最终状态不改写为 `BASELINE_DOMINATED`。

10,000 次 paired cluster bootstrap 使用 seed 20260809、replicate 0..9999、39 个实际 worker 与 synchronized multiplicities。S0-minus-`tta_angle` AUGRC 的 95% 区间为：DIOR-R `[-0.000568, -0.000360]`，FAIR1M `[0.000816, 0.001236]`，SODA-A `[-0.000140, 0.000241]`。这些区间作为可行性证据，不升格为正式科学确认。

## 4. Track D：四候选审计

| Candidate | Remote sensing | Local data | Common reproducible families | Prior outcome | Final state | 关键依据 |
|---|---:|---:|---:|---:|---|---|
| AI-TOD-R | 是 | 否 | 0 | 否 | `LICENSE_BLOCKED` | 官方页可访问，但页面 CC-BY-SA 不能无歧义关闭数据集 research-use/redistribution 条款；资产亦缺失 |
| UAV-OBB | 是 | 否 | 0 | 否 | `MISSING_ASSET` | 文章/数据声明 CC BY 4.0；本地数据、兼容环境及公共三-detector-family 资产不存在 |
| ShipRSImageNet | 是 | 否 | 0 | 否 | `LICENSE_BLOCKED` | README 声称 Apache-2.0，但所链 LICENSE 返回 404，GitHub API 未识别 license；资产亦缺失 |
| ICDAR-MLT | 否，仅 auxiliary | 否 | 已登记 4 个 model families，但无本地数据 | 是 | `CONTAMINATED` | `pth_data/readme.md` 已登记 ORCNN/PSC/ARS-DETR/LSKNet 的 ICDAR 模型和 AP outcome；污染 precedence 最高 |

四候选官方来源均保存 URL、retrieval date、HTTP status、bytes、SHA256、headers 和 stderr。ICDAR 官方 HTTPS 首次因证书链失败，失败证据保留；同 URL 的只读 `--insecure` HTML 取证成功。ShipRSImageNet 的 README、LICENSE 404 body 和 GitHub repository API 响应分别保存，未将 README 声明自动视为独立 license closure。

真实 prior-outcome 搜索覆盖 Git-tracked/persistent text、项目记录、`pth_data/readme.md` 及 dataset root filename/stat-only 视图。ICDAR 的四套已登记 config/checkpoint/log 实体及完整 SHA256 位于 `track_d_icdar_registered_assets.csv`。未打开任何候选 annotation，也未计算候选 outcome。

Track D 有效 remote-sensing candidate 数为 0，不存在共同的至少三 detector-family 可复算集合。

## 5. 联合 gate 与科学结论

```text
Track M = METRIC_REVERSAL
eligible remote-sensing Track D candidates = 0
common >=3-family set = false
future target-label tuning needed = false
joint gate = FAIL_TO_MEASUREMENT_ONLY
```

因此，本轮不授权未来方法设计、数据下载、训练、推断或 label access。现有密封资产没有同时支持稳定 Track M 候选和可执行 Track D 组合；后续只能沿 measurement-only 写作处理。该结论不是 venue readiness，也不是全项目完成声明。

## 6. 独立验证与 mutation

独立 validator 从 raw sealed inputs 重读 source hashes、row/cluster evidence，并以 `atol=1e-12, rtol=0` 重算全部 point metrics、Track M state、Track D precedence 与 joint gate；它不信任 generator gate token。结果为 `PASS`，10,000 bootstrap replicates 完整，worker 数为 39，source/registered-asset hash failure 均为 0。

在隔离 hard-link 副本中分别执行四项真实 mutation；变异文件先解除 hard link，未改 sealed source。四次 validator 均以 exit code 2 拒绝：

| Mutation | 变异对象 | 原/变异哈希是否不同 | Validator exit |
|---|---|---:|---:|
| score byte | `track_m_rows/A.parquet` | 是 | 2 |
| delete cluster | `track_m_cluster_universe.csv` | 是 | 2 |
| fake prior hit | `track_d_prior_outcome_hits.csv` | 是 | 2 |
| manifest hash | `evidence_manifest.json` | 是 | 2 |

每项的命令、cwd、时间、原始/变异 SHA256、stdout/stderr SHA256 位于 `mutations/mutation_index.csv`；临时副本已删除，仅保留验证证据。

## 7. 证据封存与完成清单

- Runtime protocol：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/protocol.json`
- Track M inventory/metrics/curves/bootstrap/state：同 runtime root 下 `track_m_*`
- Track D inventory/sources/prior hits/state：同 runtime root 下 `track_d_*`
- Joint gate：`joint_gate.json`
- Independent validation：`validator.json`
- Execution/resource evidence：`execution_ledger.csv`、`resource_telemetry.csv/json`
- Protocol closure：`protocol_closure.md`
- Evidence manifest path：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/evidence_manifest.json`
- Evidence manifest bytes：`12192`
- Evidence manifest SHA256：`acad47663d20df3425e69b4a71496557cc4d98f14f44a1c1d8dce5b1e6203a04`

completed_phases: HTTPS pull/preflight; rule and protected-file verification; Track M byte inventory; fixed-score derivation; reference-toy verification; unique-threshold point metrics and curves; 10,000 paired cluster bootstrap; Track M state; all-four Track D official-source, license, asset, angle-contract and prior-outcome audits; Track D state; joint gate; independent raw-input validation; four isolated mutation tests; evidence manifest and protocol closure; single result commit preparation; HTTPS publication preparation.

omitted_phases: none.

计划外观察仅有两项：ICDAR-MLT 在 `pth_data` 中存在明确 prior model/metric lineage，因此必须由原先的 license/missing 直觉升级为 `CONTAMINATED`；ShipRSImageNet README 的 license 声明缺少可取证 LICENSE 文件，因此按 precedence 为 `LICENSE_BLOCKED`。二者均保留全部伴随缺失事实，没有改变预注册状态规则。

最终 Git commit 与 push 后外部回执按合约不回写本报告。发布后应从远端对象重新计算本报告所记录的 manifest bytes/SHA256，并核验 remote SHA 等于 local final SHA。
