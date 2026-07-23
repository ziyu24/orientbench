# B 角色 200 条试标任务

本任务与 A 角色前 200 条使用完全相同的实例集合，但采用独立匿名 ID 和不同随机顺序。
页面不包含 A 的结果、GT 角度或模型预测信息。

启动：

```bash
bash top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_B_pilot_200.sh
```

完成 200 条后点击“导出 CSV + JSON”。B 的结果写入
`annotator_B/outputs_pilot_200/`，不会覆盖 1500 条正式任务目录。

随后运行：

```bash
bash scripts/run_m4_pilot200_analysis.sh
```

关键指标包括可用配对数、圆周角差的 mean/median/p90/p95、P(>5 deg)、
P(>10 deg)，并按数据集、类别、尺寸、长宽比分层及 ar>=2.1 子集报告。
