# A4 经验容忍角与理想几何容忍度

本审计固定使用 `ar>=2.1`。理想曲线是在共中心、同尺度、le90 矩形上数值求解的 `delta_tau(ar)`；经验量是在真实预测/GT 的中心、尺度和初始角度下，沿增加当前误差的方向旋转，记录固定 matched pair 的 IoU 首次低于 tau 的 0.5 度网格点。后者是 evaluator-state tolerance 的合法近似，但不包含竞争匹配、类别排序或 NMS 变化，因此不等于真实评测器容忍角。

K1 六个 provenance-clean full-val 单元的完整评测器基线和自适应 IoU50 边界端点继续有效：AP50 在该受约束端点不变，而 AP75 显著下降。DOTA 两个 clean 单元仅有基线。当前持久化资产没有覆盖八剂量网格所需的全部六单元完整 raw prediction dumps；因此没有用 matched-only AP、旧 partial-GT AP 或插值伪造固定剂量 AP，也不能识别正式 AP75 knee。

允许保留的结论是：AP50 存在由几何定义支持的弱敏感区，AP75 在现有端点证据中更早响应；经验固定对容忍角受真实 center/scale 影响并围绕理想几何关系分布。剂量响应 knee 仍不能作为已确认结论。

**A4 判定：PARTIAL_ALIGNMENT。**
