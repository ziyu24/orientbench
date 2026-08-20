"""Per-candidate, axial-periodic visual evidence fields for PEF-OBB."""
from __future__ import annotations

import math
import torch
from torch import nn
from torch.nn import functional as F


def axial_wrap(x: torch.Tensor) -> torch.Tensor:
    return .5 * torch.atan2(torch.sin(2 * x), torch.cos(2 * x))


class PeriodicEvidenceField(nn.Module):
    """Evaluate a separate K-way evidence field for every anchor candidate.

    Candidate geometry is ``(cx, cy, w, h, class)``: a distinct FPN anchor
    supplies center/size, class is a discrete detector candidate condition,
    and only theta varies around the fixed candidate box.  The scorer itself
    is shared across anchor, class and angle; it never receives score or GT.
    """
    def __init__(self, channels: int, candidates: int = 12, num_classes: int = 15,
                 class_embed_dim: int = 8, sample_fraction: float = .25):
        super().__init__()
        if candidates < 4 or candidates % 2:
            raise ValueError('candidates must be an even number >= 4')
        self.candidates = candidates
        self.sample_fraction = float(sample_fraction)
        self.class_embedding = nn.Embedding(num_classes, class_embed_dim)
        self.scorer = nn.Sequential(
            nn.Conv2d(channels * 2 + class_embed_dim, channels, 1), nn.SiLU(),
            nn.Conv2d(channels, 1, 1))
        self.register_buffer('candidate_angles', torch.arange(candidates) * (math.pi / candidates), persistent=True)

    def forward(self, feature: torch.Tensor, candidate_sizes: torch.Tensor,
                candidate_classes: torch.Tensor):
        """Return energy/q summaries shaped ``N,A,K,H,W`` / ``N,A,H,W``."""
        n, _, h, w = feature.shape
        candidate_sizes = torch.as_tensor(candidate_sizes, device=feature.device, dtype=feature.dtype)
        if candidate_sizes.ndim != 2 or candidate_sizes.shape[1] != 2 or (candidate_sizes <= 0).any():
            raise ValueError('candidate_sizes must have shape [anchors, 2] and be positive')
        anchors = candidate_sizes.shape[0]
        if tuple(candidate_classes.shape) != (n, anchors, h, w):
            raise ValueError('candidate_classes must have shape [N, anchors, H, W]')
        yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=feature.device, dtype=feature.dtype),
                                torch.linspace(-1, 1, w, device=feature.device, dtype=feature.dtype), indexing='ij')
        base = torch.stack((xx, yy), -1).expand(n, h, w, 2)
        norm = feature.new_tensor((2 / max(w - 1, 1), 2 / max(h - 1, 1)))
        all_anchor_energy = []
        for anchor in range(anchors):
            cls = self.class_embedding(candidate_classes[:, anchor].long()).permute(0, 3, 1, 2)
            all_angle_energy = []
            for theta in self.candidate_angles.to(feature):
                offset = self.sample_fraction * candidate_sizes[anchor] * torch.stack((torch.cos(theta), torch.sin(theta))) * norm
                plus = F.grid_sample(feature, (base + offset).clamp(-1, 1), align_corners=True)
                minus = F.grid_sample(feature, (base - offset).clamp(-1, 1), align_corners=True)
                all_angle_energy.append(self.scorer(torch.cat((plus, minus, cls), 1)).squeeze(1))
            all_anchor_energy.append(torch.stack(all_angle_energy, 1))
        energy = torch.stack(all_anchor_energy, 1)
        q = energy.softmax(2)
        angles = self.candidate_angles.to(feature).view(1, 1, -1, 1, 1)
        angle = .5 * torch.atan2((q * torch.sin(2 * angles)).sum(2), (q * torch.cos(2 * angles)).sum(2))
        delta = axial_wrap(angles - angle.unsqueeze(2)).abs()
        risk = (q * (delta >= (math.pi / 6))).sum(2)
        return energy, angle, risk
