#!/usr/bin/env python3
"""Deterministic r048 convention tests; no T_cal/test/audit access."""
import math
import sys
import torch
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from data_contract import records, render, IDENTITY, HFLIP, VFLIP, R90, R180, R270
from p2c_distribution import (wrap, p2c_logprob, transformed_logprob,
    transform_angle, HFLIP as PH, VFLIP as PV, R90 as PR90, R180 as PR180, R270 as PR270)

def circular_distance(a, b): return torch.abs(wrap(a-b))
def action_from_logprob(logp, grid):
    w = torch.softmax(logp, 1)
    return torch.atan2((w*torch.sin(grid)).sum(1), (w*torch.cos(grid)).sum(1))

def main():
    mu, kap = torch.tensor([0.0]), torch.tensor([12.0])
    plus, minus = torch.tensor([[9.0, 0., 0.]]), torch.tensor([[-9.0, 0., 0.]])
    grid = torch.linspace(-math.pi, math.pi, 4096)[None]
    # Positive logit has the single declared meaning: q(sheet=1), namely pi.
    ap = action_from_logprob(p2c_logprob(grid, mu[:,None], kap[:,None], plus[:,None,:]), grid)
    am = action_from_logprob(p2c_logprob(grid, mu[:,None], kap[:,None], minus[:,None,:]), grid)
    assert circular_distance(ap, torch.tensor([math.pi])) < .02, (ap, 'positive must decode sheet 1')
    assert circular_distance(am, torch.tensor([0.])) < .02, (am, 'negative must decode sheet 0')
    # Explicit 180-degree mutation: flipping the pole coefficients flips the
    # decoded heading by pi; a decoder with the old inverted convention fails.
    assert circular_distance(ap, am + math.pi) < .02, '180-degree sheet mutation not detected'
    # Analytic pull-back actions agree with their forward S1 action for every
    # frozen H/V/R transform, including the antipodal R180 case.
    for op in (PH, PV, PR90, PR180, PR270):
        transformed = action_from_logprob(transformed_logprob(grid, mu[:,None], kap[:,None], plus[:,None,:], torch.tensor([[op]])), grid)
        expected = transform_angle(ap, torch.tensor([[op]])).flatten()
        assert circular_distance(transformed, expected) < .025, (op, transformed, expected)
    # The rendered heading labels obey exactly the same transform contract.
    row = records('val')[0]
    base = render(row, IDENTITY)[3][1]
    for op in (HFLIP, VFLIP, R90, R180, R270):
        changed = render(row, op)[3][1]
        assert abs(float(wrap(changed - transform_angle(base, torch.tensor(op))))) < 1e-5, (op, base, changed)
    print('PASS sheet=1 convention; 180 mutation; H/V/R analytic and rendered labels')

if __name__ == '__main__': main()
