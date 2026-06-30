# Track A PSC Mechanism Diagnostic 协议（跑前冻结，043）

> SUPERVISOR_APPROVED_043_TRACK_A_PSC_MECHANISM_DIAGNOSTIC · measure_fix_v2/ · P1 frozen 只读 · 不改 thresholds/split · 不训练 detector · 不补 full matrix · 不恢复 P2 · DOTA #20 不调参。
> **Track A 仅解释机制，不再门控 P3 是否成立。**

## 0. 目标
对 PSC 做 instrumented forward dump，提取 intrinsic angle uncertainty，判定 PSC 反校准是 **angle-coder intrinsic** 还是 **detection-score proxy mismatch**。

## 1. PSC cells
DOTA #20、DIOR #22、FAIR1M #24、SODA #23。优先有 shadow farm 的 cell；farm 复用 042 pattern（不改原 dataset）。

## 2. 需 dump 的信号
- **Track A intrinsic**：PSC phase_mod = phase_cos²+phase_sin²（first freq；高=角度码自洽/置信，低=歧义/不确定）。这是 PSCCoder.decode 内部量，经 instrumented head（InstrumentedAngleBranchRetinaHead，子类，附 phase_mod 到 pred_instances 过 NMS）导出。
- 同时记录：detection score、pred OBB、matched GT、angle error。
- 若某信号不存在 → **unavailable_with_evidence**，不伪造。

## 3. Track A/B/C 定义
- A：phase_mod 作 selection（高 phase_mod=可靠，selection score=phase_mod）。
- B：detection-score 作 selection。
- C：geometry-aware selector（040/041）。

## 4. split
- P1 frozen assign_split；selector 训练只 D_cal，判定只 D_audit；不用目标 GT 调参。Track A 是 detector 原生信号（无需训练），直接在 D_audit 评估其 NRC。

## 5. 指标
NRC-AUC、AURC、Risk@70/90、p90/p95/p99、bootstrap CI、per-cell、PSC pooled、DOTA #20 negative control。

## 6. 判定规则
- **若 Track A 也 NRC>1 且 CI 支持** → 可写 **PSC intrinsic angle-coder mechanism candidate**（反校准在 angle head 内）。
- **若 Track A 正常（NRC<1）而 Track B 反校准（NRC>1）** → **detection-score proxy mismatch**（问题在用 score 选角度，非 angle head 本身）。
- **若 Track A 无法提取** → instrumentation limitation，不影响 P3 主线。

## 7. 停止条件
- 不得为 DOTA #20 调参；不得把 Track A 写成 P3 主门控；想改 frozen thresholds/split、训练 detector、恢复 P2 → 停手回报。

## 8. 持久化
- 大文件（dump pkl）→ /dev/shm/cqc/orientbench/measure_fix_v2/track_a/；项目只存 manifest/sha256/schema/summary/sample rows。
