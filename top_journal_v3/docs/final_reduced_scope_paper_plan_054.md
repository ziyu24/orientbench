# 收缩版论文计划 054

## 新定位

论文定位调整为：`Orientation Reliability Benchmark + Conformal Risk Control`。本文不再追求 broader top-tier 强主张，也不再把 P3 selector、PSC 机制或下游任务写成已成功方法。论文核心是：在真实 detector artifacts 上建立朝向可靠性的测量协议，诚实报告 mAP 与 orientation reliability 的部分错位，并给出 within-cell 场景下可形式化陈述的 conformal orientation risk control。

## 保留的主张

- OBB 检测中的 mAP 未充分刻画 orientation reliability，尤其在角度风险、risk-coverage 和选择性预测语法下仍有必要单独测量。
- NRC / AURC / Risk@70 / Risk@90 可以作为 orientation reliability benchmark 的分析指标，但不声称 NRC 与 mAP 严格独立。
- P1 构造性解耦只提供 partial evidence：angle risk 在受控扰动下显著变化，但 mAP@0.5 同样有明显响应。
- P2 是当前最稳正贡献：在 052 full real matched tables 和 frozen D_cal / D_audit 下，within-cell conformal risk control 给出了明确的 risk threshold、coverage、violation rate 和 finite-sample 口径。
- Shift setting 只保留为 audit：报告 violation / coverage 如何变化，不承诺分布移位下严格保证。
- Artifact-governed reproducibility 是论文资产：052 artifacts、manifest、schema、matched table 和 verifier 支撑结果追溯。

## 降级的主张

- P3 PSC 机制线降为 mechanism candidate / case study，不写成机制证明。
- P4 geometry-aware selector 降为分析对象，不写成稳定优于强不确定性基线的方法。
- P5 下游任务降为负结果，不写成 downstream utility proof。
- P1 解耦从“强构造效度”降为“部分支持”：可以说明 mAP 不充分，但不能证明 NRC 与 mAP 严格独立。

## 负结果

- P1 partial：真实 raw/schema 角度扰动重匹配后，mean |Delta angle risk| at 30 deg 为 26.4883 degrees，但 mean |Delta mAP@0.5| 也达到 0.1810。
- P3 partial：三项 PSC 免费测试仅 1/3 支持，不足以启动 PSC 重训矩阵。
- P4 partial：TTA circular variance 使用 theta -> 2theta 后，mean TTA NRC=0.9478，mean geometry NRC=0.9579，geometry-aware selector 未稳定打赢。
- P5 fail：angle-induced rIoU drop 下游任务在真实 matched predictions 上未显示稳定收益，mean risk improvement vs score-only=-0.0018，vs size-linear=-0.0016。

## 附录安排

- 052 artifact manifest、sha256、schema 和 matched table 放附录 A。
- D_cal / D_audit split、formal / exploratory 边界放附录 B。
- 指标定义和 conformal finite-sample 细节放附录 C-D。
- P1/P3/P4/P5 负结果和失败解释放附录 E。
- forbidden claims 和 claim ledger 放附录 F。
- verifier、复现命令和 git 大文件检查放附录 G。

## 为什么停止继续扩实验

053 已经完成真实 artifact 复跑，且主要裁决为 P1 partial、P2 pass、P3 partial、P4 partial、P5 fail。继续补 full matrix、追公开 mAP、启动 PSC 重训或继续下游任务，会把项目推回堆实验路线，但不会改变当前最稳结论：within-cell conformal risk control 是可正式陈述的正贡献，其余强方法/机制/下游 claim 尚无充分证据。

## 为什么 P2 是核心正贡献

P2 与 P1/P3/P4/P5 的差异在于它不依赖把 selector 写成成功方法，也不依赖跨域机制解释。它把任意 orientation reliability score 外面套上 conformal threshold / guarantee layer，在 D_cal / D_audit 互斥且同分布的 within-cell 设置下，给出 empirical risk、coverage、violation rate 和 finite-sample guarantee 口径。该贡献与 benchmark 定位兼容，也能把论文从单纯诊断提升为可控风险框架。

## 为什么 P3/P4/P5 不再作为主贡献

- P3 证据不足：DOTA #20、aliasing、confounding 三项免费测试没有达到至少两项支持，不足以申请 PSC 重训矩阵。
- P4 证据不足：强不确定性基线中 TTA circular variance 是可用且竞争性的 baseline，geometry-aware selector 未稳定胜出。
- P5 证据不足：真实 matched predictions 上 downstream risk 没有稳定下降，不能写下游实用性已被证明。

## 论文主线

最终中文稿按如下主线组织：问题背景 -> 指标与协议 -> 真实 artifacts -> P1 partial 测量证据 -> P2 conformal risk control 正贡献 -> P3/P4/P5 边界与负结果 -> 讨论和局限性 -> 克制结论。
