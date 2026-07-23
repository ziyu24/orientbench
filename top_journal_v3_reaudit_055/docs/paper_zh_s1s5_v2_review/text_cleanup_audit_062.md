# R3 中文审稿版 v2 合规守护审计（062）

> 只做文字合规检查；不因半成品 R1 中间结果改主结论。审计对象：
> `orientation_reliability_paper_zh_s1s5_v2_review.md`（自 2026-07-03 未改动，早于 061/062）。

| 检查项 | 结论 | 证据 |
|---|---|---|
| 待补 = 0 | **PASS** | `grep 待补/TODO/TBD` 计数 = 0。 |
| 项目管理词 = 0 | **PASS** | 无 监督员/门控(PM)/命令编号/PASS-FAIL；"门控"为科学含义；claim ledger 仅附录 G。 |
| NRC<1 不写 calibrated | **PASS** | 行39 显式约定"NRC<1…不称已校准"；其余为禁止清单否定式。无正向 calibrated 断言。 |
| phase_mod 仍机制候选 | **PASS** | "机制候选" ×9；无"已被证明/机制证明"正向断言。 |
| DOTA#20 不进主结论 | **PASS** | "不进主证据" ×1；主风险-覆盖表不含 DOTA#20。 |
| 无 full complete / TPAMI/CVPR ready | **PASS** | 无正向就绪断言（会议/期刊名仅出现在参考文献引用）。 |

## 062 R1 结果不得写入主文
本轮 R1 训练矩阵结果：**PSC/CSL/DCL 18/18 健康完成；direct_regression（NaN 发散）与 KLD
（AMP/fp16 与 GDLoss linalg.inv 不兼容）各 6 run 全部 failed_training**。这些结果：
- **不满足预注册 A/B**（masked NRC 尚未评测，见 `r1_eval_spec_062.md`）→ 不入正文机制结论；
- 只能按命令六的允许句式记录事实（"PSC/CSL/DCL completed under the shared protocol；direct
  regression/KLD failed under the shared protocol；phase_mod remains a mechanism candidate"）；
- **禁止**写"PSC angle head proven broken / phase_mod mechanism proven / angle-coder confidence
  universally fails / full project complete / TPAMI-CVPR ready"。

## 结论
v2 审稿版 **6/6 合规通过**，本轮无需改主文；R1 062 结果暂不入正文。
