# ARS-DETR Env 025

> 2026-06-28 12:04:12 CST

- env=**arsdetr** (isolated)；torch 1.9.0+cu111 / mmcv-full 1.5.0 / mmdet 2.25.1 / mmrotate 0.1.0 fork / e2cnn。
- build cmds: ['conda create -n arsdetr python=3.8', 'pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111', 'pip install mmcv-full==1.5.0 (cu111/torch1.9 wheel)', 'pip install mmdet==2.25.1', 'pip install -e third_party/ARS-DETR --no-deps', 'pip install e2cnn']
- ckpt load missing=0；DOTA-v1.0 4-GPU inference OK。**independent_archetype=true, not_RHINO_replacement=true**。base env 未动。
