# M4 独立双标说明

1. 标注者 A 仅使用 `annotatorA_tasks.csv`，标注者 B 仅使用 `annotatorB_tasks.csv`；两人不得查看对方任务顺序、标注值或导出文件。
2. 分别填写不同且稳定的 `annotator_id`。该值只用于独立性校验；合并表仅保存加盐 SHA-256。
3. 从本目录打开 `index.html`，载入自己的任务 CSV。若浏览器阻止相对图片访问，再选择本目录下的 `crops/` 文件夹。
4. 在无标记裁剪图上沿目标几何长边拖线，或手工输入 `[-90, 90)` 内的角度。不要使用语义航向。
5. 近方形、遮挡或目标不可辨认时选择“无法判定”，禁止猜测。
6. 可中途导出；未完成行保持空值。最终文件名必须分别为 `annotatorA_raw.csv` 与 `annotatorB_raw.csv`。
7. 任务不包含 GT 角、模型预测角、angle error、检测分数或预绘制方向线。如发现任何此类信息，停止标注并报告。

原始文件必须保留 `assignment_version`、`annotator_slot`、`task_order`、`anon_id`、图像定位字段及工具导出的时间戳，不得删除、增行或复制另一标注者的结果。
