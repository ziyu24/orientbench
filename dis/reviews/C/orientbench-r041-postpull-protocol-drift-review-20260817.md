---
schema_version: 1
review_id: orientbench-r041-postpull-protocol-drift-review-20260817
actor: C
dispatch_id: orientbench-b-r041-panorama-repair-20260817
plan_id: b-r041-panorama-repair-20260817
evidence_head: ba2cd67ed268169fcec264ef4a79085fd5c8d7d9
execution_verdict: INCOMPLETE_PROTOCOL_DRIFT
scientific_verdict: ASSET_ROUND_NOT_ADJUDICATED
venue_effect: NO_UPLIFT
created_at: 2026-08-17T22:25:00-07:00
---

# C 对 r041 的 post-pull 裁决

## 裁决

C 不接受 r041 的 `execution_status: complete`。正式执行裁决为 `INCOMPLETE / protocol_drift`，科学状态为 `PENDING / NOT_ADJUDICATED`。用户授权 C 本轮不等待 B、直接决定并代为关闭执行槽。

当前可辩护论文级别仍是 **strong JSTARS / Remote Sensing**。r041 是资产轮，没有运行 OER、没有新效应量、没有跨数据集方法证据，也没有清白端点确认，因此对 JPRS/TGRS 不产生升档。

## 决定性协议问题

1. 冻结计划把“读取或推理 DOTA-v2.0 任何 split”列为硬性 kill。服务器第一次执行已承认目录元数据访问，按 `failure_early_stop` 提交异常报告；该 kill 已终止原 dispatch。
2. 后续 `RESUMED_BY_USER.json` 不能修改已冻结计划或复活已经触发 hard kill 的同一 dispatch。合规做法应是新 plan、新 dispatch、新 STARTED 和新报告路径。
3. 最终提交覆盖了原来的唯一报告，并使用冻结 completion mapping 中不存在的 `user_authorized_resumption_after_historical_protocol_drift`；这不能映射到 `complete`。
4. 最终报告删除了 `plan_commit_sha/plan_blob_oid/plan_sha256`，把 `ending_commit` 写成未来占位文本，不满足报告契约。

## 资产边界

- PSC/DIOR `unit_022` 与 RTMDet-S/DIOR `unit_061` 分别对应 r036 的既有 DIOR PSC/RTMDet 单元，不是新增 dataset 或 detector-family 证据；把它们计为全景扩展会重复计数。
- LSKNet/DIOR `unit_010` 是新增候选单元，但其 101,161 行全表只在服务器 runtime，Git 仅有状态、hash 和抽样；当前只能标 `CONDITIONAL_DEVELOPMENT_ASSET`。
- RTMDet-S 状态 JSON 同时写 h/v `PENDING` 与 `TRI_VIEW_NORMALIZED_COMPLETE`，说明状态收尾不一致；其报告声称完成不能替代全表与 view artifact 的独立核验。
- tracked PSC 全表、结构 validator 与三项 mutation 证明了有限的 schema/键/IoU/finite 检查，不证明三视图逆变换、关联语义、完整 access trace 或跨三单元全表真实性。
- r040 声称的 HRSC 七单元未进入 Git audit bundle，本机不能独立核验；后续如使用，必须由新轮先做只读 admission audit。

这些资产可以保留，不需要重跑；但它们只能作为未来 source-development 候选，不能恢复 pristine/prospective 身份，也不能进入当前 headline claim。

## C 对新方法路线的决定

C 采用 B 对 OER 的核心批评：OER 单独最多是 strong-JSTARS+ 形态，只有 Stage A 先证明条件等变残差确实跨数据集/跨 family 增益，才值得设计单次 forward 的 OER-D 蒸馏头。C 不采用 B 的原 r039 文件直接派发：该计划仍含 `SET_AT_ACTIVATION` 占位符，READY sidecar 的 commit/blob/hash 全为 null，不满足治理与证据契约。

唯一下一步是新的 C-owned r042：只复用 r036 已冻结的 616,184 行做 CPU-only OER Stage A 生死门，不读取 DOTA-v2.0、SODA-A official test 或任何新标签，不使用 r041 资产抬高主 gate。只有 r042 通过，才讨论 OER-D GPU 训练；失败则终止顶刊方法路线，按测量型稿件收口。

## 证据

- `dis/plans/B/b-r041-panorama-repair-20260817/sug.md`
- `dis/server_reports/orientbench-b-r041-panorama-repair-20260817/STARTED.json`
- `dis/server_reports/orientbench-b-r041-panorama-repair-20260817/RESUMED_BY_USER.json`
- `dis/server_reports/orientbench-b-r041-panorama-repair-20260817/SERVER_EXECUTION_REPORT.md`
- Git commit `95ecc5ef675bf36eb6f500becdf1043de1ff8cdd` 中的原异常报告
- `audit_bundles/r041/validate_r041.py`
- `audit_bundles/r041/unit_summary.csv`
- `audit_bundles/r041/manifest.csv`
- `outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_061_rtmdet_s_dior/unit_status.json`
