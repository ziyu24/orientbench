# 长任务监督

SERVER 为每个长 GPU/CPU run 创建独立子目录与 `SUPERVISION.yaml`。监督记录必须绑定
活动派发的 plan path、SHA256、epoch 与 run ID；索引和状态摘要不能替代派发授权。
