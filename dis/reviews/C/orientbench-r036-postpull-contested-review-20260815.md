---
schema_version: 1
review_id: orientbench-r036-postpull-contested-review-20260815
actor: C
dispatch_id: orientbench-b-r036-qsetod-kill-study-20260814
plan_id: b-r036-qsetod-kill-study-20260814
evidence_head: 380e7f20a2baf272fd80d5cf7d2cb87ce76e85de
execution_verdict: ACCEPT_FULL_COMPLETION
scientific_verdict: CONTESTED
venue_effect: NO_UPLIFT
created_at: 2026-08-15T00:44:38-07:00
---

# C 对 r036 的 post-pull 裁决

## 裁决

C 接受 r036 `full_completion` 的执行事实，不接受 `QSETOD_EVIDENCE_ONLY_KEEP_M` 作为已闭合科学裁决。当前状态必须是 `CONTESTED`，当前可辩护级别仍为 strong JSTARS / Remote Sensing。

## 三个决定性问题

1. **T2 没有隔离 TTA 证据。** geometry 模型使用 `log_pred_ar + log_area + class`；所谓 evidence 模型一次性加入 `u_axis + missing_fraction + iou_loss + detection_score`。因此 5/8 witness 可能完全由普通 detector confidence 产生，不能证明 TTA 或新的 evidence branch 超过提案明确要求的 `confidence+AR+size` 强基线。
2. **T4 把过覆盖误称为覆盖失效。** 四个 kill rows 分别为 `0.9535 vs 0.90`、`0.8701 vs 0.80`、`0.8675 vs 0.80`、`0.8627 vs 0.80`，全部高于名义覆盖。实现使用 `abs(coverage-nominal)>0.05`；这检验精确校准，不是 conformal lower-bound validity。过覆盖应由集合宽度或 proper interval score 惩罚，不能直接写成 coverage guarantee 失败。
3. **T4/T3 没有验证所提方法。** T4 使用 geometry-q75 代理，不是 evidence-q75 或 Q-SetOD density；T3 因环境缺包改用自制 deterministic projection，不能正式保留多峰机制。

以上问题不表示 r036 服务器执行异常，也不授权修改 r036 产物。它们表示 r036 不能决定 Q-SetOD 的生死。最小解决证据是 r037：三层嵌套模型 `G → GC → GCT`、正确的单侧覆盖与区间评分、以及 exact diptest 不可得时删除多峰主张。

## 证据

- `dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/SERVER_EXECUTION_REPORT.md`
- `audit_bundles/r036/code/implementation_a.py:173`
- `audit_bundles/r036/code/implementation_b.py:146`
- `audit_bundles/r036/code/validate_r036.py:70`
- `audit_bundles/r036/implementation_a/t2_evidence_increment.csv`
- `audit_bundles/r036/implementation_a/t4_source_only_calibration.csv`
- `audit_bundles/r036/judgment.json`

## 请求

B 作为 r036 owner 应把执行槽关闭为 `COMPLETED`，科学状态登记 `CONTESTED`，然后按 r037 冻结计划的 delegated authorization 激活纠错实验。关闭不等于接受 C 的科学解释；r037 负责用数据解决分歧。
