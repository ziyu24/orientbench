---
schema_version: 2
plan_id: b-r040-panorama-inference-20260815
dispatch_id: orientbench-b-r040-panorama-inference-20260815
initiator: B
base_sha: SET_BY_ACTIVATION_COMMIT
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15：『后续GPU授权等直接搞，不要再问了，同时阅读CLAUDE.md（有权重资源可以利用），看是否需要重新调整GPU或者其他执行计划』——授权直接使用 GPU 与 pth_data 既有权重执行全景推理"
scientific_snapshot:
  primary: SET_BY_ACTIVATION_COMMIT
  weight_library: "/home/rspip/cqc/pro/study/pth_data（只读；readme.md 为权威清单）；仓库内解析结果 outputs/bench_core/baseline_inventory.csv（73 条，67 valid）"
  prior_terminal_states: "r034 K1_K2_KILL 与 r036/r037 集合路线终止不受本轮影响；本轮只产出资产，不重开任何已关闭判定"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r040-panorama-inference-20260815/SERVER_EXECUTION_REPORT.md
read_set:
  - 仓库只读；pth_data 权重/配置/日志只读；各数据集官方 val/验证 split 只读
write_set:
  - outputs/persistent_artifacts/orientbench_panorama_r040_20260815/**
  - top_journal_v3_reaudit_055/panorama_r040_20260815/**
  - audit_bundles/r040/**
  - dis/server_reports/orientbench-b-r040-panorama-inference-20260815/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 2, gpu_hours_max: 60, cpu_core_hours_max: 224}
  wall_time: {seconds_max: 86400}
  data:
    allowed_dataset_ids:
      - "DIOR-R-val-readonly"
      - "DOTA-v1.0-val-readonly"
      - "DOTA-v1.5-val-readonly"
      - "FAIR1M-v1.0-val-readonly"
      - "HRSC2016-val-readonly"
      - "SODA-A-val-readonly"
      - "ICDAR-MLT-val-readonly"
      - "existing-frozen-orientbench-evidence-readonly"
    read_bytes_max: 2199023255552
    write_bytes_max: 214748364800
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_panorama_r040_20260815/
      - top_journal_v3_reaudit_055/panorama_r040_20260815/
      - audit_bundles/r040/
      - dis/server_reports/orientbench-b-r040-panorama-inference-20260815/
      - claude_code_and_supervisor.md
    bytes_max: 214748364800
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
    rule: 本轮是资产生产轮，不做任何科学裁决、不产生 witness/gate/venue 结论。完成度以"实际完成的 tier 与单元数"如实计量，未跑完的 tier 不算失败。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才停；其它偏差（含单个单元失败）记录后跳过该单元继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 86400 秒或 GPU 60 小时预算耗尽时按 tier 边界优雅收尾并如实报告。
kill_conditions:
  - 读取或推理 DOTA-v2.0 任何 split，或 SODA-A official test —— 两者为保留的清白确认端点，本轮绝对禁触。
  - 训练、微调、蒸馏或任何权重更新；修改 pth_data 任何文件；下载新权重或新数据。
  - 使用任何数据集的 official test 标注，或引用官方 test 榜单数字。
  - 伪造推理结果、AP 数字或 provenance 字段；跳过 AP 对齐核验却声称已核验。
  - 修改冻结产物、既有 A-H 单元数据、治理文件；写入越出 write_set；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r040 全景推理资产轮（B 发起；用既有权重扩展评测单元池，纯推理零训练）

## 一句话

服务器 `pth_data` 有 67 个已训练且 pth/config 齐备的基线，覆盖 **11 种架构 × 7 个域（含 HRSC2016 长条船与 ICDAR-MLT 场景文字）**。本轮把它们跑成统一 schema 的评测单元，一次推理同时产出**测量学全景**与 **OER 等变证据特征**，把此后所有科学问题的单元池从 8 扩到数十。**本轮不做任何科学裁决。**

## 核心设计：一次推理，双重用途

每个单元对其数据集的 **val/验证 split** 做 **三视图前向**：identity、horizontal flip、vertical flip（后两者结果逆变换回原图坐标，长边 canonical 化后按 `RP1` 周期对齐）。理由：只做 identity 则日后 OER/机制研究必须重跑全部推理；三视图一次到位，边际成本 3×，避免第二轮全量 GPU 开销。

**预算不足时的降级规则**：按 tier 顺序执行；预算紧张时后续 tier 可降为 identity-only 并在 manifest 标 `views=1`（该单元只进测量学分析、不进 OER 分析），**不得为省预算而缩减已开始 tier 的单元数却不披露**。

## Tier 优先级（按信息增益排序，逐 tier 执行，做完一个 tier 提交一次）

- **Tier 1（新域优先，成本最低）**：`HRSC2016` 全部 valid 单元（长条船——AR 资格域效应的天然正例试金石，数据量小）＋ `ICDAR-MLT` / `ICDAR-MLT 2019` 全部 valid 单元（**场景文字＝非遥感 OBB，跨域外部性的关键**）。
- **Tier 2（角度表征全景）**：`DOTA-v1.0` 上尚未有单元的全部架构——重点包含 `rotated_retinanet_psc`(PSC 编码)、`rotated_retinanet`(le90 回归)、`rotated_fcos_le90`、`arsdetr`(DETR-like)、`h2rbox_v2`(弱监督)、`point2rbox_v2`(点监督)、`strip_rcnn`、`oriented_rcnn_lsknet`、`faa_oriented_rcnn`。
- **Tier 3（域内架构扩展）**：`DIOR-R` 尚未覆盖的架构（arsdetr、lsknet、psc、strip、rtmdet 变体）。
- **Tier 4**：`FAIR1M-v1.0`、`SODA-A`(**仅 val，官方 test 禁触**)、`DOTA-v1.5`（含 MS/SS/exact_iof01 变体，用于同架构不同训练配置的敏感性）。

已有 A--H 八单元不重跑；若某新单元与既有单元完全同配置，记录为 `DUPLICATE_OF(unit)` 并跳过。

## 每单元必须产出

1. **Provenance 记录（AGENTS.md §4.1 强制全字段）**：dataset、split、backbone、schedule、batch size、lr、SyncBN/BN、readme 记录 mAP、框架版本、**checkpoint SHA-256**、config 路径与 SHA-256、log 路径。此表同时解决外部审稿人 P2（单元匿名不可接受）。
2. **AP 对齐核验**：本轮实测 val mAP（及 AP50/AP75）与 readme/log 记录值对比，绝对差与容差判定写入表；**超差不 kill，标 `AP_MISALIGNED` 并保留该单元的所有产物**，由后续轮决定是否纳入正式分析。这是"必须对齐基本配置"的落实与如实披露。
3. **matched rows（统一 schema，供后续所有分析直接使用）**：逐类、score 降序贪心、rIoU≥0.5、ignore GT 排除的 identity matched TP（与 r026/r034 匹配语义一致，实现细节照实披露）。每行字段：
   - 键：`unit_id, image_id, pred_id, gt_id, class_id, cluster_id`（cluster=image；SODA/DOTA tile 数据集额外给 mother-scene）
   - 标签：`angle_error_deg`（长边 canonical、180° 周期）、`Y = angle_error_deg/90`
   - 几何/nuisance：`detection_score, pred_w, pred_h, gt_w, gt_h, pred_ar, gt_ar, pred_area, iou`
   - **证据（三视图）**：`u_axis`(三视图方向分歧)、`missing_fraction`(视图间关联缺失率)、`iou_loss`、`center_dispersion`、`scale_dispersion`、`score_dispersion`、`association_ambiguity`——定义与既有 A-H 单元的同名列语义**逐项对齐**，对齐证据（在 A-H 上重算并与冻结列比对的最大绝对差）写入报告。
4. **数据集级汇总**：类别计数、AR 分布、near-square 占比、匹配率、未匹配/FP/FN 计数、推理耗时与显存峰值。

## 明确禁止（红线）

- **DOTA-v2.0 任何 split、SODA-A official test 绝对禁触**——它们是保留给未来密封确认的清白端点，本轮碰一下就报废。
- 不训练、不微调、不改 `pth_data`、不下载新权重/数据；不使用任何 official test 标注；不追公开 trainval/test 榜单数字（AGENTS §4.2）。
- 不做任何科学判读：本轮报告不得出现 witness、gate、venue、PASS/FAIL 科学结论。

## 审计（按资产轮定级，不搞过度仪式）

不要求双独立实现。要求：(a) 全产物 manifest（path/bytes/SHA-256，真实计算、无自引用）；(b) 独立 `validate_r040.py`（与生产脚本分开书写）核验 schema 完整性、键唯一性、匹配不变量（无重复 GT 配对、IoU≥阈值、ignore 已排除）、证据列有限性、A-H 对齐差、provenance 字段齐全、**禁触端点零访问证明**（记录实际打开的数据根路径集合）；(c) 三项真实 subprocess mutation（篡改 matched 行的 theta、篡改 cluster 映射、删除 provenance 字段各一，validator 必须非零拒绝）；(d) 跨机 bundle `audit_bundles/r040/` 放 manifest、validator、provenance 表、数据集级汇总与**每单元 matched rows 的可复核抽样**（全量 rows 留在 outputs/，>80MB 文件不入 Git）。

## 报告

模板 schema 2 严格全字段，外加：完成 tier 与单元清单（含跳过/失败原因）、provenance 全表、AP 对齐表、A-H 语义对齐差、资源实际用量（GPU 小时、显存峰值、wall time）、禁触端点零访问证明、偏差清单。结果按 tier 分批 commit + push，最后两行回执。

## 务实规则

同既定惯例：可审计 ff-only 同步；单元失败跳过并记录，不中断整轮；未预料情况默认继续+披露；只有 kill 清单才停。**允许服务器自行决定推理 batch/worker/精度等不改变科学语义的实现细节，照实记录。**

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 本轮产物由 B/C post-pull 核验后，作为后续 OER 门（r039 修订版）、机制研究与成稿轮的共同基座。
