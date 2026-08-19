#!/usr/bin/env python3
"""Val-only r048 G1 evaluator; it deliberately rejects any non-val split."""
import argparse, json, math, os, sys
import numpy as np
import torch
from torch.utils.data import DataLoader
sys.path.insert(0, os.path.dirname(__file__))
from data_contract import records, HeadingDS
from train_v2 import Net, direct_params, direct_mass
from p2c_distribution import (circular_bayes_action, intrinsic_confidence,
    probability_within, p2c_logprob, vm_logprob, wrap)
from metrics_g1 import summary

if not hasattr(np, '_core'):
    sys.modules.setdefault('numpy._core', np.core)
    sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
    sys.modules.setdefault('numpy._core.numeric', np.core.numeric)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kind', required=True)
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--jitter', type=float, default=0)
    ap.add_argument('--hid', type=int, default=384)
    ap.add_argument('--layers', type=int, default=3)
    z = ap.parse_args()
    if z.jitter not in (0, 5, 10, 15): raise ValueError('only frozen G1 jitter levels allowed')
    dev = 'cuda'
    m = Net(z.kind, z.hid, z.layers).to(dev)
    m.load_state_dict(torch.load(z.checkpoint, map_location='cpu'))
    m.eval()
    dl = DataLoader(HeadingDS(records('val'), False, z.jitter), 64, num_workers=4)
    phi, pred, prob, conf, nll, rows = [], [], [], [], [], []
    with torch.no_grad():
        for am, bm, g, target, *_ in dl:
            am, bm, g = [q.to(dev) for q in (am, bm, g)]
            target = target.to(dev); out = m(am, bm, g)
            truth, rel, axis = target[:, 0], target[:, 1], target[:, 4]
            if z.kind == 'P2C_LIFT':
                mu, kap, coeff, vec = out
                local = circular_bayes_action(mu, kap, coeff)
                h = wrap(local + axis)
                c = intrinsic_confidence(mu, kap, coeff)
                q = probability_within(local, mu, kap, coeff)
                ll = p2c_logprob(rel, mu, kap, coeff)
            elif z.kind == 'DIRECT_S1_VM':
                mu, kap = direct_params(out)
                local, h = mu, wrap(mu + axis)
                c, q, ll = torch.tanh(kap / 4), direct_mass(mu, mu, kap), vm_logprob(rel, mu, kap)
            elif z.kind == 'HEADPOINT_2D':
                vec = torch.tanh(out); local = torch.atan2(vec[:, 1], vec[:, 0]); h = wrap(local + axis)
                c = vec.norm(dim=1).clamp(0, 1); q = c
                # A fixed, declared directional readout of the regressed vector.
                ll = vm_logprob(rel, local, 1 + 9 * c)
            else:
                raw = out.flatten(); positive = torch.sigmoid(raw)
                local = torch.where(raw > 0, torch.zeros_like(raw), torch.full_like(raw, math.pi)); h = wrap(local + axis)
                c = (positive - .5).abs() * 2; q = torch.maximum(positive, 1 - positive)
                sign = (torch.cos(rel) >= 0).float(); ll = -(torch.nn.functional.binary_cross_entropy_with_logits(raw, sign, reduction='none'))
            phi += truth.tolist(); pred += h.tolist(); prob += q.tolist(); conf += c.tolist(); nll += (-ll).tolist()
            rows += [{'phi': float(x), 'relative_phi': float(rr), 'axis': float(ax), 'pred': float(y), 'probability_within_90': float(w), 'intrinsic_or_baseline_confidence': float(v), 'nll': float(nn)} for x, rr, ax, y, w, v, nn in zip(truth, rel, axis, h, q, c, -ll)]
    result = summary(phi, pred, prob, conf, nll=nll)
    result.update({'kind': z.kind, 'jitter_degrees': z.jitter, 'trainable_parameters': sum(x.numel() for x in m.parameters() if x.requires_grad)})
    with open(z.out, 'w') as f: json.dump({'schema_version': 2, 'split': 'official_val', 'metrics': result, 'rows': rows}, f, indent=2)

if __name__ == '__main__': main()
