# orientbench 项目执行文件 v2：measure -> fix 联合主线

项目名称：orientbench

当前版本：v2_measure_fix

适用对象：Claude Code、监督员、项目合作者

目标：将 P1 的 orientation reliability 测量与诊断，和 P3 的 reliability-aware orientation selector 修复路线，收敛为一篇 measure -> diagnose -> fix 联合论文。该文件替代旧版 P1-only 执行逻辑，但不废弃旧版 P1 frozen 资产。

---

## 1. 总裁决

当前不再推进 P1 / P2 / P3 三篇并列。

当前唯一论文主线：

> Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in Oriented Object Detection

定位：

- P1：measure + diagnose。
- P3：fix。
- P2：appendix / ablation / negative result。

当前阶段最重要的问题不是补更多 detector，也不是追公开 mAP，而是用二值门控决定联合论文的层级：

| 门控结果 | 论文定位 |
|---|---|
| G2_double_prime pass + Deployable pass | 诊断 + 可部署方法，冲 CVPR / ICCV / strong journal |
| G2_double_prime pass + Deployable fail | 诊断 + upper-bound / calibration analysis，TGRS / ISPRS |
| G2_double_prime fail | P3 顶会线关闭，P1 benchmark / diagnostic 作为主体，P3 降附录或实用 selector |

---

## 2. 不再重开的决策

以下问题不再反复讨论，除非出现新实验事实：

### 2.1 P1 是否立即单独投稿

当前答案：暂缓。

理由：

- P1 单独是高质量 benchmark / diagnostic，但科学载荷偏诊断。
- P1+P3 合并后形成 measure -> fix，论文质量更高。
- P1 frozen 资产保留，若 P3 门控失败，P1 可回退为 TGRS / ISPRS 投稿资产。

### 2.2 P2 是否独立推进

当前答案：不推进。

理由：

- OT-dustbin 若未明显打赢 GT-identity，C1 核心机制不足。
- P2 只作为 augmentation consistency 消融、负结果或附录。

### 2.3 是否补 full 9-detector matrix

当前答案：不补。

理由：

- full matrix 不是当前论文质量瓶颈。
- 当前瓶颈是 P3 selector 是否有非平凡、可部署修复能力。
- baseline 库足以支持当前分析，不用用更多 cell 替代科学命题。

### 2.4 是否追 DOTA 公开 mAP

当前答案：不追。

理由：

- 本项目 DOTA 口径固定为 train 训练、val 验证。
- 公开论文常用 trainval / test，不可直接对齐。
- 低于公开 mAP 不构成重训理由。

---

## 3. 当前论文结构

建议主论文结构：

1. Introduction
   - OBB 检测评价长期关注 mAP，但 angle reliability 没有被充分测量。
   - detection confidence 不等于 orientation confidence。
   - 论文提出 measure -> diagnose -> fix。

2. OrientBench Protocol
   - NRC-AUC；
   - risk-coverage；
   - angle error；
   - aspect-ratio / degeneracy；
   - D_cal / D_audit；
   - Track A/B/C。

3. Measuring Orientation Reliability
   - DOTA train/val 口径；
   - cross-dataset exploratory 口径；
   - within-dataset / comparable-setting NRC vs accuracy；
   - reliability 不直接等于 mAP。

4. Diagnosing Reliability Failure
   - reliability cliff；
   - near-square ill-posedness；
   - well-defined region p99 tail；
   - PSC detection-score selection miscalibration。

5. Reliability-Aware Orientation Selector
   - P3 selector；
   - score-only / score+ar / score+ar+size 对照；
   - nonlinear geometry-aware selector；
   - G2_double_prime。

6. Deployment Gate
   - leave-dataset；
   - leave-detector；
   - TTA / augmentation-consistency proxy；
   - upper-bound vs deployable。

7. Optional Mechanism Analysis
   - Track A；
   - PSC intrinsic uncertainty；
   - angle-coder mechanism vs score-proxy mismatch。

8. Limitations
   - non-DOTA exploratory；
   - full matrix incomplete；
   - P2 not solved；
   - Track A optional；
   - DOTA not public test SOTA claim。

9. Appendix
   - claim ledger；
   - thresholds；
   - sha256；
   - verifier；
   - baseline tables；
   - P2 negative result。

---

## 4. 执行优先级

### Priority 0：保护 P1 frozen 资产

任何新工作不得破坏：

- thresholds.yaml sha256；
- frozen D_cal / D_audit；
- current approved scope tag；
- P1 reports；
- persistent artifact manifest；
- claim ledger；
- formal / exploratory 标签。

旧 P1 产物只能读、复制、引用，不能覆盖。

### Priority 1：清 P1 硬债

