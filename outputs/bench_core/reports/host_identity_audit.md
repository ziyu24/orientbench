# Host Identity Audit (RHINO / A4) — 012 task 4

> 生成时间: 2026-06-26 09:58:49 CST
> 仅本机已有官方代码核验；不伪装 ARS-DETR/其它 DETR 为 RHINO；两 host 相互独立 (R3/R6)。

## C1/B host = RHINO (rotated DETR) — IDENTIFIED
- 路径: `third_party/ai4rs/projects/RHINO/`
- 来源: **RHINO**, "Hausdorff Distance Matching with Adaptive Query Denoising for Rotated Detection Transformer" (WACV 2025)；官方 repo https://github.com/SIAnalytics/RHINO ；ArXiv 2305.07598。
- 架构: rotated DETR + RHINOPositiveHungarianClassificationHead + Hausdorff/GD 匹配代价 + adaptive query denoising；backbone R50/Swin-T；4-scale deformable；max_epochs=36 AdamW lr=1e-4。
- 配置: rhino_phc_haus_4scale_r50_2xb4_36e_dota.py（继承 rotated_dino dota base）、dotav15/dotav2、r50/swint。
- angle: rotated DETR le90（与项目 le90 一致；canonical contract 适用）。
- 官方 checkpoint: modelscope 提供 dotav2/v15 (rhino-4scale_r50_2xb2-36e_dotav2_240423.pth 等)。**DOTA-v1.0 无官方 ckpt → 需训练**。
- **判定: 真正的 RHINO-style rotated DETR，符合 R6 C1/B host。非 ARS-DETR 替代。**

## A4 host = rotated_rtdetr / O2-RTDETR (hybrid-encoder oriented DETR) — IDENTIFIED
- 路径: `third_party/ai4rs/projects/rotated_rtdetr/`
- 来源: RT-DETR (CVPR2024, "DETRs Beat YOLOs", ArXiv 2304.08069) 的 **oriented** 变体 O2-RTDETR；**hybrid encoder**（rtdetr_layers.py HybridEncoder：intra-scale + cross-scale 解耦）+ rotated head。
- 配置: o2_rtdetr_r50vd_2xb4_72e_dior.py、o2_rtdetr_r18vd_4xb1_72e_dotav15.py、dronevehicle 等；backbone R18/R34/R50vd。
- **判定: hybrid-encoder oriented DETR，符合项目 A4 host 定义；架构独立于 RHINO（RT-DETR hybrid encoder vs RHINO deformable-DETR）→ 满足 R3「A4 不得用 RHINO/便利快照替代」。**
- 普通 rtdetr（`projects/rtdetr/`）为 COCO 水平框，非 A4（A4 须 oriented）→ 已排除。

## 独立性 / R3 / R6 核对
| 项 | C1/B | A4 |
|---|---|---|
| 模型 | RHINO (rotated DETR, Hausdorff matching) | O2-RTDETR (hybrid-encoder oriented DETR) |
| encoder | deformable DETR encoder | hybrid encoder (RT-DETR) |
| 独立 frozen snapshot | 是（不同架构/权重） | 是 |
| 结论 | 符合 R6 C1/B | 符合 R6 A4，独立于 RHINO (R3) |

## checkpoint / 训练状态
- 无 DOTA-v1.0 官方 RHINO/A4 ckpt（modelscope 为 dotav2/v15/dior/COCO）→ 项目 DOTA-v1.0 scope 需训练。
- 训练框架: ai4rs tools/train.py（mmengine 新式 config，mmrotate 1.x 系，mr_dev1x 可用）。
- 隔离: 训练在 ai4rs repo 运行，输出写 orientbench/outputs/training/{rhino,a4_host}/，不覆盖 third_party、不改 pth_data。

## 下一步
RHINO/A4 DOTA-v1.0 训练（36e/72e DETR，~1+ GPU-day each）：pre-flight 短程验证后启动完整 schedule（后台长任务）。
