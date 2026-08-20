"""Candidate-conditioned, axial-periodic visual evidence field for PEF-OBB."""
from __future__ import annotations

import math
import torch
from torch import nn
from torch.nn import functional as F


def axial_wrap(x: torch.Tensor) -> torch.Tensor:
    return .5 * torch.atan2(torch.sin(2 * x), torch.cos(2 * x))


class PeriodicEvidenceField(nn.Module):
    """Score a candidate box's K axial orientations with shared evidence.

    ``box_size`` is expressed in feature pixels and is held fixed while the
    candidate angle rotates.  Consequently the sampled evidence changes with
    both the candidate's geometry and its angle, rather than being a generic
    orientation filter at each FPN location.
    """
    def __init__(self, channels: int, candidates: int = 12, sample_radius: float = .25):
        super().__init__()
        if candidates < 4 or candidates % 2:
            raise ValueError('candidates must be an even number >= 4')
        self.candidates = candidates
        self.sample_radius = float(sample_radius)
        self.scorer = nn.Sequential(
            nn.Conv2d(channels * 2, channels, 1), nn.SiLU(), nn.Conv2d(channels, 1, 1))
        self.register_buffer('candidate_angles', torch.arange(candidates) * (math.pi / candidates), persistent=True)

    def forward(self, feature: torch.Tensor, box_size=None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        n, _, h, w = feature.shape
        if box_size is None:
            # Kept solely for unit-level numerical tests.  Detector calls
            # always supply the frozen per-level candidate box size.
            box_size = feature.new_tensor((6., 6.))
        box_size = torch.as_tensor(box_size, device=feature.device, dtype=feature.dtype)
        if box_size.numel() != 2 or not torch.isfinite(box_size).all() or (box_size <= 0).any():
            raise ValueError('box_size must be two finite positive feature-pixel dimensions')
        yy, xx = torch.meshgrid(
            torch.linspace(-1, 1, h, device=feature.device, dtype=feature.dtype),
            torch.linspace(-1, 1, w, device=feature.device, dtype=feature.dtype), indexing='ij')
        base = torch.stack((xx, yy), -1).expand(n, h, w, 2)
        norm = torch.tensor((2 / max(w - 1, 1), 2 / max(h - 1, 1)), device=feature.device, dtype=feature.dtype)
        energies = []
        # Same scorer weights at all candidate angles; only the rotated grid changes.
        for theta in self.candidate_angles.to(feature):
            # The two samples sit at fixed fractions of the same candidate
            # box's major/minor axes; theta is the only changing variable.
            offset = self.sample_radius * box_size * torch.stack((torch.cos(theta), torch.sin(theta))) * norm
            plus = F.grid_sample(feature, (base + offset).clamp(-1, 1), align_corners=True)
            minus = F.grid_sample(feature, (base - offset).clamp(-1, 1), align_corners=True)
            energies.append(self.scorer(torch.cat((plus, minus), 1)).squeeze(1))
        energy = torch.stack(energies, 1)
        q = energy.softmax(1)
        # Axial circular mean and fixed tail-mass risk, neither uses a detector score.
        angles = self.candidate_angles.to(feature).view(1, -1, 1, 1)
        angle = .5 * torch.atan2((q * torch.sin(2 * angles)).sum(1), (q * torch.cos(2 * angles)).sum(1))
        delta = axial_wrap(angles - angle.unsqueeze(1)).abs()
        risk = (q * (delta >= (math.pi / 6))).sum(1)
        return energy, angle, risk
