---
schema_version: 2
plan_id: b-r036-qsetod-kill-study-20260814
dispatch_id: orientbench-b-r036-qsetod-kill-study-20260814
initiator: B
base_sha: 814a1639411a041270f7fd9c7909c613d44aa498
supersedes: null
implements: "C Q-SetOD 提案 §4.1 低成本 kill study（dis/reviews/C/orientbench-c-r035-qsetod-method-proposal-20260814.md）+ B 攻击修订（dis/reviews/B/orientbench-c-r035-qsetod-method-open-attack-20260814.md）"
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-14：『目前期刊级别不够，必须提升上去……你批判继承后（严厉的），直接给出服务器执行方案。』——授权 Q-SetOD 纸面杀伤实验（CPU-only，零训练、零 GPU、零新数据）"
scientific_snapshot:
  primary: 814a1639411a041270f7fd9c7909c613d44aa498
  r034_terminal: "K1_K2_KILL_STRONG_JSTARS（B/C 终局，不翻案；本轮不得触碰旧 selector 主张）"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与既有冻结 runtime/bundle 只读（八单元 enriched rows 优先取 audit_bundles/r034）
write_set:
  - outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/**
  - top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/**
  - audit_bundles/r036/**
  - dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/
      - top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/
      - audit_bundles/r036/
      - dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/
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
    rule: 预注册 KILL/PRUNE/PROCEED 判据（正文）；任何判定都是正常完整执行。validator 无输出强制。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 伪造或硬编码任何验证/变异结果；validator 含输出强制断言。
  - 训练神经网络、检测器 forward/inference、GPU 使用、下载新数据（本轮允许的拟合仅限 CPU 上的分位/线性/logistic/混合分布小模型，全部 cross-fitted 且 recipe 冻结于本计划）。
  - 任何 target 侧（held-out 检测器/数据集）angle label 进入任何拟合、阈值或模型选择——target 标签只用于评测。
  - 触碰 r034 终局判定或旧 selector 主张；修改冻结产物；写入越出 write_set；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r036 Q-SetOD 纸面杀伤实验（B 发起；零训练零 GPU，先杀便宜的）

## 一句话

在写任何训练代码之前，用八单元既有冻结数据回答 Q-SetOD 的三个生死问题：**(1) 图像证据是否携带几何之外的方向信息？(2) 方向残差里到底有没有多峰结构？(3) source-only 校准的方向集合在 held-out 上是否有效且非退化？** 外加一张清白 endpoint 消费审计表。全部预注册判据，杀死即止损。

## 数据与划分（全轮冻结）

八单元 enriched rows（优先 `audit_bundles/r034/` 的 616,184 行，含 gt_ar/log_pred_ar/class/angle_error/score 与 TTA 证据特征所需列；bundle 缺列时从冻结 features parquet 按 (image_id,pred_id) 连接补齐，连接零丢失）。**held-out 结构（捷径判定的核心）**：
- HO-detector：在 DIOR-R 内 train={A(PSC)}, test={B(ORCNN),C(RTMDet)}；反向 train={B,C}, test={A}。
- HO-dataset：train={DIOR-R 三单元}, test={FAIR1M D, SODA E/F, DOTA G/H}。
拟合侧仅用 train 单元的 source 行；5-fold cross-fitting，fold 按 image/mother cluster 切分，任何样本的基线/残差预测来自不含其 cluster 的 fold。seed=20260814。

## T1 endpoint 消费审计表（B 攻击 Q5）

以仓库历史为证，逐候选 endpoint（DOTA-v1.5/v2.0 标注、DIOR-R/FAIR1M/SODA 官方 test 侧、HRSC2016、遥感外 OBB）登记：是否被任何历史轮读取/拟合/裁决过、资产在服务器是否存在、合法性。输出 `endpoint_consumption_audit.csv`。**无一清白 → 报告显式声明 Q-SetOD venue 上限降为"JPRS/TGRS 带披露复用"。**

## T2 证据增量测试（primary；B 攻击 Q6）

- 几何基线 `m_g(z)`：z=(log_pred_ar, log_area, class one-hot)，梯度提升分位/均值回归预测轴向角误差（CPU，深度/迭代冻结：max_iter=200, leaf=15, lr=0.05, seed 固定）。
- 证据模型 `m_e`：同一模型族，特征 = z ∪ {u_axis, missing_fraction, iou_loss, detection_score}。
- **判据（预注册）**：在每个 held-out 配置、common support（train/test 类交集 × AR 五分位 × size 五分位的非空交叉格）内，比较 m_e 与 m_g 的 stratum 内误差预测增量（Spearman 提升与分位损失下降）＋由此诱导的排序在 AUGRC 上的增益；cluster bootstrap 10,000 次 95% CI。
- **KILL-E**：全部 held-out 配置中，证据增量的 CI 含 0 或点估计 < 预注册下限（Spearman 提升 <0.03 且 AUGRC 增益 < ε_AUGRC 公式值）→ **证据前提死亡，Q-SetOD 整体 KILL**。
- 附加披露：从 {u_axis,missing_fraction,iou_loss} 表示线性探测 z 的 R²（捷径泄漏度量）。

## T3 多峰存在性审计（B 攻击 Q3）

每个非空 stratum（类 × AR 五分位 × 单元）的轴向残差：Hartigan dip test（p<0.01）＋双成分轴向 von Mises 混合 vs 单成分的 ΔBIC>10。**判据**：多峰 strata 行数加权占比 <10% → **PRUNE-M：多峰/多弧机制删除**，Q-SetOD 若存活只保留单区间版；≥10% → 机制保留并列出多峰集中的类/AR 区。

## T4 source-only 集合校准可行性（提案 §3.3 的零训练代理）

nonconformity = 轴向角误差 / max(m_g 的 cross-fitted 0.75 分位预测, 1°)；Mondrian 桶 = 类 × AR 五分位（稀疏桶回退全局，规则冻结）。在 train 侧 source 行校准 α∈{0.1,0.2}，在全部 held-out 单元评测：总体覆盖、逐桶最差覆盖、集合归一化宽度、近全圆（>150°）集合率。**KILL-C**：任一 α 下 held-out 总体覆盖偏离名义 >5 个百分点，或达到名义覆盖所需集合的中位宽度 >120°（近全圆退化）→ 校准前提死亡。

## T5 判定汇总（预注册映射）

- KILL-E 触发 → `QSETOD_KILLED_ON_PAPER`：项目按 STRONG_JSTARS 收口成稿（含 r034 章节），不再投入方法路线；终局。
- KILL-E 未触发但 KILL-C 触发 → `QSETOD_EVIDENCE_ONLY`：证据信息存在但集合校准不可行，方法降格为"质量分数改进"候选，venue 上限 JSTARS/TGRS 待议。
- 双 KILL 未触发 → `QSETOD_PROCEED_CANDIDATE`（附 PRUNE-M 与否）：进入 C 提案 §4.2 有限训练验证的资格成立，**训练需用户另行授权 GPU**；venue 前景按 T1 审计表如实标注。
- 判定由数据说话，服务器不得偏袒任一结果。

## T6 审计（既定标准，全部真实执行）

双独立实现 A/B → comparator（atol=1e-10）→ raw validator（从 rows 重算全链、无输出强制）→ ≥5 项真实 subprocess mutation（KILL-E 下限篡改、common-support 定义篡改、覆盖名义值篡改、dip 阈值篡改、判定 token 篡改）→ 跨机 bundle `audit_bundles/r036/`（rows 引用 r034 bundle 免重复、新增拟合输入/输出/判定与 manifest 真实哈希）。

## T7 报告

模板 schema 2 严格全字段：T1 审计表、T2 全配置增量表（点估计+CI）、T3 多峰占比表、T4 覆盖/宽度表、T5 判定、泄漏度量、偏差清单、资源。结果 commit + push，两行回执。

## 务实规则

同既定惯例：可审计 ff-only 同步、干净现场照实记录、未预料情况默认继续+披露、只有 kill 清单才停。红线：验证/变异真实执行；target 角标签绝不入拟合。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull 重放与 verdict；ACCEPTED 需双方一致。KILL 判定与 r034 同等终局；PROCEED 判定不预支任何 venue 承诺。
