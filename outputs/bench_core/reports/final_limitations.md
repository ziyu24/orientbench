# Final Limitations

> 2026-06-28 22:14:10 CST

- formal gates 仅限 frozen DOTA scope（D2/host/C1/A4）；非 DOTA 全 exploratory，未冻结阈值。
- C1 cross-view = augmentation-view（旋转+真实推理），非 genuine 多物理视角。
- A4 = same-host 统计 source-attribution，非跨 host 因果。
- cross-dataset 部分 detector cell blocked（ARS-DETR class-mapping FAIR1M/SODA；Strip 仅 DIOR；HRSC 多 detector pattern 未跑）。
- point2rbox weak_nonformal 且上游 artifact 不可用。
- SODA-A/ICDAR-MLT/HRSC angle 等历史不确定项已在各轮记录；HRSC angle 现 resolved_with_evidence。
- 大文件全部在 scratch (/dev/shm)，非持久；复现需重跑 inference（见 reproducibility guide）。
