# DOTA-v1.0 PARTIAL Formal Audit

> split: **D_audit** (从未参与校准)；frozen DOTA D2 阈值；canonical long-side orientation risk；near-square masked.
> **范围仅限 DOTA-v1.0 partial（baselines #1/#20/#32）；非全数据集、非完整 9-detector 结论。**

- frozen thresholds: NRC_AUC<=1.0 pass; Spearman(mAP,NRC)<=0.95; data_fp=b49a350d5600b720
- per-detector gate PASS: **3/3**

| baseline | archetype | mAP | matched_used | masked_nearsq | med_err° | Risk@70 | Risk@90 | AURC | NRC | GATE |
|---|---|---|---|---|---|---|---|---|---|---|
| #1 oriented_rcnn_r50 | two_stage_regression | 0.7144 | 9292 | 130 | 1.571 | 1.9454 | 2.1339 | 1.734 | 0.6717 | **PASS**|
| #20 rotated_retinanet_psc_r50 | angle_coder_psc | 0.5815 | 7044 | 157 | 1.526 | 2.1046 | 2.1524 | 1.8269 | 0.7401 | **PASS**|
| #32 rotated_rtmdet_s | one_stage_realtime | 0.7023 | 9316 | 121 | 1.599 | 1.9367 | 2.1228 | 1.7036 | 0.6172 | **PASS**|

## D2 independence (stop condition)
- Spearman(mAP rank, NRC rank) over 3 detectors = **-0.5** (threshold 0.95) -> **OK**
- 注意：n=3 检测器，Spearman 仅 3 点，独立性结论为 partial（需更多 detector 才稳健）。

## Gate 判定说明
- PASS = 该 detector 的 selection score 对 orientation risk 的排序优于 random（NRC<=1.0）。
- FAIL 保留，不调阈值补救（如 PSC NRC>1 表示其 score 非好的朝向置信代理——真实诊断，非 bug）。
- orientation error 经 long-side canonical 归一化 + near-square 屏蔽；median ~1.6°。

## Known limitations
- DOTA-v1.0 partial（3 detector，600-img val 子集的 D_audit 296 图）；非全 val、非 9-detector。
- rtmdet mAP 用 readme baseline 值（本轮 DumpDetResults 未算 mAP）。
- B_C1/A_A4 gate 未冻结（待 RHINO/A4 host）。HRSC angle 未解（不影响 DOTA）。
