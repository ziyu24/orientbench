# P1 Scientific-Validity 决策包（合作者版）

> 供合作者快速判断 P1 是否进入顶刊写作 / 是否启动 PSC angle-head control / 是否把 cross-dataset reliability 推进为 P3。
> 范围：DOTA train/val（非 trainval/test，不追公开 mAP）+ cross-dataset exploratory。无新训练。thresholds 冻结 b7c4e649。

## 1. P1 当前结论
- current approved scope 完成并冻结；full project 未完成（partial，剩余为有证据的 coverage blocker）。
- P1 测到的可靠性问题经 v2 审计**判定为真实、独立、值得顶刊继续推进**（克制）。

## 2. NRC 独立于 mAP（证据）
- 23 cells：Spearman(NRC, mAP) = **-0.046**（p=0.84）；Pearson -0.26。
- 控 dataset+detector-family 偏相关 = **-0.005**（完全独立）。
- mean rank distance NRC vs mAP = 7.83/23。
- → NRC **不是 mAP 换皮**，提供 accuracy 看不到的可靠性维度。

## 3. 尾部风险（证据）
- unmasked angle-error **p99 ≈ 89-90°**（灾难性，near-square 朝向歧义驱动）。
- masked（去 near-square）**p99 ≈ 10-16°**（仍非平凡）。
- → orientation reliability 在 aspect-ratio→1 处**断崖**；reliability cliff 真实。

## 4. PSC 反校准（证据）
- PSC 在 **DOTA(1.06) / FAIR1M(1.08) / SODA(1.26) NRC>1**（唯一系统性反校准 family；DIOR 0.55 例外）。
- DOTA/SODA **mAP 不弱**（0.556/0.599）仍反校准 → accuracy 看不到的缺陷。
- 机制候选：PSC 相位置信不随角度回归质量单调（详见 psc_miscalibration_mechanism_note.md）。

## 5. selection score 三轨
- intrinsic（原生角度不确定性）/ unified-proxy（detection-score 等，公平横比）/ post-hoc upper-bound（D_cal→D_audit）。
- 当前 cross-detector NRC = **Track B (detection-score proxy)**，非 intrinsic 排名。R1-R8/GV/NRC 定义未改。

## 6. persistent artifacts 状态
- key cells（host+PSC+ARS-DETR DIOR+Strip DIOR+reps，12 artifacts ~2.6GB）已持久化 `outputs/persistent_artifacts/orientbench_v2/`（gitignored）+ manifest（sha256/path/can_recompute）。/dev/shm 非持久。

## 7. 不能宣称的内容
- ❌ full project complete / all datasets covered / 9-detector matrix complete。
- ❌ C1 genuine physical multi-view solved；❌ A4 cross-host causal proved。
- ❌ ARS-DETR = RHINO；❌ 任何 non-DOTA cell = formal gate；❌ DOTA SOTA/公开 mAP。

## 8. 需合作者裁决（见 collaborator_p1_decision_form.md 的 D1-D7）
- 是否接受 v2 作为顶刊依据；是否启动 PSC angle-head control；是否 P3 formalization；是否补剩余 blocked cells；是否冻结 current scope；是否开始论文主文；是否要额外图表。
