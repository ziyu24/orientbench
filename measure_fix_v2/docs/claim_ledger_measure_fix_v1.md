# Claim Ledger — Measure / Fix (v1)

> 2026-06-30 10:38:46 CST

## allowed claims
- G2_double_prime **passed**（固定 size-bin 内 nonlinear 显著优于 score+ar+size linear；orientation-specific 非线性几何，非 box-size prior）。
- Deployable hardening **stable-pass on tested cells**（非 DOTA 多数 unseen cell 优于 score+ar+size linear，无目标 GT，retained ~0.65-0.72）。
- Route-C **real TTA supported on tested cells**（DIOR + SODA/FAIR1M PSC real hflip/vflip；shadow farm 未改 dataset）。
- Track A **supports PSC intrinsic miscalibration candidate**（phase_mod NRC>1 显著，3/3 PSC cells）。
- NRC 与 mAP 未检出显著相关（within-dataset）；aspect-ratio reliability cliff 真实。

## qualified claims
- real TTA coverage **limited**（部分 cells；其它 next-step）。
- Track A phase_mod 是**一个** intrinsic 信号（角度码模长）；机制为 **candidate**。
- P3 method development **can continue**；当前 selector 为 reliability-aware **candidate**，训练用 source GT（calibration/upper-bound），target 无 GT（deployable 方向）。
- Track C = 最佳可用 selector，但 upper-bound（非 deployable method 完成态）。

## forbidden claims
- ❌ P3 final method complete。
- ❌ top venue ready。
- ❌ full project complete。
- ❌ C1 genuine multi-view solved。
- ❌ A4 cross-host causal proved。
- ❌ PSC angle head definitively broken（仅 candidate / supported by phase_mod evidence）。
- ❌ Track A 为唯一决定性证据。
- ❌ Track C upper-bound 为 deployable method。

## pending claims
- real TTA full coverage（all PSC + non-PSC cells across datasets）。
- DOTA #20 Track A negative control（未跑，不调参）。
- 更多 intrinsic 信号（decoded-angle 熵）佐证 Track A。
- controlled angle-head 实验（需新批准）确证机制。
