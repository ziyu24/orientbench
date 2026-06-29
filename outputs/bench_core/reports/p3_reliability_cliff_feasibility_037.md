# P3 reliability cliff feasibility (037)

> 2026-06-29 15:49:22 CST · 基于 036 cliff 数据（fig1_reliability_cliff_data.csv），无新实验。

## cliff 量化
- near-square (ar<1.3) vs well-defined (ar>2) **p99 delta ≈ 81.6°**（mean，范围 80.9-82.2°，7 cells）—— cliff 极陡，**由 near-square 朝向 ill-posedness 主导**。
- **well-defined region (ar>2) p99 ≈ 8.3°**（mean，7.8-9.1°）—— 去退化区后尾部**modest**。
- near-square NRC ~0.93-0.97（selection 在歧义区无效），well-defined NRC ~0.43-0.49（selection 有效）。

## P3 问题空间判断
- **大部分 tail（~81.6° delta）来自 near-square 几何退化（ill-posed），不是可学习的可靠性缺陷**——一个 selector 在该区只能"识别近方形并弃权"，而 aspect-ratio 本身就能 trivially 做到。
- **well-defined region 仍有问题空间但 modest**（p99 ~8°，NRC ~0.43-0.49 < 1 表示 selection 有效但远非完美）。
- **更有价值的 P3 信号 = PSC reverse-calibration（FAIR1M/SODA，Track B 显著）**：这是特定 detector family 的真实 selection 失败，非几何退化。是否可由 post-hoc selector 修复见 psc_trackabc_control_037。

## 结论（待 Track C 数据补全）
- P3 应优先做 **unified-proxy / post-hoc selector（Track C）**，而非声称 intrinsic uncertainty（Track A unavailable）。
- P3 的核心问题空间 = **well-defined region 的 selection + PSC 类 score-proxy mismatch**，而非 near-square 几何歧义（后者用 aspect-ratio 掩码即可处理）。
