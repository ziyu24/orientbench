# Host Post-Training Orientation Gate (RHINO C1/B + O2-RTDETR A4)

> 训练完成的 host 真实 prediction → canonical orientation risk → D_cal 标定 → 冻结 B_C1/A_A4 → D_audit 正式 gate.
> hosts 不混用；near-square masked；D_audit 未用于设阈值。**完整 C1 cross-view / A4 attribution 准则属 P2/P3，待其机制。**

- gate PASS: **2/2**

| host | route/block | val_mAP | D_cal NRC | D_cal med_err° | D_audit NRC | D_audit med_err° | D_audit Risk@90 | GATE |
|---|---|---|---|---|---|---|---|---|
| RHINO | C1/B/B_C1 | 0.7201 | 0.7806 | 1.518 | 0.7625 | 1.524 | 2.0866 | **PASS** |
| O2-RTDETR | A4/A_A4 | 0.6497 | 0.5561 | 1.772 | 0.5488 | 1.77 | 2.3903 | **PASS** |

## 冻结
- thresholds.yaml: B_C1=frozen_host_orientation_gate(RHINO), A_A4=frozen_host_orientation_gate(O2-RTDETR)；DOTA D2 partial_frozen 不变；含 host checkpoint sha256、D_cal 参考。
- gate=PASS 表示 host selection score 对 orientation risk 排序优于 random（NRC<=1.0）；FAIL 保留不调阈值。

## 范围/limitations
- host orientation-reliability gate（DOTA val 600 子集 D_audit）；非全 val。
- 完整 B_C1 (C1 cross-view OT vs GT-identity, DropRate) 与 A_A4 (partial-corr/HSIC source attribution) 准则需 P2/P3 实验机制，未在本轮；当前为 host 训练落地 + orientation gate。
