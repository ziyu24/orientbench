---
schema_version: 2
plan_id: b-r039-oer-stageA-kill-20260815
dispatch_id: orientbench-b-r039-oer-stageA-kill-20260815
initiator: B
base_sha: SET_AT_ACTIVATION_AFTER_R038
supersedes: null
implements: "C OER-OBB 提案 Stage A（dis/reviews/C/orientbench-c-r038-oerobb-method-proposal-20260815.md §5.1）+ B 攻击修订（dis/reviews/B/orientbench-c-r038-oerobb-method-open-attack-20260815.md）"
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15：『是需要走向顶刊的新方案……我相信你可以搞出来的』——授权顶刊新路线 Stage A 杀伤实验（CPU-only，零训练零 GPU，复用冻结资产）"
scientific_snapshot:
  primary: SET_AT_ACTIVATION_AFTER_R038
  frozen_rows: "audit_bundles/r036 的 616,184 行 A-H enriched rows（禁止重提取）"
  prior_terminal_states: "r034 K1_K2_KILL 与 r036/r037 集合路线终止均不受本轮影响；本轮检验的是全新 OER 条件残差排序主张"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r039-oer-stageA-kill-20260815/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与冻结 bundle 只读；行数据只用 audit_bundles/r036；禁触 DOTA-v2.0 val 与 SODA-A official test
write_set:
  - outputs/persistent_artifacts/orientbench_oer_stageA_r039_20260815/**
  - top_journal_v3_reaudit_055/oer_stageA_r039_20260815/**
  - audit_bundles/r039/**
  - dis/server_reports/orientbench-b-r039-oer-stageA-kill-20260815/**
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
      - outputs/persistent_artifacts/orientbench_oer_stageA_r039_20260815/
      - top_journal_v3_reaudit_055/oer_stageA_r039_20260815/
      - audit_bundles/r039/
      - dis/server_reports/orientbench-b-r039-oer-stageA-kill-20260815/
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
    rule: 预注册 PROCEED/REJECT 判据（正文）；两种结果均为正常完整执行；validator 无输出强制。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 伪造/硬编码任何验证结果；**A/B 两实现或 validator 代码相似度（归一化标签后逐行 diff）超过 60% 相同行**——独立性先查代码后查数值，复制品即 kill。
  - 读取 DOTA-v2.0 val 或 SODA-A official test 任何内容；target 侧 angle label 进入任何拟合/阈值/模型选择。
  - 重提取行数据（必须复用 r036 bundle 行）；神经网络训练；GPU；下载。
  - 触碰 r034/r036/r037 终局判定；修改冻结产物；越界写入；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r039 OER Stage A 杀伤实验（B 发起；顶刊新路线的第一道生死门，CPU-only）

## 一句话

在 r036 冻结的 616,184 行上，用嵌套 leave-dataset × leave-detector 交叉拟合检验：**条件正交化的等变残差证据，能否在最强可部署基线之上提供跨数据集、跨检测器族的方向失效排序增量。** 过 → 进入 OER-D 蒸馏与机制阶段（届时请用户授权 GPU）；不过 → 顶刊方法路线止损，项目按 r038 稿收口。

## 冻结要素

- **主标签** `Y = d_π(θ̂,θ_gt)/90°`；主域 matched-TP 且 GT_AR≥2.1；all-AR 仅敏感性。Y 分段构成（[0,30)/[30,60)/[60,90]°）随报告披露。
- **Nuisance 通道** Z=(detection_score, log_pred_ar, log_area, class, detector_family)；**证据通道 E** = r036 冻结 TTA/等变特征（u_axis、missing_fraction、iou_loss、score dispersion 等既有列；schema 冻结，禁止新提取）。
- **交叉拟合**：外层 leave-one-dataset-out × leave-one-detector-family-out 嵌套；内层 5-fold（按 image/mother cluster 切）拟合 m_E(Z)、m_Y(Z)（HistGradientBoosting，200 迭代/15 叶/lr .05/seed 20260815）；t̃E=E−m_E(Z)，t̃Y=Y−m_Y(Z)；h 为低容量线性/浅 boosting，容量按 source worst-group 协议选，λ source 内冻结。
- **六排序器**（同预算同域）：① m_Y(Z)（nuisance-only）；② pure predicted-AR；③ conf+AR+size+class + source isotonic 校准；④ **generic TTA variance（头号处刑者）**；⑤ evidence-only h(t̃E)；⑥ full OER = m_Y(Z)+λh(t̃E)。oracle GT-AR 仅揭示后诊断。⑦ 未正交化 Z∪E 消融（检验正交化必要性）。
- **推断**：AUGRC 主端点（R@70/R@90 随报），Δ_u = AUGRC(最强可部署基线) − AUGRC(OER)，scene/mother cluster bootstrap 10,000 次（seed 20260815），完整 universe 含零 eligible cluster，unit family Holm。

## 预注册判据（B 修订后，比 C 原案更严）

**PROCEED_OER 需全部成立**：
1. 对最强可部署基线（含 generic TTA variance 与校准 conf+AR+size+class 中实际最强者）Δ_AUGRC ≥ 0.005 且 cluster 95% CI 下界 > 0；
2. **unit witnesses ≥ 5/8，且至少 1 个为 DOTA unit（G/H）**（r037 已见 4/8 全非 DOTA，新门必须走出已观察区）；
3. witnesses 覆盖 ≥2 datasets、≥2 detector families；
4. equal-class 与 common-support 下方向不反转；
5. **窄层内置换 t̃E 负控制**：置换后残余增益 > 原增益 30% 即 FAIL（binding）；pure-AR/oracle 不能解释主增量；
6. leave-dataset 与 leave-detector 两类外层均有正向支持；
7. 未正交化 Z∪E 若 ≥ OER，删除 "orthogonal" 贡献（不必杀死方法，但重写主张）。
任一失败 → **REJECT_OER_METHOD**：顶刊方法路线终局止损（与 r034/r036 同等效力，不翻案），项目以 r038 稿收口。

## 审计（吸取 r026/r037 两次假独立教训）

双独立实现 A/B + comparator + raw validator + ≥5 真实 mutation + 跨机 bundle `audit_bundles/r039/`——**新增硬门：报告必须附 A/B 与 validator 的归一化代码 diff 统计（相同行占比），≥60% 相同即自判 kill**；泄漏披露：t̃E 重构 Z 的 R² 表、逐 E 成分剥离消融表。

## 报告

模板 schema 2 严格全字段：六排序器全配置表（点估计+CI）、判据逐条判定、置换控制表、泄漏表、Y 分段构成、偏差、资源。结果 commit + push，两行回执。

## 激活与回执

- 本计划 READY 冻结；**等 r038 成稿轮关闭释放槽后由 B 激活**（届时回填 base_sha 需新 revision——为免字节冻结冲突，激活时以本文件字节为准，base_sha 字段的 SET_AT_ACTIVATION_AFTER_R038 为声明性占位，实际 base 以 coordination 绑定的 plan_commit 与激活 commit 为准）。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull 重放与 verdict；PROCEED 亦不预支 venue，Stage B 规格另行评审并需用户 GPU 授权。
