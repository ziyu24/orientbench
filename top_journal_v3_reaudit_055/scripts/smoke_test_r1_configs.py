"""smoke_test_r1_configs.py — parse + build-model + load-one-sample smoke for R1 configs.
For each config: (1) Config.fromfile, (2) MODELS.build(model) [validates coder.encode_size ->
angle-branch conv wiring], (3) build train dataset and pull sample[0] [validates data paths &
annotation format]. Prints PASS/FAIL per config + a summary; writes reports CSV. No training.
"""
import os, sys, csv, glob, traceback
import mmrotate, mmrotate.models, mmrotate.datasets  # register
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmrotate.registry import MODELS, DATASETS

# Keep 'mmrotate' as the active default scope for the whole build, exactly like the
# Runner in tools/train.py — otherwise building 'mmdet.RetinaNet' switches scope to
# mmdet and its nested mmrotate head/coder ('AngleBranchRetinaHead', 'DeltaXYWHTRBBoxCoder')
# fail to resolve. This is a harness concern only; the configs themselves are unchanged.
init_default_scope("mmrotate")

ROOT = "/home/rspip/cqc/pro/study/orientbench"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
OUT = f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_config_smoke_061.csv"

def build_dataset_sample(cfg):
    ds_cfg = cfg.train_dataloader["dataset"]
    ds = DATASETS.build(ds_cfg)
    n = len(ds)
    s = ds[0]  # triggers pipeline incl LoadImageFromFile + ConvertBoxType
    inst = s["data_samples"].gt_instances
    return n, len(inst)

def main():
    args = sys.argv[1:]
    files = sorted(glob.glob(f"{CFGDIR}/*.py")) if not args else [f"{CFGDIR}/{a}" for a in args]
    rows = []
    for f in files:
        name = os.path.basename(f)
        rec = dict(config=name, parse="", model_build="", dataset_n="", sample_gt="", status="", err="")
        try:
            cfg = Config.fromfile(f); rec["parse"] = "ok"
        except Exception as e:
            rec["parse"] = "FAIL"; rec["err"] = f"parse:{e}"; rec["status"] = "FAIL"; rows.append(rec)
            print(f"[FAIL parse] {name}: {e}"); continue
        try:
            m = MODELS.build(cfg.model); rec["model_build"] = "ok"
            del m
        except Exception as e:
            rec["model_build"] = "FAIL"; rec["err"] = f"model:{e}"; rec["status"] = "FAIL"; rows.append(rec)
            print(f"[FAIL model] {name}: {e}"); continue
        try:
            n, ng = build_dataset_sample(cfg)
            rec["dataset_n"] = n; rec["sample_gt"] = ng
        except Exception as e:
            rec["dataset_n"] = "FAIL"; rec["err"] = f"data:{e}"; rec["status"] = "FAIL"; rows.append(rec)
            print(f"[FAIL data] {name}: {e}"); continue
        rec["status"] = "PASS"; rows.append(rec)
        print(f"[PASS] {name}  ds_n={rec['dataset_n']} sample_gt={rec['sample_gt']}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    npass = sum(1 for r in rows if r["status"] == "PASS")
    print(f"\nSMOKE SUMMARY: {npass}/{len(rows)} PASS -> {OUT}")
    sys.exit(0 if npass == len(rows) else 2)

if __name__ == "__main__":
    main()
