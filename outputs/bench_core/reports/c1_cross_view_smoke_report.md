# C1 Cross-View Responsibility — Mechanism SMOKE (RHINO host)

> RHINO frozen host (sha256 55a90abb…); **mechanism smoke**，非完整 C1 gate。
> cross-view = deterministic synthetic geometric transform (**synthetic_view_transform_for_mechanism_smoke=true**); **missing_real_cross_view_pairs=true**。

| split | imgs | DropRate | OT dustbin mass | OT vs GT-identity reldiff | view-consist err° | synth-view dustbin |
|---|---|---|---|---|---|---|
| D_cal | 80 | 0.235 | 0.2248 | 0.0192 | 1.666 | 0.233 |
| D_audit | 80 | 0.3029 | 0.2176 | 0.045 | 1.523 | 0.2196 |

## 机制原语已实现并跑通
- OT matching with dustbin、GT-identity 对照(R1)、responsibility、DropRate、view-consistency risk、failure taxonomy、near-square mask、D_cal/D_audit 互斥。
## 可进入 D_cal / 仍 blocked
- 可进入 D_cal 探索: OT dustbin / DropRate / view-consistency 原语（机制级）。
- **仍 blocked（不可进入 formal C1 gate）**: 缺真实 cross-view paired capture（现为 synthetic transform）；OT vs GT-identity 的正式打平阈值 (R8) 未冻结；完整 C1 cross-view responsibility distillation 需真实多视图数据 + 预注册阈值 + 批准。
## 下一步
- 需真实 cross-view（旋转/增强视图）对 RHINO 重推理生成 paired predictions，再做 OT-dustbin vs GT-identity 正式对照与阈值冻结。
