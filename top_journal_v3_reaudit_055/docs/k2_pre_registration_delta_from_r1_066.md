# K2 预注册相对 R1(063/064) 的修订（066）

| 项 | R1(063/064) | K2 修订 |
|---|---|---|
| LR | 所有 head 强行共享 lr=0.005 | 各 head 预注册 3-LR sweep {0.0025,0.005,0.010}，**等 tuning budget**，按 val mAP 选 |
| AMP | 全 AMP，KLD 因半精度 linalg.inv 崩 | 允许 **FP32 fallback**（AMP 不稳时），须记录 |
| 收敛门控 | epoch-1 NaN 门控 | + **可用收敛门控**（AP50/AP75 未塌陷才比较 uncertainty）|
| 失败归因 | direct_regression NaN / KLD AMP 崩 直接 failed | 须先排除超参/AMP（LR sweep+FP32）后仍崩，才记**方法性** failed |
| masked 口径 | ar≥1.6 | K4a derived-ar=2.1 主口径，1.6/1.3 sensitivity |
| 结局 | A/B/C（3 档）| **A/B/C/D（4 档，加 D=非相位编码也反序→机制解耦）** |
| R1 结果地位 | 当时结论 | **preliminary / superseded-by-K2-design**，不作 full-converged 结论 |

**要点**：R1 的 PSC 反序、DCL informative、CSL 随机、direct_regression NaN、KLD AMP 崩，均因 R1 共享单 LR +
全 AMP + 未 per-head 调参而**不能作机制正结论**；K2 以修订设计（per-head LR sweep 等预算 + FP32 fallback +
可用收敛门控 + A/B/C/D）在 K4 后重跑判定。本轮**不训练**。
