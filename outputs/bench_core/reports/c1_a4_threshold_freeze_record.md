# C1/A4 Threshold Freeze Record (017)

> freeze_time: 2026-06-27 21:04:08 CST
> approval_token: SUPERVISOR_APPROVED_017_R8_FREEZE_C1_A4_DCAL_ONLY

- pre-freeze audit: **PASS** (candidates pending/unfrozen, host hashes match, C1=augmentation-view, A4 bg_unavailable=0, D_cal/D_audit disjoint, D_audit not in candidate).
- thresholds.yaml sha256 **before** `aeb3f6c07a1298281f6ff2374f566e6ef7b2264b47ca63c1119233b4be088a48`
- thresholds.yaml sha256 **after**  `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`
- candidate sha256: c1=`bbc2a4f749c58353` a4=`1a207bf09bf4c13b`
- data_fingerprint=`08426e73a026ab7a` code_fingerprint=`769131f75f73c050`

## C1 frozen (augmentation-view consistency)
- view_consistency_p90_deg_max=5.04 drop_rate_across_views_max=0.184 (D_cal-derived, margin)
- not_genuine_physical_multiview=True; host=55a90abbace42927
## A4 frozen (same-host source attribution)
- partial_corr_max_abs=0.2 hsic_p_min=0.05; background_source_enabled=True; host=3e32fa11114ced82

## 样本规模 (记录；D_audit 指标未用于阈值)
- C1 D_cal/D_audit, A4 D_cal/D_audit 见 c1_cross_view_real_summary.csv / a4_source_attribution_summary.csv。
- **D_audit 仅 holdout，未参与阈值标定。**
