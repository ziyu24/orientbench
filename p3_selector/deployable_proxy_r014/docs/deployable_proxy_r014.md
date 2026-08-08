# r014 跨数据集等变性选择器

## 结论

Core 判定为 `PASS_DEPLOYABLE_EQS_R014`：FAIR1M 完整来源修复后，六个 evaluation units 均支持 EQS 相对 score+AR+size linear 的 NRC 改善，三个数据集等权聚合也全部支持。目标域角标签只在模型和目标分数封存后用于一次性 D_audit。

独立 HRSC2016/LSKNet 确认为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`。点估计为正（Delta NRC=0.0602），但 95% image-cluster bootstrap CI 为 [-0.0143, 0.1438]，未达到预注册确认门。因此 Core 证据成立，跨 host 的 general-transfer 主张不成立。

## Core 结果

| evaluation unit | Delta NRC | 95% CI | support |
|---|---:|---:|---:|
| DIOR-R/22 | 0.1608 | [0.1261, 0.1958] | yes |
| DIOR-R/3 | 0.0925 | [0.0562, 0.1301] | yes |
| DIOR-R/61 | 0.2667 | [0.2343, 0.3030] | yes |
| FAIR1M-v1.0/24 | 0.2436 | [0.2043, 0.2845] | yes |
| SODA-A/23 | 0.2450 | [0.1657, 0.3168] | yes |
| SODA-A/4 | 0.0839 | [0.0371, 0.1448] | yes |

FAIR1M 的 frozen val universe 为 4,362 images / 78,644 GT；新 identity raw 含 488,194 predictions，AP50/AP75=0.34616/0.24224，满足权威端点 parity。SODA-A 的 22,994 tiles 全部映射到 576 个 mother scenes，主 bootstrap 以 mother scene 为单位。

## 证据边界

- 历史 r012 仍是 `FAIL_PROVENANCE_R012`，当时 EQS 未评价；r014 是新证据轮次。
- 既有 source-supervised geometry 的 leave-dataset 结果仍为 0/6，不被 r014 覆盖。
- HRSC 只作外部确认，不回流 Core gate。
- 本轮没有训练 detector、修改阈值或修改 D_cal/D_audit。
