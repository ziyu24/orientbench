# Route-C GT-free Deployable Proxy 报告 (041)

> SUPERVISOR_APPROVED_041_ROUTE_C_TTA_PROXY_DEPLOYABLE_CHECK · measure_fix_v2/ 独立 · P1 frozen 只读 · 未改 thresholds(b7c4e649)/D_cal-D_audit · 未训练 detector · 未补 full matrix · 未恢复 P2 · 未启动 Track A · DOTA #20 未作调参目标。
> 唯一人读主报告。

## 1. 040 回顾
- Deployable hardening = STABLE-PASS（with DOTA #20 documented limitation）。非 DOTA 12/12 beat size-linear，retained ~0.65，无目标 GT。本轮验证 **Route-C：GT-free consistency proxy 能否支撑 deployable selector**。

## 2. 为什么 DOTA #20 不是主失败
- DOTA #20 PSC masked NRC 0.84（未显著反校准）、within-target oracle_gain 0.155（四 PSC 最低）= **low-gain / weak-structure negative control**。可靠性方法在"几无结构可学"的 cell 上提升有限是预期正确行为。**不调参**。详见 dota20_negative_control_041.md。

## 3. Route-C 协议
见 measure_fix_v2/docs/route_c_tta_proxy_protocol.md。selector 输入**不依赖目标域 GT angle-error**；consistency 信号 GT-free；source-trained，target D_audit 只评估。

## 4. TTA features
- **设计**：identity + hflip（un-flip: cx→W−cx, θ→−θ）+ vflip + 90°rot(near-square unsupported 不硬用)。
- **real flip-TTA 推理 = blocked**：DOTADataset 需 annfiles 枚举图像，DIOR `annfiles_dotaformat/test/` 为空；populate 会改 read-only dataset 目录（禁止）。已写 adapter（measure_fix_v2/configs/tta_hflip_dior3.py，4-GPU world_size=4，DumpDetResults→scratch）+ 记录 blocker（tta_proxy_manifest_041.json）→ **documented next-step**。
- **实际使用 = GT-free offline local-angle-consistency proxy**（augmentation-free：同图邻近预测 canonical 角度离散度，半径 200px，**不用任何 GT**），6 cells 全覆盖（features_v2）。

## 5. 四类 selector 对比（D_audit，无目标 GT）
- baseline1 score-only；baseline2 score+ar+size linear；baseline3 geometry-aware（040 selector）；**Route-C = geometry + GT-free consistency**。
- 完整 per-cell 表见 route_c_tta_proxy_results_041.md。代表（leave-dataset）：
  - SODA #23：score 0.98 → sizelin 0.68 → geo 0.50 → **Route-C 0.46**（retained 0.85）。
  - DIOR #22：sizelin 0.92 → geo 0.45 → **Route-C 0.41**（retained 0.71）。
  - FAIR1M #24：sizelin 0.76 → **Route-C 0.61**（geo 0.61，consistency 此 cell 中性，retained 0.76）。

## 6. non-DOTA summary
- **routeC 优于 score+ar+size linear：10/10（100%）**。
- **GT-free consistency feature 优于 geometry-only：8/10** → consistency 提供 geometry 之外的可部署增益。
- **mean retained oracle gain 0.718 / median 0.734**（高于 040 geometry-only 的 0.645）。

## 7. DOTA #20 negative control
- leave-dataset：Route-C 0.59 **beats sizelin**（consistency 改善了 040 失败的 DOTA leave-dataset）；leave-detector nonpsc→psc：仍 0.665 不及 sizelin（弱结构，符合预期）。标 documented negative control。

## 8. bootstrap CI
- 每 cell paired bootstrap 400×。DELTA(sizelin − routeC) non-DOTA 全部 CI>0（10/10）；DELTA(geo − routeC) 8/10 CI>0。详见 results csv（ci_sz_lo / ci_geo_lo）。

## 9. Route-C 裁决：**STABLE-PASS**
- Route-C 在 non-DOTA majority（实为全部 10/10）显著优于 score+ar+size linear；保留 oracle gain 主要部分（mean 0.718）；GT-free consistency feature 在 8/10 提供额外增益；DOTA #20 作 documented negative control；**不需目标域 GT angle-error 标定**。
- **诚实边界**：consistency 信号为 **offline local-angle-consistency proxy（GT-free）**，**非** real flip/rotation TTA 推理（后者被 annfile plumbing 阻塞，为 documented next-step）。selector 训练仍用 source GT（calibration setting）；leave-dataset/detector 的 target 无 GT = deployable 方向。

## 10. 是否允许下一阶段 Track A forward dump
- **前置满足，可有条件准备**；本轮**未启动**，建议待监督员批准作机制支线（非阻塞 P3）。

## 11. 是否允许 P3 method development 继续
- **支持继续**（deployable reliability-aware selector）：跨 dataset/detector 无目标 GT 时稳定优于 baselines，GT-free consistency 提供增益。
- **不得逾越**：未声称 P3 最终方法完成 / 顶会级别；严格区分 **upper-bound/calibration（用 source GT 训练）** 与 **deployable（target 无 GT）**；real-TTA 推理 proxy 仍是 next-step。

## 12. 下一步建议
- 巩固 real flip/rotation TTA：建 scratch annfile 镜像（不改原 dataset）→ 跑 hflip/vflip 推理 → 真 TTA consistency 替代 offline proxy。
- 扩 leave-dataset/detector 覆盖 + few-shot calibration 对比。
- （待批准）Track A forward dump 作机制支线。venue 决定交合作者。
