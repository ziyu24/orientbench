# Final Limitations

> 2026-06-28 22:14:10 CST

- formal gates 仅限 frozen DOTA scope（D2/host/C1/A4）；非 DOTA 全 exploratory，未冻结阈值。
- C1 cross-view = augmentation-view（旋转+真实推理），非 genuine 多物理视角。
- A4 = same-host 统计 source-attribution，非跨 host 因果。
- cross-dataset 部分 detector cell blocked（ARS-DETR class-mapping FAIR1M/SODA；Strip 仅 DIOR；HRSC 多 detector pattern 未跑）。
- point2rbox weak_nonformal 且上游 artifact 不可用。
- SODA-A/ICDAR-MLT/HRSC angle 等历史不确定项已在各轮记录；HRSC angle 现 resolved_with_evidence。
- 大文件全部在 scratch (/dev/shm)，非持久；复现需重跑 inference（见 reproducibility guide）。

- NRC construct validity（v2，23 cells）：NRC 与 mAP 基本独立（Spearman -0.05），非 accuracy 换皮；详见 docs/scientific_validity_audit.md。
- 'formal gate=NRC≤1' 为早期误述，已更正：formal gate 认证协议/阈值/split/metric，不要求每 detector NRC≤1。
