# 072 完成汇报：M4 真人双标最低协议与结果

## 编号状态

- 071：人工双标工具物理落盘与可启动验证已完成。
- 072：人工双标执行、分阶段核验、最低样本协议和重检分析已完成。
- 下一正式编号：073。

## 执行完成情况

- A/B 使用独立身份、互盲清单和不同随机顺序。
- 最终 primary 集合为 600 个相同 canonical 目标，DIOR-R、FAIR1M、SODA-A
  各 200 个；每个目标双方均已作出 angle、ambiguous 或 skip 决策，无 pending。
- 初期 B 误进入 full 清单的问题已审计并纠正；所有真人结果均保留，最终集合通过
  mapping、schema 和 set-equality 核验，未重复计数。
- 29 个“一方有角度、另一方 ambiguous/skip”的目标完成独立匿名重检；原始结果
  不被覆盖，重检只作为 secondary endpoint。

## Primary 结果

600 个目标中有 450 对双方均给出数值角度：DIOR-R 122、FAIR1M 169、
SODA-A 159。

- mean circular disagreement：2.3112 degrees；
- image-cluster bootstrap 95% CI：1.9970–2.7854 degrees；
- median：1.6359 degrees；
- p90 / p95：4.4220 / 5.9359 degrees；
- P(>5 degrees)：8.00%，95% CI 5.57%–10.56%；
- P(>10 degrees)：0.89%，95% CI 0.22%–1.79%。

ar>=2.1 主子集有 308 对，mean=2.2823 degrees，median=1.6130 degrees，
P(>5 degrees)=6.82%，P(>10 degrees)=0.65%。三个数据集方向与 200、526
检查点一致。SODA-A 的尾部风险较高，必须保留为数据集限制。

## 重检结果

29 个单方未给角度目标中，27 个在盲重检中给出数值角度，2 个仍为 ambiguous。
27 对的 mean=2.2126 degrees、median=1.9302 degrees、p90=3.8216 degrees、
p95=4.1811 degrees；结果支持“多数单方未标是可恢复的不确定决策”，但不得替换
primary 原标注。

## 科学裁决

最低人工协议为 COMPLETE。当前证据足以支撑：

- overall human annotation noise anchor；
- broad dataset-level comparison；
- 5-degree fine-risk 的 noise-sensitive 限定；
- ar>=2.1 的主分析边界。

无需为上述结论继续到 1,500。只有论文保留正式 rare-class、size 或
extreme-tail 分层 claim 时，才需要 500 targets per dataset。

本报告不宣称全项目完成或 submission frozen。072 结果尚需在后续正式命令中接入
全局一键复算和提交冻结门控。

## 合规

- 未训练、未推理、未修改论文；
- 未修改 thresholds.yaml，sha256 仍为
  `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`；
- 未修改 D_cal / D_audit、host、formal / exploratory 标签；
- 未伪造或覆盖人工标注；
- A/B 标注服务均已停止。
