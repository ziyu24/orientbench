# Host Decision Packet (RHINO / A4)

> 生成时间: 2026-06-26 09:11:25 CST
> 供合作者裁示；不替代 RHINO；不把 ARS-DETR 当 RHINO；不启动训练/推理。

## 1. RHINO-style rotated DETR — MISSING
- 现状: `pth_data/readme.md` 73 baselines 中无 RHINO-style rotated DETR（C1/B host, R6）。
- ARS-DETR (#14–19,44,72) 只能作为 DETR-like baseline，**不可替代 RHINO**（R6 冻结对象不同）。
- C1/B 若要启动，需合作者裁示其一: **下载** RHINO 权重 / **训练** RHINO / **补充**到 pth_data / **批准**明确替代方案。
- 裁示前: B-MVE-0/1 不启动。

## 2. A4 hybrid-encoder oriented DETR host — PENDING
- 现状: A4 source-attribution host (frozen hybrid-encoder oriented DETR) frozen snapshot 未提供 (R3/R6)。
- A-gate-1 必须在该 frozen host 上跑，**不得用 RHINO 或 convenience snapshot 替代** (R3)。
- 需合作者提供 frozen snapshot 路径或裁示获取方式。

## 3. 训练前对齐方案（host 选定后仍需）
- config / log / schedule / lr / batch / SyncBN 必须对齐官方或 valid baseline；
- 4×A30 默认，爆显存回退并留痕；
- 只保存最高 mAP + 最近 epoch；每 epoch 评估；
- 首 epoch 明显偏低必须停并汇报；
- 自建 baseline 放 `orientbench/pth_data`，以 `baseline_` 前缀，维护 readme。

## 4. 需要合作者裁示的事项
1. RHINO host 处置（下载/训练/补充/批准替代）。
2. A4 frozen host 提供方式。
3. 是否授权将某 coco/pseudo-label prediction 转换后用于 ingestion（非正式 gate）。
4. 阈值冻结责任角色与数值（见 threshold_freeze_proposal）。