这些是论文质量债，与 P3 门控并行推进。

#### 1. NRC 分析重写

要做：

- within-dataset NRC vs mAP；
- comparable-setting NRC vs mAP；
- NRC vs median / tail angle error；
- rank-distance；
- 控 detector family 的分析可以作为补充。

不要做：

- 把跨数据集 pooled Spearman 当主 headline。
- 宣称 NRC 完全独立于 mAP。

推荐表述：

> In comparable settings, NRC captures orientation reliability information that is not fully reflected by mAP.

#### 2. PSC 表述收紧

要做：

- 以 detector/dataset 为推断单位；
- 给 PSC NRC 报 CI；
- 分开写 FAIR1M / SODA / DOTA / DIOR。

允许表述：

- PSC 在 FAIR1M / SODA 上出现 Track B detection-score selection 反校准；
- DOTA 可写 trend 或边缘现象；
- DIOR 不反校准。

禁止表述：

- PSC 系统性跨数据集反校准；
- PSC angle head 已证明反校准。

#### 3. GV-obliquity 定义

正文必须补：

- 数学定义；
- 与 aspect ratio 的关系；
- 为什么是统一 proxy；
- 在 P1 / P3 中分别怎么用。

#### 4. Related Work

必须覆盖：

- detector calibration；
- D-ECE；
- selective prediction；
- conformal prediction；
- OBB square-like problem；
- oriented detection uncertainty；
- GWD / KLD / distribution-aware losses；
- angle representation / angle coding。

#### 5. Raw / matched predictions 持久化

要求：

- /dev/shm 只做临时计算；
- final artifacts 必须持久化；
- 每个 artifact 有 sha256；
- 有 manifest；
- 有 can_recompute；
- 有生成命令；
- 大文件不进 git。

### Priority 2：G2_double_prime 尺度混淆门控

这是下一阶段最高优先实验。

### Priority 3：Deployable 可部署门控

只有 G2_double_prime pass 后做。

### Priority 4：Track A PSC 机制支线

只有 G2_double_prime pass 且 Deployable 通过或接近通过后做。

---

## 5. G2_double_prime 实验设计

### 5.1 核心问题

当前 P3 selector 已证明 Track C 在 held-out 上能改善 PSC detection-score miscalibration，但仍需排除一个致命解释：

> selector 学到的可能只是 box size prior，即小框通常更不可靠，而不是 orientation-specific geometry。

G2_double_prime 要回答：

> 在固定 box-size 分箱内，nonlinear geometry-aware selector 是否仍显著优于 score-only 和 score + aspect-ratio + size 线性基线？

### 5.2 数据范围

优先使用已有 P1 / P3 artifacts，不新训练 detector。

必须包含：

- FAIR1M PSC；
- SODA PSC；
- 至少一个非 PSC detector 作为 sanity；
- 如果现有 artifacts 支持，可加入 DOTA / DIOR。

主分析必须在 well-defined region：

- 排除 near-square trivial 区；
- ar 阈值跑前冻结；
- 建议至少报告 ar >= 1.3 和 ar >= 1.6 sensitivity。

### 5.3 特征集合

#### score-only

- detection score。

#### score + ar linear

- detection score；
- aspect ratio 或 degeneracy coefficient 的线性项。

#### score + ar + size linear

- detection score；
- aspect ratio / degeneracy linear；
- box area / sqrt area / log area linear；
- 可加 class fixed effect，但需单独说明。

#### nonlinear geometry-aware selector

允许使用：

- score；
- aspect ratio；
- degeneracy coefficient；
- box area；
- width；
- height；
- class；
- local density；
- overlap；
- GV-obliquity；
- detector family，建议只作分析变量，不作为 deployable 主特征。

模型建议从简单到复杂：

1. logistic regression；
2. GAM / spline；
3. random forest / gradient boosting；
4. shallow MLP，仅作补充。

禁止一上来用复杂模型制造虚假增益。

### 5.4 标签

G2_double_prime 可用 D_cal 上的 GT angle-error 学 selector，并在 D_audit 上验证。

但必须明确：

- 这是 calibration / upper-bound setting；
- 不是 deployable setting。

标签形式：

- binary bad-angle label，例如 angle error > τ；
- 或 continuous angle risk；
- τ 必须跑前冻结；
- 可报告多 τ sensitivity。

### 5.5 指标

必须报告：

- NRC-AUC；
- AURC；
- Risk@70；
- Risk@90；
- p90 / p95 / p99 angle error after selection；
- bootstrap CI；
- paired bootstrap 或 per-cell paired test；
- fixed-size bin 内的结果。

### 5.6 通过条件

G2_double_prime pass 需要同时满足：

