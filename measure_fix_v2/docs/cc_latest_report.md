👇👇👇👇👇👇

# OrientBench v2 — 044 P3 Method Package + TTA Coverage 完成

- **044 完成**。原始 dataset 未修改；未改 thresholds(b7c4e649)/P1 split；未训练 detector；未补 full matrix；未恢复 P2；未追 DOTA mAP。
- **主报告（唯一人读）**：`measure_fix_v2/docs/p3_method_package_report.md`

## real TTA coverage 补强结果
- 复用 043 shadow farms（未改 dataset）跑 SODA #23 + FAIR1M #24 real hflip+vflip。real TTA Route-C **均 beat size-linear 且 beat geometry-only**（SODA NRC 0.378、FAIR1M 0.499，tta_match 0.99）。
- **real TTA 现覆盖 4 cells / 3 datasets**（DIOR ORCNN#3+PSC#22、SODA PSC#23、FAIR1M PSC#24）。非 PSC + 更多 dataset = next-step。

## P3 selector method spec 是否完成
- **完成**：p3_selector_method_spec.md（problem/features/Track A-B-C/deployable Route-C/training/leave-*/real TTA/inference/risk-coverage/why-not-calibration/why-not-size-prior/limitations）。+ paper outline + claim ledger + 7 fig/table + captions + 持久化检查（21 artifacts，all sha256）。

## Track A 机制结论口径
- intrinsic angle-coder miscalibration **mechanism candidate（supported by phase_mod evidence）**；非唯一决定性证据、非门控 P3、非最终定论。

## 是否允许进入方法写作
- **允许**（method spec + 图表 + claim ledger + outline 就绪；核心结论均有可复算 artifacts）。

## 验证/test/git
- verifier `verify_p3_method_package_044` → 见下；pytest 全过；原 dataset 0 改动；thresholds/split 未变；git 0 大文件。

## 下一步最小行动
- 补非 PSC real TTA（复用 farm）；写方法正文 §3-§7；扩 Track A negative control。**不声称 P3 最终完成 / 顶会 ready**。

👆👆👆👆👆👆
