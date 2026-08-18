---
schema_version: 2
plan_id: c-r042-oer-stagea-cheap-kill-20260817
dispatch_id: orientbench-c-r042-oer-stagea-cheap-kill-20260817
initiator: C
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 9e80dd6bf2a3b16158cdfe019724ca81479e83ab
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15 批准 OER-OBB 设计；用户 2026-08-17：『暂时不用等B了，你直接决定。』"
evidence_cutoff: 2026-08-17T22:25:00-07:00
scientific_snapshot:
  primary: 9e80dd6bf2a3b16158cdfe019724ca81479e83ab
  input_rows: "r036 qsetod_rows.parquet，616184 行，8 units，Git blob 1b348e35dfbe0a699a7bc6cbe79e639fb25384f5，SHA-256 bb4184089a0cb9e0584cdf9fe340fe76a5d831090f07a6bc0c73e4499ac8da51"
  excluded_assets: "r040/r041 panorama assets 不进入 primary、训练、调参或 gate；DOTA-v2.0 与 SODA-A official test 全部禁触"
server_report_path: dis/server_reports/orientbench-c-r042-oer-stagea-cheap-kill-20260817/SERVER_EXECUTION_REPORT.md
read_set:
  - audit_bundles/r036/inputs/qsetod_rows.parquet
  - audit_bundles/r036/inputs/cluster_universe.csv
  - audit_bundles/r036/inputs/preparation_summary.json
  - audit_bundles/r036/inputs/source_inventory.csv
  - audit_bundles/r036/inputs/join_audit.csv
  - dis/reviews/C/orientbench-c-r038-oerobb-method-proposal-20260815.md
  - dis/reviews/B/orientbench-c-r038-oerobb-method-open-attack-20260815.md
  - dis/reviews/C/orientbench-r041-postpull-protocol-drift-review-20260817.md
