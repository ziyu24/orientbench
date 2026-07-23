# R1 数据入口解阻（preflight）

> 数据：`reports/r1_dataset_preflight_060.csv`；日志：`logs/r1_angle_coder/dataset_preflight_060.log`。未改 D_cal/D_audit 切分规则，只修训练入口与格式适配。

## DIOR-R：XML → DOTA-txt 转换（已完成）
- 原生标注为 OBB XML（`DIOR/annfiles/obb/*.xml`，robndbox 四角点）。config 需要 `annfiles_dotaformat/{trainval,test}/` 的 DOTA-txt。
- 新增转换脚本：`scripts/convert_dior_obbxml_to_dota_txt.py`（40 进程并行）。
- 输出（orientbench 自有 prep 目录，**不污染共享数据集**）：`top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/{trainval,test}/`；图像以符号链接 `dotaformat_images/{trainval,test}` 指向 `DIOR/images/{trainval,test}`（不复制）。
- 配置副本 `configs/r1_angle_coder/psc_dior_seed0.py` 的 data_root 已 repoint 到 prep 目录。

### sanity check
| split | ids | ann written | objects | empty ann | missing xml | images |
|---|---|---|---|---|---|---|
| trainval | 11725 | 11725 | 68073 | 0 | 0 | 11725 |
| test | 11738 | 11738 | 124445 | 0 | 0 | 11738 |
- 类别映射：20 DIOR 类全部命中；box 坐标合法（poly8）；ann/image 计数一致；config 引用路径一致（mmengine 载入通过，train ann 11725 files）。

## SODA-A：已是 DOTA 格式（无需转换）
- `SODA-A/dota_format_tiled_ss/{train_tiled,val_tiled}/annfiles/*.txt`（DOTA-txt，tiled）+ 对应 images 已就绪。
- 只需 SODA PSC/角度头 config 指向该目录即可训练（config 待 061 从 baseline 派生）。

## 结论
- **DIOR-R、SODA-A 训练数据入口均已打通**（DIOR 转换完成并校验；SODA 原生 DOTA 格式可用）。
- 059 的数据阻断（annfiles_dotaformat 缺失）**已解除**。
