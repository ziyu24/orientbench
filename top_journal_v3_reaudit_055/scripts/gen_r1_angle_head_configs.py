"""gen_r1_angle_head_configs.py — derive R1 angle-head configs from the known-good PSC template.

Controlled comparison: load the PSC seed0 config (per dataset) as an mmengine Config, then
change ONLY the bbox_head (head type / angle_coder / angle loss / bbox loss for KLD).
Everything else — data_root, ann_file, pipelines, schedule, optimizer, anchors, assigner,
evaluator, val/test split — is inherited byte-for-byte from the PSC template, so the ONLY
variable across heads is the angle representation. Writes seed0/1/2 files per (head,dataset).

Heads: CSL, DCL(optional; only if DCLCoder importable), direct_regression_le90, KLD.
PSC seed0 already exists; we also emit psc_*_seed1/seed2 for provenance parity.
"""
import os, copy, sys
from mmengine.config import Config

ROOT = "/home/rspip/cqc/pro/study/orientbench"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
TEMPLATES = {
    "dior": (f"{CFGDIR}/psc_dior_seed0.py", 20),
    "soda": (f"{CFGDIR}/psc_soda_seed0.py", 9),
}
SEEDS = [0, 1, 2]

def plain_retina_head(nc, kld=False):
    """The official ai4rs plain rotated-retinanet head (direct angle regression)."""
    h = dict(
        type="mmdet.RetinaHead", num_classes=nc, in_channels=256,
        stacked_convs=4, feat_channels=256,
        anchor_generator=dict(
            type="FakeRotatedAnchorGenerator", angle_version="le90",
            octave_base_scale=4, scales_per_octave=3,
            ratios=[1.0, 0.5, 2.0], strides=[8, 16, 32, 64, 128]),
        bbox_coder=dict(
            type="DeltaXYWHTRBBoxCoder", angle_version="le90",
            norm_factor=None, edge_swap=True, proj_xy=True,
            target_means=(0.0, 0.0, 0.0, 0.0, 0.0),
            target_stds=(1.0, 1.0, 1.0, 1.0, 1.0)),
        loss_cls=dict(type="mmdet.FocalLoss", use_sigmoid=True,
                      gamma=2.0, alpha=0.25, loss_weight=1.0),
        loss_bbox=dict(type="mmdet.L1Loss", loss_weight=1.0))
    if kld:
        h["reg_decoded_bbox"] = True
        h["loss_bbox"] = dict(type="GDLoss_v1", loss_type="kld",
                              fun="log1p", tau=1, loss_weight=1.0)
    return h

def anglebranch_head(base_head, coder, loss_angle):
    """Keep PSC's AngleBranchRetinaHead skeleton; swap angle_coder + loss_angle only.
    use_normalized_angle_feat forced False (PSC-specific; off for CSL/DCL per upstream refs).
    bbox loss / cls loss / num_classes / anchors held identical to the PSC template."""
    h = copy.deepcopy(base_head)
    h["angle_coder"] = coder
    h["loss_angle"] = loss_angle
    h["use_normalized_angle_feat"] = False
    return h

def head_for(name, base_head, nc):
    if name == "csl":
        return anglebranch_head(
            base_head,
            dict(type="CSLCoder", angle_version="le90", omega=4,
                 window="gaussian", radius=3),
            dict(type="SmoothFocalLoss", gamma=2.0, alpha=0.25, loss_weight=0.8))
    if name == "dcl":
        return anglebranch_head(
            base_head,
            dict(type="DCLCoder", angle_version="le90", omega=1),
            dict(type="mmdet.CrossEntropyLoss", use_sigmoid=True, loss_weight=0.8))
    if name == "regression":
        return plain_retina_head(nc, kld=False)
    if name == "kld":
        return plain_retina_head(nc, kld=True)
    raise ValueError(name)

def dcl_available():
    try:
        import mmrotate, mmrotate.models  # noqa
        from mmrotate.registry import TASK_UTILS
        if "DCLCoder" in TASK_UTILS.module_dict:
            return True
        # project-local ext?
        try:
            import orientbench_ext.dcl_coder  # noqa
            return "DCLCoder" in TASK_UTILS.module_dict
        except Exception:
            return False
    except Exception:
        return False

def main():
    heads = ["csl", "regression", "kld", "psc"]
    include_dcl = dcl_available()
    if include_dcl:
        heads.insert(1, "dcl")
    print("DCL available:", include_dcl, "-> heads:", heads)
    written = []
    for ds, (tpl, nc) in TEMPLATES.items():
        cfg0 = Config.fromfile(tpl)
        base_head = copy.deepcopy(cfg0.model["bbox_head"])
        for head in heads:
            for seed in SEEDS:
                out = f"{CFGDIR}/{head}_{ds}_seed{seed}.py"
                if head == "psc" and seed == 0:
                    written.append((out, "exists(template)"))
                    continue
                cfg = copy.deepcopy(cfg0)
                if head != "psc":
                    cfg.model["bbox_head"] = head_for(head, base_head, nc)
                if head == "dcl":
                    # project-local coder must be imported at runtime (not in third_party)
                    cfg.custom_imports = dict(
                        imports=["orientbench_ext.dcl_coder"], allow_failed_imports=False)
                cfg.randomness = dict(seed=seed, deterministic=False)
                cfg.resume = False
                cfg.load_from = None
                cfg.work_dir = f"./work_dirs/r1/{head.upper()}__{ds}__seed{seed}"
                cfg.dump(out)
                written.append((out, "written"))
    print(f"wrote {sum(1 for _,s in written if s=='written')} configs "
          f"({len(written)} total incl template)")
    for o, s in written:
        print(f"  [{s}] {os.path.basename(o)}")

if __name__ == "__main__":
    main()
