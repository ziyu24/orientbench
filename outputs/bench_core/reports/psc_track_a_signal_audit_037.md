# PSC Track A intrinsic signal audit (037)

> 2026-06-29 15:47:50 CST · 只读 + 架构检查，无训练。

## 结论：**Track A intrinsic 在当前 saved predictions 中 unavailable**
- 4 个 PSC cell（DOTA #20 / FAIR1M #24 / SODA #23 / DIOR #22）的 DumpDetResults 保存的 `pred_instances` 仅含 **bboxes（已解码角度）/ scores / labels**；**无 angle logits / angle distribution / angle quality / angle uncertainty**，只有 final angle regression。
- 即：**PSC Track A unavailable in current checkpoint/output**。

## 架构上 Track A 是否存在
- PSC = Phase-Shifting Coder；配置 `PSCCoder(dual_freq=True, num_step=3)` → **encode_size=6**，角度头输出 **6 维相位码**，是角度的 **intrinsic 表征**（非单一回归值）。
- intrinsic 角度置信候选：相位向量的 **模长/一致性**（well-formed 码模长≈1，偏离表示不确定）。
- 因此 Track A **架构上可提取**，但需 **instrumented forward dump**（hook 角度头 angle_preds + 映射到 post-NMS detections），当前 saved preds 不含。

## 对 P3 的约束
- **P3 现在不能声称 PSC angle-head intrinsic miscalibration**（无 Track A 证据）。
- 现在只能研究 **Track B detection-score proxy mismatch** 与 **Track C post-hoc selector**（见 psc_trackabc_control_037）。
- Track A intrinsic 提取 = 明确的 P3 首步 follow-up（forward dump，用现有 checkpoint，不训练）。
