# 线性打分：定义（066）

> 与几何感知打分做**公平对照**的线性基线。数据：`reports/linear_score_definition_audit_066.csv`。
> **不得把线性打分写成 calibrated。**

## 三档线性打分（+ 几何非线性对照）
| 变体 | 形式 | 拟合权重 | 拟合标签 | 用 GT | 设定 |
|---|---|---|---|---|---|
| score-only | s = detection_score | 否 | 无 | 否 | **deployable 基线** |
| score+ar linear | s = w0 + w1·score + w2·log(ar) | 是（LinearRegression）| 目标域 GT 角度误差（D_cal）| **是** | calibration/upper-bound |
| score+ar+size linear | s = w0 + w1·score + w2·log(ar) + w3·log(√size) | 是（LinearRegression）| 目标域 GT 角度误差（D_cal）| **是** | calibration/upper-bound |
| 几何(GBR，非线性对照) | s = −GBR([score, log ar, log √size]) | 是（GradientBoosting）| 目标域 GT 角度误差（D_cal）| **是** | calibration/upper-bound；同一特征集 |

## 说明
- **是否标准化**：特征用 log 变换（log ar、log √size），未额外 z-score；score 原尺度。公平对照下线性与几何
  用**同一特征集**（score、log ar、log √size），差别仅在模型族（线性 vs GBR 非线性）。
- **是否拟合权重**：score-only 无拟合；score+ar、score+ar+size 与几何均在 D_cal 上拟合。
- **拟合数据**：冻结 D_cal（保形场景再分 D_fit/D_calib，见几何打分文档）。
- **是否用 GT label**：score+ar、score+ar+size、几何均以**目标域 GT 角度误差**为拟合目标 → 均为
  calibration/upper-bound；只有 score-only 是无拟合、deployable 基线。
- **class fixed effect / 目标域**：当前线性/几何均**未**加 class fixed effect；特征仅框几何+score，不含
  目标域标注型特征（但拟合目标是目标域 GT）。
- **公平对照关系**：几何(GBR) vs 三档线性共用同一特征集 X=[score, log ar, log √size]，故"几何是否胜出"是
  **模型族**（非线性 vs 线性）之差，而非特征信息之差——G2_double_prime 的核心对照。
- **写法**：线性/几何打分**不得写成 calibrated**；NRC<1 只写 informative/non-reversed。凡拟合用 GT 的变体
  一律 upper-bound，不写 deployable。
