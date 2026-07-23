# R3 中文审稿版 v2 合规守护审计（063）

> 只做文字合规检查；R1 半成品（评测进行中）不入主结论。审计对象未改动（2026-07-03）。

| 检查项 | 结论 | 证据 |
|---|---|---|
| 待补 = 0 | PASS | grep 计数 0 |
| 项目管理词 = 0 | PASS | "门控"为科学含义；claim ledger 仅附录 G |
| NRC<1 不写 calibrated | PASS | 行39 显式约定不称已校准；其余为禁止清单否定式 |
| phase_mod 仍机制候选 | PASS | "机制候选" ×9；无正向"证明" |
| DOTA#20 不进主结论 | PASS | "不进主证据" ×1；主表不含 |
| 无 full complete / TPAMI/CVPR ready | PASS | 无正向就绪断言 |

## 063 R1 评测结果不得写入主文
- R1 18 个有效 run 的完整评测**本轮仍在后台运行**（AP75/masked-NRC 逐 run 产出中），
  **未满足预注册 3-seed A/B**，不入正文机制结论。
- 冒烟已见 PSC-DIOR-seed0 masked NRC_native(phase_mod)≈1.23、CI 下界>1（反序方向），
  NRC_score≈0.50（非反序）——**仅 preliminary signal，且单 seed/子集**，按硬禁令：
  **禁止**写"phase_mod mechanism proven / PSC angle head proven broken / angle-coder confidence
  universally fails"。正文第7节维持"机制候选"。
- 待 3-seed 全矩阵完成且满足预注册 A/B，方可在正文/interim 文档以 interim evidence 措辞更新。

## 结论
v2 审稿版 6/6 合规通过；R1 063 评测结果暂不入正文。
