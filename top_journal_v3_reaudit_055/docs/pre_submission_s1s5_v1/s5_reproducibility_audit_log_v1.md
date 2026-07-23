# S5 —— Reproducibility Audit Log (v1)

- 时间: 2026-07-03 02:32:59 PDT
- 一键复算脚本: scripts/reproduce_all_main_tables_s1s5_v1.sh
- 环境: /home/rspip/anaconda3/envs/mr_dev1x/bin/python (numpy/scipy/sklearn/shapely)
- frozen assets 校验: thresholds.yaml sha256 = b7c4e649b1a3de6d... (运行前后不变); D_cal/D_audit 无 git diff。
- 输入 (raw provenance-clean):
  - raw preds: outputs/persistent_artifacts/orientbench_v2/{ds}/{bid}/schema/*.jsonl (+ /dev/shm 镜像)
  - gt: DIOR-R/FAIR1M/SODA fullval gt jsonl
  - matched 17-field: outputs/persistent_artifacts/orientbench_real_052/matched_tables/{ds}/{bid}/
  - phase_mod: psc_phase_mod_permatched_full_052.csv; TTA: tta_circular_variance_full_052.csv
- 输出主表: reports/pre_submission_s1s5_v1/s1a_*, s1b_*, s1c_*, s2_*, s3_*, s4_*.csv
- 脚本清单:
  - s1a_full_pipeline_perturb_v1.py (real evaluator; raw preds; constrained perturb)
  - s1b_independence_fix_v1.py (D_fit/D_calib/D_audit; leave-cell)
  - s1c_ltt_conformal_v1.py (LTT fixed-seq; binomial tail; Hoeffding B=90 mean; image bootstrap)
  - s2_psc_mechanism_v1.py (aliasing + confounding, masked)
  - s4_downstream_angle_unit_v1.py (real directional classes, angle-deg risk)
- 说明: FAIR1M#24 / SODA#23 / SODA#4 的 S1a 约束扰动 pass 因 raw 框量大(48万-145万)计算耗时, 后台运行; 3 个 full-val cell(DIOR#22/#3/#61) 已确证 ΔAP50=0.0000 且 FP 不变。
- 未训练 detector; 未追 public mAP; 未改 frozen thresholds/split。
