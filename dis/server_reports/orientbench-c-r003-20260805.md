# OrientBench A6R 前瞻独立复现实物门控

- round: `orientbench-c-r003-20260805`
- scientific snapshot: `e3ca1ad94d64d202a47b6635490fde439df76868`
- execution HEAD: `7cc60c52aed3503069364184866f1bf5cada0836`
- final gate: `FAIL_NO_A6R_ASSET`
- selected unit: `NONE`
- training / inference / risk computation / download: `0 / 0 / 0 / 0`

## 1. 结论

当前服务器没有可被冻结为 A6R prospective replication 的完整单元。盘点到 38 个本地 checkpoint，
并继承原 A6 的 3 个历史候选，共 41 个精确候选记录；全部在按顺序执行的硬门中被排除。
原 `NO_ELIGIBLE_CONFIRMATORY_UNIT` 保持不变，A 继续是 `A_MEASUREMENT_ONLY`。

## 2. 首个失败点

| first failed gate | candidates |
|---|---:|
| `CHECKPOINT_AND_FULL_UNIVERSE_MISSING` | 1 |
| `PRIOR_OUTCOME_EXPOSURE` | 2 |
| `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` | 38 |

本地 checkpoint 全部已经参与既有协议/机制工作或存在 prior outcome 暴露，不能重新包装成前瞻复现。
原 A6 的 ARS-DETR/Strip-RCNN 候选仍分别受 partial universe、prior risk exposure 或 vanished raw artifact 限制。
此外，当前服务器的 `dataset_store` 为空，`external_baseline_library/readme.md` 与整个 baseline 库均不存在；
因此 checkpoint 许可、完整 split、empty-image、GT、母景映射和 raw-to-final 可复算性都无法为新单元闭环。

### 2.1 完整候选清单

| candidate | dataset | detector | head/coder | seed | tier | first failed gate |
|---|---|---|---|---:|---|---|
| `ARS-DETR_DIOR-R/16` | DIOR-R | ARS-DETR | registered historical head | registered | `EXCLUDED` | `PRIOR_OUTCOME_EXPOSURE` |
| `ARS-DETR_DOTA-v1.0/14` | DOTA-v1.0 | ARS-DETR | registered historical head | registered | `EXCLUDED` | `CHECKPOINT_AND_FULL_UNIVERSE_MISSING` |
| `DIOR-R|registered|RotatedRetinaNet|CSL|seed0|961910ce16b8` | DIOR-R | RotatedRetinaNet | CSL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|CSL|seed1|fc04a60988b2` | DIOR-R | RotatedRetinaNet | CSL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|CSL|seed2|a85861553e52` | DIOR-R | RotatedRetinaNet | CSL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|DCL|seed0|719290fb5cd4` | DIOR-R | RotatedRetinaNet | DCL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|DCL|seed1|c7b383471580` | DIOR-R | RotatedRetinaNet | DCL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|DCL|seed2|ed7863c20998` | DIOR-R | RotatedRetinaNet | DCL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|PSC|seed0|c92af20f3d0d` | DIOR-R | RotatedRetinaNet | PSC | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|PSC|seed1|805af3e4533c` | DIOR-R | RotatedRetinaNet | PSC | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|PSC|seed2|dd1068986f47` | DIOR-R | RotatedRetinaNet | PSC | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|direct_regression_le90|seed0|9121ae7940f3` | DIOR-R | RotatedRetinaNet | direct_regression_le90 | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|direct_regression_le90|seed1|3ce0cd835cf9` | DIOR-R | RotatedRetinaNet | direct_regression_le90 | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DIOR-R|registered|RotatedRetinaNet|direct_regression_le90|seed2|2c8a0d1a2af9` | DIOR-R | RotatedRetinaNet | direct_regression_le90 | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DOTA|v1.0|RHINO|positive Hungarian classification head|seed42|55a90abbace4` | DOTA | RHINO | positive Hungarian classification head | 42 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DOTA|v1.0|RotatedFCOS|PSCD dual-frequency|seed0|e2b7edcc3041` | DOTA | RotatedFCOS | PSCD dual-frequency | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DOTA|v1.0|RotatedFCOS|PSCD dual-frequency|seed1|c6991079cc1a` | DOTA | RotatedFCOS | PSCD dual-frequency | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DOTA|v1.0|RotatedFCOS|PSCD dual-frequency|seed2|f60d06dfbaa8` | DOTA | RotatedFCOS | PSCD dual-frequency | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `DOTA|v1.5|RotatedRTDETR|direct le90 query head|seed42|3e32fa11114c` | DOTA | RotatedRTDETR | direct le90 query head | 42 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|CSL|seed0|b5884ea5d830` | FAIR1M | RotatedRetinaNet | CSL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|CSL|seed1|088ef67e666c` | FAIR1M | RotatedRetinaNet | CSL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|CSL|seed2|a984d18eb13c` | FAIR1M | RotatedRetinaNet | CSL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|DCL|seed0|fdfbcaadd376` | FAIR1M | RotatedRetinaNet | DCL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|DCL|seed1|acfe76992f7f` | FAIR1M | RotatedRetinaNet | DCL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|DCL|seed2|655503dd7f77` | FAIR1M | RotatedRetinaNet | DCL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|PSC|seed0|194de87e7224` | FAIR1M | RotatedRetinaNet | PSC | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|PSC|seed1|e1e3b1ae09ac` | FAIR1M | RotatedRetinaNet | PSC | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `FAIR1M|v1.0|RotatedRetinaNet|PSC|seed2|60d0d05b3f78` | FAIR1M | RotatedRetinaNet | PSC | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|CSL|seed0|b777eb8fa651` | SODA-A | RotatedRetinaNet | CSL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|CSL|seed1|60892eef4b9d` | SODA-A | RotatedRetinaNet | CSL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|CSL|seed2|fa075ed3087b` | SODA-A | RotatedRetinaNet | CSL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|DCL|seed0|cf63e803ff3e` | SODA-A | RotatedRetinaNet | DCL | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|DCL|seed1|76e6f54db65e` | SODA-A | RotatedRetinaNet | DCL | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|DCL|seed2|d7f6ab834c87` | SODA-A | RotatedRetinaNet | DCL | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|PSC|seed0|709dd4a3cf70` | SODA-A | RotatedRetinaNet | PSC | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|PSC|seed1|29b4a959cde7` | SODA-A | RotatedRetinaNet | PSC | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|PSC|seed2|6af6f1b924c8` | SODA-A | RotatedRetinaNet | PSC | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|direct_regression_le90|seed0|34c143c476d4` | SODA-A | RotatedRetinaNet | direct_regression_le90 | 0 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|direct_regression_le90|seed1|d707407a1841` | SODA-A | RotatedRetinaNet | direct_regression_le90 | 1 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `SODA-A|registered|RotatedRetinaNet|direct_regression_le90|seed2|2a51b7b15906` | SODA-A | RotatedRetinaNet | direct_regression_le90 | 2 | `EXCLUDED` | `PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION` |
| `Strip-RCNN_DIOR-R/47` | DIOR-R | Strip-RCNN | registered historical head | registered | `EXCLUDED` | `PRIOR_OUTCOME_EXPOSURE` |

