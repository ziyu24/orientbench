# HRSC mbox↔le90 Angle Proof 026 (read-only)

> 2026-06-28 12:28:44 CST

## 证据
1. **代码**: mmrotate HRSCDataset (ai4rs_clone/mmrotate/datasets/hrsc.py:175-181) 直接将 `mbox_cx,mbox_cy,mbox_w,mbox_h,mbox_ang` 构成 rbbox=[cx,cy,w,h,ang]（le90 rbox），再 `rbox2qbox`。**mbox_ang 直接作为 le90 rbox theta，无 negate/offset 变换**。
2. **经验**: LSKNet HRSC #13 在该 GT 上 dota/mAP=0.906（与 baseline 一致）→ pred(le90) 与 GT(mbox_ang as le90) 同 convention、对齐。
3. **稳健**: orientbench canonical_longside 处理 (w,h,θ)↔(h,w,θ+π/2) 对称，对 mbox_ang 残余 range 差异稳健。

## 结论
- **angle_status = resolved_with_evidence**（mbox_ang ≡ le90 rbox theta，代码+mAP 双证据）。
- 仍保持 HRSC cross-dataset = exploratory（不冻结阈值、不 formal gate）。
