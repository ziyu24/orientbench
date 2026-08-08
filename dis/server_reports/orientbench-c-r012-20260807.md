# OrientBench r012 服务器执行报告

## 1. 决策结果

- 最终状态：`FAIL_PROVENANCE_R012`
- 停止阶段：Phase A0，早于 transform smoke、GPU forward、特征构建、任何 selector fit、target label attach 与 bootstrap。
- Core-6 来源闭合：5/6；阻塞单元为 `FAIR1M-v1.0/24`。
- 方法影响：当前跨数据集 EQS 路线按冻结规则关闭；没有生成 EQS 性能结论，也没有独立 HRSC 确认。
- 论文影响：完整稿已重写为 measurement→diagnose；P3 只保留负迁移和不可评价边界。

## 2. Git 与执行边界

执行前使用 `git pull --ff-only`，execution HEAD 为 `ebf8c27eb4ff9c225be920454b7a5f013fbc5099`，分支为 `main`，upstream 为 `origin/main`。该 HEAD 同时包含 scientific snapshot `c101429cebf3454b25bd62c285feffc2fea2e1c3` 与 CC review `b959a09c021ade11241aecd970c90060dbbed84f`。未执行 merge、rebase、reset、clean 或 force push。

受保护 `dis/B.md` blob 保持 `3181a862137918f1dd41677893937c12b3c39c28`。既有未跟踪 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/` 未读取、未修改、未暂存。最终提交仅显式暂存冻结的 25 条授权路径。

## 3. A0 法证

### 3.1 FAIR1M full-universe join

冻结本地 val20 由 4,362 个 XML/image IDs 与 78,644 个 GT 实例构成。GT 实例出现在 3,896 张非空标注图像中；这可解释 GT JSONL 不含 466 个空标注 image IDs，却不能自动解释原始预测 registry 同样省略这些图像。

| 来源 | image-ID set | 数量 | missing vs split | sorted-set SHA-256 |
|---|---:|---:|---:|---|
| full split | 4,362 | - | 0 | `352c77a85b426508bd8b26ee12f21bdb73de93a33e4ccc4733b7783bd1550085` |
| GT instance JSONL | 3,896 | 78,644 GT | 466 | `b0ceefdb370bbde2edc3dca461298953b784207bf47276fefe5ba6ffb89b43ec` |
| r011 schema | 3,896 | 484,332 predictions | 466 | `b0ceefdb370bbde2edc3dca461298953b784207bf47276fefe5ba6ffb89b43ec` |
| r011 identity raw | 3,896 | 484,332 predictions | 466 | `b0ceefdb370bbde2edc3dca461298953b784207bf47276fefe5ba6ffb89b43ec` |
| m069 universe | 4,362 | 488,194 predictions（manifest） | 0 | `352c77a85b426508bd8b26ee12f21bdb73de93a33e4ccc4733b7783bd1550085` |

逐图 join 证明 r011 raw/schema 没有为 466 张缺失图像保留显式 `n_pred=0` 行。m069 虽登记 4,362 images / 488,194 predictions，但只持久化 matched table、image universe 与 manifest，没有持久化对应完整 raw prediction dump。因此无法：

1. 重算 m069 的逐图 prediction count；
2. 证明 488,194 与 484,332 的 3,862 个差异预测来自何处；
3. 将 m069 identity predictions 与 hflip/vflip 建立同一 prediction identity；
4. 对完整 4,362 行 registry 执行无 GT association。

FAIR1M official AP endpoint 的历史对齐误差虽小于 0.002，但 AP 对齐不能替代 universe equality，故触发硬停止。

### 3.2 SODA mother-scene map

- frozen tiles：22,994
- mapped：22,994
- unmapped / ambiguous / duplicate：0 / 0 / 0
- mother scenes：576
- sorted `(tile,mother)` SHA-256：`bfeea8f39200a0412725a2ccee8d7112a5b993e89147bbde158088a3e8463934`

SODA 映射通过，但不能覆盖 FAIR1M 阻塞。

### 3.3 Core lineage

DIOR-R 三单元与 SODA-A 两单元通过既有 raw view image-universe equality 与 evaluator parity 核验。FAIR1M 三个 views 均只有 3,896 image rows；因此来源状态为 5/6，而不是 6/6。

## 4. 未执行阶段

| 阶段 | 实际计数 | 状态 |
|---|---:|---|
| detector training | 0 | 禁止且未执行 |
| GPU/instrumented forward | 0 | A0 前停止 |
| transform smoke | 0 images | A0 前停止 |
| EQS feature build | 0 rows | A0 前停止 |
| source-only model fit | 0 | A0 前停止 |
| target D_audit label attach | 0 | A0 前停止 |
| bootstrap | 0 replicates | A0 前停止 |
| HRSC independent confirmation | 0 | 主门未进入 |

三个下游执行入口读取 A0 状态；在非 `PASS_A0_R012` 时以退出码 2 拒绝继续。它们不是“已运行”的占位实现。

## 5. 复算与验证

实际执行：

```text
/home/rspip/anaconda3/envs/mr_dev1x/bin/python p3_selector/deployable_proxy_r012/scripts/inventory_preflight_r012.py
/home/rspip/anaconda3/envs/mr_dev1x/bin/python p3_selector/deployable_proxy_r012/scripts/validate_r012.py
```

A0 用时 60.03 秒，峰值 RSS 1,098,461,184 bytes；没有 GPU forward。只读 validator 重算并检查：FAIR split/GT/raw/m069 计数与 set SHA、Core-6 5/6 来源状态、SODA 映射、下游全部 `NOT_RUN_PROVENANCE_GATE`、target labels 未加载、受保护文件 blob。结果为 `VALID_R012_PROVENANCE_STOP`。三个 guard entry points 均返回预期退出码 2。

## 6. 关键产物

- 法证说明：`p3_selector/deployable_proxy_r012/docs/deployable_proxy_r012.md`
- FAIR/Core 来源表：`p3_selector/deployable_proxy_r012/reports/provenance_r012.csv`
- 三视图 raw 清单：`p3_selector/deployable_proxy_r012/reports/tta_inventory_r012.csv`
- 最终门：`p3_selector/deployable_proxy_r012/reports/gate_r012.json`
- 证据身份：`p3_selector/deployable_proxy_r012/reports/evidence_manifest_r012.json`
- 完整投稿稿：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- Claim ledger：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r012.csv`
- Novelty matrix：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r012.csv`

## 7. 科学解释

本轮不能回答 EQS 是否优于 source-fitted size-linear，因为前置估计总体不满足冻结条件。它回答的是更基础的问题：现有 FAIR1M raw artifacts 不能在同一 full-validation prediction universe 上支撑 identity/hflip/vflip 直接比较。

论文因此只保留可复算的 measurement→diagnose 内容：le90 周期角误差、`ar>=2.1` 可辨识域、geometry-normalized risk、full-evaluator 扰动、NRC/AURC/risk-coverage、图像/场景统计单位与人工标注不确定性。旧 target-GT geometry 仍是 diagnostic upper bound；source-supervised geometry 的 leave-dataset 结果为 0/6，而可识别 leave-detector 4/5 依赖 source 含同数据集 sibling units，不能称跨数据集可部署。

## 8. 合规确认

- 未修改 frozen thresholds、`ar>=2.1`、D_cal/D_audit、split、NMS 或 class map。
- 未训练 detector，未运行 inference，未下载任何数据、checkpoint 或第三方仓库。
- 未修改 r009/r010/r011 资产。
- 未使用 target labels 拟合、调参或形成 selector score。
- 未运行独立确认，未声称可部署、因果、跨域保证或方法路线就绪。
- 当前跨数据集方法路线按非通过规则关闭。
