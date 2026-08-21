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
        # A 2x2 candidate-aligned rectangle grid: every cell is sampled after
        # rotating the candidate's own width/height frame by theta.
        self.scorer = nn.Sequential(
            nn.Conv2d(channels * 4 + class_embed_dim, channels, 1), nn.SiLU(),
            nn.Conv2d(channels, 1, 1))
        self.register_buffer('candidate_angles', torch.arange(candidates) * (math.pi / candidates), persistent=True)

    def init_identity(self) -> None:
        """Start from an almost-uniform field, hence a zero residual angle.

        A tiny non-zero final scorer weight keeps the candidate sampler and
        scorer on the gradient path from the first smoke batch, while the
        concentration guard below still gives exact host-angle identity.
        """
        last = self.scorer[-1]
        nn.init.normal_(last.weight, mean=0., std=1e-5)
        nn.init.zeros_(last.bias)

    def forward(self, feature: torch.Tensor, candidate_sizes: torch.Tensor,
                candidate_classes: torch.Tensor, host_angles: torch.Tensor | None = None):
        """Return energy/q summaries shaped ``N,A,K,H,W`` / ``N,A,H,W``."""
        n, _, h, w = feature.shape
        candidate_sizes = torch.as_tensor(candidate_sizes, device=feature.device, dtype=feature.dtype)
        if candidate_sizes.ndim != 2 or candidate_sizes.shape[1] != 2 or (candidate_sizes <= 0).any():
            raise ValueError('candidate_sizes must have shape [anchors, 2] and be positive')
        anchors = candidate_sizes.shape[0]
        if tuple(candidate_classes.shape) != (n, anchors, h, w):
            raise ValueError('candidate_classes must have shape [N, anchors, H, W]')
        if host_angles is None:
            host_angles = feature.new_zeros((n, anchors, h, w))
        if tuple(host_angles.shape) != (n, anchors, h, w):
            raise ValueError('host_angles must have shape [N, anchors, H, W]')
        yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=feature.device, dtype=feature.dtype),
                                torch.linspace(-1, 1, w, device=feature.device, dtype=feature.dtype), indexing='ij')
        base = torch.stack((xx, yy), -1).expand(n, h, w, 2)
        norm = feature.new_tensor((2 / max(w - 1, 1), 2 / max(h - 1, 1)))
        corner_signs = feature.new_tensor(((-1., -1.), (-1., 1.), (1., -1.), (1., 1.)))
        all_anchor_energy = []
        for anchor in range(anchors):
            cls = self.class_embedding(candidate_classes[:, anchor].long()).permute(0, 3, 1, 2)
            all_angle_energy = []
            width, height = candidate_sizes[anchor]
            for offset in self.candidate_angles.to(feature):
                # Candidate angles are an axial ring around the host decoder.
                # They still change the actual rotated sampling grid at every
                # FPN location, but a uniform untrained field is a zero
                # correction rather than an arbitrary global heading.
                theta = host_angles[:, anchor] + offset
                c, s = torch.cos(theta), torch.sin(theta)
                # [u*w, v*h] is first defined in the candidate's local
                # rectangle frame and only then rotated by theta.  The four
                # grids are tiled in the output-width dimension so one CUDA
                # kernel evaluates the full 2x2 candidate grid per theta.
                u, v = corner_signs[:, 0], corner_signs[:, 1]
                offsets = self.sample_fraction * torch.stack(
                    (u[None, :, None, None] * width * c[:, None]
                     - v[None, :, None, None] * height * s[:, None],
                     u[None, :, None, None] * width * s[:, None]
                     + v[None, :, None, None] * height * c[:, None]), -1) * norm
                grids = (base[:, None] + offsets).clamp(-1, 1)
                tiled_grid = grids.permute(0, 2, 1, 3, 4).reshape(n, h, 4 * w, 2)
                tiled = F.grid_sample(feature, tiled_grid, align_corners=True)
                samples = tiled.reshape(n, feature.shape[1], h, 4, w).permute(0, 1, 3, 2, 4).reshape(n, 4 * feature.shape[1], h, w)
                all_angle_energy.append(self.scorer(torch.cat((samples, cls), 1)).squeeze(1))
            all_anchor_energy.append(torch.stack(all_angle_energy, 1))
        energy = torch.stack(all_anchor_energy, 1)
        return energy, *self.summarize_q(energy.softmax(2))

    def summarize_q(self, q: torch.Tensor):
        """Return axial circular mean and no-GT tail risk from a K-way q."""
        if q.ndim != 5 or q.shape[2] != self.candidates:
            raise ValueError('q must have shape [N, anchors, candidates, H, W]')
        angles = self.candidate_angles.to(q).view(1, 1, -1, 1, 1)
        sine = (q * torch.sin(2 * angles)).sum(2)
        cosine = (q * torch.cos(2 * angles)).sum(2)
        # ``hypot(0, 0)`` has an undefined backward direction.  The intended
        # identity initialization makes the axial resultant nearly zero, so
        # use a tiny squared-norm floor to keep the candidate-field gradient
        # finite while leaving the 1e-3 concentration gate unchanged.
        concentration = torch.sqrt(sine.square() + cosine.square() + 1e-12)
        angle = .5 * torch.atan2(sine, cosine)
        angle = torch.where(concentration > 1e-3, angle, torch.zeros_like(angle))
        delta = axial_wrap(angles - angle.unsqueeze(2)).abs()
        risk = (q * (delta >= (math.pi / 6))).sum(2)
        return angle, risk
