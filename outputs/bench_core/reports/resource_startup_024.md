# Resource Startup 024

> 2026-06-28 10:10:07 CST

- SCRATCH=/dev/shm/cqc/orientbench (exists=True)
- /dev/shm: total 252.5GB free **170.9GB** (ample)
- GPU: 4xA30 24GB idle ~4GB baseline; leftover procs: 0; network: openmmlab+github reachable (200)
- conda envs: ['ai4rs_train', 'geostructdota', 'mr', 'mr_dev1x', 'p2_foundation']
- storage policy: large files -> SCRATCH; project keeps manifest/sha256/metrics/summaries
- 不清理磁盘/不删文件；scratch 充足(160GB)，无 blocked_scratch_space。
