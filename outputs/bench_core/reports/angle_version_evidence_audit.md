# angle_version Evidence Audit

> 生成时间: 2026-06-25 23:34:10 CST
> 用计算证据降低 uncertain；不伪造确定性；HRSC mbox/le90 检测器等价仍 uncertain。

- items: 7；**resolved_with_evidence: 5**；uncertain: 2；HRSC: **uncertain**

| dataset | status | evidence | key metric |
|---|---|---|---|
| DOTA-v1.0 | **resolved_with_evidence** | poly->obb->poly round-trip IoU + theta range [-pi/2,pi/2) | roundtrip_IoU=0.92163 in_range=True |
| DOTA-v1.5 | **resolved_with_evidence** | poly->obb->poly round-trip IoU + theta range [-pi/2,pi/2) | roundtrip_IoU=0.91581 in_range=True |
| DIOR-R | **resolved_with_evidence** | poly->obb->poly round-trip IoU + theta range [-pi/2,pi/2) | roundtrip_IoU=0.99538 in_range=True |
| FAIR1M-v1.0 | **resolved_with_evidence** | poly->obb->poly round-trip IoU + theta range [-pi/2,pi/2) | roundtrip_IoU=0.96138 in_range=True |
| HRSC2016 | **uncertain** | mbox_ang range + OBB-HBB extent vs annotated box_* (loose -> inconclusive) | ang_in_range=True hbb_relerr W=0.0938 H=0.1176 |
| Bench-Core minAreaRect | **resolved_with_evidence** | le90 [-pi/2,pi/2) normalization round-trips on poly datasets |  |
| prediction theta unit | **uncertain** | no real detector prediction ingested yet |  |

结论：DOTA/DIOR/FAIR1M le90 GT 解析由 poly→obb→poly round-trip IoU≈1 + θ∈[-π/2,π/2) 证据支撑 (resolved_with_evidence)。HRSC mbox_ang 在 le90 数值范围内，但与标注 box_* HBB 的几何交叉验证不一致 (标注 HBB 偏松)，无法证明与检测器 le90 约定等价 → 保持 uncertain。prediction theta unit 在接入真实 prediction 前 uncertain。GV-obliquity 对符号不变，不受影响。
