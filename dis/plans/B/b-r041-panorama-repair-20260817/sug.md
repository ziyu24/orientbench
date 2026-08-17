---
schema_version: 2
plan_id: b-r041-panorama-repair-20260817
dispatch_id: orientbench-b-r041-panorama-repair-20260817
initiator: B
base_sha: SET_BY_ACTIVATION_COMMIT
supersedes: null
continues: b-r040-panorama-inference-20260815
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15：『后续GPU授权等直接搞，不要再问了』+ 2026-08-17 交付本轮——授权继续全景推理并提高预算"
scientific_snapshot:
  primary: SET_BY_ACTIVATION_COMMIT
  carried_assets: "r040 已完成并验证的 HRSC2016 七单元三视图（3,190 matched TP rows，validation pass，三 mutation 拒绝）——本轮不得重跑或改动"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r041-panorama-repair-20260817/SERVER_EXECUTION_REPORT.md
read_set:
  - 仓库只读；pth_data 权重/配置/日志只读；各数据集 val split 只读
write_set:
  - outputs/persistent_artifacts/orientbench_panorama_r041_20260817/**
  - top_journal_v3_reaudit_055/panorama_r041_20260817/**
  - audit_bundles/r041/**
  - dis/server_reports/orientbench-b-r041-panorama-repair-20260817/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 2, gpu_hours_max: 120, cpu_core_hours_max: 448}
  wall_time: {seconds_max: 172800}
  data:
    allowed_dataset_ids:
      - "DOTA-v1.0-val-readonly"
      - "DIOR-R-val-readonly"
      - "FAIR1M-v1.0-val-readonly"
      - "SODA-A-val-readonly"
      - "DOTA-v1.5-val-readonly"
      - "existing-frozen-orientbench-evidence-readonly"
    read_bytes_max: 4398046511104
    write_bytes_max: 429496729600
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_panorama_r041_20260817/
      - top_journal_v3_reaudit_055/panorama_r041_20260817/
      - audit_bundles/r041/
      - dis/server_reports/orientbench-b-r041-panorama-repair-20260817/
      - claude_code_and_supervisor.md
    bytes_max: 429496729600
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
    rule: 资产轮，不做科学裁决。单元有效性门 = AP parity 通过；未通过者保留产物并标 AP_MISALIGNED，不进入后续分析池。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才停；单元级失败记录后跳过继续。
early_stop_conditions:
  - 仅硬性 kill 清单；预算耗尽时在单元边界收尾，已完成单元照常提交。
kill_conditions:
  - 读取或推理 DOTA-v2.0 任何 split、SODA-A official test、任何数据集 official test 标注。
  - 训练/微调/权重更新；修改 pth_data；下载任何数据或权重（含缺失的 ICDAR 数据）。
  - 重跑或改动 r040 已验证的 HRSC 七单元产物。
  - 伪造推理结果、AP 数字或 provenance；越界写入；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r041 全景推理修复轮（B 发起；修 DOTA 布局 + 补失败单元 + 扩 DIOR，纯推理）

## 一句话

r040 的 HRSC 七单元成功入库；DOTA 段因**数据布局用错**导致 AP 全线崩塌（PSC 0.2566 vs readme 0.5562），三单元技术失败。本轮改用 r019/r025 已验证的切片布局重跑并补齐，AP parity 作为单元有效性门。

## 根因与强制修复（T1）

r040 用了 official-val overlay；而这些权重是在**切片(sliced)**数据上训练的。r019 与 r025 在 DOTA 上取得精确 AP parity（orcnn 0.7061/0.4517、rtmdet 0.7161/0.4868）用的是：

```text
data_root = /home/rspip/cqc/data/dataset/dota/split_ss_dota10_dota15/val/
ann_file  = annfiles/     img_prefix = images/     img_suffix = png
```

**所有 DOTA-v1.0 单元一律改用该布局**；DOTA-v1.5 单元按其 readme 记录的对应切片布局（若不存在则记 `LAYOUT_UNAVAILABLE` 跳过，不得替代）。逐单元先跑 AP，与 readme/log 记录值比对：
- 通过（mAP 绝对差 ≤0.02，或 AP50/AP75 ≤0.002 若 readme 提供）→ 该单元有效，继续三视图与 matched rows；
- 不通过 → 记 `AP_MISALIGNED` + 实测值 + 已尝试布局，**跳过该单元的三视图**（省预算），不进入分析池；
- 每个单元跑完立刻提交推送一次（避免再次墙钟截断丢失成果）。

## 单元失败修复（T2）

- `rotated_fcos_le90`：config 求值时 `__file__` 未定义 → 用 `Config.fromfile` 前设置正确工作目录或以绝对路径加载；仍失败则记录跳过。
- `h2rbox_v2`：forward 完成但 evaluator/dump 阶段失败 → 绕过官方 evaluator，直接从预测结构落盘（本项目只需预测框/分数/类别，不依赖官方 eval）。
- `rotated_rtmdet_m`：overlay/config 解析出空数据集 → 改用上述切片布局后重试。
三者均非科学问题，允许服务器自行决定实现细节，照实记录。

## 执行顺序与内容（预算 48 小时墙钟 / 120 GPU 小时）

1. **T1+T2：DOTA-v1.0 全架构**——`rotated_retinanet_psc`(PSC)、`rotated_retinanet`(le90)、`rotated_fcos_le90`、`arsdetr`(DETR)、`h2rbox_v2`(弱监督)、`point2rbox_v2`(点监督)、`strip_rcnn`、`oriented_rcnn_lsknet`、`faa_oriented_rcnn`、`rotated_rtmdet`。AP 通过者做三视图(identity+hflip+vflip)。
2. **T3：DIOR-R 未覆盖架构**——arsdetr、oriented_rcnn_lsknet、rotated_retinanet_psc、strip_rcnn、rtmdet 变体，同样 AP 门 + 三视图。
3. **T4（有余量才做）**：FAIR1M、SODA-A **val**、DOTA-v1.5。
4. `ICDAR-MLT` 数据根不在盘 → 记 `DATA_ABSENT`，**不下载不替代**。

## 产出（schema 与 r040 一致，供后续分析直接拼接）

每有效单元：provenance 全字段（AGENTS §4.1 + checkpoint SHA-256 + 实际布局路径）、AP 对齐表、matched rows（键 + `angle_error_deg`/`Y` + nuisance `detection_score/pred_ar/gt_ar/pred_area/iou/class` + 三视图证据 `u_axis/missing_fraction/iou_loss/center_dispersion/scale_dispersion/score_dispersion/association_ambiguity`）、数据集级汇总。证据列语义须与既有 A-H 单元逐项对齐，对齐差写入报告。

## 审计（资产轮定级）

manifest（真实 hash）+ 独立 `validate_r041.py`（schema/键唯一/匹配不变量/证据有限性/provenance 齐全/禁触端点零访问证明）+ 三项真实 subprocess mutation + bundle `audit_bundles/r041/`（放 manifest、validator、provenance、AP 表、汇总与 rows 抽样；>80MB 不入 Git）。**允许分批提交，最终一次性给报告。**

## 报告

模板 schema 2 全字段 + 有效/失败单元清单与原因、AP 对齐全表、A-H 对齐差、资源实际用量、禁触端点零访问证明、偏差清单。两行回执。

## 激活与回执

- READY 冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
