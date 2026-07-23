# R3 中文审稿版 v2 合规守护审计（064）

> 本轮**小幅同步事实**：§7 新增"预注册头干预矩阵的初步证据（附录 R1）"段落，将 phase_mod 从
> 单 checkpoint 个案升级为 PSC-specific、跨两数据集×三 seed 的可复现机制候选；未重写主线。

| 检查项 | 结论 | 证据 |
|---|---|---|
| 待补 = 0 | PASS | grep 计数 0 |
| 项目管理词 = 0 | PASS | "门控"科学含义；claim ledger 仅附录 G |
| NRC<1 不写 calibrated | PASS | 行39 显式约定；新段用"非反序 / informative" |
| phase_mod 仍机制候选 | PASS | "机制候选" ×10；新段明写"仍非机制证明" |
| DOTA#20 不进主结论 | PASS | "不进主证据" ×1；主表不含 |
| 无 full complete/benchmark/selector victory/ready | PASS | 无正向断言；新段无 |

## 本轮同步的事实（§7 新段，受限写法）
- **允许并已写**：PSC phase_mod 在 DIOR-R 与 SODA-A、各 3 seeds 稳定反序（NRC>1，全 seed 自助
  CI 下界>1）→ "PSC-specific、可复现的机制候选 / 初步机制证据"。
- **反例已写**：DCL 内在置信度明显 informative（NRC 0.20/0.37）→ 明确**不写**"角度编码器内在
  置信度普遍失灵"；CSL 约随机/非反序。
- **失败已保留**：direct_regression（NaN）、KLD（AMP/fp16 linalg.inv 不兼容）failed_training，
  仅失败审计，未隐去、不支持机制结论。
- **边界已写**：五头矩阵未完整成立 → "受限 A-like 的 PSC-specific 证据"，非完整结局 A；
  exploratory rescue 仅附录、不进主矩阵；主线仍为 measurement + conformal，R1 为机制小节增强。

## 禁止项复核（未触发）
未写：PSC angle head proven broken / phase_mod mechanism proven / angle-coder confidence
universally fails / full benchmark / selector victory / TPAMI-CVPR ready / full project complete /
NRC<1=calibrated / DOTA#20 进主结论。

## 结论
v2 审稿版 **6/6 合规通过**；R1 以受限机制证据小幅同步入 §7 附录段，主线与边界不变。
