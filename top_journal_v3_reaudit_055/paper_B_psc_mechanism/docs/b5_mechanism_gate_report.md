# B5 机制级终审

最终判定：`PASS_MECHANISM_BOUNDED`。

真实干预在原 Rotated RetinaNet 和外部 RotatedFCOS 上都显示 secondary-frequency 解码与 modulation gate 对输出角度具有可重复因果影响，H1 与 H3 的结构响应跨 host、跨 seeds 成立。训练健康、预测身份和 endpoint 已分别审计，玩具模型仅作充分性辅助。

边界同样明确：外部 host 的 `phase_mod` 在两个 endpoint 上均为 informative，而原 host 在 continuous risk 上稳定反序；geometry-normalized severe event 继续呈 host/seed 异质。冻结候选没有独立确认稳定优于 detection score，TTA direction consistency 在该 identity 下不可测试。故不能主张所有 PSC 实现普遍反序、不能把机制干预称为 ranking-only repair，也不能把候选修复写成已完成。

B6 可以启动，但必须以 endpoint-qualified、host-qualified 的修复门控重新检验；B6 不得继承候选成功，只能继承已经复现的有界结构机制。

