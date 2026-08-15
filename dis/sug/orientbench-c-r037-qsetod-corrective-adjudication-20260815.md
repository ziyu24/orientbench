---
schema_version: 2
plan_id: c-r037-qsetod-corrective-adjudication-20260815
dispatch_id: orientbench-c-r037-qsetod-corrective-adjudication-20260815
initiator: C
activation_authorization:
  mode: delegated
  delegate: B
  reference: "C owner delegation frozen in this plan; user 2026-08-15:『给出给服务器执行的内容。』"
closure_authorization:
  mode: delegated
  delegate: B
  reference: "C owner delegation frozen in this plan; user 2026-08-15:『给出给服务器执行的内容。』"
base_sha: 380e7f20a2baf272fd80d5cf7d2cb87ce76e85de
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15：『给出给服务器执行的内容。』——承接 C 已明确说明的 r037 CPU-only 纠错实验；不含 GPU、神经网络训练、新数据或清白 endpoint 标签读取。"
evidence_cutoff: 2026-08-15T00:44:38-07:00
scientific_snapshot:
  primary: 380e7f20a2baf272fd80d5cf7d2cb87ce76e85de
  r034_terminal: K1_K2_KILL_STRONG_JSTARS_JOINT_BC_FINAL
  r036_execution: FULL_COMPLETION
  r036_scientific_state: CONTESTED
  current_level: STRONG_JSTARS_OR_REMOTE_SENSING
review_mode: open
server_report_path: dis/server_reports/orientbench-c-r037-qsetod-corrective-adjudication-20260815/SERVER_EXECUTION_REPORT.md
read_set:
  - repository tracked governance, r034/r036 reports, plans, code, manifests and audit bundles at the dispatch commit
  - /home/rspip/cqc/pro/study/pth_data/readme.md for readability and SHA-256 only
  - audit_bundles/r036/inputs/qsetod_rows.parquet at Git blob 1b348e35dfbe0a699a7bc6cbe79e639fb25384f5, 34796105 bytes, SHA-256 bb4184089a0cb9e0584cdf9fe340fe76a5d831090f07a6bc0c73e4499ac8da51
  - audit_bundles/r036/bundle_manifest.csv at Git blob 68da07a9c4c2864a4f4070d0213ba803cbf2a8fd, 5668 bytes, SHA-256 f199aeece6fa4595e560520d08c96c9d4b016c3960d727c5c6249471e1d2891f
  - audit_bundles/r036/implementation_a/source_oof_predictions.parquet at Git blob d31618225a7d8bf96fcb912e35ad0263e5fd4109, 9657188 bytes, SHA-256 2b87f19da23195529e7183d6334c691bd74f44d9d3f751c15affb3872c6e4596 for audit comparison only, never as the r037 modeling source
  - audit_bundles/r036/implementation_a/target_predictions_common_support.parquet at Git blob 67f5d309420a5aa1fb97472c58c870ca4fccbc2e, 8579581 bytes, SHA-256 b1a0e84c52f914875dc49a37da00e031f4f168769a6b5469745d3568058b8995 for audit comparison only, never as the r037 modeling source
  - audit_bundles/r036/endpoint_audit/endpoint_consumption_audit.csv as inventory only; DOTA-v2.0 and SODA-A official-test label roots must not be opened, decoded, hashed, listed or used
