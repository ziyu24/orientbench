# PSC Phase 1 拆篇门控报告

- 时间冻结：`2026-07-12 20:14:39 -0700` 至 `2026-08-23 20:14:39 -0700`。
- radial branch：**B**。
- 条件1 可干预结构性原因：True（`stable_six_cell_radial_decoder_sensitivity_including_modulation_threshold_or_wrapping`）。
- 条件2 非平凡预注册新分数：True。
- 条件3 两数据集冻结可用单元稳定优于 negative phase_mod：True。
- 条件4 不重训且 box/class/AP 不变：True。
- **拆篇裁决：PASS**。

所有正式比较（含冻结 K2 DCL/CSL native endpoint）使用 `ar>=2.1` 与 `angle_error > delta_theta_0.75(aspect_ratio)`；NRC/AURC/Risk@70/Risk@90 的区间按图像簇 bootstrap。DCL/CSL 与自身 detection score 配对，但不代替 PSC 新机制分数相对 negative phase_mod 的拆篇条件。
本次可配对 PSC score rows：38。
若 FAIL：不拆篇；有效机制证据并回主论文机制小节，停止 B 线继续搜索。
