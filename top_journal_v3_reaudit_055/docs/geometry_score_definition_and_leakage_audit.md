# 几何感知打分：定义与泄漏审计（066）

> 依据实现 `top_journal_v3_reaudit_055/scripts/a4_p4_uncertainty_055.py`（+ 保形独立性 `s1c_ltt_conformal_v1.py`）。
> 数据：`reports/geometry_score_feature_leakage_audit_066.csv`。**几何感知打分只作诊断性/几何启发候选，
> 非通用默认。**

## 定义
- **输入特征清单（3 个，全部预测端可得、GT-free）**：`detection_score`、`log(aspect_ratio)`、
  `log(sqrt(size))`（后二者来自预测框 w/h 与面积）。
- **模型形式**：`GradientBoostingRegressor(n_estimators=200, max_depth=3, lr=0.05, subsample=0.8)`
  预测**角度误差**；打分 = `-预测角度误差`（预测误差越小→打分越高）。
- **拟合数据/标签**：在标定子集上以 **GT 角度误差**为回归目标拟合（`g.fit(X[cal], angle_error[cal])`）。
- **拟合子集与独立性**：selector-fit 与 conformal-calib 互斥——保形层（`s1c`）把冻结 D_cal 再分为
  `D_fit`（拟合选择器）与 `D_calib`（保形标定），`D_audit` 独立仅报告。masked ar≥1.6。
- **评估口径**：masked ar≥1.6 的 NRC/风险-覆盖；与线性打分共用**同一特征集**做公平对照。

## 泄漏审计
| 特征/项 | 预测端可得 | 依赖 GT | 依赖目标域 | 角色 |
|---|---|---|---|---|
| detection_score | 是 | 否 | 否（输入）| 特征 |
| log(aspect_ratio) | 是 | 否 | 否（输入）| 特征 |
| log(sqrt(size)) | 是 | 否 | 否（输入）| 特征 |
| **[拟合目标] angle_error** | **否** | **是** | **是（D_cal GT）** | **回归目标** |

**关键泄漏结论**：三个**特征**均无 GT/目标域泄漏（预测端可得）；但**模型以目标域 GT 角度误差为拟合目标**
（`fit(X, angle_error)`）。因此几何感知打分**当前实现为 calibration / upper-bound setting，不是 deployable**。

## 边界写法（强制）
- 主结果中的几何感知打分须标为 **calibration / upper-bound**（因拟合用目标域 GT 角度误差）。
- 只有在**源域监督 + 目标域无 GT**（leave-dataset 重拟合）的变体下，才可讨论 deployable；该 deployable
  变体须单独报告，不得把 upper-bound 结果写成 deployable。
- 几何感知打分**非通用默认**：仅在"检测置信度对朝向弱信息"场景带来增益，强信息场景与检测打分打平/略差。
- selector-fit（D_fit）与 conformal-calib（D_calib）**独立**，D_audit 仅报告。
