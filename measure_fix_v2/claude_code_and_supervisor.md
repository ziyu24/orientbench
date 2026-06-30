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
## '+time.strftime('%Y-%m-%d %H:%M:%S %Z')+' 来源: supervisor (040)

### 输入/指令
token SUPERVISOR_APPROVED_040_P3_DEPLOYABLE_HARDENING。把 039 Deployable partial-pass 加固为 stable-pass 或降级。measure_fix_v2/ 内。

### 行动/结论
- 冻结 deployable_hardening_protocol.md（stable-pass 5 准则）。
- leave-dataset 6/7 pass（DOTA✗）；leave-detector 6/7 pass（PSC↔非PSC，DOTA✗）；均无目标 GT，复用 cached feature tables（无重匹配/无训练）。
- TTA route-C: GT-free local-angle-consistency proxy 在 FAIR1M/DIOR 优于 score-only 且<random（offline 最小版；完整 TTA 推理为 next-step limitation）。
- DOTA #20 failure = 弱内在结构（oracle_gain 0.155 四 PSC 最低；masked NRC 0.84 未显著反校准），非样本量/分布 shift/过拟合 → documented limitation。
- 裁决: STABLE-PASS（with DOTA documented limitation）。准则①85.7%(非DOTA 100%)，②非DOTA mean retained 0.645（all-cells 0.481 仅因 DOTA，差0.02 提请确认），③LD/LDET 两类 stable 无 fail，④DOTA 诊断标局限，⑤无目标 GT。
- Track A 可有条件准备本轮未启动；支持 P3 method development（边界: 仍 source-trained / route-C 仅 offline 弱版；不声称完成/顶会级别）。

### 产物路径
measure_fix_v2/docs/{deployable_hardening_protocol,p3_deployable_hardening_report,cc_latest_report}.md;
measure_fix_v2/reports/{leave_dataset_hardening_040,leave_detector_hardening_040,tta_proxy_hardening_040,dota20_failure_analysis_040,hardening_summary_040,verification_deployable_hardening_040}.*;
measure_fix_v2/scripts/{hardening_040,tta_proxy_040,verify_deployable_hardening_040}.py。

### pass/fail/partial
Deployable hardening = STABLE-PASS (with DOTA documented limitation)。未触发停止条件。

### 下一步建议
P3 method development（巩固 route-C TTA 推理 proxy + 扩 leave 覆盖 + 处理弱结构 cell）；Track A 待批准作机制支线。venue 决定交合作者。
## '+time.strftime('%Y-%m-%d %H:%M:%S %Z')+' 来源: supervisor (041)

### 输入/指令
token SUPERVISOR_APPROVED_041_ROUTE_C_TTA_PROXY_DEPLOYABLE_CHECK。验证 Route-C GT-free deployable proxy。measure_fix_v2/。

### 行动/结论
- 冻结 route_c_tta_proxy_protocol.md。
- real flip-TTA 推理: 写 4-GPU hflip adapter(tta_hflip_dior3.py)但 blocked(DIOR annfiles_dotaformat/test 空; populate 会改 read-only dataset, 禁止) → documented next-step(tta_proxy_manifest_041.json), 未改 dataset。
- 实际 Route-C 信号 = GT-free offline local-angle-consistency proxy(6 cells, features_v2, 无 GT)。
- Route-C 对照(无目标 GT, source-trained): non-DOTA 10/10 优于 score+ar+size linear; GT-free consistency feature 8/10 优于 geometry-only; mean retained 0.718/median 0.734(>040 的 0.645)。
- DOTA #20 negative control: 加 consistency 后 leave-dataset 转 pass(0.59 beats sizelin), leave-detector 仍弱(弱结构 oracle_gain 0.155); 不调参。
- 裁决: Route-C = STABLE-PASS。诚实边界: consistency 为 offline proxy(非 real TTA, blocked); selector 训练仍用 source GT(calibration); target 无 GT = deployable。未声称 P3 最终完成/顶会级别。

