# B4 外部 PSC 变体验证预注册

冻结时间：2026-07-23 18:38:04 CST

## 外部对象

- 选择状态：`NEW_FREQUENCY_VARIANT_REQUIRED`
- 数据集：DOTA-v1.0，`train -> val`，单尺度切片。
- 外部 host：官方 RotatedFCOS + PSCD，ResNet-50/FPN。
- 外部性：B1--B3 使用 Rotated RetinaNet + PSCD；FCOS 的点式距离回归、centerness、正样本分配和 NMS 前排序均不同，且未参与 H1--H4 或候选公式设计。
- 频率配置：官方 `dual_freq=True, num_step=3, thr_mod=0.47`，不搜索频率。
- 三个随机种子：0、1、2；同一配置，唯一变化为随机种子。

现存 DOTA PSC 资产均不足以直接承担本门控：RetinaNet 单 checkpoint 与开发 host 相同；24 epoch load-from 资产仍是同一 RetinaNet 结构；DOTA-v1.5 MS 资产被历史审计标为 invalid；官方 FCOS 权重使用公开训练口径而非本项目 `train -> val`，且只有单 seed。因而本轮按预注册规则在项目 split 上训练一个外部 host 的三 seeds，不作 LR sweep。

## 训练协议

- 配置来源：PSC 官方 RotatedFCOS-PSCD 配置，复制为项目内独立配置，不修改第三方源码。
- backbone：ResNet-50；neck：FPN；head：RotatedFCOSHead + PSCD。
- 输入与增强：1024 x 1024；horizontal/vertical/diagonal random flip，概率 0.75。
- schedule：12 epochs；每 epoch 验证；milestones 8/11。
- optimizer：SGD，LR 0.0025，momentum 0.9，weight decay 1e-4。
- precision：FP32；4 GPU；每 GPU batch size 2。
- checkpoint：只按 val AP50 选择，AP75 只作次级披露；机制指标不得参与选择。
- epoch-1 健康门控：loss 有限、预测非空、验证流程可结束。loss 稳定但 AP 低不早停。
- 模型可比较门槛：AP50 >= 0.45、预测非空、至少覆盖 14/15 类、matched count >= 1000、无 NaN/Inf。

## 冻结风险对象

- Endpoint C：continuous le90 circular absolute angle error。
- Endpoint E：`angle_error > delta_theta_0.75(aspect_ratio)`。
- 主 mask：GT aspect ratio >= 2.1。
- coverage grid：0.10, 0.20, ..., 1.00；Risk@70/90 直接取 0.70/0.90。
- cluster：由 DOTA tile 文件名恢复 original mother-scene ID；若恢复失败，降为 tile/image cluster 并明确限制。
- bootstrap：paired mother-scene bootstrap，800 replicates，正负/候选分数共享 resample IDs。

## 冻结干预

- radial k：0.25、0.5、0.75、0.9、1.0、1.1、1.25、1.5、2.0、4.0。
- tangential angle：-15、-7.5、-2、0、2、7.5、15 degrees。
- primary-only、secondary-only、frequency-conflict 使用相同角度网格。
- candidate-switch surface offset：-10、-5、-1、1、5、10 degrees。
- boundary strata：near [0,10)、intermediate [10,30)、far [30,90] degrees。

机制干预允许改变 angle box、NMS 与 AP，但必须标记为 `MECHANISM_ONLY_NOT_RANKING_ONLY`。冻结候选只在同一 post-NMS prediction identity 上重排，不改变 box、class、NMS 或 AP。

## 冻结候选

1. `tta_phase_direction_consistency = -circular_variance(2 theta_tta)`；
2. `multi_frequency_consistency = -d_circ(theta_f1/2, theta_unwrapped_f2/2)`；
3. `unwrap_candidate_energy_gap = |cos(theta_f1-c0)-cos(theta_f1-c1)|`；
4. `phase_direction_margin = unwrap_gap * secondary_phase_norm`。

B1 未登记历史 fitted fusion，因此本轮不存在第五个融合候选，禁止临时发明。强制基线为 phase_mod、negative_phase_mod、detection score 与 TTA circular variance；CSL/DCL 只引用已冻结跨-head 参考，不用新 variant 伪造。

## 机制复现规则

- 每条 H1--H4 对 Endpoint C/E 分开判定。
- `REPLICATED`：三个健康 seeds 方向一致，至少两个 seed 的 paired mother-scene bootstrap 95% CI 支持，且效应不由 prediction identity 或训练崩坏解释。
- `PARTIALLY_REPLICATED`：方向多数一致但 endpoint、seed 或区间异质。
- `NOT_REPLICATED`：无稳定响应。
- `CONTRADICTED`：稳定方向与 B3 相反。
- `NOT_TESTABLE`：冻结数据中缺少必要信号，不以代理替代。

## B5 门控

`PASS_MECHANISM_STRONG` 要求至少一条假说在新 host 完整复现，跨 seed/dataset/variant 稳定且主要混杂被排除。仅 Endpoint C 或特定边界稳定、Endpoint E 异质时判 `PASS_MECHANISM_BOUNDED`。不复现、混杂无法排除或只能由玩具模型支撑时判 `FAIL_MECHANISM`。

