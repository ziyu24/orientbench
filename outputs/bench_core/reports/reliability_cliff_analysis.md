# Reliability Cliff 分析（near-square → 主分析）

> 2026-06-29 13:19:53 CST。near-square 不再当噪声排除，而是核心退化分析（出路 A）。

## 结论：reliability cliff **成立** —— orientation reliability 随 aspect-ratio→1 断崖
- p99 angle error 随 aspect ratio：ar 3.0+ ~5-7° → ar 2.0-3.0 ~8-10° → ar 1.6-2.0 ~11-45° → **ar<1.3 ~84-90°**。
- NRC：well-defined region(ar 2-3) ~0.47-0.49（selection 有效）；near-square region NRC→0.93-0.97（selection 在歧义区无效，符合预期）。
- masked NRC（去近方形）= well-defined orientation region 的 summary；主文须报告该曲线，不把近方形简单当排除噪声。

## 含义（P1/P3 核心动机）
- 可靠性诊断必须 **aspect-ratio / degeneracy aware**；天真全量 angle error 被方形歧义主导。
- selection/reliability 在 well-defined region 仍有提升空间（NRC~0.47-0.5，非 0），且 PSC 在该区反校准（见下）。
- 曲线成立 → 这是 P1/P3 的核心动机图（reliability_cliff/cliff_p99_nrc_vs_aspect_ratio.png）。
- 数据：reliability_cliff_curve.csv（per detector × aspect-ratio bin：NRC/median/p90/p99）。
