# S1b —— selector / conformal-calibration 独立性修复 (v1)

> 数据：`reports/pre_submission_s1s5_v1/s1b_score_menu_resplit_v1.csv`、`s1b_conformal_independent_v1.csv`。masked ar≥1.6。未改冻结 D_cal/D_audit 成员。

## 问题
早期 geometry selector 在 target cell 的 D_cal 上训练，conformal threshold 也在同一 D_cal 上标定 —— selector-fit 与 conformal-calibration **重合**，破坏 split-conformal 交换性，guarantee 判为无效。

## 修复
不改变冻结的 D_cal/D_audit 成员，仅对 D_cal 按 md5(image_id) 再分：D_fit（训 selector）/ D_calib（标 conformal threshold）；D_audit（审计）保持不动。三者互斥 → selector-fit / calibration / audit 独立。另做方案 B 对照：selector 在其它 cell 的 D_cal 上训练（leave-cell）。

## 结果一：score menu NRC（独立评估，masked D_audit，越低越好）
| cell | detection | geometry(A, D_fit) | geometry(B, leave-cell) | TTA | phase_mod |
|---|---|---|---|---|---|
| DIOR#22 | **0.562** | 0.600 | 0.624 | 0.534 | 1.128 |
| FAIR1M#24 | 0.921 | **0.617** | 0.722 | 0.647 | 1.117 |
| SODA#23 | 0.906 | **0.506** | 0.505 | 0.527 | 1.091 |
| DIOR#3 | 0.528 | **0.495** | 0.591 | 0.570 | — |
| DIOR#61 | 0.419 | **0.404** | 0.595 | 0.684 | — |
| SODA#4 | 0.706 | **0.508** | 0.517 | 0.948 | — |

**关键更正：修复独立性后，geometry selector 不再普遍占优。**
- 在 detection 弱信息 cell（FAIR1M#24 0.92 / SODA#23 0.91 / SODA#4 0.71）geometry 大幅更优（0.62/0.51/0.51）。
- 在 detection 已强 cell（DIOR#22 0.56 / DIOR#3 0.53 / DIOR#61 0.42）geometry 打平或略差（DIOR#22 反而更差 0.600>0.562）。
- 方案 B（leave-cell 迁移）普遍差于方案 A → selector 跨 cell 迁移会退化。

## 结果二：独立 conformal（tail P(err>5°)≤α，D_calib 标定→D_audit 审计，fit≠calib，有效）
α=0.05 覆盖（越高越好，同一有效保证下）：
| cell | detection cov | geometry(A) cov |
|---|---|---|
| DIOR#22 | 0.706 | 0.718 |
| FAIR1M#24 | 0.018 | **0.227** |
| SODA#23 | 0.0001 | **0.451** |
| DIOR#3 | 0.786 | 0.834 |
| DIOR#61 | 0.826 | 0.824 |
| SODA#4 | 0.067 | **0.323** |

## 裁决
- 独立性已修复（selector-fit / calibration / audit 三者互斥，guarantee 有效）。
- **不得写 “geometry selector recommended default（6/6 最优）”**。正确表述：**geometry selector 是安全的默认——在 detection score 弱信息的 cell（FAIR1M/SODA）显著提升同保证下覆盖，在 detection 已强的 cell 与其打平**。增益集中在“detection 对朝向弱信息”的 cell，可由可靠性协议本身诊断。
- 跨 cell 迁移（leave-cell）会退化 → deployability 更弱，只作候选。
- S1b 判为 **qualified pass**（独立性修好，但 selector 优势非普遍 → claim 收缩），非 fail。
