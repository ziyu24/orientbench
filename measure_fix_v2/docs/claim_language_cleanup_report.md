# Claim Language Cleanup Report (046)

> 2026-06-30 14:44:40 CST。SUPERVISOR_APPROVED_046。清除自我推销式/过度宣称措辞；不改 frozen 历史事实。

## 修正项

### 1. 删除/改写"顶刊点 / 顶会 ready / top venue ready"
- measure_fix_v2/docs/orientation_reliability_measure_diagnose_fix_draft.md：合作者审核摘要 "顶刊点在哪里" → 改 **"科学贡献点（克制，不绑定 venue）"**；删除 venue-selling 语气。
- cc_latest_report 中 "顶刊点在哪里" 段（046 cc 重写时移除）。
- 历史报告（039-044、P1 035）中 "不声称顶会 ready / 为什么还不够 CVPR/ICCV" 为**负向/边界**表述，保留（非自我推销，且是 forbidden-list / 边界说明）。
- governance input/（CLAUDE (8).md、项目执行文件）列 "NRC 完全独立"/"顶会 ready" 为 **forbidden claims**，不动（正确）。

### 2. "NRC 独立于 accuracy" → 改口径
- 统一为：**在当前可比设置中，NRC 提供 mAP 之外的 reliability signal；不主张严格独立**。
- 主稿 §合作者摘要、§10 结论已改（"NRC 独立性" → "提供 mAP 之外的 reliability signal（不主张严格独立）"）。
- §4 已是 "未检出显著相关；提供不同于 accuracy 的 reliability signal"（保留）。

### 3. "P3 deployable method" → "deployable candidate / GT-free route under evaluation"
- 主稿与 method spec 已用 **reliability-aware selector candidate**；本轮进一步明确 **source-supervised + target GT-free inference**（见 route_c_dataflow_audit）。**未发现**正向 "deployable method complete" 表述。

### 4. "PSC angle head proven broken" → 禁止
- 全文仅写 **phase_mod intrinsic signal supports a mechanism candidate**；"definitively/最终证明反校准" 仅出现在 forbidden-list（负向），保留。

## 结论
- 主稿活跃过度宣称已清除（顶刊点、NRC 独立于）。historical/forbidden-list 负向表述保留。Route-C "GT-free" 口径在 route_c_dataflow_audit 焊死为 source-supervised + target GT-free inference。
