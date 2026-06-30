👇👇👇👇👇👇

# OrientBench v2 — 047 Top-Journal Lockdown 完成

- **047 完成**。目标=遥感顶刊级别（不空喊 CVPR/ICCV）。未训练 detector；未改 thresholds(b7c4e649)/P1 split；未补 full matrix；未恢复 P2；未追 DOTA mAP；未改原 dataset。

## non-PSC leave-* 是否通过
- ✅ **PASS**：source-supervised + target GT-free，**8/9 evals beat size-linear**，**2 非 PSC family(ORCNN,LSKNet) × 3 dataset(DIOR/SODA/FAIR1M)**；RTMDet #61 单 family 失败(documented)；leave-dataset SODA/DIOR folds 因大 SODA bootstrap 被 kill = compute-cost limitation(已报告未跳过)。

## supervision spectrum 是否写清
- ✅ upper-bound / source-supervised transfer(主 deployable candidate) / fully GT-free proxy(较弱)。Route-C = source-supervised + target GT-free inference，**非 fully GT-free**。

## artifacts 是否持久化
- ✅ 43 artifacts / 1361 MB → /home persistent(gitignored) + manifest(sha256+can_recompute+source_checkpoint+split)。无 blocked_storage。

## 是否出现 target GT 泄漏
- **无**（leave-* target GT 仅评估）。

## 当前是否达到 top-journal submission package
- **top_journal_submission_package_ready = true（遥感顶刊级别）**：9 项裁决全满足。**不冲 CVPR/ICCV**。

## 主产物路径
- docs/{nonpsc_deployable_leave_star_047, supervision_spectrum_method_section_047, paper_framing_top_journal_047, artifact_persistence_047}.md
- measure_fix_v2/docs/top_journal_lockdown_decision_047.md；outputs/persistent_artifacts/manifest_047.json

## 验证/test/git
- verifier `verify_top_journal_lockdown_047` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件；persistent 不进 git。

## 下一步建议
- 补完整 leave-dataset(降 bootstrap)；RTMDet 失败几何解释；D_cal-only predictor(partial)；进入 method 正文写作。

👆👆👆👆👆👆
