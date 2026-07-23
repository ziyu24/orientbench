# PSC Phase 1：相位向量径向缩放干预

- 原始开始时间：`2026-07-12 20:14:39 -0700`；原始截止时间：`2026-08-23 20:14:39 -0700`，未重置。
- 预注册 SHA-256：`c1f88a6a975d158e42e6c26ddd936a12d269ecbd05ac7999dc11980c45292f7f`。
- 六个 K2 final PSC seed 单元均通过 manifest、config、checkpoint、输出 SHA 和正常结束日志校验。
- actual-head loss/gradient 列来自只补该缺口的 network-coordinate supplement；原 forward 中 evaluator-coordinate anchor-assignment 列已 superseded，AP/NMS/matching/radial decode 未重跑。
- 冻结分支裁决：**B**。
- 六单元一致的可干预结构性解释：`stable_six_cell_radial_decoder_sensitivity_including_modulation_threshold_or_wrapping`；verified=True。
- 六单元最大 decoded median/p95 差：8.66230246° / 40.15501647°。
- 六单元最大 loss 相对变化：20.8733926506。
- Branch A 仅在全部 k、两个数据集、三个 seed 同时满足 median<0.5°、p95<1.0°、configured anchor-assigned head loss relative change<1e-3 时成立。
- Branch B 不自动判定结构原因成立；仅当六单元均为 B 且 decoder radial sensitivity 或 configured-loss magnitude semantics 在六单元一致复现时，条件1才通过。异质响应按未验证处理。
- loss gate 使用实际配置的 anchor-assigned PSC angle loss；controlled matched L1 与 post-NMS matched L1 仅作诊断。
- AP50/AP75、角误差、实际 head 径向/切向梯度、box/class/NMS 集合诊断见 `psc_phase1_radial_scaling.csv`；聚合脚本未训练或重新推理。
