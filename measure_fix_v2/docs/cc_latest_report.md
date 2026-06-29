👇👇👇👇👇👇

# OrientBench v2 — 042 Real-TTA Deployability Proof 完成

- **042 完成**。原始 dataset **未修改**；未改 thresholds(b7c4e649)/P1 split；未训练 detector；未补 full matrix；未恢复 P2；未启动 Track A；DOTA #20 未调参。
- **主报告（唯一人读）**：`measure_fix_v2/docs/real_tta_deployability_report.md`

## real TTA 裁决：**STABLE-PASS（on tested cells；coverage limited）**
- real flip 推理（hflip+vflip，shadow farm 修复 annfile blocker，未改 dataset）→ real TTA consistency feature。
- selector（leave-detector within DIOR，无目标 GT）：**2/2 cells 显著优于 score+ar+size linear**（DIOR ORCNN #3 0.391、PSC #22 0.419），mean retained 0.717；**方向与 041 offline proxy 一致** → real TTA 证实 offline proxy 结论。

## 成功 TTA cells
- DIOR ORCNN #3、DIOR PSC #22（identity+hflip+vflip，4-GPU world_size=4）。未成功：DIOR LSKNet #10（registry 阻塞，3 次）、SODA/FAIR1M real-TTA（未建 farm）= documented next-step。

## transform sanity 结果
- hflip/vflip/rot90 round-trip IoU=**1.0000**（inverse 几何可靠）。

## real TTA vs offline proxy 结论
- 一致：real TTA Route-C 优于 size-linear；consistency 在 ORCNN #3 优于 geometry-only、PSC #22 边际。real TTA（非 offline proxy）已跑通。

## DOTA #20 状态
- weak-structure negative control，本轮 real TTA 未跑、**未调参**；延续 040/041 诊断。

## 是否允许 Track A
- 可有条件准备，本轮未启动；待批准作机制支线（非阻塞）。

## 是否允许 P3 method development
- **支持继续**。边界：real TTA coverage 限 2 DIOR cells；selector 训练仍用 source GT（calibration），target 无 GT（deployable）。**不声称 P3 最终完成/顶会 ready**。

## 验证/test/git
- verifier `verify_real_tta_deployability_042` → 见下；pytest 全过；原 dataset 0 文件改动；thresholds/split 未变；git 0 大文件。

👆👆👆👆👆👆
