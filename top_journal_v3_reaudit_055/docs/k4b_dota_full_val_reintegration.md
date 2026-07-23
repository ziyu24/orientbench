# K4b DOTA 完整 full-val 回归（066）

> 补 DOTA-v1.0 provenance-clean full-val 单元，**两个检测族**，不用 19 图 D20。数据
> `reports/k4b_dota_full_val_metrics.csv`、`reports/k4b_dota_cell_inclusion_exclusion_066.csv`；
> 日志 `logs/k4b_dota_full_val_reintegration_066.log`。冻结 checkpoint 重新 full-val 推理（**不训练**），
> K1 验证过的评测器（torch VOC-AP == DOTAMetric）。

## 数据与口径
- GT 源：`/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/val`（**持久化，非 /dev/shm**），
  5297 tiles / **n_gt=55804**，DOTA-txt。masked ar≥1.6（K4a derived-ar=2.1 为推荐主口径，此处先报 1.6）。
- 不追公开 test mAP；不用 D20。

## 结果（两 clean full-val 单元）
| 单元 | 检测器 | AP50 | AP75 | n_gt | masked n | masked NRC(score) | AURC | Risk@70 | masked 角误差° | checkpoint 自评 |
|---|---|---|---|---|---|---|---|---|---|---|
| DOTA(ORCNN) | Oriented R-CNN | **0.7061** | 0.4517 | 55804 | 39566 | **0.6912** | — | 1.753 | — | 0.7061 ✓ |
| DOTA(RTMDet) | Rotated RTMDet-m | **0.7161** | 0.4868 | 55804 | 41650 | **0.6458** | — | 1.717 | — | 0.7161 ✓ |

- 两单元 AP50 **与 baseline 自评 DOTAMetric 精确一致**（0.7061 / 0.7161）→ provenance-clean、评测器对齐。
- masked ar≥1.6 检测置信度 NRC **0.65–0.69（<1，informative / non-reversed）**——DOTA 上检测打分对朝向误差
  提供优于随机的排序（与其它数据集一致）。

## D20 处置
- **DOTA#20（19 图 D_cal 子集）正式排除**：mAP 异常、/dev/shm、非 full-val。主文彻底移除，仅在排除附录一句话
  说明（见 `k4b_dota_cell_inclusion_exclusion_066.csv`）。不进任何主结论。

## K4 初步判定
- masked 阈值有几何原则（K4a：derived-ar=2.1，1.6/1.3 sensitivity）；DOTA 有 **≥2 个 clean full-val 单元**
  （ORCNN + RTMDet，AP50 与自评一致）→ **K4 初步 PASS**。
- conformal tail / score menu on DOTA：可后续补（本轮已给 detection-score ranking quality = masked NRC/Risk）。
