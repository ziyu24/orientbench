# M2：ar≥2.1 固定 size-bin 下的 G2_double_prime

- 主口径 ar≥2.1；size bins 为冻结的既有 small/medium/large（在查看 D_audit 前已定义）。
- ar≥2.1 是 matched-GT 的朝向可辨识性评估掩码；固定 size-bin 与 selector 的 ar/size/w/h 特征全部由预测框计算，不把 GT 几何作为 selector 输入。
- 比较 detection / score+log(ar) linear / score+log(ar)+log(size) linear / nonlinear geometry；线性与非线性同拆分、同 D_cal-fit 拟合目标（目标域 GT 角度误差 → calibration/upper-bound），D_audit 评估。
- 通过依据是配对 NRC 差（linear score+ar+size 减 nonlinear）图像级 bootstrap CI 下界>0，不采用 feature importance。
- 支持 cells（≥2 size-bin 显著）：['A', 'B', 'C', 'E']；显著 bin 数 11/15。
- **M2 判定：PASS** — fixed-size-bin 内 nonlinear geometry 稳定优于 score+ar+size linear，>=2 cells 且非单一 size-bin 驱动

## cell × size-bin 结果（ar≥2.1）
| cell | size-bin | n | det NRC | +ar linear | +ar+size linear | nonlinear | (lin−nl) diff [CI] | nl 更优? |
|---|---|---|---|---|---|---|---|---|
| A | small | 15234 | 0.7027 | 0.7065 | 0.7065 | 0.705 | 0.002 [-0.0205,0.0248] | False |
| A | medium | 7589 | 0.5838 | 0.8799 | 0.7384 | 0.5991 | 0.1388 [0.0943,0.1805] | True |
| A | large | 2242 | 0.5897 | 0.6479 | 0.6233 | 0.4719 | 0.151 [0.1034,0.1983] | True |
| B | small | 17081 | 0.6538 | 0.7077 | 0.6742 | 0.6324 | 0.0419 [0.0085,0.078] | True |
| B | medium | 8030 | 0.6608 | 0.9785 | 0.8372 | 0.6172 | 0.2206 [0.1777,0.2617] | True |
| B | large | 2560 | 0.5388 | 0.7021 | 0.6627 | 0.4777 | 0.185 [0.1389,0.2295] | True |
| C | small | 16836 | 0.5621 | 0.5796 | 0.5797 | 0.5413 | 0.0386 [0.0222,0.0553] | True |
| C | medium | 7859 | 0.5578 | 0.8305 | 0.7261 | 0.5603 | 0.1642 [0.1312,0.1977] | True |
| C | large | 2690 | 0.4236 | 0.4562 | 0.4367 | 0.3587 | 0.0781 [0.0464,0.107] | True |
| D | small | 13765 | 0.9661 | 0.7735 | 0.7735 | 0.7368 | 0.0364 [0.0,0.0784] | False |
| D | medium | 1136 | 0.9573 | 0.6655 | 0.6594 | 0.7107 | -0.0513 [-0.1216,0.0254] | False |
| E | small | 99811 | 0.7848 | 0.5991 | 0.5802 | 0.54 | 0.0404 [0.027,0.0538] | True |
| E | medium | 1291 | 1.357 | 0.4422 | 0.4384 | 0.3845 | 0.0538 [0.0177,0.0923] | True |
| F | small | 119367 | 0.6858 | 0.5877 | 0.5577 | 0.543 | 0.0146 [0.0048,0.0256] | True |
| F | medium | 1558 | 0.9495 | 0.4129 | 0.4171 | 0.44 | -0.0232 [-0.0789,0.0198] | False |