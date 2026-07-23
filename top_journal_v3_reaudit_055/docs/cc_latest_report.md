👇👇👇👇👇👇

# 056 执行回执：从 re-audit 结果重写正式中文论文

**056 状态：完成。** 基于已确认可信的 re-audit 结果重写正式中文论文，未新增实验、未训练、未推理、未改 thresholds(b7c4e649)/D_cal-D_audit、未补 full matrix、未追公开 mAP。

## 正式中文论文路径
`top_journal_v3_reaudit_055/docs/orientation_reliability_paper_zh_reaudited.md`
（配套：`coauthor_review_note_056.md` 合作者审稿说明；`final_claim_ledger_reaudited_056.md` claim ledger）

## 论文身份
**Orientation Reliability：面向旋转目标检测的朝向可靠性测量协议与保形风险控制。**
非 full benchmark；非 detector SOTA；非 P3 final method；非顶会 ready；非 full project complete。

## P1/P2/P3/P4/P5 在文中的定位
- **P1（第 5 节）动机**：precise-pass——约束扰动（保持 rIoU>0.5，~35° 角扰动）下 mAP@0.5 各 ar-bin Δ=0，朝向误差 +约30°、AP75 塌陷；受 ar 与 IoU 阈值门控。
- **P2（第 6 节）主贡献/脊柱**：有限样本保形朝向风险控制；严格预算下带弃权 + Hoeffding 界；打分菜单确立“保形层 + 几何选择器”默认（几何选择器 6/6 最高覆盖）；shift 审计如实报告退化。
- **P4（第 7 节）**：并入 P2 打分菜单；θ→2θ 圆统计 TTA 基线；几何选择器 masked NRC 6/6 显著优于检测置信度、5/6 优于 TTA；checkpoint-ensemble unavailable。
- **P3（第 8 节）机制候选与边界**：检测置信度反校准（unmasked）作废；masked 下检测置信度校准、intrinsic phase_mod 反校准 = 机制候选（非定论）；DOTA#20 invalid_pending。
- **P5（第 9 节 + 附录）边界**：反事实 angle-induced rIoU drop，方向对但微弱（~0.3% IoU），进附录，不作 utility 主张。

## 是否清除了 Codex 错误
是。正文已彻底不再使用 053/054 被 superseded 的 unmasked NRC headline（作为 pooling artifact 记入附录 E）；DOTA#20 残缺 artifact 排除主表（invalid_pending）；均匀 30° 扰动由约束扰动替代；phase_mod 限定为机制候选；下游不写成功。

## 是否建议交合作者审稿
**建议交合作者审稿。** 已附一页审稿说明，标明可审点、不可回退点、待补项（重点：P2 保证措辞的克制度、机制候选语气、相关工作真实文献补齐）。

## 仍缺什么
更多 provenance-clean cell 在冻结 masked 口径下重算；受控 angle-coder 实验（phase_mod 机制候选→证据）；角度主导的下游任务（heading）；更紧的迁移保证；DOTA full-val provenance dump；相关工作真实文献。

## 验证 / 测试 / git
- `scripts/verify_reaudited_paper_056.py` = **28/28 PASS**（论文非项目报告、含 P1 precise-pass / P2 主贡献 / P4 打分菜单 / P3 机制候选 / P5 边界 / retained-superseded；无 top-venue/CVPR/ICCV/TPAMI 正向主张；DOTA#20 非 validation；phase_mod 非定论；下游非成功；unmasked NRC 仅作 artifact；去项目化）。
- `pytest tests/test_bench_core0.py` = **17 passed**。
- thresholds.yaml sha256 = b7c4e649…（未变）；D_cal/D_audit protected diff = clean；git 无 >100MB tracked。

👆👆👆👆👆👆
