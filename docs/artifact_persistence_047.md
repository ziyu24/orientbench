# Artifact Persistence (047)

> 2026-06-30 17:40:18 CST。关闭 /dev/shm-only 硬伤：主表/主图/TTA/Route-C/Track A 必需 raw/matched predictions 已持久化到 **/home**（persistent，gitignored）。

- persistent dir：（1361.6 MB，43 artifacts）。
- manifest：（path/sha256/schema/generation_command/can_recompute/source_checkpoint/split）。
- all_have_sha256=True；all_can_recompute=True；original_dataset_modified=False。
- 大文件**不进 git**（outputs/persistent_artifacts/ gitignored）。
- ⚠️ /dev/shm 副本非持久；/home 副本持久；二者 sha256 一致，可复算。
- 覆盖：feature tables（11 cells，selectors/主表）、real TTA preds（TTA/Route-C）、Track A dumps（phase_mod）。
- blocked_storage：无（/home 75G free，足够；未触发 blocked_storage_with_size_estimate）。