1. nonlinear geometry-aware selector 在 D_audit 上显著优于 score + ar + size linear；
2. 增益在 well-defined region 仍存在；
3. 增益在至少两个 dataset / detector cells 上方向一致；
4. fixed-size bin 内仍存在显著或稳定增益；
5. 不是仅由 near-square 样本驱动。

若只满足部分：

- 记录为 partial；
- 不得进入 CVPR / ICCV 路线；
- 可作为 TGRS practical selector。

### 5.7 失败条件

任一情况触发 fail：

- nonlinear selector 打不赢 score + ar + size linear；
- 增益只存在于 near-square；
- fixed-size bin 内增益消失；
- bootstrap CI 跨 0 或方向不稳定；
- 需要修改 thresholds / split 才能得到正结果；
- 主要效果来自数据泄漏或 GT-derived feature。

---

## 6. Deployable 门控设计

### 6.1 前置条件

只有 G2_double_prime pass 后才启动。

### 6.2 核心问题

G2_double_prime 仍然允许用 D_cal 的 GT angle-error 标定 selector。Deployable 门控要回答：

> 没有目标域 GT angle-error 标定时，selector 是否仍能工作？

### 6.3 可接受路线

至少完成一种，最好两种。

#### 路线 A：leave-dataset

训练 selector：

- dataset A/B/C。

测试：

- unseen dataset D。

不能在 D 上用 GT angle-error 重标定。

#### 路线 B：leave-detector

训练 selector：

- detector family A/B。

测试：

- unseen detector family C。

不能在 C 上用 GT angle-error 重标定。

#### 路线 C：TTA / augmentation consistency proxy

用无 GT proxy label 学 selector，例如：

- rotation TTA angle consistency；
- flip consistency；
- scale consistency；
- query / box stability；
- view-consistency residual。

再在 D_audit GT 上评估。

#### 路线 D：minimal calibration

允许极少量标定样本，但必须明确标为 few-shot calibration，不得称 fully deployable。

### 6.4 通过条件

Deployable pass：

- 在未见 dataset 或未见 detector 上仍显著优于 score-only；
- 尽量优于 score + ar + size linear；
- 保留 G2_double_prime 中主要增益的一定比例；
- 不使用目标域 GT angle-error 重新标定。

Deployable fail：

- 只能在同 cell D_cal -> D_audit 成功；
- leave-dataset / leave-detector 失败；
- TTA proxy 不稳定；
- 必须每个新 cell 用 GT 重标定。

### 6.5 结果解释

若 Deployable pass：

- 可以写 deployable reliability-aware selector；
- 联合论文具备 CVPR / ICCV / strong journal 路线。

若 Deployable fail：

- P3 是 oracle / upper-bound analysis；
- 不得称 method；
- venue 收缩为 TGRS / ISPRS。

---

## 7. Track A 机制支线

### 7.1 前置条件

Track A 不阻塞 P3 启动。

建议只有以下条件满足后启动：

- G2_double_prime pass；
- Deployable pass 或 close；
- 论文需要 mechanism depth。

### 7.2 目标

提取 PSC intrinsic angle uncertainty：

- angle logits；
- phase code；
- dual frequency outputs；
- native angle quality；
- entropy / margin / consistency。

比较：

- Track A intrinsic selection；
- Track B detection-score selection；
- Track C post-hoc selector。

### 7.3 解释规则

若 Track A 也 NRC>1：

- 可以写 PSC angle-coder intrinsic miscalibration；
- 仍需克制，因为样本是 detector/dataset 级小样本。

若 Track A 正常：

- 写 detection-score proxy mismatch；
- 不得说 PSC angle head 坏。

若 Track A 无法稳定提取：

- 写入 limitation；
- 不影响主线门控结论。

### 7.4 持久化

Track A dump 不能只放 /dev/shm。

必须有：

- persistent path；
- manifest；
- sha256；
- schema；
- can_recompute；
- hook 代码版本。

---

## 8. P2 / C1 处理

P2 当前不作为主线。

仅保留：

- augmentation-view consistency gate；
- OT-dustbin vs GT-identity 对照；
- negative result；
- appendix；
- optional ablation。

若未来有人提出恢复 P2，必须先满足：

- OT-dustbin 明显打赢 GT-identity；
- 打赢 OTA/SimOTA + KL；
- padding-only 不打平；
- stress bucket 有收益；
- G2 / P3 主线不受影响。

否则不得恢复。

---

## 9. 产物清单

### 9.1 文档产物

必须生成或更新：

```text
docs/paper_outline_measure_fix.md
docs/p1_hard_debt_checklist.md
docs/p3_g2doubleprime_report.md
docs/p3_deployable_gate_report.md
docs/psc_track_a_mechanism_report.md
docs/claim_ledger_for_paper.md
docs/venue_gate_decision_table.md
```

