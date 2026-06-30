# 046 命令执行详细报告

> 指令：SUPERVISOR_APPROVED_046_CLAIM_CLEANUP_ROUTE_C_BOUNDARY_TTA_EXTENSION
> 主题：Orientation Reliability 收口审计 —— 话术清理 + Route-C 数据流接缝 + diagnose→fix 预测边界 + 非 PSC real TTA 扩展 + Track A 机制边界
> 工作区：`measure_fix_v2/`（旧 P1 frozen 只读）。git commit `ec78d93`。

---

## 0. 总裁决与合规

- 主线仍是 measure → diagnose → fix 联合论文：P1 测量诊断 / P3 修复尝试 / P2 降为附录或负结果。
- **合规**：未训练 detector；未追 DOTA 公开 mAP；未补 full matrix；未改 `thresholds.yaml`（sha256 `b7c4e649…` 未变）；未改 D_cal/D_audit；未把 exploratory 改 formal；未恢复 P2 主线；未改原始 dataset（DIOR/FAIR1M source 0 文件改动）；git 0 大文件。
- 未触发停止条件（无 target GT 泄漏，deployable claim 不需降级为 upper-bound）。

---

## 任务一：话术矛盾清理（claim cleanup）

**做了什么**：扫描 `measure_fix_v2/docs/`、`docs/` 主稿与摘要，定位并修正主动过度宣称（区分自我推销 vs 已是负向/forbidden-list 的合规表述）。

**修正项**：
1. 主稿 `orientation_reliability_measure_diagnose_fix_draft.md` 合作者摘要 **"顶刊点在哪里" → "科学贡献点（克制，不绑定 venue）"**，删除 venue-selling 语气。
2. **"NRC 提供独立于 accuracy"** / **"NRC 独立性"** → **"在当前可比设置中 NRC 提供 mAP 之外的 reliability signal；不主张严格独立"**（摘要 + §10 结论均改）。
3. "P3 deployable method" 全文已是 candidate；未发现正向 "deployable method complete"。
4. "PSC angle head proven broken" 仅出现在 forbidden-list（负向），保留；正文只写 phase_mod supports mechanism candidate。
5. governance `input/`（CLAUDE (8).md、项目执行文件）列 "NRC 完全独立 / 顶会 ready" 为 forbidden claims，**不动**（正确负向）。

**产物**：`docs/claim_language_cleanup_report.md`

---

## 任务二：Route-C source-GT / GT-free 接缝审计（焊死）

**逐问裁决**：
| 问题 | 答案 |
|---|---|
| Q1 selector 由 source GT angle-error 训练？ | **是**（GBR 在 D_cal 用 GT-derived angle error 训练）→ source-supervised |
| Q2 target 上用任何 GT angle-error 标定？ | **leave-dataset/detector：否**（target GT 仅评估，无泄漏）；**within-cell 044/042：用本 cell D_cal GT = calibration/upper-bound，非 deployable** |
| Q3 TTA consistency 是单独 signal 还是喂 selector？ | **两者分清**：Route-C selector 中是 feature；041 standalone consistency proxy 才是 fully-GT-free（但更弱，NRC≈0.77 vs selector≈0.4） |
| Q4 用 source GT 训练权重 → 正确写法 | **source-supervised selector + target GT-free inference**，不得写 fully GT-free |
| Q5 何时可写 "GT-free deployable candidate" | 仅 standalone proxy（无 GT-trained 权重）；Route-C selector 不满足 |

**裁决**：Route-C deployable candidate 统一定义为 **source-supervised reliability-aware selector + target GT-free inference**；**非 fully GT-free / 非 deployable method complete**。无 target GT 泄漏 → **不降级为 upper-bound**，仅措辞更正。

**产物**：`docs/route_c_dataflow_audit.md`

---

## 任务三：diagnose → fix predictive-boundary 分析

**做了什么**：构建 14 unseen-cell 的 cell-level 表（leave-dataset/detector），检验诊断指标能否预测 selector 增益/失效边界。**关键纪律：不得用 D_audit 结果当 predictor 再解释 D_audit gain。**

**核心发现（含循环论证排查）**：
- ❌ **循环（无效）**：Spearman(oracle_gain, retained)=**0.868**（p=0.0001）—— 但 `retained=(NRC_score−NRC_deployed)/oracle_gain`，**oracle_gain 在分母 → 循环**，该相关无效。
- ✅ **非循环检验**：以 `abs_deployed_gain=NRC_score−NRC_deployed`（不含 oracle）为 outcome：Spearman(oracle_abs, abs_gain)=**0.018（p=0.95）** → **oracle 不预测绝对 gain**。
- 无干净 source-side（D_cal）predictor 建立。

**判定**：**predictive boundary 未成立（本轮）** → measure→diagnose→fix 写成**并列结构**，不写 "framework predicts repairability boundaries"；**DOTA #20 仍是 limitation，不是 validation**（DOTA detection-score 已较良校准 NRC 0.70，selector 可改空间小）。

**产物**：`docs/diagnose_predicts_fix_boundary.md` + `measure_fix_v2/reports/diagnose_predicts_fix_boundary.csv` + `..._stats.json`

---

## 任务四：非 PSC detector real TTA 扩展

