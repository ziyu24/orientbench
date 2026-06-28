# Training Need Scan 026

> 2026-06-28 12:26:11 CST

## 结论: **no_training_needed**

- 所有 remaining cells（Strip / ARS-DETR cross-dataset, HRSC detectors）在 pth_data 均有 valid matching checkpoint。
- 按规则「已有匹配 checkpoint 优先不用训练」→ 不启动训练，直接 inference。
- GPU 不空闲（连续 inference）。

| cell_group | datasets | checkpoint | training_needed |
|---|---|---|---|
| Strip cross-dataset | DIOR-R(47)/HRSC(37)/DOTA-v1.5(36) | exists | False |
| ARS-DETR cross-dataset | DIOR(16)/FAIR1M(18)/SODA(17)/HRSC(19) | exists | False |
| HRSC detectors | orcnn(6)/rtmdet(34,40)/strip(37)/arsdetr(19)/lsknet(13) | exists | False |
