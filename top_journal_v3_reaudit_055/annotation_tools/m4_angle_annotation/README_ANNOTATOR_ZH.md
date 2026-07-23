# M4 人工双标说明

## 标注目标

标注 OBB 的**几何长边朝向**，角度标准化到 `[0°, 180°)`。只考虑 180° 周期，不判断物体头尾或语义航向。

## 操作

1. 在图像上沿目标长边方向拖动鼠标，黄色线仅表示你当前输入的方向，数值显示在图像下方。
2. 使用“上一个/下一个”切换；切换和输入后会自动保存，也可点击“保存”。断开后用相同启动命令恢复。
3. near-square 目标若仍能可靠判断几何长边则标注；无法可靠区分两轴时选 `ambiguous`。
4. 遮挡或截断目标：只在可见证据足以判断长边时标注；方向存在但证据不足时选 `ambiguous`。
5. 图像损坏、目标不可见或无法确认被标实例时选 `skip`。
6. 不得参考其他标注者、GT、模型预测框、phase_mod 或 reliability score。青色中心圆仅用于指出目标中心，不编码方向。
7. 完成后点击“导出 CSV + JSON”。已有导出文件不会被覆盖。

## 输出位置

- A：`annotator_A/outputs/annotations_A.csv` 和 `annotations_A.json`
- B：`annotator_B/outputs/annotations_B.csv` 和 `annotations_B.json`

两名标注者必须独立工作，不得互看结果。

## 全量剩余任务

200 对 pilot 通过后，只标尚未完成的任务：

```bash
bash top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_A_remaining.sh
bash top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_B_remaining.sh
```

A 页面显示 1305 条，B 页面显示 1123 条。此前有效真人结果已经冻结并从页面隐藏，
不会要求重复标注。两人完成并导出后运行：

```bash
bash scripts/run_m4_full_human_analysis.sh
```

## 当前 600 目标补量与单方未标重检

当前阶段使用：

```bash
bash top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_A.sh
bash top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_B.sh
```

A 页面共 86 条，B 页面共 91 条。每人均包含相同的 74 个新目标，使三个数据集
各达到 200 个双标目标；此外，A 重检 12 条、B 重检 17 条此前“一方有角度、另一方
ambiguous/skip”的实例。页面不会显示任务类型或对方结果。原始标注保持不变，重检
仅作次级分析。
