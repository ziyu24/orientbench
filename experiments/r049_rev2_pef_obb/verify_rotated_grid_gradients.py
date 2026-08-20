#!/usr/bin/env python3
"""One-batch full-model finite-gradient admission check for final PEF grid."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import torch
from mmengine.config import Config
from mmengine.runner import Runner
from mmrotate.utils import register_all_modules

GROUPS = {'backbone': 'backbone', 'neck': 'neck', 'bbox_reg': 'bbox_head.retina_reg',
          'angle_head': 'bbox_head.retina_angle_cls', 'pef_sampler_scorer': 'bbox_head.pef'}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--config', required=True); p.add_argument('--out', type=Path, required=True); a = p.parse_args()
    register_all_modules(); cfg = Config.fromfile(a.config); cfg.launcher = 'none'
    runner = Runner.from_cfg(cfg); batch = next(iter(runner.train_dataloader)); data = runner.model.data_preprocessor(batch, True)
    values = runner.model(**data, mode='loss'); loss = sum(sum(x) if isinstance(x, list) else x for x in values.values()); loss.backward()
    out = {'loss': float(loss.detach()), 'modules': {}}
    for label, prefix in GROUPS.items():
        ps = [param for name, param in runner.model.named_parameters() if name.startswith(prefix)]
        gs = [param.grad for param in ps if param.grad is not None]
        out['modules'][label] = {'parameters': len(ps), 'grads': len(gs), 'nonzero_finite': any(torch.isfinite(g).all().item() and g.abs().sum().item() > 0 for g in gs)}
    if not all(v['nonzero_finite'] for v in out['modules'].values()): raise RuntimeError(json.dumps(out, sort_keys=True))
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(out, indent=2) + '\n'); print(json.dumps(out, sort_keys=True))
if __name__ == '__main__': main()
