# GPU-Busy Replicate Training 027

> 2026-06-28 13:30:52 CST

## GPU job 启动（10 分钟内）
- replicate training: oriented_rcnn DOTA-v1.0（官方 #1 config，data_root 路径修正，**不调参**）。
- 4-GPU world_size=4，util 45-100%，eta ~1.6h，workdir=scratch。**status=running**。
- 标注: trained_by_027_replicate=true, not_original_readme_checkpoint=true, not_formal_gate=true, exploratory_or_fallback=true。

## 关键运行期发现
- bare `run_in_background` torchrun 命令 GPU 正常启动（util 高）；之前 nohup-bash-wrapper 启动 stall（worker 不上 GPU, util 0%）。
- **结论**: 026/027 早期 Strip/ARS-DETR cross-dataset blocked_runtime 主因 = **nohup-wrapper 启动方式**，非模型/数据。下一轮用 bare 命令重试 cross-dataset Strip/ARS-DETR 应可跑通。

## 并行策略
- 训练占用 4 卡；inference 并发会与训练争显存（baseline ~4GB/卡 + 训练）。本轮训练优先占满，cross-dataset 重试留待训练后或显存允许时 bare-command 并发。

---
## replicate training COMPLETED (2026-06-28 15:31:29 CST)
- 12-epoch (1x) 完成；best **dota/mAP 0.7015** @epoch12（原 baseline #1 = 0.7061，delta 0.0046，**忠实复现**）。
- best=best_dota_mAP_epoch_12.pth(sha a237ed41a9599a4f), latest=epoch_12.pth(sha 0008c83d4b207ef3)，均在 scratch。
- trained_by_027_replicate, exploratory/fallback, **NOT formal / NOT readme-checkpoint substitute**。usable_for_inference=true。
