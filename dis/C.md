# OrientBench C 侧 r011 验收与 r012 顶刊/顶会资格判别

- round: `orientbench-c-r012-20260807`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- active manuscript: [`orientation_reliability_measure_diagnose_fix_r011.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md)
- r011 report: [`orientbench-c-r011-20260807.md`](server_reports/orientbench-c-r011-20260807.md)
- formal verdict: `FAIL_PROTOCOL_R011`，并触发 evaluator/implementation 子失败；不得采纳仓库自报的 `PASS_STRONG_JSTARS_EVIDENCE_R011`
- scientific status: P1 fixed-dose 信号为 **descriptive credible, confirmatory invalid**；现有 P3 geometry selector 的 leave-dataset 路线被反证
- current venue: **JSTARS plausible、尚未 ready；完整重写后有 strong-JSTARS 潜力。TGRS/ISPRS JPRS/CVPR/ICCV 当前均未达到**
- `cc_recommendation: recommended_now`：贡献路线已到冻结节点，服务器 PASS 与预注册契约冲突，且下一步决定是否永久关闭顶会方法线；适合独立投稿级攻击，最终仍由可复算证据裁决。

## 1. r011 可采纳事实

1. official mmrotate baseline endpoint 与独立 Shapely clean-room evaluator 在 Core-6 的 dose=0 AP50/AP75 一致，双端差最大约 `2.45e-6`；这一项可作为 baseline evaluator parity。
2. 6000 条 paired image-bootstrap replicate 的汇总可独立复算。代码已改用 full-GT denominator；D/S 各六单元的 point、CI、Holm 与 CSV 精确一致：D point `0.00527–0.10955`、S point `0.00860–0.10022`，D/S 均 6/6 CI 下界大于 0，Holm 最大 p 为 `0.01998`/`0.005994`。
3. S 的 AP 与真实正负方向算术平均逐行相等；D AP75 单调点曲线及 dose15 三 AR-bin 生存率顺序均为 6/6。
4. P3 不是空结果：11 个 eligible folds 仅 4 个支持，且全部来自 leave-detector；leave-dataset 为 **0/6**，其中五个显著反向。当前 geometry selector 不具备跨数据集 deployability。
5. r011 累计 changed set 恰为授权的 33 路径，`git diff --check` 通过，32 个非自身输出的 Git blob 与 manifest 相符，保护文件未变化。

上述 2–3 说明科学信号不是伪造或旧 r010 错分母的重复，但不克服下述确认性前置失败。

## 2. 必须拒绝的 PASS 与最弱环节

1. 预注册要求 Core-6 的 dose0、D15、+15、-15 双端 full parity，共 24 个条件；实际 parity 表只有六个 dose0 baseline。144 点 fixed-dose 网格由第三套自写 evaluator 生成，未被 official/clean-room 在变体上复核。
2. golden 没调用 official `eval_rbbox_map`；优化器只做 20 个同公式 synthetic 对照，缺每个 Core 10 个真实 draws。
3. survival 应覆盖 `D,+,-,S × 8 doses × 3 bins × 6`，实际只算 dose15；risk 表虽有 960 键，但大量分量分层是 `NOT_AVAILABLE` 或无分母。
4. provenance 脚本没有加载 frozen split universe，却直接写 subset/PASS；未绑定 config、checkpoint、framework、class/tile map 与生成命令。P3 的 m069 输入也不在 manifest。
5. validator 信任已写入的 PASS/泄漏字符串并把 survival universe 弱化成 90 行，没有重算 24 parity、真实 draws、D 未匹配恒等、完整 risk/survival、真实 Git diff 或 P1 每个 gate。
6. 生成链内部不自洽：`finalize()` 只会生成 3 行 ledger，但提交产物有 8 行且 validator 要求至少 8 行；同一命令还会覆盖当前服务器报告。公开命令无法重生提交状态。
7. 资源表只是四行静态标签，不是每 30 秒 CPU/RAM/GPU 实测，不能证明 4×A30 和 80% CPU 纪律。
8. 合同要求单一最终提交，实际是两个提交；首个 preflight 提交后的 root section 又被第二提交原位修改。
9. 联合稿仍主要是 v080 measurement-only 主体。P3 只在结论后追加两段；摘要、贡献、方法、主结果、讨论、限制和结论没有整合。正文把 `4/11` 写成宽泛“跨域”，却没有正面报告 leave-dataset `0/6`。
10. 稿内仍有内部 gate 字符串、旧 formal certification 残留及数字源漂移；ledger 哈希的是短 claim 标签而非稿件原句。

正式裁决因此是 `FAIL_PROTOCOL_R011`，并记录 `FAIL_EVALUATOR_R011`、`FAIL_IMPLEMENTATION_R011` 子条件。科学机制并非被证伪，但 r011 CI/PASS headline 永久 quarantine；按预注册不再开 fixed-dose 修补轮次。

## 3. novelty 与顶刊攻击（核查日 2026-08-07）

- ARS-DETR 已在 TGRS 2024 明确指出 AP50 对朝向偏差容忍过大并倡导 AP75（DOI `10.1109/TGRS.2024.3364713`）。因此“AP50 不足、AP75 更敏感”不能作为本文首创。
- CVPR 2023 SAOD、MCCL 与 WACV 2024 detection calibration 已覆盖检测器自知、定位感知校准和结构化检测校准；本文必须明确 NRC/选择性风险不是概率校准。
- CVPR 2022 OSKDet 已引入 localization-quality uncertainty；WACV 2025 Oriented Cell Dataset 已做多标注者 OBB 一致性。本文的人工标注实验只能作为遥感朝向噪声锚点，不能声称首次 OBB 标注者研究。
- 当前仍有实质差异的候选是：`le90 + ar>=2.1` 可辨识域、几何归一化严重事件、full-image/scene 统计单位、跨三遥感数据集多检测头的朝向选择性风险审计，以及可复算的 target-GT-free selector gate。前三项足以支撑分析论文；要到 CVPR/ICCV，最后一项必须产生真正跨数据集的方法收益。

## 4. 可证伪候选与 gate

| candidate | substantive difference | minimum decisive evidence | kill condition |
|---|---|---|---|
| P1 orientation reliability audit | 不把 AP50/AP75 观察当首创，主张几何归一化风险、统计单位与人类噪声边界 | 清理 invalid CI/formal claim；数字逐行绑定；完整稿件与 2026 一手相关工作 | 仍依赖 r011 PASS 字符串或未闭合认证；正文不能从生成端复算 |
| R12 equivariance-normalized selector | 用 hflip/vflip 轴向一致性并按理论 `delta_0.75(pred_AR)` 归一化；仅 source D_cal 拟合，target D_audit 一次性评估，因而是 target-GT-free 而非无监督 | Core-6 leave-dataset；相对 score+AR+size linear 在至少 4/6 单元 CI/Holm 通过，覆盖三数据集和两 family，无数据集全反向 | target GT/target audit 参与特征或选择；少于 3/6；任一数据集整体显著反向；无法持久化 forward dump |
| top-venue joint paper | measure + diagnose + genuinely deployable selection，而非 target-GT upper bound | R12 PASS、独立确认单元/复算链、全文整合和投稿级攻击 | R12 FAIL/INCONCLUSIVE；收益只来自同数据集/同场景泄漏或近方形样本 |

## 5. 决策台账

| item | decision | confidence | action |
|---|---|---:|---|
| r011 baseline dual parity | adopt, baseline only | high | 可证明两 evaluator 在原始预测一致，禁止外推为变体 parity |
| r011 D/S 6×1000 数值 | revise/adopt descriptive | medium-high | 保留点估计与“候选信号”；删除 confirmatory PASS/CI headline |
| r011 provenance/gate/validator | reject | 0.99 | 记录 protocol/implementation failure，不修 r011 |
| current P3 nonlinear geometry | reject as deployable | high | 正面报告 leave-dataset 0/6，保留 target-GT upper bound 诊断定位 |
| old TTA reports | experiment input only | medium | 先核验 current lineage/raw；不得继承旧 PASS |
| r011 joint manuscript | reject as submission draft | high | r012 无论 PASS/FAIL 都要完整重写，不得结论后追加 |
| next server work | experiment once | medium | 只做 R12 target-GT-free leave-dataset gate；失败即关闭顶会方法线 |

唯一服务器报告路径：[`orientbench-c-r012-20260807.md`](server_reports/orientbench-c-r012-20260807.md)。
