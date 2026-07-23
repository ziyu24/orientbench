# S2 —— PSC 机制免费测试 (v1)

> 冻结 masked ar≥1.6，真实 phase_mod。DOTA#20 排除（invalid）。数据：`reports/pre_submission_s1s5_v1/s2_phase_mod_aliasing_masked_v1.csv`、`s2_phase_mod_confounding_masked_v1.csv`。phase_mod 仅 **mechanism candidate**。

## 测试一：Aliasing fingerprint
取 phase_mod 高分位（top 25%，高内在置信度）样本，看角度误差分布是否集中在编码频率相关角度。
- 结果：高置信样本中位角度误差 **高于**低置信样本（DIOR#22 1.56 vs 1.08；FAIR1M#24 2.06 vs 1.94；SODA#23 1.96 vs 1.88）——重申 reverse ordering，但**误差在各角度 bin 上分散，无特征频率峰**。
- 判定：**无 aliasing 特征峰 → 不得写 aliasing 机制解释。**

## 测试二：Class / size / ar confounding check
在 masked 区内按 class / size 三分 / ar 三分分层，看 phase_mod NRC>1 是否被类别或尺寸驱动。
- 结果：phase_mod NRC>1 在分层中普遍持续（DIOR#22 9/9、FAIR1M#24 9/9、SODA#23 8/9 层 NRC>1）。
- 判定：**反校准未被 class/size/ar 中介 → confounding 基本排除，支持机制候选。**

## 综合裁决
- 两测试：Test 2 支持（非 confound），Test 1 不支持（无 aliasing 峰）。**仅 1/2 支持。**
- 因此 **phase_mod 保持 case study / mechanism candidate；本轮不设计、不启动 PSC/CSL/DCL/regression 重训矩阵**。
- DOTA#20：invalid_pending，仅作 artifact limitation，不作负对照或验证点。
- 正确机制叙述：PSC 角度编码器内在置信度对朝向误差反序（非 confound 驱动），但无 aliasing 频率指纹 → 机制**候选**，未定论。
