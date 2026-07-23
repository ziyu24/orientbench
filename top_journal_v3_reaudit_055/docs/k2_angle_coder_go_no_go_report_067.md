# K2 angle-coder go/no-go 报告（067）

- **判定：PASS**；对应结局：**A**。
- reversing heads（main derived-ar=2.1，全 seed 反序且 CI 下界>1）：['PSC']。
- 完整 3-seed 可比 block 数：6。failed_training heads：['KLD', 'direct_regression_le90']。
- 结论：only PSC reverses under full convergence -> phase-based angle coder intrinsic confidence reverse-ranks angle risk。

## block 结果（main derived-ar=2.1）
| head | dataset | n_seeds | native | mean AP50 | mean NRC_native | mean NRC_score | 全seed反序CI>1 |
|---|---|---|---|---|---|---|---|
| CSL | DIOR-R | 3 | softmax_margin | 0.3124 | 0.9749 | 0.9388 | False |
| CSL | SODA-A | 3 | softmax_margin | 0.3486 | 1.0222 | 1.0272 | False |
| DCL | DIOR-R | 3 | softmax_margin | 0.4298 | 0.2474 | 0.6657 | False |
| DCL | SODA-A | 3 | softmax_margin | 0.5469 | 0.3815 | 0.8515 | False |
| PSC | DIOR-R | 3 | phase_mod | 0.5375 | 1.2504 | 0.61 | True |
| PSC | SODA-A | 3 | phase_mod | 0.5865 | 1.1527 | 0.8048 | True |

## 约束
- failed_training 不支持机制正结论；direct_regression=负对照(无 native)、KLD=not_emitted 不计入 D。
- 不写 PSC angle head proven broken；phase_mod 仅按结局 A 写为 PSC-specific reverse-ranking，非通用机制证明。
- NRC<1 = informative/non-reversed（不写 calibrated）。旧 R1 为 preliminary，被本 K2 supersede。