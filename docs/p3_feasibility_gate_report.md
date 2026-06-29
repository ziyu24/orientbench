# P3 可行性门控报告（feasibility gate）

> SUPERVISOR_APPROVED_037 · 无训练 · 无 host 重训 · 无 full matrix 扩展 · 不追公开 mAP · thresholds 冻结 b7c4e649 未变 · frozen DOTA D_cal/D_audit 未改。
> 合作者可读单文件。本轮为**可行性验证**，非 P3 方法开发。

## 1. P1 当前阶段已完成
- P1 工程 + 科学效度审计 + 中文论文标准审稿稿已交付（docs/orientbench_p1_chinese_paper_draft.md）。current approved scope 完成并冻结；full project partial。

## 2. 为什么现在进入 P3 gate
- P1 留下两个待门控前置：reliability cliff 是否构成可学习问题空间；PSC reverse-calibration 是 angle-head 机制还是 score-proxy mismatch。本轮用**现有 checkpoint 离线分析**给出门控，不做大规模方法开发。

## 3. PSC Track A 是否可用
- **不可用**。4 个 PSC cell 的 saved predictions 仅含 bboxes（已解码角度）/scores/labels，**无 angle logits/distribution/quality/uncertainty**。
- 架构上 Track A 存在（PSCCoder dual_freq num_step=3，**encode_size=6 相位码**），可经 **instrumented forward dump** 提取（hook 角度头 + 映射 post-NMS），但当前 saved preds 不含。
- 故 **P3 现在不能声称 PSC angle-head intrinsic miscalibration**。详见 psc_track_a_signal_audit_037.md。

## 4. Track A / B / C 对比结果（D_audit，split 互斥）
| cell | B det-score NRC | C post-hoc NRC | C AURC vs B | A intrinsic |
|---|---|---|---|---|
| DIOR #22 | 0.557 | 0.510 | 1.11 vs 1.18 | unavailable |
| DOTA #20 | 0.740 | 0.503 | 1.49 vs 1.83 | unavailable |
| FAIR1M #24 | **1.153** [1.07,1.23] | **0.627** [0.59,0.67] | 1.98 vs 2.97 | unavailable |
| SODA #23 | **1.254** [1.23,1.28] | **0.464** [0.45,0.48] | 1.59 vs 3.07 | unavailable |

- **Track B**：det-score selection 在 FAIR1M/SODA 反校准（NRC>1，CI 排除 1）。
- **Track C post-hoc selector**（D_cal 学，D_audit 验证）：**显著改善**——把 FAIR1M/SODA 的反校准（1.15/1.25）降到良校准（0.63/0.46），AURC、Risk@70 全面下降。
- **Track A**：unavailable（forward dump pending）。
- 详见 psc_trackabc_control_037.md。

## 5. reliability cliff 是否支持 P3
- cliff 极陡：near-square vs well-defined **p99 delta ≈ 81.6°**，但**主要来自 near-square 朝向 ill-posedness（几何退化）**，用 aspect-ratio 掩码即可 trivially 处理，非可学习可靠性缺陷。
- **well-defined region p99 ≈ 8.3°**（modest），NRC ~0.43-0.49（selection 有效但不完美）→ 有限但真实的问题空间。
- **真正有价值的问题空间 = well-defined region selection + PSC 类 score-proxy mismatch**，后者 Track C 已证明可改善。详见 p3_reliability_cliff_feasibility_037.md。

## 6. 是否建议启动 P3 方法开发
- **建议有条件启动**（克制）：证据支持 **selective / reliability-aware orientation 作为 unified-proxy / post-hoc selector 路线**——Track C 在 held-out 上显著改善 PSC selection 反校准。
- **不**建议把 P3 立项为 intrinsic-uncertainty 方法（Track A 未验证）或 near-square 几何处理（trivial）。

## 7. 如果启动，建议最小方法路线
1. **先做 PSC forward dump 提取 Track A**（现有 checkpoint，不训练）：确认 PSC 反校准是 angle-head 机制（Track A NRC>1）还是纯 score-proxy mismatch（Track A 正常）。这是 P3 立项的关键判别。
2. **Track C selector 形式化**：unified-proxy / post-hoc selective-orientation（degeneracy-aware 特征 + 校准），在多 detector/dataset 上验证泛化；明确标 upper-bound vs deployable。
3. 仅在 1-2 成立后再考虑 angle-head 方法（如换 coder / 训练时校准）。

## 8. 如果不启动，P3 降级原因
- 若后续 forward dump 显示 Track A 正常且 Track C 增益主要来自 near-square 几何（trivial），则 P3 降级为 P1 的 selection-proxy 附录/负结果，不独立成线。
- 当前证据**不支持**该降级（Track C 在 well-defined region 仍改善，PSC mismatch 真实）。

## 9. 需要合作者批准的事项
- 批准 **PSC Track A forward dump**（现有 checkpoint，少量 dump，无训练；大文件入 /dev/shm）。
- 批准 **P3 作为 unified-proxy / post-hoc selective-orientation 路线**立项（非 intrinsic-only，非 near-square-only）。
- 是否扩展 Track C selector 到更多 detector/dataset（exploratory，需预算）。

---
### 边界与合规
- 未改 thresholds.yaml（b7c4e649）/ frozen DOTA D_cal/D_audit。未训练、未重训 host、未扩 full matrix、未追公开 mAP。
- 本轮 cross-dataset PSC cells 的 D_cal/D_audit 为 **exploratory 应用**（assign_split 确定性），与 frozen DOTA formal split 区分。
- **未声称**：P3 已成立 / PSC angle-head 已证明反校准 / Track A intrinsic 反校准。
### 产物
- psc_track_a_signal_audit_037.{md,csv}；psc_trackabc_control_037.{md,csv,json}；p3_reliability_cliff_feasibility_037.{md,csv}。
