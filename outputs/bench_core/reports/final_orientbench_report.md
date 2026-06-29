# OrientBench — Final Report (Current Approved Scope)

> 2026-06-28 22:14:10 CST | git a54d5364597b | thresholds.yaml sha256 b7c4e649b1a3de6d

## 总体定性
- **current_approved_scope_complete = true**
- **full_project_complete = false**
- DOTA scoped milestone = **pass**（D2 partial / host orientation / C1 augmentation-view / A4 same-host，已冻结阈值 + D_audit formal_pass）。
- cross-dataset matrix = **exploratory partial success**（23 real cells / 6 datasets）。

## 已完成（formal, DOTA frozen scope）
- DOTA D2 partial formal gate（认证协议/阈值冻结/split 互斥/metric 可计算，**非**要求每 detector NRC≤1；组成 detector #1/#20/#32，D2-audit NRC 0.67/0.74/0.62；#32 仅 dcal-subset 未入 summary table）。
- RHINO host(C1/B, mAP 0.7201) + O2-RTDETR host(A4, mAP 0.6497) 训练+锁定。
- C1 augmentation-view consistency gate（formal_pass, D_audit）。
- A4 same-host source-attribution gate（formal_pass, D_audit）。
- 阈值经 D_cal 冻结（token 017），D_audit 仅 holdout。

## 已完成（exploratory, 非 DOTA / 多 detector）
- DIOR-R 6 detectors, DOTA-v1.0 6, DOTA-v1.5 4, FAIR1M 3, SODA-A 3, HRSC 1（全 exploratory）。
- full-val: DIOR/FAIR1M/SODA orcnn+psc+rtmdet+lsknet + ARS-DETR DIOR + Strip DIOR。
- ARS-DETR 隔离 env(mmrotate 0.1.0) 建成，DIOR cross-dataset 解锁。Strip cross-dataset DIOR 解锁。HRSC angle resolved_with_evidence。

## 未完成 / blocked（见 final_blocker_evidence.md）
- ARS-DETR FAIR1M/SODA: blocked_class_mapping_final（空格/类名映射）。
- point2rbox: blocked_upstream_artifact_unavailable_final（ted.pth 全上游死）。
- Strip FAIR1M/SODA: 无 baseline; HRSC: pattern available（未跑）。
- genuine physical multi-view C1 / cross-host A4: out_of_scope。

## benchmark finding（构造效度）
- NRC ⟂ mAP：Spearman(NRC,mAP)=-0.05(p=0.84)，控 dataset+family 偏相关≈0 → NRC 提供独立于 accuracy 的信息（非 mAP 换皮）。
- **PSC angle-coder orientation selection 反校准**：PSC 在 DOTA/FAIR1M/SODA NRC>1（1.06/1.08/1.26），mAP 不弱时仍 selection 弱于 random → benchmark 真实发现。

## 可宣称结论
- DOTA 范围内 D2/host/C1(augmentation-view)/A4(same-host) 已冻结 + D_audit formal_pass。
- 6 datasets × 多 detector 的 exploratory orientation-reliability（NRC/Risk）已真实测量。
- ARS-DETR 为独立 archetype（NOT RHINO 替代）。

## 禁止宣称结论
- full project complete / all datasets covered / 9-detector matrix complete。
- C1 genuine physical multi-view / A4 cross-host causal。
- ARS-DETR = RHINO。
- 任何非 DOTA cell 为 formal gate。

## 后续最小行动（若继续）
- ARS-DETR FAIR1M/SODA: class-name adapter（config CLASSES ↔ GT 名对齐, 无空格映射）。
- Strip/ARS-DETR HRSC: HRSC native farm（pattern 已验证）。
- point2rbox: 待上游恢复 ted.pth（weak_nonformal）。
- C1 genuine multi-view / cross-host A4: 需新数据 + P2/P3 机制 + 批准。
