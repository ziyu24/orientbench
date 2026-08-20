_base_ = './dota_psc_baseline_parity.py'
load_from = None
# Fixed conservative scale eliminates AMP overflow skips observed in the
# re-admission smoke; all four rerun arms inherit the same setting.
optim_wrapper = dict(loss_scale=128.)
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2/dota_psc_cont'
