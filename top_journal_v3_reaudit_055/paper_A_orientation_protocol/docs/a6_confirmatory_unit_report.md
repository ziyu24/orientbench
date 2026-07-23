# A6 独立确认单元报告

确认协议在候选风险计算前冻结。优先候选 ARS-DETR DIOR-R/16 的持久化 schema 实际只覆盖 5,863 个 image IDs，而当前 DIOR-R full-val 为 11,738；它还已有历史 NRC 结果，因此既非 provenance-clean full-val，也非未查看确认单元。ARS-DETR DOTA-v1.0/14 的 manifest 仅指向已经消失的 `/dev/shm` raw/schema，无法从持久化 prediction identity 复算。其它现有独立架构候选同样是旧 partial universe 或已有风险结果。

按照冻结优先顺序，不因结果不理想更换或伪装 unit，也不训练新 detector、不引入新数据集。因此 AP75、NRC 与 scene-risk confirmatory point 均不生成伪数值；风险前沿显式输出 `INFEASIBLE_NO_ELIGIBLE_UNIT`。

**A6 判定：NO_ELIGIBLE_CONFIRMATORY_UNIT。** 这不是对协议数值的反证，而是确认性证据缺失；075 的严格预算 deployable certification 不可行结论没有获得独立确认。
