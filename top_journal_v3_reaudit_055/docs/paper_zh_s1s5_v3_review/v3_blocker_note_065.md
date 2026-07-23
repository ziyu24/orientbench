# v3 生成阻断说明（065）

**v3 中文论文本轮不定稿。** 原因：表 1（P1 扰动）绝对 AP 锚点尚未解冻——K1 判定其 FAIL-as-published
（DIOR 单元用了 partial GT n_gt=35436，且持久化预测落在错误/部分图像集，与 full-val test 图像零重叠），
六单元 full-val 重算仍在后台进行（`recompute_table1_by_inference_065.py`）。

- 现有 v3 草稿仍含旧的表 1 数值（含 0.6964 一类 partial-GT artifact），**不得作为定稿**。
- 只有六单元 full-val 重算完成、表 1 用重算结果替换、旧值进入 superseded 表后，才允许生成/定稿 v3。
- 已确认的替换：DIOR#22 表 1 AP@0.5 由 0.6964 → 约 0.53（K1 full-val：DOTAMetric 0.531 / S1a 0.5297 /
  项目 VOC-AP 0.5311；冻结 baseline 自报 0.537）。其余 5 单元重算进行中（FAIR1M 因数据集
  split_ss_fair1m1.0 缺失为数据 blocker）。

## 更新（解除）
表 1 六单元 full-val 重算已全部完成（6/6），表 1 已用 full-val 值替换（旧 0.69/0.80/0.89 → 0.5368/0.6448/0.6462；SODA/FAIR1M 本为 full GT 几乎不变）。v3 §4 表 1 + 摘要/正文角度量级已更新；全文 forbidden/venue/PM/K1 token 复核 grep=0。**v3 阻断解除**。
