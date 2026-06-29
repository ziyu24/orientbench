## '+time.strftime('%Y-%m-%d %H:%M:%S %Z')+' 来源: supervisor (039)

### 输入/指令
token SUPERVISOR_APPROVED_039_V2_MEASURE_FIX_G2_DOUBLE_PRIME。新阶段 v2 measure->fix；建独立 measure_fix_v2/。
读取新文件: CLAUDE.md(=CLAUDE (8).md, 已装为当前 CLAUDE.md, .bak 为旧版) + 项目执行文件_v2_measure_fix.md → 复制到 measure_fix_v2/docs/input/。

### 行动/结论
- G2_double_prime 协议冻结(g2_double_prime_protocol.md)。实验: 7 cells(4 PSC+3 非PSC sanity), ar>=1.6 primary(+1.3/2.0), fixed size bins(log sqrt area 三分位), 4 selector(score-only/score+ar/score+ar+size linear/nonlinear GBM), continuous angle-error label, D_cal训练 D_audit判定。
- G2_double_prime = PASS: 固定 size bin 内 nonlinear 显著优于 score+ar+size linear(21/21 primary, CI>0; ar1.3 20/21, ar2.0 21/21) → 非 box-size prior, orientation-specific 非线性几何(GV imp 0.2-0.25)。
- Deployable = PARTIAL-PASS: leave-dataset+leave-detector 无目标GT, 9/11 unseen evals nonlinear 显著>score-only 且>size-linear, retain ~69% oracle gain; 唯一例外 DOTA #20(结构最弱)。
- P1 硬债修订建议完成(p1_hard_debt_patch_notes.md)。
- 严格区分: G2DP upper-bound(用 D_cal GT) vs Deployable(无目标 GT)。未声称 P3 顶会级别。

### 产物路径
measure_fix_v2/docs/{g2_double_prime_protocol,g2_double_prime_and_deployable_report,p1_hard_debt_patch_notes,cc_latest_report}.md;
measure_fix_v2/reports/{g2_double_prime_results_039,deployable_results_039,v2_feature_persistence_manifest_039,verification_measure_fix_v2_039}.*;
measure_fix_v2/artifacts/features/*.jsonl(gitignored, persisted+sha256); measure_fix_v2/scripts/*.py。

### pass/fail/partial
G2_double_prime=PASS; Deployable=PARTIAL-PASS。未触发停止条件。

### 下一步建议
扩 leave-dataset/detector + 路线C(TTA proxy) 巩固 deployable; 之后再考虑 Track A forward dump(本轮未启动); venue 决定交合作者。
