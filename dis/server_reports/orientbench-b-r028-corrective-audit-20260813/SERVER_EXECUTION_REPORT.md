---
schema_version: 2
dispatch_id: orientbench-b-r028-corrective-audit-20260813
execution_status: complete
completion_mode: COMPLETE_CORRECTIVE_AUDIT_PENDING_BC_REPLAY
---

# r028 服务器执行报告

- T1：新 r026 raw validator 96/96 字段与冻结表一致；新 r023 validator 覆盖 405 hypotheses，4,950/4,950 字段一致。
- T2：六项真实 subprocess mutation 全部 pristine=0、mutated!=0；stdout/stderr 和 exit 都已留存。
- T3：Git replay bundle 19 files、92,680,050 bytes，manifest 哈希逐项核验，无自引用。
- T4：DOTA GT conversion：5,297 tiles、458 mothers、55,804 nonignored GT；两个 matched GT-id 集均为 GT 集子集。
- T5：`tta_localization=-(missing_fraction+iou_loss)` 已更正；受影响 r027 描述表已标 `SUPERSEDED_BY_R028`；重建 r027 非自引用 manifest。
- T6：已写 post-outcome audited identity 的主稿/补充稿，未称 preregistered independent confirmation。

本轮没有改变正式 gate；r026 contest 仍须 B/C clone 后按 bundle 重放并裁决。
