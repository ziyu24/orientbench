# K2 角度编码头干预矩阵（预注册修订，066）— 不启动训练

> 依 K1–K4 执行令，K2 在 K4 之后启动；**本轮不启动 K2 训练矩阵**，仅修订预注册草案，吸收合作者关键修正。
> LR sweep 预算：`reports/k2_planned_lr_sweep_budget_066.csv`。差异对比 R1：`k2_pre_registration_delta_from_r1_066.md`。

## 1. 对照组与规模
5 类角度头 × 2 数据集（DIOR-R、SODA-A；资源允许再加 FAIR1M，不阻塞前二）× 3 seeds：
PSC / CSL / DCL / direct_regression(le90) / KLD(或 distribution-aware head)。

## 2. 固定项（预注册，训练后不改）
同 backbone、同训练数据、同 schedule family、同 augmentation policy、同 evaluator、同 masked ar 口径
（K4a derived-ar=2.1 主口径，1.6/1.3 sensitivity）、同 D_cal/D_audit 划分。

## 3. 关键修正（吸收合作者意见）
1. **不强行共享同一 LR**：各 head 做**预注册 LR sweep**（网格 {0.0025, 0.005, 0.010}），但**tuning budget
   相同**（每 head：3-LR 网格 × 1 pilot seed，按 val mAP 选最优 LR，再在最优 LR 上跑 3 seeds）。
2. **FP32 fallback**：若混合精度导致不稳定（如 GDLoss linalg.inv 半精度崩溃），允许关 AMP/FP32，但**必须记录**
   为该 head 的登记偏离。
3. **可用收敛门控**：每 head 须达"可用收敛"（AP50/AP75 未塌陷、loss 有限）才纳入 uncertainty 比较；否则
   failed_training。
4. **失败归因**：direct_regression / KLD 若训崩，须先证明是**方法本身**问题，而非超参/AMP——即在 LR sweep +
   FP32 fallback 后仍崩，才记方法性 failed_training；否则属工程问题需修复重试。
5. **native uncertainty**（预注册，不强构等价信号）：PSC=phase_mod；CSL/DCL=angle-class entropy/max-prob/margin；
   direct_regression=none（负对照）；KLD=predicted angle variance / distribution uncertainty，若头不原生输出则记
   not_emitted（不伪造）。

## 4. 预注册结局 A/B/C/D（训练后据此判定）
- **A**：仅 PSC 在 full-converged 设置下稳定 NRC>1 → phase-based angle coder intrinsic confidence reverse-ranks
  angle risk；机制线可升主文。
- **B**：多种 angle coders 均 NRC>1 → angle-coder native confidence generally unreliable for orientation
  selection；重写机制章为更广泛现象。
- **C**：PSC 反序随充分训练消失 → 原现象是 checkpoint/undertraining artifact；PSC 机制线降附录。
- **D**：regression/KLD 等无相位编码也反序 → 问题与 PSC 解耦，需重新定义机制，不得写 PSC-specific。

## 5. 与既有 R1 结果的关系
063/064 的 R1 结果（PSC 跨 2 数据集×3 seed NRC>1；DCL informative；CSL≈随机；direct_regression NaN、KLD
AMP 崩）**只作 preliminary / superseded-by-K2-design**，**不作 K2 full-converged 结论**——因 R1 强行共享同一
LR、未做 per-head LR sweep、direct_regression/KLD 的失败未排除超参/AMP 因素。K2 在 K4 后以修订设计重跑。

## 6. 禁止
不启动训练（本轮）；不把 R1 preliminary 当 K2 结论；不把 phase_mod 写成通用机制证明；不把 NRC<1 写 calibrated。
