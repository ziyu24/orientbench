# AGENTS.md — OrientBench 客户端中立入口与服务器安全基线

本文件由 Git 跟踪，是 Codex、Claude Code 与服务器共同可见的项目入口；它不按客户端、登录账号、电脑或历史会话猜测 B/C/SERVER 角色。

每个独立 clone 只需绑定一次稳定 worker：

```text
git config --local paper.worker-id peer-b-primary
git config --local paper.worker-id peer-c-primary
git config --local paper.worker-id server-primary
```

实际只选择其中一个。随后从 `dis/governance/workers.json` 恢复角色并读取对应公开角色配置。缺失、未知、停用或与任务冲突时 fail closed，只读并请用户完成一次绑定；不得从模型品牌或文件名推断身份。同一 clone 不得切换或同时承担 B/C，另一角色使用独立 clone。换 Codex/Claude Code 账号不影响绑定。

B/C 权力完全对等、文件所有权分离；共享规则以 `dis/governance/role_contract.json`、`dis/collaboration_protocol.md` 和 `dis/coordination.json` 为准。服务器只执行用户交付的精确 `dispatch_id + plan_path + dispatch commit SHA`，不扫描候选计划，也不裁决科学结论。

本文件后续章节保存 OrientBench 的科学、数据、资源与服务器安全基线，只约束相应任务，不产生 B/C 层级。每轮冻结计划可在不放宽这些上界的前提下设置更严格边界。若用户明确更新治理或项目事实，以 Git 中更新后的规则为准。

项目：orientbench

迁移时保留的科学阶段基线：P1 + P3 measure -> diagnose -> fix 联合主线

---

## 0. 当前唯一主线

当前项目不再是单纯扩展 P1 benchmark，也不是 P1 / P2 / P3 三篇并列推进。

当前唯一主线：

> Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in Oriented Object Detection

含义：

- P1 = measure + diagnose：定义和验证 orientation reliability、NRC、risk-coverage、reliability cliff、PSC score-level miscalibration。
- P3 = fix：验证 reliability-aware orientation selector 能否修复现有 OBB detector 的角度可靠性排序问题。
- P2 / C1 = 附录、消融或负结果；除非 OT-dustbin 明确打赢 GT-identity，否则不得恢复为主线。

当前阶段的核心问题不是补 full matrix，也不是追公开 mAP，而是用二值门控判断 P1+P3 联合论文到底是：

- CVPR / ICCV / strong journal 路线；
- TGRS / ISPRS JPRS 路线；
- 或降为 benchmark + appendix。

---

## 1. 思考模式

对任务复杂度分级处理。

### 1.1 琐碎任务

直接执行，不展开长推理。

示例：

- 单行修改；
- 格式调整；
- 查看文件；
- 查看日志；
- 简单解释；
- 统计文件路径或 sha256。

### 1.2 中等任务

先给出简要判断和方案，再执行。

示例：

- 普通代码修改；
- 配置调整；
- 常规问题排查；
- 轻量分析；
- 补图表；
- 修正文档 claim。

### 1.3 复杂任务

使用最高级别深度思考，但只输出关键结论、判断依据和行动方案，避免冗长推理。

示例：

- 核心模块设计；
- selector 门控实验设计；
- 训练不收敛调试；
- 超参选择；
- 消融分析；
- 失败归因；
- 论文写作；
- venue 判断。

---

## 2. GPU / CPU 规则

服务器资源上限：

- GPU：4 x A30，每卡 24GB；
- CPU：48 核。

硬规则：

- 训练必须默认 4 卡对齐。
- 某卡被小内存占用时仍然先上 4 卡，只有爆显存才允许回退。
- CPU 密集任务必须使用 >= 80% 核。
- CPU 密集任务使用 < 60% 核视为违规，除非有明确理由并记录。
- 大规模评估、匹配、bootstrap、risk-coverage 计算应尽量使用多核并行。

当前阶段优先级：

- G2_double_prime / Deployable / Track A forward dump 之前，不允许启动大规模 detector 重训。
- 若必须训练 selector 或轻量模型，先跑小样本 smoke test，再正式运行。
- 所有训练或评估日志必须记录完整路径。