**做了什么**：复用 shadow farm（未改 dataset），4-GPU world_size=4 real hflip+vflip 推理 + 离线 un-flip 一致性 + selector 对比。**未调参、未追 mAP、未为正结果改 transform**。

**结果（D_audit，within-cell calibration 口径）**：
| cell | family | tta_match | NRC_sizelin | NRC_geo | **NRC_realTTA** | beats_sizelin | beats_geo |
|---|---|---|---|---|---|---|---|
| DIOR-R #61 | RTMDet | 0.996 | 0.501 | 0.339 | **0.331** | True | True |
| FAIR1M #5 | ORCNN | 0.995 | 0.661 | 0.567 | **0.537** | True | True |

- **2 非 PSC family（RTMDet, ORCNN）× 2 dataset（DIOR, FAIR1M），均 beat size-linear 且 beat geometry-only，无失败**。
- real TTA 现覆盖 **6 cells / 3 datasets / 3 families**：PSC（DIOR#22/SODA#23/FAIR1M#24）+ ORCNN（DIOR#3/FAIR1M#5）+ RTMDet（DIOR#61）。
- **诚实边界**：口径为 within-cell calibration（非 deployable leave-*）；**SODA ORCNN #4（304k 推理过慢，~36min）本轮未完成 = next-step（成本，非失败）**；coverage 仍未含全部 family×dataset。

**运行中的工程修复**：RTMDet #61 config 无 `__file__` 问题，直接跑通；FAIR1M #5 首两次失败因 adapter 文件被前序 `pkill` 误清/未生成，第三次补建 adapter 后跑通；SODA ORCNN #4 因 304k 过慢主动切换为 FAIR1M #5。

**产物**：`docs/real_tta_non_psc_extension.md` + `measure_fix_v2/reports/real_tta_nonpsc_046.csv`

---

## 任务五：Track A 机制边界

**边界声明**：
- phase_mod 保留为 **intrinsic signal supports a mechanism candidate**（3/3 PSC cell NRC>1：DIOR 1.156 / SODA 1.117 / FAIR1M 1.121）。
- DOTA #20 = weak-structure negative control，**不调参**（未跑 Track A）。
- Track A 反校准 → 写 intrinsic mechanism candidate（非仅 score-proxy mismatch）；**禁止写 PSC angle head definitively broken**。
- Track A **不决定主线启动、不决定 venue、不恢复 P2、非唯一决定性证据**。

**产物**：`docs/track_a_mechanism_boundary.md`

---

## 任务六：验证

- 新增 `scripts/108_verify_claim_routec_boundary_046.py` → **VERIFIED 18/18**。
- 验证覆盖：五文件存在；主稿无 venue-selling / 无严格独立；Route-C 区分 source-supervised vs target GT-free；predictive boundary 标循环且未成立、DOTA 为 limitation；non-PSC ≥2 family + ≥2 dataset；Track A 机制支线；thresholds/split 未变；git 无大文件；cc 有入口/出口。
- `pytest tests/ -q` → **264 passed**。

---

## 产物路径汇总

**五个主文件**（`docs/`，并镜像 `measure_fix_v2/docs/`）：
1. `docs/claim_language_cleanup_report.md`
2. `docs/route_c_dataflow_audit.md`
3. `docs/diagnose_predicts_fix_boundary.md`
4. `docs/real_tta_non_psc_extension.md`
5. `docs/track_a_mechanism_boundary.md`

**数据/验证**（`measure_fix_v2/reports/`）：
- `diagnose_predicts_fix_boundary.csv`、`diagnose_predicts_fix_boundary_stats.json`
- `real_tta_nonpsc_046.csv`
- `verification_claim_routec_boundary_046.json`

**脚本**：`scripts/108_verify_claim_routec_boundary_046.py`、`measure_fix_v2/scripts/{real_tta_nonpsc_046.py, run_ttanp_046.sh, run_ttanp5_046.sh}`、`measure_fix_v2/configs/ttanp_*.py`

**大文件（scratch，非持久，未进 git）**：`/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds/{DIOR-R_61, FAIR1M-v1.0_5}/{identity,hflip,vflip}.pkl`；shadow farms `/dev/shm/cqc/orientbench/measure_fix_v2_tta/{DIOR-R, FAIR1M-v1.0}/`

**执行回执**：`measure_fix_v2/docs/cc_latest_report.md`；审计日志 `measure_fix_v2/claude_code_and_supervisor.md`

---

## pass / fail / partial 小结

| 项 | 结论 |
|---|---|
| 话术清理 | ✅ 完成（主稿主动过度宣称已除） |
| Route-C 接缝 | ✅ 焊死 = source-supervised + target GT-free inference（非 fully GT-free，无泄漏，不降级） |
| predictive boundary | ⚠️ **未成立**（循环；并列结构；DOTA 仍 limitation） |
| non-PSC real TTA | ✅ 通过（2 family × 2 dataset，无失败；SODA#4 = next-step） |
| Track A 边界 | ✅ 机制支线，非门控 |
| 验证/测试/git | ✅ verifier 18/18；pytest 264；thresholds/split 未变；git 0 大文件 |

**下一步建议**：补 SODA ORCNN #4 等剩余 non-PSC real TTA；构造 D_cal-only 非循环 diagnose predictor 以重新检验 predictive boundary；进入 method 正文写作。**不声称 P3 final / 顶会 ready / PSC angle head 最终证明反校准 / full project complete。**
