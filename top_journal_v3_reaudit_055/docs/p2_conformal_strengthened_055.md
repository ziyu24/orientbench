# A1 —— P2 conformal risk control 强化 (055)

> 真实 052 matched tables；冻结 masked 协议 ar≥1.6；冻结 D_cal/D_audit（字段 d_cal_daudit_split_flag）。split-conformal / CRC：D_cal 标定阈值，D_audit 审计经验 coverage/risk/violation。未训练 detector、未改 threshold/split；selector 仅用 D_cal 特征。
> 数据：`reports/p2_alpha_scan_055.csv`、`p2_tail_conformal_055.csv`、`p2_conformal_score_menu_055.csv`、`p2_mondrian_ar_conformal_055.csv`、`p2_shift_audit_055.csv`。

## 0. B 的“空洞保证”质疑与回应
B 指出旧 P2 有空洞保证嫌疑。**确认部分成立**：若 alpha 设在 base risk 之上（如 mean≤15° 或 tail P(err>10°)≤0.10），masked 细长实例本就满足（base tail P(err>5°)≈0.07–0.14），保证在 coverage=1 时平凡成立、无需弃权 → 空洞。
**修复**：把保证设在 **operationally-strict 区（alpha < base rate）**，即“要求优于平均可靠性”，此时保证强制弃权，coverage–risk 出现真实权衡，且不同 score 显著分化。P2 由此从空洞变为有效贡献。

## 1. A1-1 base risk + mean-risk alpha 扫描（detection score）
base mean angle risk（D_audit，masked）：DIOR#22 1.74° / FAIR1M#24 2.49° / SODA#23 2.41° / DIOR#3 1.89° / DIOR#61 2.06° / SODA#4 2.65°。

在 alpha < base 时出现真实弃权（例）：
| cell | alpha=1.0° | alpha=1.5° | alpha=2.0° |
|---|---|---|---|
| DIOR#22 | cov 0.305（弃权 70%），risk 0.99 | cov 0.79 | cov ~1.0 |
| DIOR#3 | cov 0.229 | cov 0.69 | cov ~1.0 |
| SODA#4 | cov 0.018 | cov 0.067 | cov 0.24 |

→ 非空洞：越严的角度预算 → 越低 coverage、越强弃权。个别 cell 在 D_audit 上有轻微 mean-loss 溢出（如 DIOR#22 alpha=1.5 emp 1.589>1.5），因均值损失无界、finite-sample slack 未加，属诚实的近似保证（tail 版有 Hoeffding slack）。

## 2. A1-2 尾部 conformal（indicator loss，有限样本界干净）
控制 P(err>5°) ≤ alpha（bounded loss，适合 CRC + Hoeffding）。base tail P(err>5°)≈0.07–0.14。在 alpha<base 时强制弃权、guarantee 生效；Hoeffding 半径 sqrt(ln(1/0.1)/(2 n_cal)) 已并入阈值。n_cal 大（1.2万–16万）→ 半径 0.003–0.01，界紧。

## 3. A1-3 score menu（同一 conformal layer，套不同 score；strict P(err>5°)≤0.03）
**在固定保证下，coverage 越高的 score 越好。geometry-aware selector 在 6/6 cell 取得最高 coverage：**
| cell | detection | geometry | tta_circ_var | phase_mod |
|---|---|---|---|---|
| DIOR#22 | 0.327 | **0.472** | 0.001 | 0.000 |
| FAIR1M#24 | 0.015 | **0.164** | 0.000 | 0.001 |
| SODA#23 | 0.000 | **0.227** | 0.228 | 0.000 |
| DIOR#3 | 0.502 | **0.593** | 0.490 | — |
| DIOR#61 | 0.582 | **0.631** | 0.126 | — |
| SODA#4 | 0.032 | **0.202** | 0.137 | — |

- geometry selector 一致最优；TTA circular variance 不稳定（SODA 好，DIOR#22/FAIR1M/DIOR#61 崩）；**intrinsic phase_mod 作为 selector coverage≈0（因其反校准，A0）**。
- 这把 P4 融进 P2：**推荐默认 = conformal layer 套 geometry-aware selector**；TTA 作 GT-free 后备（不稳定）。
- 注：少数 cell geometry 在 D_audit 上 emp_tail 略超 0.03（如 FAIR1M 0.033），为有限样本近似；加大 slack 可换更保守 coverage。

## 4. A1-4 Mondrian（ar-bin 分层）+ 跨数据集 shift 审计
- 同分布（D_cal→D_audit）：全体阈值与分层阈值 coverage/violation 接近（base 已 masked，层内同质）。
- **跨数据集 shift**（源 cell → 不同 dataset 目标 cell，alpha=0.05）：全体阈值出现 violation（保证退化）；**ar 分层在 4 对中 3 对降低 violation**：
  | source→target | global tail | strat tail | strat 降 violation |
  |---|---|---|---|
  | DIOR#22→SODA#23 | 0.099(违) | 0.099 | 部分 |
  | DIOR#3→SODA#4 | 0.087(违) | 0.058 | 是 |
  | DIOR#22→FAIR1M#24 | 0.099(违) | 0.042(合规) | **是（修复）** |
  | SODA#4→DIOR#3 | 0.029(合规) | 0.034 | 否 |
- 结论：**无严格跨域 conformal guarantee**；shift 下如实报告退化；ar-Mondrian 缓解但不消除。诚实写为 limitation，不承诺 shift guarantee。

## 5. A1-5 有限样本界松紧
tail（bounded）CRC 的 Hoeffding 半径 = sqrt(ln(1/δ)/(2 n_cal))，δ=0.1。大 cell n_cal 1.2万–16万 → 半径 0.003–0.010（界紧）。**DOTA#20 n_cal 仅 206（且 subset 无效）→ 界极保守（半径≈0.067），保证近乎平凡**——正说明 DOTA#20 不能进主表（A0-2）。

## 6. P2 裁决
- **P2 从“空洞保证”变为有效贡献**：在 operationally-strict（优于平均可靠性）区，within-cell conformal 提供真实的 coverage–risk 弃权权衡与有限样本尾部保证；score menu 证明 conformal + geometry selector 是推荐默认。
- **边界**：均值版为近似保证（无界损失）；tail 版有干净 Hoeffding 界；跨数据集 shift 无严格保证（如实报告退化，Mondrian 部分缓解）。
- 这是全项目**最稳的正贡献**（脊柱），P1 是动机、cliff 是测量层、P4 已并入 score menu。
