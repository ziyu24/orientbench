# C1 Real Cross-View Availability Audit

> 2026-06-27 20:28:21 CST

## 结论
- **genuine multi-physical-view pairs: 不存在**（DOTA/HRSC/DIOR 单视图航拍；无 view-pair 元数据）。
- **可构造**: deterministic view transform（图像旋转/翻转）+ **真实 RHINO inference** → 真实 detector 在视图变换下的响应；object identity 经共享 GT 可追踪，满足 R1 GT-identity。
- cross_view_kind = **augmentation_view_real_inference**（项目 C1/B 的 augmentation-consistency 定义），**非**真实第二物理视角。

- 可用图像(transformed view): 5297(DOTA-v1.0 val)；object-pair 估计 >20000；类别 DOTA-v1.0 15 类；可达 >=2000 图: 是。
- 缺失: 真实多物理视角采集 / 人工 cross-view 对应标注。

## 推进决定
- C1 升级路径: 用真实旋转视图 + 真实 RHINO inference 生成 paired predictions（比 015 的纯几何 smoke 更真实）。
- 诚实边界: 仍是 augmentation-view（变换派生），非 genuine multi-viewpoint；formal gate 仅在阈值冻结+批准后；本轮只到 candidate。
