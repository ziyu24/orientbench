# K1 反证：旧高 AP 是 partial-GT artifact，不是新评测算错（066）

> 用户关切："旧数据看着好，是不是现在 full-val 算错了？" 结论：**不是**。旧高 AP 由 DIOR 单元的
> partial GT（split/图像集不全）造成；当前 full-val 重算与每个检测器的**自评 DOTAMetric 日志**精确一致
> （6/6），故当前评测无误。数据：`reports/k1_old_vs_new_ap_anchor_audit_066.csv`、
> `reports/k1_dior61_taos_pad32_residual_audit_066.csv`。

## 反证矩阵（每单元）
| 单元 | 检测器 | old(partial) | old n_gt | **new full-val** | new n_gt | 检查点自评 DOTAMetric AP50 | new−log | GT 曾为 | 解释 |
|---|---|---|---|---|---|---|---|---|---|
| DIOR#22 | PSC | 0.6964 | 35436 | **0.5368** | 124445 | 0.5370 | 0.0002 | partial | partial GT(~28%)虚高，纠正后=自评 |
| DIOR#3 | ORCNN | 0.7999 | 35436 | **0.6448** | 124445 | 0.6448 | 0.0000 | partial | 同上 |
| DIOR#61 | RTMDet | 0.8866 | 35436 | **0.6462** | 124445 | 0.6440 | 0.0022 | partial | 同上（见残差核对）|
| FAIR1M#24 | PSC | 0.3452 | 78638 | **0.3462** | 78644 | 0.3462 | 0.0000 | full | full GT，本未虚高 |
| SODA#23 | PSC | 0.6119 | 449644 | **0.5991** | 449644 | 0.5991 | 0.0000 | full | full GT，本未虚高 |
| SODA#4 | ORCNN | 0.7592 | 449644 | **0.7295** | 449644 | 0.7295 | 0.0000 | full | full GT，本未虚高 |

**关键**：6/6 单元的 new full-val AP 与检查点自评 DOTAMetric AP50 差 ≤0.0022（多数 0.0000）。若当前评测
"算错"，不可能同时与 6 个独立检查点的自评日志吻合。因此**当前 full-val 评测正确**，旧高 AP 是 partial-GT
产物（仅 DIOR 三单元），SODA/FAIR1M 本为 full GT、从未虚高。

## DIOR#22 明确链条
old 0.6964 ← partial GT(n_gt=35436) ← /dev/shm 已丢失；full n_gt=124445；full-val AP=0.5368；检查点日志
`dota/AP50 0.5370`（文件名 best_mAP_5368）。→ **旧高值不是新评测算错，是 partial GT。**

## DIOR#61 taos_pad32 残差核对 — **已解决**
- 早前"0.5489 vs 0.6462"的疑似残差是**指标名混淆**：文件名 `best_mAP_5489` 的 5489 指 **dota/mAP**
  （多阈值主指标 = 0.5469），**不是 AP50**。
- 该检查点日志实际 `dota/AP50 = 0.6440`、`dota/AP75 = 0.4500`；我的重算 AP50=0.6462、AP75=0.452 —
  **与日志一致（差 ≤0.0022）**。config（taos_pad32、pad_size_divisor=32、Resize800 keep_ratio、
  test/annfiles、20 类）、split（full-val 124445）、evaluator 均一致。
- 故 DIOR#61 **无残差**，AP50 锚点=0.6462 有效，非 provisional。

## 治理
旧 0.6964 / 0.7999 / 0.8866 已从主表移除、进 superseded 表；partial-GT AP 不入主表；无 /dev/shm 主表依赖
（GT 已持久化，复算链加禁用检查）。

## K1 本轮判定
旧高 AP 完全由 partial GT 解释，当前 full-val 与 evaluator/日志对齐（6/6）→ **K1 remains PASS**。
（注：K1 evaluator PASS ≠ K1–K4 全过；K2/K3/K4 仍待判。）
