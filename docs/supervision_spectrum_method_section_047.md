# Supervision Spectrum — Method Section (047)

> 2026-06-30 16:46:48 CST。把 P3 selector 方法重写为 **supervision spectrum**（按监督预算分三档）。Route-C 正确口径 = **source-supervised selector + target GT-free inference**，**不是 fully GT-free**。

## 监督光谱（三档）

### 档 1 — Upper-bound（calibration）
- **数据流**：用本 cell **D_cal 的 GT angle-error** 训练 selector，同 cell **D_audit** 评估。
- **作用**：证明 **orientation-specific geometry structure 可学**（G2_double_prime：固定 size-bin 内 nonlinear 显著优于 score+ar+size linear → 非 size prior）。
- **口径**：**非 deployable**（同 cell 需 GT 标定）；是可达上界参照。

### 档 2 — Source-supervised transfer（主 deployable candidate）
- **数据流**：用 **source cells 的 GT** 训练 selector；**target（unseen dataset/detector）不使用任何 GT**，仅 inference。
- **作用**：**主 deployable candidate**。leave-dataset / leave-detector 评估。
- **口径**：**source-supervised + target GT-free inference**；无 target GT 泄漏（target GT 仅用于评估 NRC）。**不得写 fully GT-free**（selector 权重来自 source GT）。

### 档 3 — Fully GT-free proxy（弱但更干净）
- **数据流**：**不训练任何 GT-supervised selector**；直接用 TTA / augmentation consistency（identity vs hflip/vflip 角度一致性，或同图邻域一致性）作 selection score。
- **作用**：**低监督替代部署变体**；**效果较弱**（041 standalone proxy NRC≈0.77 vs source-supervised selector≈0.4，须如实报告）。
- **口径**：**fully GT-free**（唯一可如此称的部分）。

## 主稿口径锁定
- **source-supervised transfer 是主方法候选**（deployable candidate）。
- **fully GT-free proxy 是弱但更干净的部署变体**。
- **不得把 source-supervised transfer 写成 fully GT-free**。
- 三档共同回答："**在不同监督预算下，orientation reliability selection 能做到什么程度？**" —— 这是论文的 deployability spectrum 贡献。
