# M3：图像级有限样本风险保证

- 正式 exchangeable unit 是完整 evaluation-image universe；没有 eligible/retained prediction 的图像也以 L_I=0 进入统计。
- eligible instance 是与 GT 同类、旋转 IoU>=0.5 的一对一匹配预测；未匹配预测没有可定义的 GT angle error，不进入分子或实例分母，但其图像仍留在完整图像总体中。
- D_cal-fit 只定义候选阈值；独立 D_cal-calib 只做 Hoeffding-Bentkus fixed-sequence LTT；D_audit 只报告，不参与阈值、认证或总判定。
- 冻结 JSON 中大写 `CALIBRATION split` 按其 `splits` 条款解释为外层 D_cal；外层再确定性拆成上述 fit/calib，避免候选阈值与 LTT 标定复用同一图像。
- 正式 primary 是 detection_score × geometry-normalized severe event。主 bounded loss 不使用 exact binomial。
- ar>=2.1 掩码与 delta_theta_0.75(ar) 的 ar 均来自 matched GT box；选择打分特征来自预测端。
- geometry_score_upper_bound 使用目标域 GT error 拟合；M2 已通过，但 Deployable 门控未建立，故只列附录、不参与 primary 判定。
- 冻结 score menu 的 phase_mod、negative_phase_mod 与 TTA circular variance 使用同一图像级 HB-LTT；它们不改变 detection_score primary 判定。
- secondary Z_I 使用 exact Clopper-Pearson；实例风险仅为 empirical instance-weighted risk with image-cluster bootstrap CI。
- 冻结协议 SHA-256：`d88e0d4f3866ced04efc6e06dfb10ea55502bf409d827cb8b2eb7d048492a8e5`；协议文件未修改。
- **M3 判定：PASS**。

## Primary selected thresholds
| cell | alpha | target coverage | calibration HB UCB | audit mean image risk | audit nonempty images | audit instance coverage |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.03 | 1.0 | 0.0153817 | 0.012077 | 0.592203 | 1 |
| A | 0.05 | 1.0 | 0.0153817 | 0.012077 | 0.592203 | 1 |
| A | 0.1 | 1.0 | 0.0153817 | 0.012077 | 0.592203 | 1 |
| B | 0.03 | 1.0 | 0.0161449 | 0.0132485 | 0.616949 | 0.999928 |
| B | 0.05 | 1.0 | 0.0161449 | 0.0132485 | 0.616949 | 0.999928 |
| B | 0.1 | 1.0 | 0.0161449 | 0.0132485 | 0.616949 | 0.999928 |
| C | 0.03 | 1.0 | 0.0258754 | 0.0215337 | 0.625424 | 0.999927 |
| C | 0.05 | 1.0 | 0.0258754 | 0.0215337 | 0.625424 | 0.999927 |
| C | 0.1 | 1.0 | 0.0258754 | 0.0215337 | 0.625424 | 0.999927 |
| D | 0.03 | 1.0 | 0.00536176 | 0.00349409 | 0.570028 | 1 |
| D | 0.05 | 1.0 | 0.00536176 | 0.00349409 | 0.570028 | 1 |
| D | 0.1 | 1.0 | 0.00536176 | 0.00349409 | 0.570028 | 1 |
| E | 0.03 | 1.0 | 0.00307779 | 0.00163027 | 0.353758 | 0.99999 |
| E | 0.05 | 1.0 | 0.00307779 | 0.00163027 | 0.353758 | 0.99999 |
| E | 0.1 | 1.0 | 0.00307779 | 0.00163027 | 0.353758 | 0.99999 |
| F | 0.03 | 1.0 | 0.00300844 | 0.00223282 | 0.357577 | 0.999983 |
| F | 0.05 | 1.0 | 0.00300844 | 0.00223282 | 0.357577 | 0.999983 |
| F | 0.1 | 1.0 | 0.00300844 | 0.00223282 | 0.357577 | 0.999983 |

