# OrientBench P1 — 科学有效性审计（v2）

> SUPERVISOR_APPROVED_033_P1_SCIENTIFIC_VALIDITY_AUDIT_V2 · 无训练 · 不追公开 mAP · thresholds 未变。
> DOTA 口径：**train 训练 / val 验证**（非 trainval/test）；mAP 低于公开论文为正常，不追 SOTA。
> 数字来自 construct_validity_nrc_v2 / tail_risk_analysis_v2，基于 23 real cells。

---

## 1. 已修正的三处报告矛盾

1. **PSC #20「formal gate = NRC≤1」误述** → 已更正：formal gate 认证的是**协议 / 阈值冻结 / split 互斥 / metric 可计算**，**不**要求每个 detector NRC≤1。PSC NRC>1 改写为 benchmark 发现（orientation selection 反校准）。
2. **rtmdet #32 缺表** → 已注明：#32 是 D2 formal gate 组成 detector（D2-audit NRC 0.62），但**仅 dcal-subset 推理，未进入 final-val summary table**；不含糊。
3. **NRC↔mAP 独立性 n=3 误述** → 已删除；改为基于 **23-cell 构造效度分析**（下节）。
- 修正文件：docs/orientbench_project_progress_report.md、final_orientbench_report.md、final_claim_ledger.md、final_limitations.md。

---

## 2. 构造效度：NRC vs mAP / median error（23 cells）

| 关系 | 值 |
|---|---|
| Spearman(NRC, mAP) | **-0.046**（p=0.84，不显著） |
| Pearson(NRC, mAP) | -0.260（p=0.23） |
| partial(NRC, mAP \| dataset) | -0.567 |
| partial(NRC, mAP \| family) | 0.157 |
| **partial(NRC, mAP \| dataset+family)** | **-0.005** |
| Spearman(NRC, median orient err) | 0.400 |
| mean rank distance NRC vs mAP | 7.83 / 23 |

**结论**：NRC 与 mAP **基本独立**（Spearman≈0；控 dataset+family 偏相关≈0）。NRC **不是 mAP 换皮**，提供独立于 accuracy 的可靠性信息。NRC 与 median orientation error 中度相关（0.40，符合预期：NRC 部分反映朝向误差但非全部）。→ **P1 顶刊叙事保留/增强**。

---

## 3. 尾部风险（p75/p90/p95/p99 angle error°）

| 分组 | masked p99 范围 | unmasked p99 范围 |
|---|---|---|
| 全部 12 cells | **10.0 – 16.1°** | **88.4 – 90.0°** |

- **unmasked p99 ≈ 89-90°**：存在**灾难性尾部**，集中在 near-square 目标（朝向 90° 翻转/方形歧义）。
- **masked p99 ≈ 10-16°**：去除 near-square 后尾部仍**非平凡**（DOTA/DIOR ~10-13°，SODA 小目标 ~15-16°）。
- ARS-DETR DIOR（弱模型）masked p99=26°（n=33）。

**结论**：朝向错误存在**少数灾难性尾部**（unmasked p99≈89°），且 near-square 是主因；非 near-square 仍有非平凡尾部。→ **reliability cliff 真实，P1/P3 selection/reliability 叙事成立**（非 p99 仍很小的收缩情形）。

详见 outputs/bench_core/reports/tail_risk_analysis_v2.csv（per-cell，含 aspect-ratio/near-square 分组）。

---

## 4. aspect-ratio / near-square reliability curve

- near-square mask 是 p99 灾难尾的开关：unmasked 89° → masked 10-16°。
- 即：**orientation reliability 在 aspect-ratio→1（近方形）处断崖**；这是 GV-obliquity / near-square mask 设计的实证依据。
- 含义：可靠性诊断必须 near-square aware；天真的全量 angle error 被方形歧义主导。

---

## 5. PSC 反校准机制候选

- 见 docs/psc_miscalibration_mechanism_note.md。
- 要点：PSC 在 **DOTA/FAIR1M/SODA NRC>1**（唯一系统性反校准 family）；DOTA/SODA 上 **mAP 不弱但 selection 反校准**。
- 建议：**暂不开大规模训练**；证据支持回合作者讨论是否启动 angle-head control experiment。

---

## 6. selection score 三轨

- 见 docs/selection_score_three_track_definition.md。
- 当前 cross-detector NRC = **Track B（detection-score 统一 proxy）**，非 intrinsic 排名。PSC 反校准在 Track B 成立；intrinsic 归因需 Track A（angle-head control，待批准）。R1-R8/GV/NRC/selection score 定义**未改**。

---

## 7. raw / matched 持久化状态

- /dev/shm 为**临时区**（重启丢失）。已持久化 key cells（host + PSC + ARS-DETR DIOR + Strip DIOR + reps，12 artifacts ~2.6GB）到 `outputs/persistent_artifacts/orientbench_v2/`（**gitignored**）。
- manifest：outputs/bench_core/reports/persistent_prediction_manifest_v2.json（source/persistent path、sha256、size、cell、schema version、generation command、can_recompute）。
- 其余 cells 可按 reproducibility guide 重算（不重训）。

---

## 8. P1 是否具备顶刊（TGRS/顶刊）继续推进价值 — 结论

**具备，且证据增强（克制表述）**：
1. **NRC 构造效度成立**：NRC ⟂ mAP（Spearman≈0，控 dataset+family 偏相关≈0）→ 提供 accuracy 看不到的可靠性维度。
2. **PSC orientation-selection 反校准**：跨 3 数据集、mAP 不弱时仍反校准 → 真实、可复述的 benchmark 发现。
3. **灾难性朝向尾部**（unmasked p99≈89°，near-square 驱动；masked p99 10-16°）→ reliability cliff 真实。
- 若上述任一不成立才降级；当前**三者均成立**，P1 不降级。

**不得夸大**：以上为 DOTA train/val + cross-dataset exploratory 范围内的诊断证据；非 full project、非全数据集 SOTA、非因果结论。

---

## 9. P2 / P3 边界

**P2（C1 cross-view）**：
- P1 只提供 Bench-Core、RHINO host、**augmentation-view** evidence。
- **不能替代 genuine C1**（无多物理视角数据）；**不能证明 OT-dustbin 机制成立**（OT 与 GT-identity 接近打平，025 已记）。

**P3（selection / reliability）**：
- P1 的**尾部风险 + reliability cliff** 是 P3 是否值得继续的**前置证据**。
- 本审计：尾部风险**强**（unmasked p99≈89°、masked p99 10-16°、PSC 反校准）→ **P3 是后续主线**，值得继续。
- 若尾部弱（p99 很小）才应收缩 P3；当前不收缩。

---

## 10. 需合作者裁决
- 是否启动 PSC **angle-head control experiment**（确认机制归因；需批准+算力）。
- 是否将 cross-dataset 从 exploratory 推进为更正式的 P3 reliability 评测（需新预算/协议）。
- 当前 P1 current scope 已可作为顶刊 P1 章节的诊断基线。
