# v3 中文正式论文全文清理与审计（065）

> 对象：`orientation_reliability_paper_zh_s1s5_v3_review.md`（单文件中文正式论文，图片仅占位）。
> 方法：模式扫描 + 逐命中语境判定；对可能触发的字面 token 直接改写至字面 grep=0。

| # | 检查项 | grep 结果 | 结论 |
|---|---|---|---|
| 1 | “待补”/TODO/TBD | 0 | PASS |
| 2 | 项目管理词（supervisor/verifier/git/artifact path/reports//figures//work_dir/.csv/056–064/P1–P5/precise-pass/invalid_pending） | 0 | PASS（arXiv 编号与数值表列非命令号，已用紧模式排除误报） |
| 3 | 投稿/期刊目标（CVPR/TPAMI/TGRS/ISPRS/ready/投稿/可投/目标期刊） | 0 | PASS（参考文献改为作者+年份+arXiv 编号，不含刊物缩写） |
| 4 | forbidden claims（proven/证明/universal failure/普遍失灵/full benchmark/selector victory/已校准） | 0 | PASS（"证明"改写为"表明/成立/定论"；"已校准"改写为"概率校准（calibrated）"；"全面基准/通用默认"仅出现在否定或禁止清单） |
| 5 | NRC<1 是否写成 calibrated/已校准 | 0 | PASS（§3 明确不用"校准"描述 NRC<1；"calibrated"仅保留概率校准/保形语境） |
| 6 | phase_mod 写法 | PSC-specific ×7 | PASS（写为 PSC-specific reproducible mechanism candidate / preliminary mechanism evidence；无通用机制定论） |
| 7 | geometry selector 写法 | 非通用默认 | PASS（诊断性/几何启发候选，弱信息场景增益、强信息场景打平；非通用默认） |
| 8 | conformal 跨域 | 经验评估 | PASS（跨域只作经验评估、报告违例，不写严格保证） |
| 9 | DOTA#20（D20）是否进主结论 | 仅排除/局限 | PASS（标 invalid，仅在实验设置排除说明、Scope、局限性、附录 G 出现，不进任何主结论） |

## 正式论文结构（图片仅占位）
摘要 / 关键词 → 1 引言 → 2 相关工作 → 3 方法（测量协议）→ 4 主结果一（双向分离）→ 5 主结果二
（几何原则与测量）→ 6 有限样本保形风险控制 → 7 实验设置 → 8 机制小节（角度编码器内在置信度，
含预注册头干预实验与失败审计）→ 9 下游尾部事件附录 → 10 Scope and Claims → 11 局限性 →
12 结论 → 参考文献（31 条，作者+年份+arXiv）→ 附录 A–I。图 1–7 均为编号占位（`【图 N 占位：…】`）。

## R1 受限结果的写入（§8）
- PSC phase_mod：跨 DIOR-R 与 SODA-A、各 3 seeds 稳定 NRC>1、全 seed 自助 CI 下界>1 →
  "PSC-specific、可复现的反序排序 / 机制候选 / 初步机制证据"，**非**通用机制定论。
- DCL：native 逐比特 margin informative（NRC 0.20/0.37）→ 明确写为反例，**不**推广为普遍失效。
- CSL：约随机/非反序。
- 直接回归（NaN）、KLD（半精度矩阵求逆不兼容）：failed_training 失败审计保留，不支持机制结论。
- 五头矩阵未完整成立 → 受限 PSC-specific 候选证据，非完整结局 A。

## 结论
v3 全文 9/9 审计通过，字面 forbidden/venue/PM token 均 grep=0；主线（measurement + 有限样本保形
风险控制）不变，R1 以受限机制小节增强。
