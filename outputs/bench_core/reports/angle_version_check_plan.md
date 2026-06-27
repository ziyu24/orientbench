# angle_version Verification Plan

> 生成时间: 2026-06-25 18:21:48 CST
> 计划，不做正式结论；uncertain 保留 uncertain。

- checks: 6; uncertain/unverified: 6; all_resolved: False
- note: GV-obliquity is sign-invariant (unaffected); angle-error gate IS affected.

| check_id | scope | current_status | blocking_for |
|---|---|---|---|
| dota_le90_sign | DOTA-v1.0/v1.5 GT | **uncertain** | DOTA angle-error gate |
| dior_le90_sign | DIOR-R GT | **uncertain** | DIOR angle-error gate |
| fair1m_le90_sign | FAIR1M-v1.0 GT | **uncertain** | FAIR1M angle-error gate |
| hrsc_mbox_le90_equiv | HRSC2016 GT | **uncertain** | HRSC angle-error gate (highest priority) |
| prediction_theta_unit | prediction ingestion | **uncertain** | any real-prediction angle gate |
| minarearect_normalization | Bench-Core geometry | **derived_unverified** | GT<->pred angle alignment |

## Method 细节
- **dota_le90_sign**: poly8 -> cv2.minAreaRect -> theta; cross-check sign vs mmrotate poly2obb_le90 on a sample
- **dior_le90_sign**: robndbox corners -> minAreaRect vs raw <angle>; compare sign/range
- **fair1m_le90_sign**: points polygon -> minAreaRect; verify le90 range/sign on a sample
- **hrsc_mbox_le90_equiv**: mbox_ang (rad) vs le90: confirm convention & sign; visual + numeric on sample
- **prediction_theta_unit**: confirm each real prediction theta is radians & le90 (angle_unit/angle_version fields)
- **minarearect_normalization**: verify poly8_to_obb le90 normalization [-pi/2,pi/2) matches detector convention
