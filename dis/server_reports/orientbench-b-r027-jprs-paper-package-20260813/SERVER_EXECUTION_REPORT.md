---
schema_version: 2
dispatch_id: orientbench-b-r027-jprs-paper-package-20260813
plan_id: b-r027-jprs-paper-package-20260813
initiator: B
execution_status: complete
completion_mode: COMPLETE_DESCRIPTIVE_PAPER_PACKAGE_PENDING_BC_REVIEW
starting_commit: ae4fb274dfe965cca83705c49d8876d31c8c135b
ending_commit: recorded by the result commit that contains this report
---

# 服务器执行报告

## 已完成

- T1：已生成 `all_ar_scans_with_cluster_ci_descriptive.csv`。它覆盖 AR 1.0--3.0 的 DIOR A/B/C、DOTA 两 unit、DOTA equal-unit 与 pooled-unit 聚合，AUGRC/Risk@70/Risk@90 均含 200-draw cluster CI。equal-unit CI 在每个 draw 对两个 detector 的母图 cluster 重采样结果直接等权汇总，并非平均两个单独 CI。
- T1：已生成 DOTA 两域 Risk@90 表、15 类分解、FAIR1M/SODA-source beta 敏感性（1,000 mother-cluster CIs）、八 unit × 四 probe × 三 endpoint × 两域完整表，以及四数据集 cluster/eligible cluster/SE/MDE80 披露。所有新增数字标记为 `DESCRIPTIVE`。
- T2：`claim_recompute_r027.py` 从冻结 r023 replicate parquet 与 r026 原始表独立复算/核对：r023 七 witness 行的 point/CI/p，以及 r026 六 hypotheses 全字段、swap、matched counts (48,889/51,736) 与 AP parity 四值。`claim_check.json=PASS`，177/177 字段一致。
- T3--T5：hash-linked evidence ledger 覆盖 formal finding、边界、历史负路线、每个 T1 表；已写新 JPRS 主稿与补充材料草稿，正文数字均有 `[L#]` 映射。
- T6：`package_manifest.json` 保存本轮生成物的 SHA-256；无 GPU、训练、推理、下载、阈值/split 改动或旧冻结产物修改。

## 产物

- `outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/`
- `top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/{build_package.py,add_scan_ci.py,build_final_t1.py,claim_recompute_r027.py,finalize_r027.py}`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r027_draft.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/jprs_r027_supplement_draft.md`

## 偏差与边界

- 首版 AR scan 误将 DOTA unit CIs 平均为 aggregate CI；该版未被报告为完成，已替换为直接 cluster-resample 的等权 aggregate CI，并完成读回验证。
- DOTA Risk@90 的 SE 由其新建 cluster CI 显式推导；r026 冻结 formal bootstrap 未含 Risk@90。该行标记 `DESCRIPTIVE_CI_DERIVED`。
- 本包的服务器执行已完成；B/C 内容审阅、稿件定稿与投稿决定仍在服务器职责之外。