---

## 3. Git 与项目路径

Git 仓库：

```text
https://github.com/ziyu24/orientbench
```

项目根目录：

```text
/home/rspip/cqc/pro/study/orientbench
```

允许操作最高根目录：

```text
/home/rspip/cqc/pro/study/
```

数据集目录：

```text
/home/rspip/cqc/data/dataset
```

可能包含：

- hrsc2016
- dota1.0
- dota1.5
- dior
- fair1m
- soda-a

第三方仓库目录：

```text
/home/rspip/cqc/pro/study/third_party
```

规则：

- 第三方源码禁止直接改。
- 需要改配置时，将配置复制到 orientbench 项目内再改。
- 缺少三方源码时，只能下载到 third_party。
- 可以将 third_party 下源码安装到专用 conda 环境。
- 不得污染其他项目。
- 所有 orientbench 产物必须放在 orientbench 内，或放在明确登记的持久化 artifact 目录中。

---

## 4. 数据与基线规则

### 4.1 pth_data 基线库

参考基线目录：

```text
/home/rspip/cqc/pro/study/pth_data
```

只读 readme：

```text
/home/rspip/cqc/pro/study/pth_data/readme.md
```

规则：

- 先查 readme.md。
- 若未提供 readme.md 或 readme.md 不可读，先报告用户并停止后续实验设计。
- 此处标记为 valid 的 baseline 优先使用。
- 使用前必须解析对应 config / log / pth，记录：
  - dataset；
  - split；
  - backbone；
  - schedule；
  - batch size；
  - lr；
  - SyncBN / BN；
  - mAP；
  - 框架版本；
  - checkpoint sha256。
- baseline 只用于对齐实验，不得左右项目内在科学逻辑。
- 自建 baseline 存入项目下 pth_data，格式与原 pth_data 保持一致。
- 自建训练的 baseline 文件必须以 `baseline` 开头命名。

### 4.2 DOTA 规则

DOTA 系列固定规则：

- train 训练；
- val 验证；
- 不追公开 trainval/test mAP；
- 不下载官方 trainval 模型；
- 不引用官方 test 数字；
- 只和本项目自跑 baseline 比。

重要说明：

> DOTA val mAP 低于公开论文 trainval/test 数字是正常现象，不构成重训理由。

只有以下情况才允许重训 DOTA baseline：

- dataset split 用错；
- config 与预注册规则不一致；
- log 缺失或损坏；
- checkpoint 无法加载；
- sha256 或 valid 状态无法确认；
- 监督员或合作者明确批准。

### 4.3 非 DOTA 规则

默认：

- trainval 训练；
- test 测试。

特殊情况必须先沟通，不能自行改口径。

### 4.4 训练与评估纪律

- 先跑通 smoke test，再做正式版。
- 每 epoch 必评估。
- 只存最高 mAP checkpoint + 最近 epoch checkpoint。
- 首 epoch 明显偏低时停下报告，不盲跑。
- 必须与官方或自定 baseline 对齐：
  - epoch；
  - batch size；
  - lr；
  - 4 卡 global batch 线性调整；
  - SyncBN / BN。
- 不对齐则实验作废。
- 始终默认 4 卡训练。
- 训练必须给出日志全路径。

---

## 5. 当前阶段硬禁区

以下事项禁止执行，除非用户和监督员共同批准：

1. 禁止追 DOTA 公开 mAP。
2. 禁止因为 DOTA val 精度低重训 host。
3. 禁止修改 frozen thresholds。
4. 禁止修改 D_cal / D_audit split。
5. 禁止把 exploratory 结果改成 formal。
6. 禁止补 full 9-detector matrix 来制造全面性。
7. 禁止复活 P2 作为主线。
8. 禁止把 near-square trivial gain 包装成方法贡献。
9. 禁止把 Track C upper-bound 写成 deployable method。
10. 禁止宣称：
    - full project complete；
    - all datasets covered；
    - 9-detector matrix complete；
    - C1 genuine physical multi-view solved；
    - A4 cross-host causal proved；
    - PSC angle head 已证明反校准；
    - NRC 完全独立于 mAP；
    - DOTA SOTA。

