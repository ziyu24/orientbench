# 负结果与边界 054

## P1 partial 为什么不是失败

P1 的目标是检验 mAP 与 orientation risk 是否可以在受控扰动下分离。053 真实 artifacts 复跑显示，角度扰动会显著改变 angle risk，30 度扰动下 mean |Delta angle risk| 为 26.4883 degrees；但 mAP@0.5 也出现较强响应，mean |Delta mAP@0.5| 为 0.1810。因此，P1 不能写成强解耦或 construct validity pass。

这不是完整失败，因为实验仍说明 angle risk 有独立可观测的变化轨迹，且 reverse perturb 显示非角度扰动可明显改变 mAP 而对角度风险影响较弱。正确写法是：mAP 未充分刻画 orientation reliability，但本文不声称 NRC 与 mAP 严格独立。

## P3 partial 为什么不启动重训矩阵

P3 本轮只允许做 DOTA #20 phase_mod negative control、aliasing fingerprint 和 confounding check 三项免费测试。053 使用 052 per-matched phase_mod full table 后，三项中仅 1/3 支持机制线。该结果不足以申请 PSC / CSL / DCL / regression 多 seed 重训矩阵。

正确定位：PSC 保持 mechanism candidate / case study。可以写检测分数与朝向可靠性之间存在错配现象，但不能写 PSC 机制已经被证明，也不能写 PSC angle head 已被证明反校准。

## P4 partial 对 selector claim 的限制

P4 加入 TTA circular variance 后，角度方差按 pi 周期变量处理，即 theta -> 2theta 后计算 circular variance。053 结果为 mean geometry NRC=0.9579，mean TTA NRC=0.9478。由于 TTA circular baseline 具有竞争力，geometry-aware selector 不能写成稳定优于强不确定性基线。

正确定位：selector 是 benchmark 中的分析参照和候选 score，不是已证明可部署的最终方法。

## P5 fail 对 downstream claim 的限制

P5 使用 052 full real matched predictions 做 angle-induced rIoU drop 任务。结果显示 mean risk improvement vs score-only=-0.0018，vs size-linear=-0.0016。该任务没有证明 selector 降低下游风险。

正确定位：本文不能写下游实用性已经被证明。P5 应作为负结果，说明 orientation reliability 指标向具体下游收益迁移仍需要更合适任务或应用约束。

## DOTA #20 的正确定位

DOTA #20 是真实 PSC Track A per-matched phase_mod 证据的一部分，用于 negative control 和跨数据集机制线检查。它不是公开 test mAP validation，也不是 DOTA 排行榜证据。本文采用 DOTA train/val 自跑协议，不追公开 trainval/test mAP。

## 必须删除或下沉的 claim

- 删除 P3 方法已成功的正面表述。
- 删除 broader top-tier readiness 的正面表述。
- 删除 PSC mechanism proof 的正面表述。
- 删除 downstream utility proof 的正面表述。
- 删除 full project completion 的表述。
- 删除 NRC 与 mAP 严格独立的表述。
- 删除检测器排行榜或 DOTA public mAP 对齐表述。

## 保留的边界性价值

负结果并非无价值。P1 partial 定义了 mAP blind spot 的真实边界；P3 partial 阻止过早进入昂贵重训；P4 partial 提醒强不确定性 baseline 必须纳入；P5 fail 约束了指标到任务收益的外推。它们共同支持一个更可信的收缩版论文：benchmark + conformal risk control，而不是过度包装的方法论文。
