# Orientation Reliability Toolbox

Python 3.10；依赖 `numpy scipy shapely`。工具箱实现 le90 canonical angle error、`delta_tau(ar)`、geometry-normalized event、NRC/AURC/risk-coverage、固定角 sensitivity、eligible/nonempty scene risk、scene event、cluster bootstrap、HB/Clopper-Pearson UCB、固定序列 alpha frontier 和 score-menu 认证。

CLI：

```bash
PYTHONPATH=. python -m orientation_reliability.cli examples/synthetic.csv --ap75 0.50
```

输入 CSV 至少含 `score,risk,severe,scene_id`。输出固定包含 AP75、detection-score NRC 和 scene-risk frontier；无工作点时显式返回 `INFEASIBLE`。默认 score menu 不包含 target-GT geometry，也不含 PSC 机制代码。
