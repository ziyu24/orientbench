# EQS 跨数据集门控：A0 数据来源法证

## 结论

本轮在任何变换前向、特征构建、模型拟合、目标标签加载和 bootstrap 之前触发数据来源硬停止。六个核心 evaluation units 中五个通过已有来源核验；`FAIR1M-v1.0/24` 未形成满足冻结协议的完整原始预测宇宙，因此最终状态为 `FAIL_PROVENANCE_R012`。该状态关闭当前 EQS 跨数据集方法路线，不能解释为选择器性能失败或成功。

## 冻结问题

拟验证的问题是：选择器完全不使用目标域 `D_cal/D_audit` 的角度标签时，基于 identity、水平翻转和垂直翻转的真实预测等变性特征，能否相对 source-fitted `score+AR+size` 线性基线跨数据集改善归一化连续角风险排序。主风险冻结为

\[
y=\min\left(\frac{e_{\mathrm{le90}}}{\max(\delta_{0.75}(a_{GT}),1^\circ)},3\right),
\]

主比较、最小效应、六单元与三数据集双层门控均已在执行前冻结，但因 A0 失败均未运行。

## FAIR1M 完整总体核验

冻结本地验证划分含 4,362 张图像，标注表含 78,644 个实例，分布在 3,896 张非空标注图像中。逐来源 sorted image-ID set 法证得到：

| 来源 | 图像 ID 数 | 预测/标注数 | 相对完整 split 缺失 |
|---|---:|---:|---:|
| split | 4,362 | - | 0 |
| GT 实例表 | 3,896 | 78,644 | 466 |
| r011 schema | 3,896 | 484,332 | 466 |
| r011 identity raw | 3,896 | 484,332 | 466 |
| m069 image universe | 4,362 | 488,194（manifest 登记） | 0 |

GT 实例表不含空标注图像本身可以解释，但 r011 原始预测 registry 同样省略这 466 张图像，没有显式的 `n_pred=0` 行。另一方面，m069 manifest 登记了 4,362 图像和 488,194 个预测，但对应完整原始预测 dump 未持久化，无法逐图重算、无法与三视图建立相同 prediction identity，也无法证明 3,862 个预测差值仅来自空图。AP50/AP75 与既有 endpoint 的差异小于 0.002 不能替代 universe equality。

## 其它来源事实

DIOR-R 三个单元与 SODA-A 两个单元的 identity/hflip/vflip registry 在各自视图内具备唯一 image IDs，视图 image-ID universe 相等。SODA-A 冻结 22,994 tiles 均可由文件名唯一映射至 576 个 mother scenes；未映射、歧义和重复均为零。这些事实不足以绕过 Core-6 的 6/6 要求。

## 停止范围

按冻结协议，本轮没有：

- 启动 GPU 或 detector forward；
- 执行 transform smoke；
- 建立等变性 association 或 feature registry；
- 加载 target `D_audit` 标签；
- 拟合 source-only linear、geometry 或 EQS；
- 执行 source CV、target gate、bootstrap 或 HRSC 独立确认。

因此不存在可报告的 EQS NRC、跨数据集收益或独立确认结果。历史 target-GT-fitted geometry 仍只作为诊断上界；历史 leave-dataset `0/6` 与 identifiable leave-detector `4/5` 的分层解释不变。

## 可复算性

`inventory_preflight_r012.py` 从 split、GT、r011 schema/raw、m069 image universe、三视图 raw、SODA tile 目录和既有 evaluator parity 表重建 A0 证据。`validate_r012.py` 独立检查冻结计数、五比六来源状态、下游未运行状态、目标标签未加载以及受保护文件身份。下游三个入口均读取 A0 状态并在失败时以非零状态拒绝执行。

## 科学影响

本次结果是数据身份法证失败，不是统计不显著。它排除了将不同 FAIR1M 总体的候选数字拼接成方法证据的可能，也防止用 AP 近似对齐掩盖缺失图像行。当前方法路线按预注册规则关闭；论文只保留 measurement→diagnose 主线，并将跨数据集选择器视为失败的迁移尝试，而非可部署方法。
