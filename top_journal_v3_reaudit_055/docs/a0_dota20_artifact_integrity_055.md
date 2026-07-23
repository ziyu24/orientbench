# A0-2 —— DOTA #20 artifact 完整性核验 (055)

> 数据：`reports/a0_dota20_integrity_055.csv`。源：052 matched_17field + full_matched_tables_052 + psc_phase_mod_permatched_full_052。只读，未重跑 detector。

## 现象（B 指出）
DOTA #20 mAP@0.5 = 0.0132、2428 preds、486 matched，疑似 dump 断裂。

## 核验结果
- `matched_17field_full_052` 的 GT 源 = `outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl`，即 **仅 19 张图的 D_cal subset**，不是 full val。
- n_matched=486，覆盖 18 图；D_audit 280 / D_cal 206；match_iou 中位 0.744（匹配本身正常）。
- 486 实例 **全部 ar≥1.6，near_square_n=0** —— 与 full-val cell 的 ar 分布（含大量 near-square/moderate）完全不同，进一步说明它是被裁剪过的偏样本。
- 同一 checkpoint 存在 **另一份更完整的 DOTA#20 dump**：`psc_phase_mod_permatched_full_052.csv` 有 **17960 行**（vs 486）。两份 DOTA#20 artifact 的 scope 严重不一致。
- mAP@0.5=0.0132：在 19-图 subset GT 上评估 2428 preds，scope 不匹配 → 该 mAP 无意义，不能解释为“检测器崩溃”。

## 裁决
- **DOTA #20 的 P1 主表结果（486 matched / mAP 0.0132）= invalid_pending**，移入脚注，不进主表、不作为 P3 negative control 结论。
- 更完整的 17960-行 phase_mod dump 可作为 Track A 机制的一个 **数据点**（masked ar≥1.6, n=16873, phase_mod NRC=0.964[0.929,0.998]），但因 scope 与其它 cell 不一致，仅供参考，**不作为 headline**。
- 是否值得从 checkpoint 重跑一份 full-val DOTA#20（对齐其它 cell 的 scope）= 建议项，非本轮 A0 结论的必要条件；A0 的核心裁决（detection-score 反校准是 pooling artifact；phase_mod 反校准幸存）在 3 个 full-val PSC cell（DIOR#22/FAIR1M#24/SODA#23）上已充分成立，不依赖 DOTA#20。

## 是否 Codex 执行错误
是（部分）：Codex 在 052/053 把一份 19-图 subset dump 当作 DOTA#20 的 full 结果混入 P1 主表并计算 mAP，属 artifact scope 错误。本轮标 invalid_pending 更正。
