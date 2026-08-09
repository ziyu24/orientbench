# r019 协议闭合

## 范围

本轮在标签前封存修正型 EQS-RC-R019，并在 DOTA-v1.0 的 Oriented R-CNN 与 Rotated RTMDet-M 两个 evaluation units 上执行一次前瞻端点验证。

## 阶段映射

|阶段|状态|证据|
|---|---|---|
|无标签预检、实现微测、50-image smoke|完成|prelabel inventories|
|Core source-only LODO、功效与唯一模型拟合|完成|source LODO/model inventory|
|DOTA 三视图 5297-tile 前向、feature、score、draw seal|完成|prediction/feature/score/draw inventories|
|prelabel Git 时间锁|完成|runtime post-commit receipt|
|首次标签附着、official AP parity、同步 mother bootstrap|完成|results and runtime postlabel|
|独立重算与负例|完成|validator_r019.json|

## 边界

DOTA 是一个外部数据集上的两个 detector-family evaluation units；不能解释为两个独立数据集，也不能解释为 unseen-family transfer。r014 HRSC 与 r015 Core 结果未进入本轮 gate。