精确 checkpoint/config/log 身份、bytes、SHA-256、Git blob、许可与 split/schema 字段见 candidate inventory；
逐候选 overlap 与污染证据见 overlap registry。

## 3. 污染与 overlap

overlap registry 保留每个候选的 checkpoint/config 命中、同 hash、selection lineage、协议参与和 prior exposure。
未读取 D7/PCP-OBB、pcbobb、pcbobb_beyond 或 pcbobb_score_study；它们的 overlap 身份保持 UNKNOWN，
并且 UNKNOWN 不计作 clean。完全未暴露、可进入中性排序的候选为 0，因此没有执行 outcome-based 比较或换 unit。

## 4. 协议边界

A1/A6 冻结协议、原 A6 provenance audit 与迁移交接均已读取；未修改任何冻结文件。
若未来取得合格资产，missing-TTA policy 固定为保持 eligible universe，把非有限 TTA 排在有限值之后；
TTA 完全不可得时从该单元 score menu 删除，不能切到 complete-case universe。

## 5. 最弱环节与下一步

最弱环节不是计算资源，而是物理资产不存在：没有本地 dataset full split，也没有可验证许可/选择来源的外部 baseline 库。
下一轮若要继续，应先由 C 单独冻结一个官方 acquisition contract，明确官方 dataset/checkpoint URL、版本、公开 checksum、
许可、full split/empty-image/scene mapping 和预计磁盘；获取前仍不得查看 target NRC/risk。当前报告不虚构 URL 或 checksum，
也未执行任何下载。只有资产获取并独立核验通过后，才可设计一次性推理合同。

## 6. 复算与合规

脚本登记 107 个实际读取输入，只读取协议、provenance、迁移、配置/日志元数据、checkpoint bytes 和许可；
候选 target NRC、angle-risk、severe-event、certification/frontier 文件打开数为 0。
未写入 B，未修改 A 主稿、数据、split、checkpoint、旧报告、`dis/B.md` 或 `dis/sug.md`。
