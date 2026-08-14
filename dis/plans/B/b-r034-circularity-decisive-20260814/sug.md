---
schema_version: 2
plan_id: b-r034-circularity-decisive-20260814
dispatch_id: orientbench-b-r034-circularity-decisive-20260814
initiator: B
base_sha: 5500634be2e65e5760824b9407acefae1f25dc87
supersedes: null
implements_roadmap: "C r033 阶段 1（dis/C.md 2026-08-14 复盘）+ B open attack 修订（dis/reviews/B/orientbench-c-r033-uplift-roadmap-critique-20260814.md）"
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-14：『必须把期刊搞到顶刊上去。给出服务器需要执行的内容。』——授权执行决定性循环性/类别控制实验（CPU-only，无新数据无训练）"
scientific_snapshot:
  primary: 5500634be2e65e5760824b9407acefae1f25dc87
  fixed_cohort: "八单元 A-H（DIOR-R/{PSC,ORCNN,RTMDet}、FAIR1M/PSC、SODA-A/{PSC,ORCNN}、DOTA/{ORCNN,RTMDet}），字节身份沿用既有冻结 manifest 与 audit_bundles/r028"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r034-circularity-decisive-20260814/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与既有冻结 runtime/bundle 只读；官方标注根只读（仅 T1 lineage 用）
