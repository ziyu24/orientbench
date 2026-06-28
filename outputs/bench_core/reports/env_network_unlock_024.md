# Env & Network Unlock 024

> 2026-06-28 10:58:48 CST
> network 已用（下载尝试）；**未创建新 env**（full-val 复用 mr_dev1x 足够）；**未装新依赖**；未破坏已有 env。

## ARS-DETR
- independent_archetype=**true**；not_RHINO_replacement=**true**。status=**needs_env**。
- unlock: 隔离创建 mmrotate 0.1.0 env（third_party/ARS-DETR + old mmcv-full/torch）；构建风险高，本轮未建以免破坏 env；路径已记录。

## point2rbox_v2
- **weak_nonformal**。status=**needs_download**。
- ted.pth URL=https://www.modelscope.cn/models/wokaikaixinxin/mmrotate/resolve/master/Point2Rbox_v2/ted.pth；raw curl 返回 JSON（需 modelscope SDK/auth 取二进制）；下载未完成；下载后 patch clone 跳过网络初始化，仍 nonformal。

## LSKNet/Strip cross-dataset
- status=**needs_adapter**（ckpt head 已匹配数据集 num_classes；需 class-map adapter，不假改 head；本轮未跑）。
