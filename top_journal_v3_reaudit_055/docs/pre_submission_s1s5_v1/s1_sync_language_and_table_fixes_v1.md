# S1 —— 同步语言与表格修正 (v1)

## 1. 打分菜单“6/6”更正
旧稿“geometry 6/6 最高覆盖”**作废**。独立性修复后（S1b）：
- SODA#23 在旧口径 TTA 0.228 > geometry 0.227（统计打平），且独立训练下 geometry 优势非普遍。
- 正确表述：**geometry selector 在 detection 弱信息 cell 显著更优，在 detection 已强 cell 打平或略差；非普遍最优、非 recommended default（收缩为“弱信息 cell 的安全默认”）。**

## 2. P1/P2 样本口径标注
所有表必须标注：
- **P1（S1a）使用 unmasked / mixed 样本**（full evaluator over 全 val；约束扰动施于 TP@0.5）。
- **P2 / NRC / conformal（S1b/S1c/S3）使用 masked ar≥1.6 样本**。
否则表间 baseline 角度误差对不上（unmasked 均值含近方形 ~40°+，masked 均值 ~1.7–2.7°）。

## 3. cliff 分位在冻结 masked 管线重列
cliff 分位数须用当前冻结 masked 管线重列，不沿用被 supersede 的旧数字。冻结 masked（ar≥1.6）下角度误差分位：p90≈4–6°、p99≈8–12°（细长良态）；near-square（ar→1）分位跳升至 ~88–90°（病态）。（依 S1a dose-response 与 masked 统计；正式表在复算脚本产出。）

## 4. DIOR#10 / SODA#11 位置
无 full-val 17字段匹配表（仅 features_v2 masked），**移入附录**（S3），不进主结果表。

## 5. “先前文献报告的反校准” → “本项目早期分析报告的反校准”
unmasked NRC>1 反校准是 **本项目早期分析** 的口径漂移所致（pooling artifact），非“先前文献”结论。全文据此更正措辞。

## 6. NRC<1 措辞统一（不叫 calibrated）
NRC<1 一律改为 **better-than-random risk ranking / non-reversed ranking / informative ranking**。`calibration / calibrated` 仅用于概率校准或 conformal 语境。NRC>1 = **reverse ranking**（反序）。示意：NRC=0 oracle / NRC=1 random / NRC>1 reverse。
