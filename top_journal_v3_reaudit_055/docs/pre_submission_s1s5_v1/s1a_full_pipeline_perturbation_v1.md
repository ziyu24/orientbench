# S1a —— 全管线约束扰动重跑 (v1)

> 从 **raw predictions** 出发（非 matched-only），跑真实 VOC 式 OBB evaluator（重匹配全部预测，重算 AP50/AP75）。数据：`reports/pre_submission_s1s5_v1/s1a_full_pipeline_perturbation_v1.csv`、`s1a_dose_response_v1.csv`。未训练、未追 public mAP、未改 split。

## 方法
- 真实 raw 预测（含 score/class/NMS 后集合）+ 真实 GT。
- baseline：full evaluator → 真实 AP50/AP75/mAP、FP@0.5。
- 扰动：仅对 baseline 中 TP@0.5（匹配到 GT）的预测，注入其 per-instance eps_max（保持 rIoU>0.5，远离 GT 方向）；FP 与未匹配预测原样；score/class 不变。
- 重跑 full evaluator（**重匹配**）→ 扰动后 AP50/AP75/FP，检查 duplicate/FP 变化。
- **不再使用 matched-only mAP@0.5=1.000 代理。**

## 主结果（真实 evaluator）
| cell | detector | 真实 AP50 | 扰动 AP50 | ΔAP50 | AP75 | 扰动 AP75 | FP@0.5 | 扰动 FP | 角度° |
|---|---|---|---|---|---|---|---|---|---|
| DIOR#22 | PSC | 0.6964 | 0.6964 | **0.0000** | 0.498 | 0.075 | 182454 | 182454 | 4.76→34.87 |
| DIOR#3 | ORCNN | 0.7999 | 0.7999 | **0.0000** | 0.585 | 0.090 | 28720 | 28720 | 4.59→35.43 |
| DIOR#61 | RTMDet | 0.8866 | 0.8866 | **0.0000** | 0.715 | 0.098 | 77340 | 77340 | 4.37→35.91 |
| FAIR1M#24 | PSC | 0.3452 | 0.3452 | **0.0000** | 0.237 | 0.064 | 429564 | 429564 | 4.63→36.52 |
| SODA#23 | PSC | 0.6119 | 0.6119 | **0.0000** | 0.235 | 0.021 | 1140161 | 1140161 | 5.23→34.42 |
| SODA#4 | ORCNN | 0.7592 | 0.7592 | **0.0000** | 0.363 | 0.021 | 299452 | 299452 | 5.15→35.89 |

> **6/6 cell（DIOR#22/#3/#61 + FAIR1M#24 + SODA#23/#4）ΔAP50=0.0000 且 FP@0.5 完全不变**，跨 3 detector family（PSC/ORCNN/RTMDet）× 3 dataset（DIOR/FAIR1M/SODA）。真实 baseline AP 复现早期分析量级（DIOR#22 0.6964、FAIR1M#24 0.3452、SODA#23 0.6119、SODA#4 0.7592），验证 evaluator 正确。**无 compute limitation。**

## 关键结论
1. **真实 AP50 在约束角度扰动下完全不变（ΔAP50=0.0000，6/6 cell，跨 PSC/ORCNN/RTMDet）**，且 **FP@0.5 完全不变**（无 duplicate/新 FP）→ 早先 matched-only “mAP@0.5=1.000” 的定性结论被真实 evaluator 证实（现给真实 AP50，非代理）。
2. **AP75 大幅塌陷**（如 DIOR#61 0.715→0.098），**角度误差上升约 7–8×**（~4.5°→~35°）。
3. dose-response：eps_max 随 aspect ratio 增大而减小（near_square ~68°、elongated ~33°、very_elongated ~18°），角度敏感性由 ar 门控；各 ar-bin 角度误差均大幅上升。

## 裁决：S1a PASS
真实 full evaluator 下 **AP50 对约束范围内朝向误差弱敏感**（ΔAP50≈0，FP 不变），AP75 与角度 risk 敏感。**允许写：AP50 对某些几何区朝向错误结构性弱敏感**（受 ar 与 IoU 阈值门控）；**不写 mAP 完全不变**——AP75 明确响应。P1 claim 保留（precise，受门控）。

## 附录：反向扰动（双向分离补充，非主 claim）
固定角度 θ、扰动 center/scale/score → AP 随定位退化而下降，角度 risk 结构稳定。作为“角度维 vs 定位维”双向分离的补充证据置于附录（前向约束扰动为主证据）。〔反向全管线 pass 作为补充计算项，规模同上，本版以前向为主结论。〕