### 产物路径
measure_fix_v2/docs/{route_c_tta_proxy_protocol,route_c_tta_proxy_report,cc_latest_report}.md;
measure_fix_v2/reports/{route_c_tta_proxy_results_041,tta_proxy_features_041,route_c_tta_proxy_results_041(md),dota20_negative_control_041(md),tta_proxy_manifest_041,route_c_summary_041,verification_route_c_tta_proxy_041}.*;
measure_fix_v2/configs/tta_hflip_dior3.py; measure_fix_v2/artifacts/features_v2/*.jsonl(gitignored); measure_fix_v2/scripts/{enrich_features_041,route_c_eval_041,verify_route_c_tta_proxy_041}.py。

### pass/fail/partial
Route-C = STABLE-PASS。未触发停止条件。

### 下一步建议
real flip/rotation TTA(建 scratch annfile 镜像, 不改 dataset); 扩 leave 覆盖 + few-shot calibration; Track A 待批准作机制支线; venue 交合作者。
## '+time.strftime('%Y-%m-%d %H:%M:%S %Z')+' 来源: supervisor (042)

### 输入/指令
token SUPERVISOR_APPROVED_042_REAL_TTA_DEPLOYABILITY_PROOF。real TTA deployability proof。measure_fix_v2/。原 dataset 不改。

### 行动/结论
- 修复 041 real-TTA blocker = shadow farm（/dev/shm/.../measure_fix_v2_tta/DIOR-R: 5863 image symlinks + 由 GT 生成 annfiles）；原 dataset 0 文件改动（find -newer=0）。
- transform sanity: hflip/vflip/rot90 round-trip IoU=1.0。
- real TTA 推理（4-GPU world_size=4, DumpDetResults→scratch, bare torchrun）: DIOR ORCNN #3 + PSC #22 各 identity+hflip+vflip 成功; 坐标 un-flip(cx->W-cx, theta->-theta) 经验确认; consistency match_frac 0.99-1.0, mean disagree ~1.4-2deg。未成功: #10 lsknet(OrientedRCNN registry, 3 次) + SODA/FAIR1M(未建 farm)=next-step。
- real TTA selector(leave-detector within DIOR, 无目标 GT): 2/2 显著优于 score+ar+size linear(#3 0.391, #22 0.419), realTTA 优于 geometry-only on #3, marginal on #22, mean retained 0.717; 方向与 041 offline proxy 一致 → real TTA 证实 offline 结论。
- 裁决: real TTA = STABLE-PASS (on tested cells; coverage limited to 2 DIOR cells). 区分 offline proxy vs real TTA; 未声称 P3 最终完成/顶会 ready。

### 产物路径
measure_fix_v2/docs/{real_tta_deployability_report,cc_latest_report}.md;
measure_fix_v2/reports/{tta_transform_sanity_042,real_tta_inference_manifest_042,real_tta_feature_table_042,real_tta_selector_results_042,dior_farm_manifest_042,verification_real_tta_deployability_042}.*;
measure_fix_v2/configs/tta_*.py(adapters); measure_fix_v2/artifacts/features_real_tta/*.jsonl(gitignored); shadow farm /dev/shm/.../measure_fix_v2_tta/(scratch); scripts/{build_dior_farm_042,extract_real_tta_042,real_tta_selector_042,run_tta_driver_042.sh,verify_real_tta_deployability_042}.py。

### pass/fail/partial
real TTA = STABLE-PASS (tested cells; coverage limited). 未触发停止条件。

### 下一步建议
扩 real TTA coverage(修 lsknet registry; SODA/FAIR1M shadow farm); few-shot calibration; Track A 待批准。venue 交合作者。
## '+time.strftime('%Y-%m-%d %H:%M:%S %Z')+' 来源: supervisor (043)

### 输入/指令
token SUPERVISOR_APPROVED_043_TRACK_A_PSC_MECHANISM_DIAGNOSTIC。Track A PSC 机制支线(非门控 P3)。measure_fix_v2/。原 dataset 不改。

### 行动/结论
- 冻结 track_a_psc_mechanism_protocol.md。
- instrumentation: InstrumentedAngleBranchRetinaHead 子类(track_a_pkg)把 PSC phase_mod(phase_cos^2+phase_sin^2, first freq=intrinsic 角度码置信)经 NMS 附 pred_instances 导出; phase_mod dump 成功(range 0.18-2.51)。entropy/margin: PSC 连续 coder 无 softmax → unavailable_with_evidence。
- shadow farms(未改 dataset): DIOR(042), FAIR1M(3896 symlinks+dummy-class annfiles 绕 space-class), SODA(原 val_tiled populated read-only)。4-GPU world_size=4。
- Track A/B/C(masked ar>=1.6, D_audit): Track A(phase_mod) 3/3 PSC cell 显著 NRC>1: DIOR#22 1.156[1.11,1.19], SODA#23 1.117[1.11,1.13], FAIR1M#24 1.121[1.08,1.16]; Track B(score) 0.56-0.98; Track C(geometry) 0.36-0.52(最佳)。
- 机制裁决: PSC intrinsic angle-coder miscalibration mechanism candidate SUPPORTED(angle 码自身置信反校准, 非仅 score-proxy mismatch)。克制: phase_mod 一 intrinsic 信号, candidate 非定论。
- DOTA #20: 未跑 Track A(未建 farm, negative control, 未调参)=next-step。real TTA coverage: farms 已建可复用, 本轮未跑额外=next-step。
- Track A 不门控 P3; P3 继续(G2''/Deployable/Route-C 支撑)。未声称 P3 最终完成/顶会 ready。

### 产物路径
measure_fix_v2/docs/{track_a_psc_mechanism_protocol,track_a_psc_mechanism_report,measure_fix_route_status,cc_latest_report}.md;
measure_fix_v2/reports/{track_abc_results_043,track_a_dump_manifest_043,track_a_schema_sample_043,verification_track_a_psc_mechanism_043}.*;
measure_fix_v2/track_a_pkg/(instrumented head); measure_fix_v2/configs/tracka_*.py; scripts/{track_abc_043,build_farm_general_043,verify_track_a_psc_mechanism_043}.py;
dumps /dev/shm/cqc/orientbench/measure_fix_v2/track_a/(scratch); farms /dev/shm/.../measure_fix_v2_tta/(scratch)。

### pass/fail/partial
Track A = intrinsic angle-coder miscalibration mechanism candidate SUPPORTED(3/3 PSC NRC>1)。未触发停止条件。

### 下一步建议
扩 Track A 到 DOTA #20 negative control + 更多 intrinsic 信号; real TTA 复用 farms 扩 SODA/FAIR1M; controlled angle-head 实验需新批准。