## Appendix-only geometry score
| cell | alpha | target coverage | calibration HB UCB |
|---|---:|---:|---:|
| A | 0.03 | 1.0 | 0.0153817 |
| A | 0.05 | 1.0 | 0.0153817 |
| A | 0.1 | 1.0 | 0.0153817 |
| B | 0.03 | 1.0 | 0.0161449 |
| B | 0.05 | 1.0 | 0.0161449 |
| B | 0.1 | 1.0 | 0.0161449 |
| C | 0.03 | 1.0 | 0.0258754 |
| C | 0.05 | 1.0 | 0.0258754 |
| C | 0.1 | 1.0 | 0.0258754 |
| D | 0.03 | 1.0 | 0.00536176 |
| D | 0.05 | 1.0 | 0.00536176 |
| D | 0.1 | 1.0 | 0.00536176 |
| E | 0.03 | 1.0 | 0.00307779 |
| E | 0.05 | 1.0 | 0.00307779 |
| E | 0.1 | 1.0 | 0.00307779 |
| F | 0.03 | 1.0 | 0.00300844 |
| F | 0.05 | 1.0 | 0.00300844 |
| F | 0.1 | 1.0 | 0.00300844 |

## Preregistered native/GT-free score menu
| cell | score | alpha | target coverage | calibration HB UCB |
|---|---|---:|---:|---:|
| A | tta_neg_circular_var | 0.03 | 1.0 | 0.0153817 |
| A | tta_neg_circular_var | 0.05 | 1.0 | 0.0153817 |
| A | tta_neg_circular_var | 0.1 | 1.0 | 0.0153817 |
| A | phase_mod | 0.03 | 1.0 | 0.0153817 |
| A | phase_mod | 0.05 | 1.0 | 0.0153817 |
| A | phase_mod | 0.1 | 1.0 | 0.0153817 |
| A | negative_phase_mod | 0.03 | 1.0 | 0.0153817 |
| A | negative_phase_mod | 0.05 | 1.0 | 0.0153817 |
| A | negative_phase_mod | 0.1 | 1.0 | 0.0153817 |
| B | tta_neg_circular_var | 0.03 | 1.0 | 0.0157636 |
| B | tta_neg_circular_var | 0.05 | 1.0 | 0.0157636 |
| B | tta_neg_circular_var | 0.1 | 1.0 | 0.0157636 |
| C | tta_neg_circular_var | 0.03 | 1.0 | 0.0262444 |
| C | tta_neg_circular_var | 0.05 | 1.0 | 0.0262444 |
| C | tta_neg_circular_var | 0.1 | 1.0 | 0.0262444 |
| D | tta_neg_circular_var | 0.03 | 1.0 | 0.00527888 |
| D | tta_neg_circular_var | 0.05 | 1.0 | 0.00527888 |
| D | tta_neg_circular_var | 0.1 | 1.0 | 0.00527888 |
| D | phase_mod | 0.03 | 1.0 | 0.00536176 |
| D | phase_mod | 0.05 | 1.0 | 0.00536176 |
| D | phase_mod | 0.1 | 1.0 | 0.00536176 |
| D | negative_phase_mod | 0.03 | 1.0 | 0.00536176 |
| D | negative_phase_mod | 0.05 | 1.0 | 0.00536176 |
| D | negative_phase_mod | 0.1 | 1.0 | 0.00536176 |
| E | tta_neg_circular_var | 0.03 | 1.0 | 0.00307779 |
| E | tta_neg_circular_var | 0.05 | 1.0 | 0.00307779 |
| E | tta_neg_circular_var | 0.1 | 1.0 | 0.00307779 |
| E | phase_mod | 0.03 | 1.0 | 0.00307779 |
| E | phase_mod | 0.05 | 1.0 | 0.00307779 |
| E | phase_mod | 0.1 | 1.0 | 0.00307779 |
| E | negative_phase_mod | 0.03 | 1.0 | 0.00307779 |
| E | negative_phase_mod | 0.05 | 1.0 | 0.00307779 |
| E | negative_phase_mod | 0.1 | 1.0 | 0.00307779 |
| F | tta_neg_circular_var | 0.03 | 1.0 | 0.00285424 |
| F | tta_neg_circular_var | 0.05 | 1.0 | 0.00285424 |
| F | tta_neg_circular_var | 0.1 | 1.0 | 0.00285424 |



<!-- HUMAN_073_START -->
## 人工噪声与风险预算解释

真人双标均值分歧为 2.3112°，其 95% 区间为 1.9970°–2.7854°。因此 1.5°–2° 的均值风险预算接近人工分歧地板，只能解释为 label-noise-aware mean risk，不能写成强语义精度保证。5° 事件仍有 8.00% 的人工分歧越界，属于 noise-sensitive fine-risk；10° 事件的人工越界率为 0.89%，具有更清楚的 severe-risk 解释。正式保证仍以完整图像为可交换单位、以 geometry-normalized severe event 为主风险；人工分歧不进入阈值选择，也不从模型风险中扣除。
<!-- HUMAN_073_END -->

