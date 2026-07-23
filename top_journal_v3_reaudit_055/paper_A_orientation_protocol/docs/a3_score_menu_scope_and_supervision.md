# A3 Score Menu 的监督范围与同层认证

| score | 训练/监督 | 目标推理可得 | 定位 |
|---|---|---:|---|
| detection score | 无额外 GT 拟合 | 是 | deployable baseline |
| TTA circular consistency | theta→2theta 圆方差，无目标 GT | 是 | deployable, inference-costly |
| source-supervised leave-* geometry | 其他数据集 D_fit 的 GT angle error | 是 | source-supervised transfer；不称 fully GT-free training |
| target-GT nonlinear geometry | 目标 D_fit 的 GT angle error | 是 | diagnostic/calibration upper bound；不可部署 |

四项使用同一 eligible universe、风险事件、冻结 split、coverage grid、固定序列、UCB 和 cluster 定义。NRC 不替代本认证层；`D_audit` 不参与 threshold 或 score direction 选择。

严格主事件的 nontrivial certification 计数为：{"detection_score": 0, "source_supervised_leave_geometry": 0, "target_gt_nonlinear_geometry_upper_bound": 1, "tta_circular_consistency": 0}。形式认证、非平凡认证和 practical success 在结果表中分列。**A3 判定：PARTIAL_SCORE_MENU。**
