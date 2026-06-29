# OrientBench P1 — 一页摘要

## 当前完成什么
- OrientBench Bench-Core + DOTA formal scope（D2 partial gate / RHINO C1B host / O2-RTDETR A4 host / C1 augmentation-view formal_pass / A4 same-host formal_pass，阈值冻结）。
- 23 real cells / 6 datasets（DIOR-R 6 detectors, DOTA-v1.0 6, DOTA-v1.5 4, FAIR1M 3, SODA-A 3, HRSC 1）的 cross-dataset exploratory orientation-reliability。
- v2 科学有效性审计（NRC 构造效度 + 尾部风险 + PSC 反校准）。

## 为什么 P1 有科学价值
- **NRC 提供 accuracy 独立的可靠性信号**：Spearman(NRC,mAP)=-0.05，控 dataset+family 偏相关≈0。可靠性≠精度，NRC 不是 mAP 换皮。
- **存在灾难性朝向尾部**：unmasked p99≈89°（near-square 断崖），masked p99 10-16°。orientation reliability cliff 真实。

## 为什么不是 SOTA/mAP 项目
- DOTA 用 **train 训练 / val 验证**（非 trainval/test），mAP 低于公开论文属正常，**不追 SOTA、不下载官方 trainval 模型**。
- P1 命题是“朝向可靠性诊断尺子”，不是刷精度；mAP 仅作 sanity。

## 为什么 PSC 是机制候选
- PSC angle-coder 在 **DOTA/FAIR1M/SODA NRC>1**（唯一系统性反校准 family），且 DOTA/SODA mAP 不弱时仍反校准 —— 一个 accuracy 看不见、跨数据集稳定的可靠性缺陷。机制候选：相位置信与角度回归质量不单调。

## 下一步需要什么批准
- D1 接受 v2 作为顶刊依据；D2 PSC angle-head control experiment（机制归因，需算力批准）；D3 P3 cross-dataset reliability formalization；D5 冻结 current scope；D6 启动论文主文。详见 collaborator_p1_decision_form.md。

> 边界：full project 未完成；C1≠genuine 多视角；A4≠跨 host 因果；ARS-DETR≠RHINO。thresholds 冻结 b7c4e649。无新训练。
