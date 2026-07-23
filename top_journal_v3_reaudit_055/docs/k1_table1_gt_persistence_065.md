# K1 表 1 full-val GT 持久化（065）

持久化目录（非 /dev/shm）：`outputs/persistent_artifacts/k1_table1_fullval_065/gt/`；清单：
`reports/k1_table1_gt_manifest_065.csv`；构建：`scripts/build_k1_fullval_gt_065.py`（DOTA-txt poly8
→ mmrotate qbox2rbox le90，与评测器同一角度约定）。

| dataset/split | n_images | n_gt | classes | 状态 |
|---|---|---|---|---|
| DIOR-R test | 11738 | **124445** | 20 | 已确认 full-val（旧 partial=35436，约 28%）|
| SODA-A val_tiled | 22994 | **449644** | 9 | full（与旧 449644 一致，SODA GT 未 partial）|
| FAIR1M-v1.0 val | — | — | — | **BLOCKER**：数据集 split_ss_fair1m1.0 缺失，GT 不可构建（旧 78638 无法核验）|

要点：DIOR GT 曾为 partial（35436），是表 1 DIOR 单元 AP 抬高的根因之一；SODA GT 本为 full。
所有 GT 已带 sha256、n_gt、生成命令、can_recompute，复算链已加“DIOR n_gt=124445 + 禁止 /dev/shm 主表 GT”检查。