---

## 6. 当前阶段三门控

当前阶段只围绕三个门控推进。

### 6.1 G2_double_prime：尺度混淆排除

最高优先级。

核心问题：

> 在固定 box-size 分箱内，geometry-aware selector 是否仍显著优于 score-only 和 score + aspect ratio + size 线性基线？

必须比较：

- score-only；
- score + aspect-ratio linear；
- score + aspect-ratio + size linear；
- nonlinear geometry-aware selector；
- oracle / upper-bound，仅作上界，不作部署方法 claim。

必须在 well-defined 区域报告主结果，不允许靠 near-square trivially 获益。

若 G2_double_prime fail：

- P3 顶会线关闭；
- P1+P3 收缩为 TGRS / ISPRS benchmark + practical selector；
- 不启动 Deployable；
- 不启动 Track A 大诊断；
- 不启动 detector 训练。

若 G2_double_prime pass：

- 进入 Deployable 门控。

### 6.2 Deployable：可部署性门控

核心问题：

> selector 是否能在没有目标域 GT angle-error 标定的情况下保持显著增益？

至少验证一种：

- leave-dataset；
- leave-detector；
- TTA / augmentation consistency 生成无 GT proxy label；
- 训练后在新 detector / 新 dataset 上不重新用 GT 标定。

若 Deployable fail：

- P3 是 analysis / upper-bound；
- 不能称 deployable method；
- venue 收缩到 TGRS / ISPRS 或分析型论文。

若 Deployable pass：

- P1+P3 联合论文具备 CVPR / ICCV / strong journal 路线资格。

### 6.3 Track A：PSC 机制支线

Track A 不门控 P3 启动。

Track A 只在以下条件满足后进入关键路径：

- G2_double_prime pass；
- Deployable pass 或至少 Deployable 有明确可行路径；
- 需要增强 PSC mechanism 小节。

Track A 目标：

- instrumented forward dump；
- 提取 PSC angle logits / phase code / intrinsic uncertainty；
- 比较 intrinsic angle uncertainty selection vs detection-score proxy selection。

结果解释：

- 若 Track A 也反校准：可写 angle-coder mechanism；
- 若 Track A 正常：写 detection-score proxy mismatch；
- 无论结果，不重新讨论主线 venue，只作为机制深度补充。

Track A 产物必须持久化，不能只放 /dev/shm。

---

## 7. P1 硬债清单

以下任务与 G2_double_prime / Deployable 并行清理。

### 7.1 NRC 与 mAP

禁止把跨数据集 Spearman 作为 headline。

改为：

- within-dataset 分析；
- comparable-setting 分析；
- rank-distance；
- detector-family 控制；
- 克制表述为：NRC 在可比设置内提供 accuracy 之外的 reliability signal。

### 7.2 PSC 推断单位

PSC 结论从 instance-level 降为 detector / dataset-level。

允许表述：

- PSC 在 FAIR1M / SODA 上，Track B detection-score selection 显著反校准；
- DOTA 可写趋势或边缘结果；
- DIOR 不反校准。

禁止表述：

- PSC 系统性跨所有数据集反校准；
- PSC angle head 已证明反校准。

### 7.3 GV-obliquity 定义

正文必须给出 GV-obliquity 的明确数学定义、使用位置和与 aspect-ratio / degeneracy 的关系。

### 7.4 Related Work

必须补：

- detector calibration / D-ECE；
- selective prediction；
- oriented object detection calibration；
- GWD / KLD / distribution-aware losses；
- square-like problem；
- OBB angle periodicity；
- uncertainty / conformal prediction。

### 7.5 Artifacts 持久化

/dev/shm 只能作为临时计算区。

投稿前必须持久化：

- raw 或 matched predictions；
- manifest；
- sha256；
- 生成命令；
- schema 版本；
- can_recompute 标记。

### 7.6 治理内容放附录

frozen sha256、claim ledger、verifier、threshold token、PM 表等是优势，但不应压过正文科学结果。

