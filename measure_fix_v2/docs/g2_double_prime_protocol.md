# G2_double_prime 协议（跑前冻结）

> SUPERVISOR_APPROVED_039_V2_MEASURE_FIX_G2_DOUBLE_PRIME · 本文件在运行实验前冻结，不得因结果修改。
> 依据 CLAUDE.md(v2) + 项目执行文件_v2_measure_fix.md §5。

## 0. 核心问题
> 在**固定 box-size 分箱内**，nonlinear geometry-aware selector 是否仍**显著优于 score-only 和 score + aspect-ratio + size 线性基线**？
排除致命替代解释：selector 是否只学到 box-size prior（小框更不可靠），而非 orientation-specific geometry。

## 1. 数据来源（只读引用现有 artifacts，不新训练）
- PSC cells（必含 FAIR1M/SODA）：DOTA PSC #20、DIOR PSC #22、FAIR1M PSC #24、SODA PSC #23。
- 非 PSC sanity：SODA ORCNN #4、DIOR ORCNN #3、DIOR LSKNet #10（至少一个非 PSC）。
- matched predictions 来源：/dev/shm scratch schema + persistent_artifacts（P1 产物，只读）。

## 2. D_cal / D_audit
- 用 P1 frozen `assign_split(image_id)`（确定性 md5，**不修改**）。
- selector **只在 D_cal 训练**；**最终判定只看 D_audit**；不得用 D_audit 调参。

## 3. well-defined orientation 区域
- **primary：ar ≥ 1.6**。sensitivity：ar ≥ 1.3、ar ≥ 2.0。
- near-square（ar<阈值）排除，不得当主贡献。阈值此处冻结。

## 4. 固定 box-size 分箱（冻结）
- 在 **D_cal** 上用 `log(sqrt(area))` 的三分位定义 **small / medium / large** 三箱；边界存盘，应用到 D_audit。
- within-bin 分析：在每个 size bin 内（size 近似恒定）比较 nonlinear vs score+ar+size linear；若增益只来自 size prior，则 within-bin 增益应消失。

## 5. selector 输入特征（冻结）
- **score-only**：[score]。
- **score+ar linear**：[score, log_ar]（LinearRegression）。
- **score+ar+size linear**：[score, log_ar, log_sqrt_area]（LinearRegression；class fixed-effect 作单独 sensitivity）。
- **nonlinear geometry-aware**：GradientBoosting([score, log_ar, log_sqrt_area, gv_obb_needed, w, h])；n_estimators=200, max_depth=3, lr=0.05, subsample=0.8, **random_state=0**。
- **主判定不使用 dataset id**；detector family 仅作分析变量。
- 模型由简到繁；不一上来用复杂模型制造虚假增益。permutation importance 输出。

## 6. 标签（冻结）
- 主：**continuous angle error**（canonical long-side，°）作 risk；selection score 降序排 NRC/AURC。
- sensitivity：**binary bad-angle = (angle error > τ), τ=5°（冻结）**。
- τ 跑前冻结，不换标签追结果。

## 7. 指标（D_audit）
- NRC-AUC、AURC、Risk@70、Risk@90、p90/p95/p99 after selection、bootstrap CI、**paired bootstrap**（resample D_audit，配对比较 nonlinear vs size-linear）、**fixed-size bin 内结果**、per-cell breakdown、ar sensitivity。
- pooled 仅辅助，不替代 within-dataset / within-size-bin 分析。

## 8. 判定规则
**pass 需同时满足**：① nonlinear 在 D_audit 显著优于 score+ar+size linear；② 增益在 well-defined 仍存在；③ ≥2 个 cell 方向一致；④ **fixed-size bin 内仍有显著/稳定增益**；⑤ 非仅 near-square 驱动。
**fail（任一）**：nonlinear 打不赢 size-linear / 增益仅 near-square / **fixed-size bin 内增益消失** / bootstrap CI 跨 0 或方向不稳 / 需改 thresholds·split / 主效果来自泄漏或 GT-derived feature。
**partial**：仅部分满足 → 记 partial，不进 CVPR/ICCV 线，可作实用 selector。

## 9. bootstrap 设置
- paired bootstrap 500×（若慢 500，记录原因）；报告 DELTA = NRC(size_linear) − NRC(nonlinear) 的 median + 95% CI；CI>0 视为支持。

## 10. 停止条件
- G2″ fail → 立即停手回报，P3 顶会线关闭，不启动 Deployable / Track A / detector 训练。
- 想改 frozen thresholds/split、重训 host、补 full matrix、恢复 P2 → 停手回报。
- inconclusive → 停手回报，只列最小补证。
