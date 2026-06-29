👇👇👇👇👇👇

# OrientBench — 035 P1 深度科学有效性核验 + 单文件报告 完成

- **035 完成**。无训练、无 GPU、thresholds 未变（b7c4e649）、D_cal/D_audit split 未变。
- **主报告（唯一人读）**：`docs/orientbench_p1_scientific_report.md`（034 分散文件已移入 docs/_superseded/）。

## p99 核验结论
- 角度误差代码**正确**（π-周期最短距离，max 90°，无 bug）。**p99≈90° = near-square / aspect-ratio 退化（朝向 ill-posed），非 detector 灾难性失败** → 已纠正 033 的 "catastrophic" 措辞。well-defined region masked p99 = **10-16°**（真实非平凡尾部）。

## reliability cliff 结论
- **成立**：p99 随 aspect-ratio：ar>2 ~8-10° → ar<1.3 ~84-90°；NRC well-defined ~0.47-0.49、near-square ~0.93-0.97。core 动机图：figures/reliability_cliff/。

## NRC 构造效度结论
- **克制措辞**：23-cell 上**未检测到 NRC 与 mAP 显著相关**（Spearman -0.046，CI95 [-0.49,0.48]；partial ctrl both df=7，CI 退化 → under-powered）。NRC 提供不同于 accuracy 的信号；**不主张严格独立**。最强反例 = PSC。

## PSC preflight 结论
- Track B（detection-score proxy）下 PSC 反校准**稳定**（DOTA/FAIR1M/SODA NRC>1，延伸到 well-defined 区）。**只能说 score-level 反校准，不能说 angle head 本身**。Track A/C pending。

## 是否建议 angle-head control experiment
- **建议申请**（Track B 证据足够）；但**现在不启动大训练**（边界）。需合作者批准 + 算力。

## 是否建议 P3 继续
- **建议继续**：reliability cliff + well-defined tail + PSC 反校准 = P3 前置证据成立（非收缩情形）。

## 顶刊判断（克制）
- TGRS/ISPRS JPRS：有希望（p99/cliff/NRC 严谨写）。CVPR/ICCV/TPAMI：现在不够（需把 PSC/cliff 做成机制/方法贡献，非仅评测表）。

## 验证/test/git
- verifier `104_verify_p1_scientific_report_035` → VERIFIED 19/19；pytest 全过；thresholds 未变；git 0 大文件（figures/persistent gitignored）。

👆👆👆👆👆👆
