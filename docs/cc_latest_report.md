# OrientBench — 033 P1 科学有效性审计（v2）完成

- **033 完成**：P1 科学有效性审计。无训练、无 GPU、thresholds 未变（b7c4e649）。

## 三处矛盾是否修复
- **是**。① PSC「formal gate=NRC≤1」误述已更正（gate 认证协议/阈值/split/metric，非每 detector NRC≤1）；② rtmdet #32 已注明（gate 组成项但仅 dcal-subset，未入 summary table）；③ NRC↔mAP「DOTA n=3 独立性 OK」删除，改为 23-cell 构造效度。

## NRC 构造效度结论
- **NRC ⟂ mAP**：Spearman(NRC,mAP)=-0.046(p=0.84)，控 dataset+family 偏相关=-0.005。NRC **非 mAP 换皮**，提供 accuracy 独立的可靠性信息 → P1 叙事保留/增强。

## 尾部风险结论
- **存在灾难性尾部**：unmasked p99≈89-90°（near-square 驱动）；masked p99 10-16°（非平凡）。reliability cliff 真实 → P3 selection/reliability 叙事成立，不收缩。

## PSC 反校准是否成立
- **成立**：PSC 在 DOTA/FAIR1M/SODA NRC>1（唯一系统性反校准 family），DOTA/SODA mAP 不弱时仍反校准。真实跨数据集 benchmark 发现。

## selection score 三轨是否完成
- **是**：intrinsic / unified-proxy / post-hoc-upper-bound 三轨定义已写；现有 cross-detector NRC 标注为 Track B（detection-score proxy），非 intrinsic 排名。R1-R8/GV/NRC 定义未改。

## 持久化状态
- key cells（host+PSC+ARS-DETR DIOR+Strip DIOR+reps，12 artifacts ~2.6GB）已持久化到 outputs/persistent_artifacts/orientbench_v2/（gitignored）+ manifest。/dev/shm 非持久警告已记。

## P1 是否值得继续顶刊推进
- **值得**（克制）：NRC 独立性 + PSC 反校准 + 灾难性朝向尾部 三者均成立。非 full project、非 SOTA、非因果。

## 需合作者裁决
- 是否启动 PSC angle-head control experiment（机制归因，需批准+算力）；是否将 cross-dataset 推进为正式 P3 评测。

## 主报告 / 验证 / git
- 主报告：docs/scientific_validity_audit.md（+ psc_miscalibration_mechanism_note.md, selection_score_three_track_definition.md）。
- 验证：102_verify_scientific_validity_audit_v2 → VERIFIED 21/21；pytest 全过。thresholds b7c4e649 未变；git 0 大文件。