### 9.2 数据产物

建议路径：

```text
outputs/p3_selector/g2_size_control/
outputs/p3_selector/deployable_proxy/
outputs/p3_selector/track_a_diagnostics/
outputs/persistent_artifacts/
```

每个目录必须有：

- manifest；
- sha256；
- README；
- generation command；
- schema。

### 9.3 图表产物

主文候选图：

1. reliability cliff curve；
2. masked / unmasked angle-error CDF；
3. within-dataset NRC vs mAP；
4. PSC Track B bar + CI；
5. G2_double_prime 对照图；
6. fixed-size bin selector gain；
7. Deployable leave-dataset / leave-detector performance；
8. Track A/B/C comparison，若 Track A 成功。

---

## 10. 汇报与记录

所有执行记录写入：

```text
claude_code_and_supervisor.md
```

每条记录包含：

- 服务器时间；
- 指令来源；
- 执行动作；
- 关键命令；
- 产物路径；
- pass / fail / partial；
- 是否触发停止；
- 下一步建议。

对话汇报仅报告：

- 门控结论；
- pass / fail；
- 严重异常；
- 需要裁决的问题；
- 论文 claim 变更。

汇报必须使用：

```text
👇👇👇👇👇👇

内容

👆👆👆👆👆👆
```

---

## 11. 早停与回退

### 11.1 G2_double_prime fail 回退

动作：

- 立即停止 P3 顶会线；
- 不做 Deployable；
- 不做 Track A 大诊断；
- P1 回退为 benchmark / diagnostic 主体；
- P3 作为 practical selector 或 appendix。

论文目标：

- TGRS / ISPRS；
- 或 workshop，如果 P1 硬债也无法清。

### 11.2 Deployable fail 回退

动作：

- 不称 P3 method；
- 称 upper-bound analysis；
- 可保留 P3 作为修复潜力展示；
- Track A 可选，取决于是否能增强 P1 诊断。

论文目标：

- TGRS / ISPRS；
- 不冲 CVPR / ICCV。

### 11.3 Track A fail 回退

动作：

- 不影响主线；
- 写 limitation；
- 删除 PSC angle-head mechanism claim；
- 保留 score-proxy mismatch claim。

论文目标：

- 由 G2_double_prime / Deployable 决定，不由 Track A 决定。

---

## 12. 当前第一批任务

### Task 1：冻结新主线

更新文档：

- CLAUDE.md；
- 项目执行文件_v2_measure_fix.md；
- docs/paper_outline_measure_fix.md。

### Task 2：P1 硬债清单

输出：

```text
docs/p1_hard_debt_checklist.md
```

必须列出：

- NRC within-dataset 重画；
- PSC 推断单位修正；
- GV-obliquity 定义；
- related work；
- artifact 持久化；
- governance 放附录；
- claim ledger 更新。

### Task 3：G2_double_prime 实验

输出：

```text
docs/p3_g2doubleprime_report.md
```

必须包括：

- 数据 cell；
- split；
- well-defined 区定义；
- size bin 定义；
- baseline 定义；
- nonlinear selector 定义；
- 指标；
- bootstrap CI；
- pass / fail 裁决；
- 下一步是否进入 Deployable。

### Task 4：若 G2_double_prime pass，启动 Deployable

输出：

```text
docs/p3_deployable_gate_report.md
```

### Task 5：若 Deployable pass 或 close，启动 Track A

输出：

```text
docs/psc_track_a_mechanism_report.md
```

---

## 13. 最终成功标准

### CVPR / ICCV / strong journal 路线

必须满足：

- G2_double_prime pass；
- Deployable pass；
- P1 硬债清理完成；
- P2 不抢主线；
- claims 克制；
- artifacts 可复算；
- 方法不是普通 calibration；
- 方法不是 size prior；
- 方法不是 near-square trivial rule。

### TGRS / ISPRS 路线

满足任一：

- G2_double_prime pass 但 Deployable fail；
- G2_double_prime partial；
- P3 是 upper-bound / practical selector；
- P1 诊断扎实，P3 作为实用扩展。

### 降级路线

若：

- G2_double_prime fail；
- P1 硬债无法清；
- artifacts 不可复算；
- 核心 claims 不能成立；

则：

- 不投顶刊；
- 整理为技术报告、workshop 或内部报告。

---

## 14. 一句话执行原则

> 现在只做能推进 measure -> diagnose -> fix 联合论文的事。先清 P1 硬债，再做 G2_double_prime；G2_double_prime 过才做 Deployable，Deployable 过才做 Track A 机制线。所有 venue 判断按门控结果查表，不再用主观“够不够”反复讨论。

