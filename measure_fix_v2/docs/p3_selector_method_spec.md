# P3 Reliability-Aware Orientation Selector — Method Spec

> measure_fix_v2 · 方法定义稿（克制）。当前 selector 为 **reliability-aware selector candidate**，**非** final production method，**非** detector retraining。

## 1. Problem definition
给定 OBB detector 在图像上的检测集合 {(box_i, score_i)}，每个 box 含朝向 θ_i。目标：学一个 **orientation reliability selector** s(·)，对每个检测输出可靠性分数，使按 s 降序的 selective risk-coverage（朝向误差）尽量低——即在高 coverage 下保留朝向可信的预测、滤除不可信的。**不改 detector，不重训**。

## 2. Input features（部署期可得，不含目标 GT）
- detection score；
- box geometry：log aspect-ratio、log sqrt(area)、width、height；
- GV-obliquity（gv_obb_needed = 1 − OBB_area/HBB_area，朝向相关几何）；
- **TTA consistency**（可选，GT-free）：identity 与 hflip/vflip 预测 un-flip 后的角度一致性；
- （分析用，不作部署主特征）detector family / class。

## 3. Track A / B / C 区分
- **Track A intrinsic**：detector 原生角度置信（PSC = phase_mod 角度码模长）。**机制诊断用**；本项目 phase_mod 反校准（NRC>1）→ 不宜作 selector。
- **Track B detection-score proxy**：用 detection score 作 selection。简单基线；在 PSC 上反校准/弱。
- **Track C geometry-aware selector**：非线性（GBM）拟合 geometry(+consistency) → 预测 angle risk，selection = −risk。**本方法主体**（NRC 最佳 0.36-0.52）。

## 4. Deployable Route-C feature
- 在 Track C 特征基础上加 **GT-free TTA consistency**（real hflip/vflip 角度一致性 或 offline local-angle-consistency）。consistency 不依赖目标 GT → 支持 leave-dataset / leave-detector 部署。

## 5. Training protocol
- selector 在 **D_cal** 上用 source GT angle-error 作标签训练（GradientBoosting，n_estimators=200/depth=3/lr=0.05/subsample=0.8，seed=0）；**判定只在 D_audit**，不用目标域 GT 调参。
- **D_cal / D_audit**：P1 frozen 确定性 md5 split（互斥，未改）。

## 6. leave-dataset / leave-detector
- deployability 通过 leave-one-dataset-out / leave-one-detector-out 评估：selector 训练于 source cells，应用于 unseen target（target 无 GT angle-error 标定）。040/041/042 显示非 DOTA 多数 cell 仍优于 score+ar+size linear。

## 7. real TTA usage
- TTA consistency 由 identity+hflip+vflip 真实推理（shadow farm，不改 dataset）un-flip 后角度一致性计算；inverse 几何经 round-trip IoU=1.0 sanity。042/044 在 DIOR/SODA/FAIR1M 多 cell 验证。

## 8. inference-time pipeline
1. detector 推理 → {box, score}；（可选）hflip/vflip TTA 推理 → consistency。
2. 计算 geometry + consistency 特征（无需 GT）。
3. selector s(features) → reliability score。
4. 按 s 降序做 selective prediction（coverage 阈值由 D_cal 标定）。

## 9. risk-coverage objective
- 最小化 selective risk（朝向误差）在给定 coverage；报告 NRC-AUC、AURC、Risk@70/90。

## 10. Why not simple calibration
- 单调校准（isotonic/temperature）不改 selection 排序 → NRC 不变。本方法**重排**（学非线性 risk），在 well-defined region 显著优于 score-only 与 score+ar+size linear（G2″）。

## 11. Why not size prior
- G2_double_prime：**固定 box-size bin 内** nonlinear 仍显著优于 score+ar+size linear（21/21 bin×cell CI>0）→ 增益为 orientation-specific 非线性几何，**非** box-size prior。

## 12. Limitations
- selector 训练用 source GT（calibration / upper-bound setting）；deployable 变体（leave-*、TTA consistency）为 candidate，**非** final production method。
- real TTA coverage 有限（DIOR + SODA/FAIR1M PSC；其它 next-step）。
- DOTA #20 weak-structure negative control（不调参）。
- Track A phase_mod 是一个 intrinsic 信号；机制为 candidate。
- **不重训 detector，不追 mAP，不改 frozen P1**。