write_set:
  - outputs/persistent_artifacts/orientbench_qsetod_corrective_r037_20260815/**
  - top_journal_v3_reaudit_055/qsetod_corrective_r037_20260815/**
  - audit_bundles/r037/**
  - dis/server_reports/orientbench-c-r037-qsetod-corrective-adjudication-20260815/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 0
    gpu_hours_max: 0
    cpu_core_hours_max: 112
  wall_time:
    seconds_max: 43200
  data:
    allowed_dataset_ids:
      - repository-tracked-evidence
      - existing-frozen-orientbench-r036-evidence-readonly
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_qsetod_corrective_r037_20260815/
      - top_journal_v3_reaudit_055/qsetod_corrective_r037_20260815/
      - audit_bundles/r037/
      - dis/server_reports/orientbench-c-r037-qsetod-corrective-adjudication-20260815/
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
  - gate_id: G_EVIDENCE
    rule: TTA increment is tested only as GCT minus GC; PASS requires at least 4 of 8 unit witnesses spanning at least 2 target datasets and 2 detector families, with all three endpoint CI lows positive, the intersection-union p passing Holm-8 at 0.05, Spearman gain at least 0.02 and AUGRC gain at least its frozen floor.
  - gate_id: G_SET
    rule: evaluated only after G_EVIDENCE passes; every held-out unit and alpha must satisfy one-sided overall and supported-cell coverage deficits, width, near-full and fallback limits, while GCT must improve proper interval score over GC in at least 4 of 8 units spanning at least 2 datasets and 2 detector families.
  - gate_id: G_MULTIMODALITY
    rule: exact diptest is optional and never rescues G_EVIDENCE or G_SET; unavailable or unverified exact implementation forces MULTIMODALITY_NOT_ADJUDICATED and deletion of the multi-arc claim.
early_stop_conditions:
  - G_EVIDENCE fails after complete T2 bootstrap and validation; report QSETOD_KILLED_CORRECTED_EVIDENCE and stop before calibration/multimodality while still returning gated_early_stop complete.
  - wall time reaches 43200 seconds before a hard scientific gate is complete; return failure_early_stop incomplete.
kill_conditions:
  - any neural-network training, detector forward/inference, GPU use, download, new dataset access, or access to DOTA-v2.0/SODA-A clean endpoint labels
  - any target-unit angle label passed to fit, threshold selection, feature selection, hyperparameter selection or model selection
  - treating GCT-minus-G or GC-minus-G as the registered TTA evidence increment
  - using symmetric absolute coverage deviation as validity failure; only lower-tail coverage deficit is permitted
  - using r036 generated predictions as r037 model outputs, changing r034/r036 artifacts, writing outside write_set, hardcoding validator/mutation outcomes, or exceeding resource caps
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r037 Q-SetOD 纠错性裁决：隔离 confidence、修正覆盖语义

## 0. 唯一问题与解释边界

本轮只回答两个连续问题：

1. 在 geometry、class、size 与 detector confidence 已经用尽后，TTA 证据 `u_axis + missing_fraction + iou_loss` 是否仍提供可迁移的方向误差信息？
2. 若有，该证据能否改善 source-calibrated axial interval 的 proper interval score，同时保持非退化的经验下界覆盖？

本轮是已见 r036 结果后的 corrective adjudication，不得称 prospective、independent confirmation 或新 endpoint。它不训练 Q-SetOD，不生成方法论文正结果，不读取清白 endpoint；PASS 只授予以后另行审批有限训练的资格。

## 1. T0：身份、输入和零扩张预检

服务器必须先完成：

- `git pull --ff-only`，确认 post-pull HEAD 精确等于 dispatch commit，worker 为 `server-primary`，tracked/index clean；
- 核验 active `dis/sug.md` 与本 committed plan 的 Git blob OID/SHA-256 完全相同；
- 读取并哈希 `pth_data/readme.md`；
- 在任何科学输入读取前提交并推送唯一 `STARTED.json`；
- 用 `git cat-file blob` 逐项核验 front matter 锁定的 r036 输入 bytes/SHA-256；
- 确认五个 write roots 在本轮开始前均不存在，旧 r034/r036 路径只读；
- 不访问 DOTA-v2.0、SODA-A official-test 或任何新标签根。只可逐字携带 r036 已提交的 endpoint inventory，并明确 `inventory_not_authorization=true`。

输入 cohort 固定为 r036 的 616,184 行 A--H。八个 held-out 配置、source/target unit、fold seed `20260814`、image/mother cluster、source-defined common support 全部沿用 r036；不得增删 unit、改 class alias、AR/size bin 或目标行。

## 2. T1：分相数据视图与拟合边界

新建独立 r037 代码目录，至少包含：

- `prepare_views_r037.py`
- `implementation_a.py`
- `implementation_b.py`
- `compare_ab.py`
- `validate_r037.py`
- `run_mutations.py`
- `finalize_r037.py`
- `verify_bundle_manifest.py`

`prepare_views_r037.py` 从锁定的 r036 rows 生成并哈希三类 runtime views：source labeled partitions、target covariates-only partitions、target evaluation labels。模型拟合 subprocess 只允许打开前两类；target predictions 完成并封存 SHA-256 后，独立 evaluation subprocess 才可打开第三类。该隔离不恢复前瞻身份，只防止计算实现把 target labels 传入 fit。

每次 estimator `fit` 必须在 append-only ledger 记录 source units、row count、cluster count、feature schema、label schema、target-label rows in fit=`0`、start/end/exit。validator 从代码执行输入和 ledger 重建这些事实，不能只信布尔字段。

## 3. T2：三层嵌套证据增量（唯一 primary）

### 3.1 模型

所有层使用相同 CPU `HistGradientBoostingRegressor`：`max_iter=200`、`max_leaf_nodes=15`、`learning_rate=0.05`、`random_state=20260814`、`early_stopping=false`。每层分别拟合 mean 与 0.75 quantile：

- `G = log_pred_ar + log_area + class_onehot`
- `GC = G + detection_score`
- `GCT = GC + u_axis + missing_fraction + iou_loss`

source OOF 使用按 image/mother cluster 固定的 5 folds；target prediction 使用全部 source rows 拟合后冻结。任何层不得拥有另一层没有登记的预处理、权重或超参数。

### 3.2 Common support

每个配置仅在 source/target 共有 semantic class、source-defined predicted-AR quintile 和 source-defined size quintile 的非空交叉格评测。source 与 target 原始 keys、保留/排除 keys、各 cell rows/clusters 和 sorted-key SHA-256 必须持久化；target labels 不参与 support 构造。

### 3.3 指标与精确 bootstrap

注册的 TTA 增量只能是 `GCT − GC`：

- `Delta_rho = Spearman(GCT,y) - Spearman(GC,y)`；
- `Delta_q75 = pinball_0.75(GC,y) - pinball_0.75(GCT,y)`；
- `Delta_AUGRC = AUGRC(GC,y) - AUGRC(GCT,y)`，risk=`clip(angle_error/90,0,1)`。

`G→GC` 与 `G→GCT` 仅作诊断，禁止进入 gate 或被称为 TTA evidence。

每配置按完整 target cluster universe 有放回抽取与 universe 等长的 cluster multiset，`B=20000`，seed=`20260815 + config_index`；同一 multiplicity 同时施加 G/GC/GCT 与三个 endpoints。零行 cluster 保留。Spearman 必须等价于真实展开重抽样：对每个唯一值按 replicate multiplicity 重算 weighted midrank，再计算 weighted Pearson；禁止复用 observed-sample 固定 ranks。AUGRC 对相同预测值采用 whole-tie group，按 group coverage 增量做梯形积分，禁止 stable-row-order 拆 tie。

每 endpoint 保存 point、percentile 95% CI 和 `p=(1+count(Delta_b<=0))/(B+1)`。每 unit 的 intersection-union `p_unit=max(p_rho,p_q75,p_AUGRC)`；八个 `p_unit` 做 Holm-8。unit witness 当且仅当：三个 point 与 CI-low 均大于 0、Holm-adjusted `p_unit<=0.05`、`Delta_rho>=0.02`、`Delta_AUGRC>=max(0.0005,0.02*max(abs(AUGRC_GC),abs(AUGRC_GCT)))`。

`G_EVIDENCE=PASS` 当且仅当 8 个配置中至少 4 个 unit witnesses，且覆盖至少 2 个 target datasets、2 个 target detector families，并至少含 2 个 cross-dataset units。否则 `G_EVIDENCE=FAIL`，输出 `QSETOD_KILLED_CORRECTED_EVIDENCE`，完成 validator/mutation/bundle/report 后合规 gated early stop；不得进入 T3/T4。

## 4. T3：正确的 source-only interval transport

仅在 `G_EVIDENCE=PASS` 后执行。这里评测的是经验 transport，不宣称 covariate shift 下的 distribution-free target coverage。

### 4.1 两个 interval variants

- `GC interval`：source nonconformity=`angle_error/max(q75_GC_OOF,1 degree)`；target half-width=`q_source * max(q75_GC_target,1 degree)`。
- `GCT interval`：同式替换为 `q75_GCT`。

主 Mondrian bucket 仅用 source-defined predicted-AR quintile × predicted-size quintile，不使用 class。source cell 至少 200 rows 且 20 clusters才有 local threshold，否则回退 source global；阈值采用 finite-sample higher quantile。r036 的 class×AR bucket 只做 descriptive reproduction，不得进入 gate。

`alpha={0.1,0.2}`。轴向 interval half-width 上限 90°，full set width=180°。覆盖只按 `angle_error<=half_width`。

### 4.2 Validity 与 efficiency

每个 target unit/alpha 的 GCT interval 必须同时满足：

- overall coverage `>= nominal-0.05`；高于 nominal 不判 validity failure；
- 对 target rows≥200 且 clusters≥20 的每个 supported primary bucket，coverage `>= nominal-0.10`；若没有 supported bucket则失败；
- median width `<=30°`；width>150° rate `<=0.10`；global fallback rate `<=0.05`。

proper interval score 固定为 `IS_alpha = width + (2/alpha)*max(angle_error-half_width,0)`。paired gain=`mean(IS_GC)-mean(IS_GCT)`，正值为 GCT 更好。两个 alpha 的 standardized paired gains在每 replicate 内等权平均形成 unit set gain；沿用 T2 cluster multiplicities重算 20,000 次、95% CI、one-sided p 与 Holm-8。set witness 要求 point>0、CI-low>0、Holm-adjusted p≤0.05、relative gain≥0.02，且该 unit 两个 alpha 均通过全部 validity/efficiency 条件。

`G_SET=PASS` 当且仅当 8 个 unit 中至少 4 个 set witnesses，覆盖至少 2 个 datasets 和 2 个 detector families，并且全部 16 个 unit-alpha rows 都通过 overall validity；任何 unit 的 supported-bucket/width/near-full/fallback 硬条件失败也使 `G_SET=FAIL`。

## 5. T4：多峰主张的处理

启动时只检查现有环境能否 import 正式 `diptest`，记录包版本、module path 和文件 SHA-256，并用三个冻结 fixture 验证返回值范围与确定性。禁止联网安装、复制第三方源码或自制“近似 dip”。

- 若 exact implementation 不可用或 fixture 失败：`MULTIMODALITY_NOT_ADJUDICATED`，多峰/多弧机制从后续 claim 删除；不影响 G_EVIDENCE/G_SET。
- 若可用：在 r036 固定 536 strata 上重跑 exact Hartigan dip p<0.01 与 two-vs-one axial-mixture `Delta_BIC>10`，只有 row-weighted fraction≥0.10 才记 `MULTIMODALITY_SUPPORTED_R037`，否则 `MULTIMODALITY_PRUNED_R037`。

## 6. T5：唯一科学映射

按以下顺序，禁止改 gate 救场：

1. `G_EVIDENCE=FAIL` → `QSETOD_KILLED_CORRECTED_EVIDENCE`；当前论文按 strong JSTARS / Remote Sensing 收口，不再投入 Q-SetOD。
2. `G_EVIDENCE=PASS` 且 `G_SET=FAIL` → `QSETOD_EVIDENCE_SCORE_ONLY`；集合/覆盖主张删除，只保留 scalar evidence-quality 候选；不授权训练，当前论文不升档。
3. `G_EVIDENCE=PASS` 且 `G_SET=PASS`、多峰未支持 → `QSETOD_SINGLE_INTERVAL_PROCEED_CANDIDATE`；仅获得以后另行用户批准的小规模方法训练资格。
4. `G_EVIDENCE=PASS` 且 `G_SET=PASS`、exact 多峰支持 → `QSETOD_MULTIMODAL_PROCEED_CANDIDATE`；同样只获得有限训练资格。

任何 PASS 都不等于 TGRS/JPRS ready。只有以后训练后的方法在至少两个 held-out datasets、两个 families 和一个真正清白 endpoint 上通过完整检测代价与强基线，才可重评 venue。

## 7. T6：双实现、validator、mutation 与 bundle

- A/B 必须是两个不互相 import、不读取对方输出的实现；都从 r037 views 独立拟合 G/GC/GCT、构造 support、20,000 multiplicities、指标、Holm、interval 与 gate。
- comparator 必须逐字段核对 predictions、support keys、20,000 multiplicities、replicates、T2/T3 tables 与 final judgment，numeric `atol=1e-10, rtol=0`。
- raw validator 不 import A/B，不信 CSV gate；从 r037 views 独立重拟合全部模型、重生全部 multiplicities、重算 weighted midranks、whole-tie AUGRC、interval score、CI/p/Holm 与最终 token。validator 必须检查 target-label fit ledger 和 clean-endpoint zero-access。
- 至少七个真实临时副本 subprocess mutations并要求同一 validator 非零拒绝：把 registered increment 改成 GCT−G；把 detection_score 从 GC 移出；使用 fixed observed ranks；把 coverage 改回 absolute deviation；把 primary bucket 改为 class×AR；篡改 interval-score penalty；篡改 final token或 target-label fit ledger。
- bundle `audit_bundles/r037/` 保存代码、协议、输入 identity、views、predictions、support、replicates、tables、A/B comparator、validator、mutations、judgment 与 manifests；可引用 r036 locked blob而不复制大文件。每个 tracked object小于80 MiB。
- `bundle_manifest.csv` 最后生成，列出此前冻结的非 self bundle objects；self bytes/SHA 写 `N/A_SELF_REFERENCE`。post-manifest verifier只读校验所有非 self objects；server report不得声称哈希自身或未来 commit。

## 8. 资源、Git 与报告

正式 CPU 阶段设置 BLAS threads=1，workers=`ceil(0.8*detected_logical_cpu_count)`，每30秒记录 parent+children CPU/RSS/affinity；持续低于60%可用核且无记录理由为 protocol drift。GPU、CUDA、detector inference 和 neural training计数必须为0。

所有命令记录 cwd、完整 argv、start/end、exit、stdout/stderr SHA-256。科学产物完成后运行 validator、mutations、bundle verifier、`git diff --check`、write-set 检查和 B/受保护文件 blob检查；仅显式暂存 write_set tracked files。结果提交并显式 HTTPS push main，报告的 ending commit指向报告之前的结果 commit，禁止自引用。

唯一报告必须逐项披露：执行完整性、T2 三层结果与 confidence/TTA 分解、G_EVIDENCE、T3 16 rows及 proper interval score、G_SET、多峰状态、target-label fit guard、clean-endpoint zero-access、A/B/validator/mutations、偏差、资源、所有路径与最终 candidate token。

最终聊天严格两行：第一行只写“执行完毕”或“未执行完毕”；第二行只写 `dis/server_reports/orientbench-c-r037-qsetod-corrective-adjudication-20260815/SERVER_EXECUTION_REPORT.md`。
