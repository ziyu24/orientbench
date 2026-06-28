# Unlock Remaining Detectors 025

> 2026-06-28 12:04:12 CST
> 大胆执行：能建 env/下载/写 adapter/跑 full-val 就做；失败记录继续。

## ARS-DETR — UNLOCKED ✅
- 创建隔离 conda env **arsdetr**（python3.8, torch 1.9.0+cu111, torchvision 0.10.0, mmcv-full 1.5.0, mmdet 2.25.1, mmrotate 0.1.0 fork, e2cnn）。
- config build + #14 ckpt load: **missing=0 unexpected=0**。
- DOTA-v1.0 4-GPU inference 跑通（result_b14.pkl 6.2MB）；exploratory NRC 1.20 med_err 1.73°。
- **independent_archetype=true, not_RHINO_replacement=true**（绝不替代 RHINO/host 55a90abb）。

## LSKNet cross-dataset — UNLOCKED ✅
- num_classes + img_suffix adapter（ai4rs config + cfg-options，ckpt head 匹配，**不假改 head**）。
- DIOR-R #10 / FAIR1M #12 / SODA-A #11 full-val 4-GPU 跑通；NRC 0.53 / 0.83 / 0.76。

## point2rbox — BLOCKED ⛔
- modelscope ted.pth：服务器返回「文件内容为空」(Code 10990101007)；SDK repo 404；raw resolve 返回 JSON。**upstream 文件不可用**（非 auth）。标 blocked_download_source_empty。weak_nonformal，不影响 formal gate。

## psc/rtmdet full-val — DONE ✅
- DIOR psc#22/rtmdet#61, FAIR1M psc#24, SODA psc#23 全 full-val 4-GPU。