正文强调：

- finding；
- method；
- evidence；
- limitation。

治理基建放附录。

---

## 8. 输出与汇报纪律

### 8.1 汇报内容

只报告：

- 决策性结果；
- 触发停止条件；
- 分支触发；
- 训练 / 评估结论；
- 严重异常；
- 用户主动询问的结果。

不要刷屏报告：

- bash 调试过程；
- 语法检查碎片；
- task / monitor 提示；
- 权限提示；
- 中间无意义日志。

这些内容只写入日志。

### 8.2 汇报格式

每次对话汇报必须使用唯一入口和出口：

```text
👇👇👇👇👇👇

汇报内容

👆👆👆👆👆👆
```

规则：

- 前后空行；
- 整条汇报仅 1 对该入口 / 出口；
- 内部不再使用同类 emoji；
- 汇报必须短而决策相关。

### 8.3 固定记录文件

每次汇报与下达的指令必须记录到：

```text
claude_code_and_supervisor.md
```

记录必须包含：

- 人类可读服务器时间戳；
- 指令来源；
- 执行动作；
- 关键产物路径；
- 是否触发停止条件；
- 下一步建议。

---

## 9. 早停机制

必须有早停机制，防止项目准备很久后一上手失败。

当前阶段早停条件：

- G2_double_prime 中 nonlinear selector 打不赢 score + ar + size linear；
- selector 增益只来自 near-square；
- fixed-size bin 内增益消失；
- D_cal / D_audit 泄漏；
- bootstrap CI 显示关键增益不稳；
- Deployable 中 leave-dataset / leave-detector 完全失败；
- 产物无法持久化；
- 需要修改 frozen thresholds 才能得到结论。

触发早停必须：

1. 停止继续扩展；
2. 写明触发条件；
3. 输出最小证据表；
4. 报告监督员和用户；
5. 不自行改方向。

---

## 10. 权限与自主边界

Claude Code 应具有足够执行权限，不要在小事上来回等待。

原则：

- 想清楚再干；
- 不懂就问；
- 小事自决；
- 边界停手；
- 所有边界行为留痕。

小事可自决：

- 补充日志；
- 生成中间 csv；
- 修复明显路径错误；
- 增加只读检查；
- 增加可视化；
- 整理文档格式。

必须停手询问：

- 改 frozen thresholds；
- 改 D_cal / D_audit；
- 改 formal / exploratory 标签；
- 重训 host；
- 启动大规模 detector 训练；
- 引入新数据集；
- 删除或覆盖旧产物；
- 将 P2 恢复为主线；
- 宣称 CVPR / ICCV ready；
- 宣称 full project complete。

---

## 11. 推荐项目结构

当前阶段建议在 orientbench 内新增或维护：

```text
orientbench/
  docs/
    paper_outline_measure_fix.md
    claim_ledger_for_paper.md
    p1_hard_debt_checklist.md
    p3_g2doubleprime_report.md
    p3_deployable_gate_report.md
    psc_track_a_mechanism_report.md
  p3_selector/
    g2_size_control/
    deployable_proxy/
    track_a_diagnostics/
  outputs/
    p3_selector/
      g2_size_control/
      deployable_proxy/
      track_a_diagnostics/
    persistent_artifacts/
```

旧 P1 frozen 产物不得移动或覆盖。

---

## 12. 最终目标

当前长期目标：

> 一篇 measure -> diagnose -> fix 联合论文。P1 测量诊断，P3 修复；P2 降附录。G2_double_prime 和 Deployable 两个二值门控决定 venue；Track A 只决定机制深度。所有任务必须服务于这条主线。

若 G2_double_prime 和 Deployable 均通过：

- 进入 CVPR / ICCV / strong journal 路线。

若 G2_double_prime 通过但 Deployable 失败：

- 收缩为 TGRS / ISPRS 分析型论文或 benchmark + upper-bound selector。

若 G2_double_prime 失败：

- P3 顶会线关闭；
- P1 作为 benchmark / diagnostic 主体交付；
- P3 作为 practical selector 或附录。

