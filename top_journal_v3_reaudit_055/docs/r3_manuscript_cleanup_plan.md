# R3 —— 中文稿审前检查与降噪清理计划

> 对象：`docs/paper_zh_s1s5_v1/orientation_reliability_paper_zh_s1s5_v1.md`。本计划不破坏原稿，仅列出清理项。

## 一、审前十项检查结果
| # | 项 | 结论 | 依据 |
|---|---|---|---|
| 1 | 已去项目化 | **通过** | 正文 PM 词计数 0（supervisor/verifier/artifact path/056/057/P1-P5/precise-pass/invalid_pending 均 0） |
| 2 | 用 full evaluator 而非 matched-only | **通过** | “完整评测器”8 处；无“仅取匹配对 mAP=1.0”，反而显式声明不使用代理 |
| 3 | selector-fit 与 conformal-calib 独立 | **通过** | 第 5 节说明拟合子集/标定子集/审计集互斥 |
| 4 | LTT + bounded mean + image bootstrap | **通过** | 第 5 节：固定序列、有界 [0,90°] 均值、图像级聚类自助 |
| 5 | geometry selector 非通用默认 | **通过** | “非通用默认”4 处 |
| 6 | phase_mod 仅机制候选 | **通过** | “机制候选”9 处；无“已证明” |
| 7 | 下游仅 modest 附录 | **通过** | 第 8 节 + 附录 F，写明幅度小、不影响主线 |
| 8 | 真实文献补齐 | **未通过 → 待整合** | 正文第 10 节仍有 9 处“待补”占位；真实文献已在 `r3_related_work_completed.md` 备齐，需整合入正文并删除占位 |
| 9 | Scope and Claims 集中写边界 | **通过** | 第 9 节集中；有表 8 |
| 10 | 正文含 PM 词 | **通过（无）** | 同 #1 |

**唯一未过项 = #8。** 其余九项已满足。

## 二、降噪清理项（不破坏原稿）
1. **文献整合**：用 `r3_related_work_completed.md` 的真实条目替换正文第 10 节全部“待补”；无法核验精确字段者移入该文件 blocker 小节，正文只保留可核验条目，不留占位。
2. **删除项目管理词**：确认正文不含 supervisor/verifier/git/artifact path/056/057/P1–P5/precise-pass/invalid_pending（当前已为 0，维持）。
3. **保留科学章节叙事**：引言/协议/测量/风险控制/机制/下游/边界/结论结构不动。
4. **Scope and Claims**：正文保留第 9 节；**删除与附录 G 重复的表**（表 8 与附录 G claim ledger 二选一在正文，另一移附录）。
5. **forbidden claims 放附录**：禁止项清单集中于附录 G，正文 Scope 只留精炼三类（allowed/qualified/forbidden 摘要）。
6. **NRC 方向示意图（图 1）保留**。
7. **“更高档位就绪”改学术表达**：正文已用“不主张达到更高档位就绪”，维持学术措辞，不出现会议名。
8. **NRC<1 统一**：全文“非反序 / 优于随机 / 有信息的排序”，不写“已校准”（当前已一致）。
9. **下游**：仅作 modest 附录（维持）。
10. **phase_mod**：仅机制候选（维持）；升级需 R1 预注册矩阵结局 A/B 成立。
11. **geometry selector**：非通用默认（维持）。

## 三、执行顺序建议（059+）
先整合真实文献（消除 #8），再做正文/附录去重（#4/#5），最后加入 IoU-δθ 理论段（`r3_iou_aspect_ratio_theory.md`）与图 1/图 2 的最终图形化。本轮不改正文，仅登记计划。
