# Paper Reframing (055)

> 目标：从“内部审计/收缩稿”改回论文。脊柱 = orientation reliability measurement protocol + finite-sample risk control。去项目化（无 052/053/054、无“本轮”、无监督批准、无 verifier、无 artifact 路径进正文、无顶刊口号、无 CVPR/ICCV，用 OBB 不用 “OOD”）。

## 建议结构
1. **引言**：mAP 主导 OBB 评测，但不刻画朝向可靠性；给出核心反差（约束扰动 35° / mAP@0.5 不变 / risk 与 AP75 崩）。贡献 = 协议 + 有限样本风险控制 + 机制候选。
2. **相关工作**：detector calibration / D-ECE；selective prediction；conformal / CRC；OBB angle periodicity 与 square-like problem；GWD/KLD 分布损失；uncertainty in detection。（补齐 P1 硬债 §7.4）
3. **问题与协议**：angle error 定义（long-side 对称）；GV-obliquity 数学定义；**masked 主协议 ar≥1.6（+敏感度 1.3）** 与其理由（cliff）；NRC/AURC/risk-coverage 定义；D_cal/D_audit。
4. **Measure（动机层）**：P1 约束扰动 → mAP@0.5 受 ar/IoU 门控、朝向不受保护（precise-pass）；cliff 测量层核心（经验+理论 IoU(δ;ar)）。
5. **Control（脊柱）**：within-cell conformal（base risk、alpha 扫描、tail CRC + Hoeffding 界）；**score menu**（几何选择器最优）；Mondrian + shift audit（退化如实报告）。
6. **Diagnose（机制候选）**：masked 下 detection-score 校准、intrinsic phase_mod 反校准 → angle-coder 机制候选（非证明）。
7. **下游（边界）**：反事实 angle-induced rIoU drop，真实但微弱 → 附录/负结果。
8. **局限**：仅有限 provenance-clean cell；无严格跨域保证；下游收益小；phase_mod 机制未做控制实验；DOTA cell 数据不足。
9. **结论**：measure→control 推进；协议可复现。

## 反转要点（相对收缩稿）
- 主贡献从“benchmark + conformal”改为“**protocol + risk control**”，P2 明确为脊柱、P1 为动机、cliff 为测量层核心。
- 删除“score-only 反校准”叙事（作废），机制信号移到 intrinsic phase_mod。
- P4 不独立成节，融入 P2 score menu。
- P3（deployable selector）与 P5（下游）降为边界/附录。
- 全文删项目管理与治理词，治理基建下沉附录。

## 需删除清单（正文）
项目管理词汇；052/053/054；“本轮”；监督批准；verifier；artifact 路径；顶刊口号；CVPR/ICCV/TPAMI ready；“oriented object detection (OOD)” 缩写改 OBB；“full benchmark / all datasets / SOTA” 类全面性话术。
