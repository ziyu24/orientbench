# Route-C Data-flow Audit (046)

> 2026-06-30 14:45:49 CST。焊死 source-GT / GT-free 接缝。逐问回答。

## 数据流逐问

### Q1. Route-C real TTA 的 selector 是否由 source GT angle-error 训练？
- **是**。selector = GradientBoostingRegressor，训练标签 y = matched pair 的 canonical angle error（**GT-derived**），在 D_cal 上拟合。→ **source-supervised**。

### Q2. target dataset / detector 上是否使用任何 GT angle-error 标定？
- **leave-dataset / leave-detector（042 deployable 设置）：否**。selector 训练只用 **source cells 的 D_cal GT**；target（unseen dataset/detector）的 D_audit GT **仅用于评估 NRC，不用于训练/调参**。→ **target GT-free inference，无 target GT 泄漏**。
- **within-cell（044 coverage / 042 within-cell）：用本 cell 的 D_cal GT 训练**，应用本 cell D_audit → 这是 **calibration / upper-bound 设置（同 cell 需 GT 标定）**，**非 deployable**，已如此标注。

### Q3. TTA consistency 是单独 selection signal，还是喂给 source-GT-trained selector？
- **两者都有，必须分清**：
  - **Route-C selector**：TTA consistency 是**一个 feature**，喂给 source-GT-trained selector（GBR）。→ selector 仍 source-supervised。
  - **standalone GT-free proxy（041）**：local-angle-consistency 直接作 selection score（**不训练任何 selector，无任何 GT**），NRC 评估。→ 这是**唯一 fully GT-free** 的部分，但**较弱**（041 NRC ~0.77 vs source-supervised selector ~0.4）。

### Q4. 若用 source GT 训练权重 → 正确写法
- **source-supervised selector + target GT-free inference**。**不得写 fully GT-free**（selector 权重来自 source GT）。

### Q5. 何时允许写 "GT-free deployable candidate"
- 仅 **standalone consistency proxy（不依赖任何 GT-trained selector 权重）** 可写 GT-free deployable candidate（且须标其较弱）。Route-C selector **不**满足，只能写 **source-supervised + target GT-free inference**。

## 泄漏检查
- **未发现 target GT 泄漏**：leave-dataset/detector 训练从不使用 target GT；target GT 仅评估。→ **deployable claim 不降级为 upper-bound**，但**措辞更正**为 source-supervised + target GT-free inference。
- within-cell 044/042 = calibration/upper-bound（同 cell D_cal GT），已正确标注，**非 deployable**。

## 裁决
- **Route-C deployable candidate 定义（统一）**：**source-supervised reliability-aware selector + target GT-free inference**（leave-dataset/detector 无 target GT）。**非 fully GT-free，非 deployable method complete。**
- standalone GT-free consistency proxy = 较弱的 fully-GT-free 方向（候选，未达 selector 水平）。
- 措辞修正：凡 "GT-free deployable / fully GT-free selector" → 改 "source-supervised + target GT-free inference deployable candidate"。
