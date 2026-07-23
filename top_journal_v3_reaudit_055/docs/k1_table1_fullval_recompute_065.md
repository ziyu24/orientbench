# K1 表 1 full-val 重算（065，进行中）

**背景（比 partial-GT 更深的发现）**：表 1 冻结的持久化预测（`orientbench_v2/.../pred_*_fullval.jsonl`）
的图像集与 full-val test **零重叠**（预测覆盖 5863 张、图像号在 trainval 段如 07919；full test 为 11738
张、号段如 20604）。即旧预测既是 **partial GT** 又落在 **错误/部分图像集**，且 DIOR#61、SODA#4 的预测
在 /dev/shm 已丢失。→ **表 1 必须用冻结 baseline 权重在正确 full-val split 上重新推理后重算**（非训练）。

**方法**：`scripts/recompute_table1_by_inference_065.py`。每单元用 pth_data 冻结 config+checkpoint，在正确
full-val split 上推理，用数据加载器的 gt_instances（精确约定）+ K1 验证过的 torch VOC-AP（==DOTAMetric 差
≤0.0014）算 AP50/AP75，并施加与 s1a 相同的约束角度扰动（仅扰动 TP@0.5，eps_max 保 rIoU>0.5）。DIOR 单元
数据 repoint 到持久化 data_prep（annfiles_dotaformat/test + 图像符号链接）。

**状态（本轮进行中）**：5 单元后台重算（`logs/k1_table1_fullval_recompute_065.log`）。FAIR1M#24 排除
（数据 blocker）。已确立：**DIOR#22 full-val AP@0.5 ≈ 0.53**（K1：DOTAMetric 0.531 / S1a 0.5297 / VOC-AP
0.5311；baseline 自报 0.537），**取代旧 0.6964**。其余单元结果落 `reports/k1_table1/*.json`、
`reports/table1_fullval_final_065.csv`。

**判定**：评测器 PASS；**表 1 尚未 PASS**（需六单元全部 full-val 重算完成；当前 1/6 确立、4 重算中、
1 数据 blocker）。ΔAP@0.5 结论只能在各单元 full-val 重算后如实报告。
