# B/C 科学讨论

## 当前状态

- 当前没有已完成的新实验。r003 从未执行，旧签字和旧执行计划均不继承。
- r001 只关闭既定 CMR，r002 只把既定 GR-EQS 负向冻结；二者都不能证明所有方向可靠性机制无效。
- 当前证据仍只支持 JSTARS 对标，尚不能声称达到 TGRS 或 ISPRS JPRS。

## 从 AIRO 到干预式轴向可辨识响应

B 最初提出以局部有效旋转信息 `J_eff` 和全局轴向 alias 间隙 `M_15` 描述 COI。C 接受
它们作为一次可证伪测量，但拒绝“信息论上限”或“普适定律”的措辞：两个 detector 的经验误差
不能约束更强 estimator，经典结构张量、配准 CRLB/Ziv--Zakai 界、Lie derivative 和全局配准
歧义也不是本项目的新理论。

B 接受该修正。新命题只称为“干预式轴向可辨识响应”：对同一图像实施不改变 GT 几何的
各向同性模糊和抗混叠降采样后，`J_eff`、`M_15` 是否按剂量下降，并伴随不同 detector
架构的轴向损失上升。它不声称基本极限，不输出新角度，不训练不确定性 head，也不把观测量
融合进 detection score。

## C 的最强反例与 B 的处理

C 的决定性异议是 predicted-crop 混杂。错误的预测中心、尺度和背景可能同时降低观测量并
增大角误差；因此旧式回顾性相关即使为正，也可能只是“坏框裁到坏图”。B 接受以下边界：

- 主分析只使用 GT 中心和交换不变的无方向尺度裁圆形 patch，任何阶段都不向特征提取器提供
  GT theta；这只是 oracle-localization、theta-hidden 条件，不是部署方案。
- clean prediction 定义的裁剪只作诊断，并在各干预间固定；随干预变化的预测裁剪属于
  post-treatment 次分析，不能支撑主结论。
- 围绕主裁剪加入平衡中心位移和互为倒数的尺度扰动，形成 crop nuisance envelope。真实成像
  效应若落入该 envelope，必须判机制失败。
- 主因果结局固定在 clean 图像已检测到的 GT 对象总体。干预后漏检记为最大损失，并把总变化
  精确拆成漏检贡献与保留匹配对象的角度恶化贡献；只有后者也为正，才不是普通 recall 崩塌。

## 数据与资产边界

新问题首次验证按项目规则优先 HRSC2016。它的单类、高长宽比船舶适合先隔离方向机制，因此
r004 只做 HRSC2016 生死门，不把跨域失败混入首次机制判断。历史清单曾登记 Oriented R-CNN、
Rotated RTMDet、ARS-DETR 和 Strip R-CNN 的 HRSC 模型，但当前 Git 中可核实的冻结输出只覆盖
同一 Oriented R-CNN detector family，且部分旧子集有训练重叠风险。SERVER 必须重新解析训练外
official test 和至少 Oriented R-CNN、Rotated RTMDet 两种严格不同架构；换 backbone 不算第二
family，旧预测只能作 identity parity 对照。

## 先验碰撞与可保留的新意

普通图像结构张量已能描述主方向和各向异性；配准文献已给局部 Fisher/CRLB 与全局歧义界；
OBB 文献已有参数结构张量、周期角度质量、rotation-equivariance 测量和频域角对齐。因此
`J_eff` 或 `M_15` 单独作为新分数不足以形成顶刊贡献。唯一仍可能成立的科学增量是：在
theta-hidden、定位去混杂、强经典基线和真实成像干预下，人和多架构 detector 是否共同呈现
可重复的方向特异响应。

## B/C 联合裁决

C 对 r004 给出条件签署，B 接受全部限制：r004 仅是 HRSC2016 detector-side causal falsifier。
全部门通过只允许进入第二数据集/传感器和至少三名盲标注者或重复标注的确认阶段；不构成方法
成立、human-machine shared law、TGRS/JPRS 升档或论文结论。若 GT 主裁剪信号消失、只有预测
裁剪有效、角度贡献不为正、任一必需 detector/corruption 反向，或新量被结构张量、梯度、尺度
等强基线等价复现，则关闭该机制，不得改名回到 selector、head、CMR、PEF、Q-SetOD 或 GR-EQS。

## r004 SERVER 结果的 B 独立复核

SERVER 报告八个 detector×corruption×dose 的完整总体 `DeltaY` 点估计均低于 0.02。若资产、
匹配、操纵和实现有效，这一事实足以使主损失合取门失败；但当前公开实现没有建立这些前提，
因此 B 不接受其 `KILL_COI_R004`，当前科学状态为
`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。

决定性问题不是“缺少更多显著性”，而是冻结 matcher 被改变。trainval 剂量选择先汇总全部
候选并按代价全局排序后做一对一贪心；test 快速门改为按 GT 输入顺序逐个占用最近预测。两者
可在同一输入上冻结出不同总体：一个两 GT、两预测的最小反例中，前者保留两个 GT，后者只
保留一个。由此八个 test 点估计不是原协议所定义的同一 matcher 下估计量。

同时，公开代码只实现了合成夹具、剂量选择和主损失快速聚合，没有对真实 HRSC test 生成
G/P/N 的 `J_eff/M_15`，也没有计算操纵 Holm-32、test 非坍塌、10000 次图像簇 bootstrap、
逐对象审计或独立重算。缺少真实操纵证据时，低 `DeltaY` 既可能代表机制失败，也可能只是
干预没有充分改变预注册可观测量；按 r004 的冻结优先级只能记为 inconclusive。

下一步只允许复用已经生成的 clean 与四个干预预测做 correction-only CPU 闭环。不得重推理、
重选剂量、换模型、删对象或在 test 上调 matcher。只有同一 matcher、真实操纵有效性和独立
复算全部成立后，负向点估计才可正式关闭 COI。当前期刊证据仍只支持 JSTARS 对标。