write_set:
  - outputs/persistent_artifacts/orientbench_oer_stagea_r042_20260817/**
  - top_journal_v3_reaudit_055/oer_stagea_r042_20260817/**
  - audit_bundles/r042/**
  - dis/server_reports/orientbench-c-r042-oer-stagea-cheap-kill-20260817/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 0
    gpu_hours_max: 0
    cpu_core_hours_max: 448
  wall_time:
    seconds_max: 43200
  data:
    allowed_dataset_ids:
      - repository-tracked-r036-evidence-readonly
    read_bytes_max: 1099511627776
    write_bytes_max: 34359738368
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_oer_stagea_r042_20260817/
      - top_journal_v3_reaudit_055/oer_stagea_r042_20260817/
      - audit_bundles/r042/
      - dis/server_reports/orientbench-c-r042-oer-stagea-cheap-kill-20260817/
      - claude_code_and_supervisor.md
    bytes_max: 34359738368
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - outputs/persistent_artifacts
  - audit_bundles/r042
gates:
  - gate_id: G0_INPUT_AND_IMPLEMENTATION
    rule: "五个冻结输入逐 blob/bytes/SHA 核验；616184 行、A-H 单元计数、schema、cluster universe、finite/key invariants 全过；production tests 先红后绿；无 forbidden path access。任一失败为 failure_early_stop / NOT_ADJUDICATED。"
  - gate_id: G1_OER_SURVIVAL
    rule: "PROCEED_OER 当且仅当 8 单元中至少 5 个满足 Delta_AUGRC>=0.005、cluster 95% CI_low>0、Holm-8 p<0.05，且至少含 1 个 DOTA 单元、2 datasets、2 detector families；两个 dataset equal-unit aggregates 同样满足 point/CI/p；所有 witness 的 equal-class/common-support 方向为正、permutation residual ratio<=0.30，且 OER 不被未正交化 Z+E 以 dataset aggregate Delta>0.001 稳定支配。否则 REJECT_OER_METHOD。"
early_stop_conditions:
  - 只有 G0 技术/输入失败、禁止路径访问、资源上限或 43200 秒墙钟耗尽允许提前停止；科学负结果必须完整计算 8 units、两个 dataset aggregates、全部 controls 后再裁决。
kill_conditions:
  - 读取、stat、glob、hash 或打开 DOTA-v2.0、SODA-A official test、r040/r041 panorama 全表或任何新 dataset/label；这些对象不属于本轮。
  - 把 angle_error、signed_residual_deg、gt_ar、unit/dataset target identity 或任何其派生结果放入预测特征、标准化、超参、模型选择或阈值选择。
  - GPU、神经网络训练、host detector 推理、下载、修改 r036 输入、改 split/metric/gate/seed、丢弃不利 unit、替补数据集或调整 effect floor。
  - 伪造/硬编码验证、gate、访问日志、资源、mutation 或 completion；覆盖旧报告/产物；越界写入。
completion_mapping:
  full_completion:
    execution_status: complete
    receipt_first_line: 执行完毕
  gated_early_stop:
    execution_status: complete
    receipt_first_line: 执行完毕
  failure_early_stop:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
  partial:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
  protocol_drift:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
---

# r042 OER Stage A 生死门（C 发起；CPU-only；零新标签）

> **执行者要求：**按本文任务顺序执行；先写测试和协议，再写 production。不得改动本计划或用 B 的 r039 计划替代。

## 1. 科学问题与论文决策

本轮只回答一个问题：在同时留出目标 dataset 与 detector family，并排除 confidence、预测 AR、面积和类别的可预测贡献后，`u_axis/missing_fraction/iou_loss` 是否仍能稳定改善 matched-TP、`GT_AR>=2.1` 条件下的方向失效排序？

这是 OER/OER-D 路线的最终 cheap kill。`PROCEED_OER` 只允许下一轮撰写 OER-D 训练规格，不升级 venue；`REJECT_OER_METHOD` 立即终止 OER/OER-D 顶刊方法线，论文按测量/诊断型 strong JSTARS/Remote Sensing 收口。两种科学结果只要完整执行都属于 `full_completion`。

当前主张严格限定为 matched true positives 的方向失效排序。不得宣称因果识别、完全去混杂、prediction-set coverage、跨域确认或 JPRS/TGRS ready。

## 2. 冻结输入与单元注册

只读五个 Git-tracked r036 输入；开始时从 committed blob 重算 bytes/SHA-256：

| path | blob | bytes | SHA-256 |
|---|---|---:|---|
| `audit_bundles/r036/inputs/qsetod_rows.parquet` | `1b348e35dfbe0a699a7bc6cbe79e639fb25384f5` | 34,796,105 | `bb4184089a0cb9e0584cdf9fe340fe76a5d831090f07a6bc0c73e4499ac8da51` |
| `audit_bundles/r036/inputs/cluster_universe.csv` | `a24ef2a16fee73b63e80b9f9fdaacfca26565df4` | 176,693 | `4131f34dbeaa442e1328a7f3fb8b2306ac7ac40d09563561ad504b74e8bedb53` |
| `audit_bundles/r036/inputs/preparation_summary.json` | `52b5f600a8944f9029059cb076ddd42042dcb060` | 599 | `2c10a07c468ced8de8fafde88c2782a530fd175fd53cb6977fd02cfae21d07af` |
| `audit_bundles/r036/inputs/source_inventory.csv` | `1808ab0173f1a4558915ea81a69af659bc6abde3` | 3,351 | `3205f62ba8729fd89c89b80cdf2f65971bccce758e0898115342b955353ed8e1` |
| `audit_bundles/r036/inputs/join_audit.csv` | `4bd627069686ce92c0f0ebf3cc82cc7e698129b8` | 475 | `64bf9339a93e3a78ac83937ce670ca20154e9fbe5a2a265d39f82a7d7417834f` |

冻结 registry：A=`DIOR-R/PSC`，B=`DIOR-R/Oriented R-CNN`，C=`DIOR-R/RTMDet`，D=`FAIR1M/PSC`，E=`SODA-A/PSC`，F=`SODA-A/Oriented R-CNN`，G=`DOTA-v1.0/Oriented R-CNN`，H=`DOTA-v1.0/RTMDet`。冻结行数 A=43,848、B=47,887、C=47,881、D=26,108、E=157,586、F=192,249、G=48,889、H=51,736，总数 616,184。

主域是 `gt_ar>=2.1`；主标签 `Y=clip(angle_error/90,0,1)`。`gt_ar` 和 `angle_error` 只准用于揭示后的 eligibility/evaluation，严禁进入任何 fit、transform 或 selection。all-AR 与误差段 `[0,30) / [30,60) / [60,90]` 只作描述性敏感性。

## 3. 文件与职责

服务器在唯一 runtime root 下创建以下聚焦文件：

- `protocol_r042.json`：冻结 registry、columns、模型参数、seed、bootstrap 和 gate。
- `test_contract_r042.py`：G0 fixture、split/leakage/metric/bootstrap/gate/mutation tests。
- `fit_oer_r042.py`：唯一 production 拟合与 OOF/held-out 预测生成端。
- `metrics_r042.py`：AUGRC、fixed-coverage risk、cluster bootstrap、Holm 与 controls。
- `validate_r042.py`：不 import `fit_oer_r042.py`；从输入与已封存 predictions 重算 split/key/leakage、全部指标、bootstrap summary 和 gate，不重新拟合模型，也不声称独立模型实现。
- `access_trace_r042.csv`：实际 read/open 路径、phase、pid、bytes、SHA-256；不得事后用计划 read_set 批量生成。
- `execution_ledger_r042.csv`：命令、cwd、start/end、exit、stdout/stderr SHA-256。

所有大表放 runtime；`audit_bundles/r042/` 只提交代码、协议、完整小表、manifest、验证结果、mutation 结果和每 unit 100 行 deterministic sample。

## 4. 先测试后生产

### Task 1：RED fixture

在读全量 parquet 前，`test_contract_r042.py` 用内置 24 行 synthetic fixture 覆盖：

1. dataset 与 family 同时留出；
2. `Y/angle_error/gt_ar/unit/dataset` 进入 feature matrix 必须非零退出；
3. source-only scaler/encoder，unseen target class 映射 `__OTHER__`；
4. weighted AUGRC 与 Risk@70/90 固定手算向量；
5. zero-eligible cluster 保留、同步 multiplicity 与 Holm-8；
6. duplicate key、nonfinite、train-target overlap、gate token tamper 必须拒绝。

先运行并保存 production 尚不存在导致的 RED；实现后同一测试必须 GREEN。不得把预期布尔硬编码成测试结果。

### Task 2：G0 输入与访问闭包

核验五个 committed inputs 的 blob/bytes/SHA、schema、行数、unit counts、唯一 `row_id`、有限值、cluster universe 完整性和 r036 join audit。启动 production 前保存 `input_admission_r042.json`。

执行进程必须使用显式 allowlist 打开五个输入和本轮代码/runtime。通过 `strace -f -e trace=open,openat,statx` 保存原始 trace；validator 对 `/home/rspip/cqc/data/`、`orientbench_panorama_r040`、`orientbench_panorama_r041`、`dota2.0`、`official test` 路径做零命中检查。系统库/code/output opens 单列，不得伪装成 scientific reads。

## 5. 冻结建模协议

### 5.1 双重 held-out

对每个目标 unit `u`，训练行必须同时满足：

```text
row.dataset != dataset(u) AND row.detector != detector_family(u)
```

也就是目标 dataset 的全部 units 与目标 family 的全部 units 都不进入训练。任何 target row、同 dataset row 或同 family row 出现在 fit index 都是 hard failure。

内层 5-fold 按 `dataset|cluster` 分组，fold 固定为 `MD5(UTF8(dataset + "|" + cluster)) mod 5`。所有标准化、class vocabulary、分位数和模型均只从当前外层训练集得到；class one-hot vocabulary 固定为排序后的 source classes 加一个保留的 `__OTHER__` 列，目标未见类别只能进入该列。

### 5.2 特征与模型

Nuisance `Z` 精确为：`detection_score, log_pred_ar, log_area, class_name`。`detector family` 只用于 held-out grouping，不进入预测特征。Evidence `E` 精确为：`u_axis, missing_fraction, iou_loss`。不得加入 r041 新列或 `detection_score` 的重复副本。

每个外层训练集内：

1. 用 inner-OOF `HistGradientBoostingRegressor(loss=squared_error,max_iter=200,max_leaf_nodes=15,learning_rate=0.05,l2_regularization=0.1,random_state=20260817)` 拟合 `m_Y(Z)`；
2. 用同参数三个独立模型拟合 `m_Ej(Z)`；
3. 以 inner-OOF 残差 `tilde_Y=Y-m_Y(Z)`、`tilde_E=E-m_E(Z)` 拟合 `StandardScaler + Ridge(alpha=1.0,fit_intercept=true)`；
4. 在全部外层训练行重拟合 nuisance models，保持 Ridge 来自 OOF residual；
5. 目标风险 `R_OER=clip(m_Y(Z)+h(tilde_E),0,1)`；`lambda` 固定为 1，不搜索。

部署基线精确为：`1-detection_score`、pure-AR HGB、`m_Y(Z)`、generic TTA（训练集 z-score 后对 `u_axis/missing_fraction/iou_loss` 等权平均）、未正交化 HGB `Z+E`。所有监督基线使用与 OER 相同的外层训练集和 inner folds；不做目标校准。每 unit 的 strongest deployable baseline 是这些基线中目标 AUGRC 最低者，选择只用于保守评估，不回写模型。

## 6. 指标、controls 与统计

风险分数越大表示越可能失败。AUGRC 的唯一公式为：按风险升序稳定排序，把数值相等的 risk 作为完整 tie group；组权重 `W_g=sum(w_i)`、组损失 `L_g=sum(w_i*Y_i)`、总权重 `W=sum_g W_g`、累计 generalized risk `G_g=sum_{h<=g}L_h/W`、`G_0=0`，最终 `AUGRC=sum_g 0.5*(G_{g-1}+G_g)*(W_g/W)`。不得再次把已经归一化的 `Y` 除以 90。validator 以独立排序/累计实现对 production 输出逐 unit 重算，容差 `atol=1e-12, rtol=0`。Risk@70/Risk@90 从低风险端纳入完整 tie groups，包含第一个使累计 coverage 达到或超过目标 coverage 的完整组，并报告实际 coverage。

主差值：

```text
Delta_u = AUGRC(strongest deployable baseline) - AUGRC(OER)
```

bootstrap 固定 B=10,000、seed=20260817；从完整 image/mother cluster universe 有放回抽与 universe 等长的 cluster multiset，保留 zero-eligible clusters。同 dataset 各 units 在同 replicate 使用同一 cluster multiplicity；先算 unit，再对 dataset 内 units 等权平均。恰好 10,000 个 finite replicates，不得丢弃后补抽。95% percentile CI；one-sided centered p=`(1 + count((Delta_b-Delta_hat)>=Delta_hat))/(10001)`；8 unit p 做 Holm-8，两个 dataset aggregates 各自报告 raw p。

controls：

- equal-class：目标中 eligible rows>=100 且 source 可见的类别逐类算 AUGRC 后等权平均；
- common-support：class source 可见，且 target `log_pred_ar/log_area` 均落在该 class 的 source 1%--99% 区间；
- permutation：在 target 的 `class × source-defined AR quintile × source-defined area quintile` 内整行置换 `tilde_E`，100 次、seed=`20260817+unit_index`；ratio=`median(max(Delta_perm,0))/Delta_observed`；
- leakage disclosure：用 source-OOF `tilde_E` 重构连续 Z 的 cross-validated R²、重构 class 的 balanced accuracy，并做逐 E 成分删除；只报告，不代替 permutation gate。

## 7. 唯一科学裁决

unit witness 同时要求：`Delta_u>=0.005`、95% CI_low>0、Holm-8 p<0.05、equal-class Delta>0、common-support Delta>0、permutation ratio<=0.30。

`PROCEED_OER` 当且仅当：

1. unit witnesses 至少 5/8；
2. 至少一个 witness 来自 G/H DOTA；
3. witnesses 覆盖至少 2 datasets 与 2 detector families；
4. 至少两个 dataset equal-unit aggregates 各自 `Delta>=0.005`、CI_low>0、raw p<0.05；
5. 在这些 dataset aggregates 上，未正交化 `Z+E` 相对 OER 的优势不同时满足 point>0.001 且 CI_low>0。

否则唯一裁决是 `REJECT_OER_METHOD`。不得使用 `INCONCLUSIVE` 延长该方法路线；完整负结果必须照常提交。任何科学结果都不读取 r040/r041、DOTA-v2.0 或 SODA official test 来救场。

## 8. 验证与 mutation

生产完成后冻结 `heldout_predictions.parquet`、`bootstrap_replicates.parquet` 和全部小表，再运行 validator。validator 必须逐字段保存 expected/actual/max_abs_error/witness，且至少执行六个真实 subprocess mutations：

1. 一个 fit index 注入目标 dataset row；
2. feature list 注入 `angle_error`；
3. duplicate `row_id`；
4. 一个 evidence 值改为 NaN；
5. 一个 bootstrap multiplicity 改写；
6. 把最终科学 token 翻转。

每项 pristine exit=0、mutated exit!=0；mutation 在临时 copy 上执行，不改 pristine runtime。manifest 在所有 runtime 输出冻结后生成，自身标 `N/A_SELF_REFERENCE`，不得声称核验未来 Git commit 或自身哈希。

## 9. 提交、报告与回执

允许实现/测试 seal commit 与结果 commit，但最终报告只有一个。报告必须包含：冻结身份、输入核验、精确命令/资源、8 units 全表、两个 dataset aggregates、所有 baselines/controls、bootstrap/Holm、permutation/leakage/ablation、validator/mutations、访问路径、偏差、唯一科学 token 和 completion mode。

缺任何 unit、control、bootstrap、mutation、访问证据或报告字段都是 `partial/protocol_drift`，不得写完整执行。服务器最终对话严格两行：

```text
执行完毕
dis/server_reports/orientbench-c-r042-oer-stagea-cheap-kill-20260817/SERVER_EXECUTION_REPORT.md
```

只有 failure/partial/protocol drift 时首行改为 `未执行完毕`，第二行路径不变。
