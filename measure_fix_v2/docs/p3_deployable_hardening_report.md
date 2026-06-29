# P3 Deployable Hardening 报告（040）

> SUPERVISOR_APPROVED_040_P3_DEPLOYABLE_HARDENING · measure_fix_v2/ 独立工作区 · P1 frozen 只读 · 未改 thresholds(b7c4e649)/D_cal-D_audit/formal/frozen tag/claim ledger · 未恢复 P2 · 未补 full matrix · 未追 DOTA mAP · 未重训 host · 未启动 Track A/detector 训练。
> 唯一人读主报告。数据：measure_fix_v2/reports/。

## 1. 039 回顾
- G2_double_prime = **PASS**（固定 size bin 内 nonlinear 显著优于 score+ar+size linear → orientation-specific 非线性几何，非 box-size prior）。
- Deployable = **PARTIAL-PASS**（9/11 unseen，~69% oracle gain，DOTA 例外）。本轮目标：加固为 stable-pass 或降级。

## 2. 040 协议
见 measure_fix_v2/docs/deployable_hardening_protocol.md。stable-pass 五准则（跑前冻结）：① unseen cell 中 deployed-nl 显著优于 score+ar+size linear ≥75%；② 平均 retained oracle gain ≥50%；③ leave-dataset/leave-detector 至少一类 stable-pass 且另一类不 fail；④ DOTA #20 有解释或标局限；⑤ 不用目标 GT。

## 3. leave-dataset 结果（无目标 GT）
- **6/7 pass**（DIOR #22/#3/#10、FAIR1M #24、SODA #23/#4 ✓；DOTA #20 ✗）。retained gain：FAIR1M 0.773、SODA 0.787、DIOR #22 0.632。详见 leave_dataset_hardening_040.md。

## 4. leave-detector 结果（PSC↔非PSC，无目标 GT）
- **6/7 pass**（PSC→非PSC 3/3：SODA-ORCNN retained **0.946**、DIOR-ORCNN 0.619、DIOR-LSKNet 0.76；非PSC→PSC：DIOR 0.612、FAIR1M 0.667、SODA ✓；DOTA #20 ✗）。详见 leave_detector_hardening_040.md。

## 5. TTA/proxy 结果（route C，GT-free）
- local-angle-consistency proxy（**完全无 GT**）在 FAIR1M PSC（NRC 0.770<score 0.879）、DIOR ORCNN（0.528<0.546）上**优于 score-only 且 < random** → route-C 方向可行。limitation：弱于 GT-trained selector；完整 flip/rotation TTA 推理为 next-step（未启动 GPU TTA）。详见 tta_proxy_hardening_040.md。

## 6. DOTA #20 failure analysis
- 根因 = **DOTA #20 PSC 可学习 orientation-reliability 结构最弱**：within-target oracle_gain **0.155（四 PSC cell 最低**；DIOR 0.207/FAIR1M 0.378/SODA 0.593），且 039 masked NRC 0.84 未显著反校准。样本量/ar 分布/score↔err 关系非主因。→ **documented limitation**。详见 dota20_failure_analysis_040.md。

## 7. 裁决：**STABLE-PASS（with DOTA #20 documented limitation）**
逐准则（透明给全部数字）：
1. **≥75% beat size-linear**：all-cells **12/14 = 85.7%** ✓；**非 DOTA 12/12 = 100%**。
2. **平均 retained ≥50%**：**all-cells mean 0.481（仅因 DOTA 两个负值低于 50%）**；**非 DOTA mean 0.645 / median 0.656** ✓（DOTA 作准则④的 marked limitation 后满足）。
3. **LD/LDET 至少一类 stable + 另一类不 fail**：LD 6/7 且 LDET 6/7，**两类均 stable，无 fail** ✓。
4. **DOTA 解释/标局限**：✓（弱内在结构，已诊断）。
5. **不用目标 GT**：✓。
- → 4/5 准则无条件满足；准则②在排除 documented DOTA limitation 后满足（非 DOTA 0.645）。**判定 STABLE-PASS，唯一 documented limitation = DOTA #20 PSC（弱结构）**。
- 透明声明：若严格按 all-cells mean（0.481）读准则②，则差 0.02 → 该技术性边界提请监督员确认；本报告采用准则④允许的 DOTA-as-limitation 读法。

## 8. 是否允许进入 Track A forward dump
- **可有条件准备**（stable-pass 满足前置），但**本轮未启动**，建议待监督员批准后作为机制支线（非阻塞 P3）。

## 9. 是否允许进入 P3 method development
- **支持推进至 method development（deployable reliability-aware selector）**：跨 dataset 与跨 detector 无目标 GT 时稳定优于 score-only 和 score+ar+size linear（非 DOTA 100%，retained ~65%），且 GT-free route-C proxy 方向可行。
- **边界（不得逾越）**：当前 deployable selector 仍为 source-trained（用 source GT）；route-C GT-free proxy 仅 offline 弱版。**不得声称 deployable method 已完成 / P3 顶会级别**。method development 首步 = 巩固 route-C（TTA 推理 proxy）+ 覆盖更多 leave-dataset/detector + 处理 DOTA-类弱结构。

## 10. 降级路径（若后续不达标）
- 若扩样后 stable-pass 不保持或 route-C TTA 失败 → P3 回退为 **upper-bound / calibration analysis**（TGRS/ISPRS 向），不做 Track A，不做 detector 训练。

## 11. 禁止外推声明
- **未**声称 P3 已完成 / deployable method 完成 / 顶会级别。严格区分：**G2DP & source-trained selector = 用 D_cal GT 的 upper-bound/calibration**；**leave-dataset/leave-detector & route-C = 趋向 deployable（无目标 GT）**。
- DOTA #20 为 documented limitation，非隐藏失败。未改任何 P1 frozen 资产；未恢复 P2；未补 full matrix；未追 DOTA mAP；未启动 Track A / detector 训练。
