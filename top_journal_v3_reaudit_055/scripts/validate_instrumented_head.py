"""Validate InstrumentedAngleBranchRetinaHead alignment on one checkpoint (PSC/DIOR-R/seed0).
Checks: (1) pred_instances.angle_encoded present, shape (N, encode_size);
(2) angle_coder.decode(angle_encoded) == box theta (alignment through NMS);
(3) phase_mod computes and is finite. Runs on a few images. Single GPU."""
import os, sys, math
import torch
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055")
import orientbench_ext.instrumented_heads  # register
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS
init_default_scope("mmrotate")

ROOT = "/home/rspip/cqc/pro/study/orientbench"
CFG = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder/psc_dior_seed0.py"
WD = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1/PSC__DIOR-R__seed0"
CKPT = f"{WD}/epoch_12.pth" if os.path.isfile(f"{WD}/epoch_12.pth") else f"{WD}/best_dota_mAP_epoch_12.pth"

cfg = Config.fromfile(CFG)
cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
model = MODELS.build(cfg.model)
load_checkpoint(model, CKPT, map_location="cpu")
model.eval().cuda()
print(f"loaded {CKPT}")

# build val dataset + pipeline
ds = DATASETS.build(cfg.val_dataloader["dataset"])
from mmengine.dataset import Compose
pipe = ds.pipeline
n_check = 0; max_theta_err = 0.0; total_dets = 0
with torch.no_grad():
    for i in range(6):
        data = ds[i]
        data = model.data_preprocessor(dict(inputs=[data["inputs"].cuda()],
                                            data_samples=[data["data_samples"].cuda()]), False)
        out = model.predict(data["inputs"], data["data_samples"])
        pi = out[0].pred_instances
        assert hasattr(pi, "angle_encoded"), "angle_encoded MISSING"
        enc = pi.angle_encoded
        boxes = pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes
        if enc.shape[0] == 0:
            continue
        assert enc.shape[1] == model.bbox_head.encode_size, (enc.shape, model.bbox_head.encode_size)
        # alignment: decode(enc) == box theta
        dec = model.bbox_head.angle_coder.decode(enc)
        theta = boxes[:, 4]
        err = (dec - theta).abs()
        # angle is periodic pi; wrap
        err = torch.minimum(err, (math.pi - err).abs())
        max_theta_err = max(max_theta_err, err.max().item())
        # phase_mod (PSC): first num_step dims
        coder = model.bbox_head.angle_coder
        ns = coder.num_step
        cs = coder.coef_sin.to(enc); cc = coder.coef_cos.to(enc)
        psin = (enc[:, :ns] * cs).sum(-1); pcos = (enc[:, :ns] * cc).sum(-1)
        phase_mod = pcos**2 + psin**2
        assert torch.isfinite(phase_mod).all(), "phase_mod non-finite"
        total_dets += enc.shape[0]; n_check += 1
print(f"images_checked={n_check} total_dets={total_dets} "
      f"max|decode(enc)-theta|={math.degrees(max_theta_err):.4f} deg")
print("ALIGNMENT OK" if max_theta_err < 1e-2 else f"ALIGNMENT WARN ({max_theta_err})")
print(f"phase_mod sample range: computed & finite over {total_dets} dets")
