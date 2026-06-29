👇👇👇👇👇👇

# OrientBench v2 — 041 Route-C GT-free Deployable Proxy 完成

- **041 完成**。未改 thresholds(b7c4e649)/P1 split；未训练 detector；未补 full matrix；未恢复 P2；未启动 Track A；DOTA #20 未调参。
- **主报告（唯一人读）**：`measure_fix_v2/docs/route_c_tta_proxy_report.md`

## Route-C 裁决：**STABLE-PASS**
- non-DOTA **10/10 优于 score+ar+size linear**；GT-free consistency feature **8/10 优于 geometry-only**（提供额外可部署增益）；mean retained oracle gain **0.718**（>040 的 0.645）；全程无目标 GT。

## TTA cells / 信号
- 实际信号 = **GT-free offline local-angle-consistency proxy**（6 cells，augmentation-free，无 GT）。
- **real flip-TTA 推理 = blocked**（DIOR annfiles_dotaformat/test 为空，populate 会改 read-only dataset；已写 4-GPU hflip adapter + 记录 blocker）→ documented next-step。

## 关键指标
- SODA #23 leave-dataset：score 0.98→sizelin 0.68→geo 0.50→**Route-C 0.46**（retained 0.85）。DIOR #22：sizelin 0.92→**Route-C 0.41**。

## DOTA #20 解释
- weak-structure / low-oracle-gain（0.155，未显著反校准）**negative control**；加 consistency 后 leave-dataset 由 fail 转 pass（0.59），leave-detector 仍弱（符合预期）。**不调参**。

## 是否允许 Track A
- **可有条件准备**，本轮未启动；待监督员批准作机制支线（非阻塞）。

## 是否允许 P3 method development
- **支持继续**（deployable reliability-aware selector）。边界：consistency 为 offline proxy（非 real TTA）；selector 训练仍用 source GT（calibration）；target 无 GT = deployable 方向。**不声称 P3 最终完成/顶会级别**。

## 验证/test/git
- verifier `verify_route_c_tta_proxy_041` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件（artifacts/logs/configs-TTA gitignored）。

👆👆👆👆👆👆
