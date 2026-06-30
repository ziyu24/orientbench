# Figure / Table Captions (044)

> 2026-06-30 10:40:23 CST。每项：caption draft / data path / main takeaway / cannot claim。

## Fig 1 — G2'' size control
- caption：Within fixed box-size bins (D_cal tertiles of log√area), nonlinear geometry-aware selector vs score+ar+size linear (ΔNRC, D_audit). data: fig_g2doubleprime_size_control.csv。
- takeaway：所有 size-bin×cell ΔNRC CI>0 → 增益非 box-size prior。
- cannot claim：非 deployable final method；用 source GT 训练。

## Fig 2 — Deployable leave-dataset/detector
- caption：Deployed selector NRC on unseen dataset/detector (no target GT), vs score-only/size-linear/oracle. data: fig_deployable_leave_dataset_detector.csv。
- takeaway：非 DOTA unseen cells 多数优于 size-linear，retain ~65% oracle gain。
- cannot claim：DOTA #20 例外；非 full deployability。

## Fig 3 — Route-C offline proxy vs real TTA
- caption：Route-C selector NRC (offline consistency proxy 041 vs real TTA 042/044). data: fig_route_c_real_tta.csv。
- takeaway：real TTA 与 offline proxy 方向一致，beats size-linear。
- cannot claim：coverage limited；consistency 增益部分 cell 边际。

## Fig 4 — Track A PSC mechanism
- caption：Track A intrinsic phase_mod vs Track B score vs Track C geometry NRC (3 PSC cells, D_audit). data: fig_track_a_psc_mechanism.csv。
- takeaway：phase_mod NRC>1 sig (3/3) → intrinsic angle-coder miscalibration candidate。
- cannot claim：phase_mod 为一 intrinsic 信号；非最终定论。

## Table 1 — Main results
- data: table_main_results_measure_fix.csv。takeaway：G2''/Deployable/Route-C/Track A 汇总。cannot claim：P3 final / top venue。

## Table 2 — Ablation Tracks A/B/C
- data: table_ablation_tracks_abc.csv。takeaway：Track C geometry 最佳，Track A 反校准。

## Table 3 — Limitations & blockers
- data: table_limitations_and_blockers.csv。
