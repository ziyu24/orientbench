# B4 外部 RotatedFCOS-PSCD 验证

## 资产与质量

外部对象为 DOTA-v1.0 `train -> val` 上的 RotatedFCOS-PSCD。三个 seeds 均使用 4 GPU、FP32、12 epochs 和冻结 LR 0.0025，AP50 分别为 0.629、0.627、0.632，AP75 为 0.324、0.323、0.333；三者预测非空、覆盖全部 15 类，ar>=2.1 的匹配数分别为 33,363、33,182、33,218，均为 `HEALTHY_COMPARABLE`。

## 外部干预

冻结径向缩放在三个 seeds 上均可跨越 modulation gate；总体平均解码变化约 5.87 degrees，部分条件 p95 接近 90 degrees。同步切向和 secondary-frequency-only 干预的平均解码响应约 8.17 degrees；primary-frequency-only 响应接近零。这复现了最终角度主要受 secondary-frequency 解码支配、径向量可经 modulation threshold 改变解码结果的结构。

所有机制干预从同一 post-NMS detection identity 出发。它们会改变 angle box，因此只属于 `MECHANISM_ONLY_NOT_RANKING_ONLY`；class 与 detection score 未改变，NMS 未重新运行，AP 不声称不变。冻结候选分数只重排同一 prediction identity，box/class/NMS/AP 均不变。

## 风险泛函分离

与 Rotated RetinaNet 开发 host 不同，外部 RotatedFCOS 上 `phase_mod` 对 Endpoint C 为 informative：三个 seeds 的 NRC 为 0.937、0.950、0.917；Endpoint E NRC 为 0.661、0.742、0.733。`negative_phase_mod` 对两个 endpoint 均明显反序。该结果否定“PSC 原生模长必然反序”的通用表述，但不否定径向门控和 secondary-frequency 解码的结构作用。

Detection score 是外部 host 上最稳定的排序：Endpoint C NRC 为 0.796--0.824，Endpoint E 为 0.131--0.148。冻结机制候选未在 paired mother-scene bootstrap 下稳定优于 detection score，也未形成跨 seed 的独立修复确认。TTA direction consistency 因没有与冻结 prediction identity 对齐的 TTA dump 而记为 `NOT_TESTABLE`，未以代理值替代。

## 外部复现边界

- H1：Endpoint C 复现；Endpoint E 部分复现。
- H2：两个 endpoint 均部分复现，candidate switching 稀少且边界效应不构成通用解释。
- H3：Endpoint C 复现；Endpoint E 部分复现。
- H4：两个 endpoint 均部分复现，方向候选未稳定胜过 detection score。

因此外部证据支持“secondary-frequency decoding 与 modulation gate 可使径向模长语义依赖 host/endpoint”，不支持通用 reverse-ranking 或现成候选已完成修复。

