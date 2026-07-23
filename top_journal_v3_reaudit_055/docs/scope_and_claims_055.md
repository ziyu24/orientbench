# Scope and Claims (055)

## 允许主张（evidence-backed，masked ar≥1.6 冻结协议）
1. mAP@0.5 对朝向误差高度不敏感：约束扰动下（IoU>0.5，~35° 角扰动）mAP@0.5 不变而朝向 risk/AP75 大幅恶化；受 aspect ratio 与 IoU 阈值门控（P1 precise-pass）。
2. 近方形朝向在 IoU 上不可分辨（cliff），是测量层核心发现，且是 masked 协议与分层 conformal 的动机。
3. within-cell finite-sample 朝向风险控制成立：strict 区提供带弃权的尾部保证（P2 主贡献）。
4. conformal score menu：几何感知选择器在固定保证下一致取得最高覆盖，且 NRC 上 6/6 显著优于检测置信度、5/6 优于 TTA（P4 并入 P2）。
5. PSC 角度编码器内在置信度（phase_mod）在良态实例上仍显著反校准（3/3 full-val PSC cell，CI>1）——机制候选。

## 禁止主张
- ~~检测置信度反校准~~（masked 下显著校准；unmasked 反校准是 pooling artifact）。
- ~~PSC 系统性/已证明反校准~~；只写 angle-coder 内在置信度机制**候选**。
- ~~full 23-cell benchmark / all datasets covered~~；只写 protocol + 有限 provenance-clean cell。
- ~~几何选择器是 validated deployable method~~；写 candidate（source-supervised，target GT-free 推理）。
- ~~NRC 严格独立于 mAP~~；写“可比设置内提供 mAP 之外的 reliability signal”。
- ~~下游实用性已证明~~；写真实但微弱。
- ~~跨域严格 conformal guarantee~~；写退化 + Mondrian 部分缓解。
- ~~DOTA#20 有效~~；invalid_pending（19-图 subset）。
- CVPR/ICCV/TPAMI ready、full project complete、top venue ready —— 一律禁止。

## 论文身份
Orientation Reliability Measurement Protocol + Finite-Sample Conformal Risk Control（非 full benchmark）。

## 治理内容位置
claim ledger / forbidden claims / sha256 / verifier / split token → 附录与复现部分，不进正文主叙述。
