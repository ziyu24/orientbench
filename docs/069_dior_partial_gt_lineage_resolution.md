# 069 DIOR partial-GT lineage 清债

**当前裁决：RESOLVED：A-C 均已由冻结 checkpoint 的 DIOR test full-validation 持久化产物替代，旧 052 reliability lineage 不再进入正式结果。**

## 已 supersede 的 052 lineage

| cell | 052 状态 | matched rows | matched images | observed IDs | n_gt | sha256 |
|---|---|---:|---:|---|---:|---|
| A / DIOR-R/22 | SUPERSEDED_WRONG_SPLIT_PARTIAL_GT | 29994 | 5548 | 5863..11725 | 35436 | `f596a441d14e82a6a8ae9cf61c6e32a60854d9334b1d9caf667710eb0220a783` |
| B / DIOR-R/3 | SUPERSEDED_WRONG_SPLIT_PARTIAL_GT | 32161 | 5581 | 5863..11725 | 35436 | `c8031cfb64085d145a493d69aff3e4004417bfc6bfedcf9c0cf856d46561a44b` |
| C / DIOR-R/61 | SUPERSEDED_WRONG_SPLIT_PARTIAL_GT | 32696 | 5739 | 5863..11725 | 35436 | `7d27907ec0150199879c5b60f6ad1228cc38ce01f5923416a2a0ad986c8c7ad4` |

052 的 GT metadata 只有 35,436 个实例，记录的源域为 DIOR trainval 子域；matched IDs 全在 5,863..11,725，和冻结 test IDs 11,726..23,463 零重叠。其 GT 路径位于已丢失的 `/dev/shm`，因此只保留 provenance，不具备正式复算资格。

## 069 replacement A-C

| cell | 状态 | final matched | manifest | images | n_gt | test ID set exact |
|---|---|---|---|---:|---:|---|
| A / DIOR-R/22 | AUTHORITATIVE_FULLVAL | `outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl` | `outputs/persistent_artifacts/m069_fullval_reliability/A/manifest.json` | 11738 | 124445 | True |
| B / DIOR-R/3 | AUTHORITATIVE_FULLVAL | `outputs/persistent_artifacts/m069_fullval_reliability/B/matched_fullval.jsonl` | `outputs/persistent_artifacts/m069_fullval_reliability/B/manifest.json` | 11738 | 124445 | True |
| C / DIOR-R/61 | AUTHORITATIVE_FULLVAL | `outputs/persistent_artifacts/m069_fullval_reliability/C/matched_fullval.jsonl` | `outputs/persistent_artifacts/m069_fullval_reliability/C/manifest.json` | 11738 | 124445 | True |

转正条件同时要求：manifest `status=complete`；11,738 图 universe 与冻结 test ID 集完全一致；GT 总数 124,445；matched/universe/GT/checkpoint/config 的 sha256 与 manifest 一致；TTA 为正式启用状态；无 `/dev/shm` 依赖；无完成后的残留 `.partial`。

## DOTA clean full-val artifact

| cell | 状态 | rows | matched images | eval images | n_gt | sha256 | DOTA#20 |
|---|---|---:|---:|---:|---:|---|---|
| DOTA-v1.0/orcnn | AUTHORITATIVE_CLEAN_FULLVAL | 48889 | 2906 | 5297 | 55804 | `055d415b6e9ec86b4f339c33a17108a02317b4bde7edf3190bbc36178dbbf79d` | excluded |
| DOTA-v1.0/rtmdet | AUTHORITATIVE_CLEAN_FULLVAL | 51736 | 2916 | 5297 | 55804 | `4c19f140c395757b83ca868aab7763fdd0e01f99de2e345461f330a7a8c73e3e` | excluded |

DOTA 两个 JSONL 是 matched-instance artifact；其 full-val 身份由 5,297-tile/55,804-GT 持久化 val 数据、K4b metrics、冻结 checkpoint/config、生成脚本及正常结束日志联合绑定。权威 metadata 见 `reports/069_dota_clean_artifact_manifest.csv`。DOTA#20 不在产物中。

## 复核入口

```bash
python scripts/m069_lineage_audit.py
```

该命令不导入 detector/GPU 依赖，只读核验并原子更新本页和两份 CSV。在 A-C 全部转正前返回非零，sentinel 或 `.partial` 不构成完成证据。
