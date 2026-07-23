# A2 场景级风险定义与裁决

eligible-scene universe 在任何分数和阈值之前固定为至少含一个 `ar>=2.1` eligible matched prediction 的原始场景。阈值后没有 selected prediction 的场景是 abstained scene：它进入 nonempty scene rate 分母，但不以零损失稀释条件风险。

对非空场景，主损失为 selected predictions 中 geometry-normalized severe events 的比例，并使用 bounded-loss Hoeffding-Bentkus 单侧 UCB。co-primary scene event 表示非空场景是否至少含一个 severe event，使用 Clopper-Pearson 单侧 UCB。两者必须连同 nonempty rate、selected-instance coverage 和 selected count 报告。

DIOR-R 与 FAIR1M 的 image ID 对应原始场景，既有冻结 split 在 mother-scene 层无交叉。SODA-A 的 tile filename 可高置信恢复 mother scene，但全部 576 个 mother scenes 的 tiles 跨越既有 D_cal/D_audit 角色；在不修改冻结 split 的约束下，严格 mother-scene calibration/audit independence 不成立。因此 SODA-A 的正式 exchangeable unit 降为 tile/image，mother-scene 聚合只作相关性 sensitivity，不称严格 mother-scene guarantee。

旧 instance-i.i.d. exact-binomial 仅保留为统计审计，不是 distribution-free 主保证。

**A2 判定：PASS_TILE_ONLY_WITH_LIMITATION。**