write_set:
  - outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/**
  - top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/**
  - audit_bundles/r034/**
  - dis/server_reports/orientbench-b-r034-circularity-decisive-20260814/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["existing-frozen-orientbench-evidence-readonly", "official-annotation-roots-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/
      - top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/
      - audit_bundles/r034/
      - dis/server_reports/orientbench-b-r034-circularity-decisive-20260814/
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
    rule: 预注册三元分解与 12 条 primary family（正文）；任何四态结果（含杀死顶刊路线的 K1/K2）都是正常完整执行。validator 不得含输出强制断言。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 伪造或硬编码任何验证/变异结果；validator 含输出强制检查。
  - T1 lineage 回连成功但几何/内容与冻结 cohort 矛盾（LINEAGE_CONTRADICTION）——这是唯一因 lineage 而停的情形；lineage 不可建仅记录 LINEAGE_GAP 并继续。
  - 修改冻结 cohort/split/threshold/科学产物；在任何数据上拟合新系数（四个 ranker 均为无参或既有冻结参数）。
  - 写入越出 write_set；使用 GPU/训练/推理；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r034 决定性循环性/类别控制实验（B 发起，实施 C 阶段 1 + B 修订；顶刊去留就看这轮）

## 一句话

在固定 A-H 八单元上，用三元分解回答外部审稿与 C 共同锁定的致命问题：观察到的翻转有多少是**风险定义的算术后果**、多少是**AR 信息本身**、多少是**探针的真实剩余效应**。剩余效应跨 DIOR-R+DOTA 存活 → 顶刊路线继续；触发 K1/K2 → 主张降格、按 STRONG_JSTARS 成稿，不再翻案。

## T1 官方 lineage（provenance 层，非硬门）

对八单元尝试建立不可变 official raw annotation → evaluation object 回连映射（只读官方根；不改任何冻结 cohort）。逐单元产出 lineage 表 + 覆盖率。**规则**：回连成功但与冻结 cohort 几何/内容矛盾 → `LINEAGE_CONTRADICTION`，kill；官方根缺失或覆盖不全 → 记 `LINEAGE_GAP(unit)`，**继续执行 T2**。lineage 状态只影响论文数据声明的措辞分级。

## T2 决定性对照（primary，全 CPU，字段均在既有 matched rows/features）

**固定要素**：八单元冻结 cohort；mother/image cluster bootstrap，`seed=20260814`，replicates 0..9999，同数据集共用 multiplicity；冻结 ε_AUGRC 公式、percentile CI、centered-p `(1+count)/10001`、Holm、方向判据——witness 机器与既有设计逐字相同。

**维度**：
- 风险定义 2：`R_norm` = 现行 GT-AR 归一化 r_geo；`R_raw` = AR 无关的 `clip(e_can/90°,0,1)`。
- eligibility 2：all-AR 与 AR≥2.1（构成 2×2，含此前缺失的 `all-AR × R_raw` 格）。
- ranker 4（全部无参或冻结参数，禁止任何新拟合）：`conf` = detection_score；`ARonly` = −log_pred_ar（单变量，方向使长条排前）；`oracleAR` = −log_gt_ar（诊断用）；`probe` = 冻结 linear_source_frozen（r024 系数）。
- estimand 2：pooled 与 class-standardized（eligibility 内等类权，冻结类清单按各数据集官方类）。
- endpoint：AUGRC（primary）；Risk@70（secondary，全套照算仅不入门）。

**每个 (unit|dataset, risk, estimand, ranker-pair) 计算 DoD**（all-AR 与 AR≥2.1 两域的 Delta 之差，与既有 witness 机器同构）。

**Primary family（恰 12 条，单一 Holm 族，预注册）**：dataset 级 {DIOR-R, DOTA} × contrasts {probe−conf, ARonly−conf, probe−ARonly} × risk {R_norm, R_raw} × class-standardized × AUGRC。其余全部 secondary/descriptive。

**预注册判读（G1）**：
- 三元分解 headline：机械占比（R_raw 下翻转消失程度）、AR 信息占比（|DoD_ARonly|/|DoD_probe|）、剩余效应（probe−ARonly witness 与幅度）。
- **K1（杀死）**：两个 dataset 级、R_norm 下 |DoD_ARonly| ≥ 0.8·|DoD_probe| 且 probe−ARonly 不成 witness。
- **K2（杀死）**：probe−ARonly 在 DIOR-R 或 DOTA 任一 dataset 级（R_norm、class-standardized）不成 witness。
- **存活（顶刊路线继续）**：probe−ARonly 于两 dataset 同向成 witness，且该结论在 class-standardized 与 pooled 两 estimand 下同号。
- oracleAR 仅用于诊断 predicted-AR 质量成分，不入 primary；FAIR1M/SODA 单元照算入 secondary 作边界。

## T3 机制诊断（描述性，零门槛，喂给阶段 2）

逐单元：score 分布熵/分位、AR 分布形态与 near-square 占比、类别构成、匹配率与未匹配处置、NMS 配置存档。只出表，不判读。

## T4 审计（r028 已验证的标准，全部真实执行）

双独立实现 A/B（禁互抄互读）→ comparator（键身份精确、数值 atol=1e-10、witness/判读精确）→ raw 级独立 validator（从 rows+bootstrap 重算全链，无输出强制）→ ≥5 项真实 subprocess mutation（含 K1 阈值 0.8→0、estimand 篡改）→ 跨机 bundle `audit_bundles/r034/`（matched rows 增列 gt_ar/log_pred_ar/class、bootstrap 数组、hypotheses/judgment、manifest 真实哈希；单文件>80MB 分卷）。

## T5 报告

模板 schema 2 严格全字段：lineage 状态表、12 条 primary 全数表、三元分解 headline、K1/K2/存活判读、T3 诊断表、偏差清单、资源。结果 commit + push，两行回执。

## 务实规则

同 r023 以来惯例：可审计 ff-only 同步；在干净 worktree（如 `orientbench_r032_clean`）执行均可，照实记录现场；未预料情况默认继续+披露；只有 kill 清单才停。**红线唯一：所有验证/变异真实执行，validator 无输出强制。**

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull 重放与 verdict（C 已对本路线发起 review request，B 回应见 reviews/B；C 对本计划的 critique 随时欢迎）；ACCEPTED 需双方一致。判读无论存活或杀死，双方 verdict 后即为终局，不再开翻案轮。
