# Bench-Core v0.2 — Prediction Contract & angle_version Audit (dry-run)

> 生成时间: 2026-06-26 10:08:38 CST
> SYNTHETIC prediction（is_synthetic / not_detector_output）；未跑 detector；无 gate 结论。

## 1. Prediction Schema
- schema: dataset, split, image_id, detector_id, baseline_id, class_name, score, obb_cx, obb_cy, obb_w, obb_h, obb_theta, angle_unit, angle_version, source_path, is_synthetic, warnings
- mode=synthetic detector=synthetic_gv_proxy views=['original']
  - pred_dior_trainval.jsonl: n_preds=1019 valid=1019/1019
  - pred_dota10_train.jsonl: n_preds=2774 valid=2774/2774
  - pred_dota15_train.jsonl: n_preds=6727 valid=6727/6727
  - pred_fair1m_train.jsonl: n_preds=2874 valid=2874/2874
  - pred_hrsc_trainval.jsonl: n_preds=613 valid=613/613

## 2. Format Auto-Detection (supported)
- json / jsonl / csv 已实现；pickle_placeholder / mmrotate_placeholder 为占位（未实现解析）。
- 文件缺失 -> `no_prediction_available`，不阻塞，回退 synthetic fixture。

## 3. GT↔Prediction Matching Skeleton
| dataset/split | n_preds | matched | iou_method | approximate_iou | risk_mode |
|---|---|---|---|---|---|
| DIOR-R/trainval | 1019 | 978 | shapely_polygon | False | synthetic_prediction_angle_error |
| DOTA-v1.0/train | 2774 | 2174 | shapely_polygon | False | synthetic_prediction_angle_error |
| DOTA-v1.5/train | 6727 | 6140 | shapely_polygon | False | synthetic_prediction_angle_error |
| FAIR1M-v1.0/train | 2874 | 2753 | shapely_polygon | False | synthetic_prediction_angle_error |
| HRSC2016/trainval | 613 | 326 | shapely_polygon | False | synthetic_prediction_angle_error |
- 同图同类、score 降序、贪心匹配；IoU 阈值=0.5 placeholder（pending_threshold_freeze）。
- shapely 可用时 iou_method=shapely_polygon；否则 approx_aabb 并标 approximate_iou。

## 4. angle_version Audit
- baselines: 73；angle_version: {'le90': 73}；source: {'config_scan': 70, 'model_id_suffix': 3}
- HRSC mbox le90 等价 = **uncertain**；DOTA/DIOR/FAIR1M le90 = derived(minAreaRect)。
- 详见 angle_version_audit.md / .csv。不伪造确定性；无法确认 = unknown。

## 5. Synthetic Prediction Replacement Chain (03 -> 07 -> 11)
- 03_collect_predictions（synthetic）由 GT 生成 prediction → predictions/pred_*.jsonl。
- 07_eval_risk_coverage 匹配 pred↔GT，risk=角度误差(deg)，score=pred score → NRC（替换原 synthetic-risk demo）。
- 11_report_bench_core 汇总。全链路 dry-run，**不代表 detector 性能**。

## 6. Missing Dataset 裁示 (006)
- SODA-A / ICDAR-MLT：非阻塞，不下载/不改路径；保留 missing dataset risk；full coverage 需声明时再裁示。

## 7. 下一步 — 接真实 prediction
1. 真实 detector predictions 经 03 --pred-file 接入（json/jsonl/csv），validator 校验后替换 synthetic。
2. 接真实 prediction 若需启动 detector 推理 → 触发停手汇报条件（本轮不跑 detector）。
3. angle_version le90 符号一致性核验（尤其 HRSC）后再做 angle-error gate。
4. 阈值冻结(R8) → 正式 NRC/Risk gate。
