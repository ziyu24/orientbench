"""Frozen CMR-OBB primitives for decoded-proposal cyclic evidence.

The module deliberately keeps the intervention explicit: a proposal's centre,
size, class and source identity are fixed while each of K periodic candidate
angles is passed independently through the host rotated-RoI extractor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import torch
from torch import Tensor, nn

K_DEFAULT = 12
ROI_SIZE_DEFAULT = 7


def axial_wrap(angle: Tensor) -> Tensor:
    """Map angles to [-pi/2, pi/2) without a non-periodic branch."""
    return torch.remainder(angle + torch.pi / 2, torch.pi) - torch.pi / 2


def build_candidate_ring(proposals: Tensor, batch_ids: Tensor, k: int = K_DEFAULT) -> Tensor:
    """Return flattened (batch,cx,cy,w,h,theta) RoIs for K candidates.

    ``proposals`` is decoded, not anchor-template geometry, and has columns
    ``(cx, cy, w, h, theta)``. Each source proposal owns one contiguous K-row
    block; this invariant is consumed by the provenance ledger.
    """
    if proposals.ndim != 2 or proposals.shape[-1] != 5:
        raise ValueError('proposals must have shape [N, 5] = (cx,cy,w,h,theta)')
    if batch_ids.ndim != 1 or len(batch_ids) != len(proposals):
        raise ValueError('batch_ids must have one entry per proposal')
    if k != K_DEFAULT:
        raise ValueError(f'K is frozen at {K_DEFAULT}, got {k}')
    if not torch.isfinite(proposals).all() or (proposals[:, 2:4] <= 0).any():
        raise ValueError('decoded proposals must be finite with positive width/height')
    offsets = torch.arange(k, device=proposals.device, dtype=proposals.dtype) * (torch.pi / k)
    candidates = proposals[:, None, :].expand(-1, k, -1).clone()
    candidates[..., 4] = axial_wrap(candidates[..., 4] + offsets)
    batches = batch_ids.to(dtype=proposals.dtype)[:, None, None].expand(-1, k, 1)
    return torch.cat((batches, candidates), dim=-1).reshape(-1, 6)


def cyclic_mean(q: Tensor, candidate_angles: Tensor, fallback: Tensor) -> tuple[Tensor, Tensor]:
    """Axial circular mean with a finite, host-angle identity fallback."""
    if q.shape != candidate_angles.shape:
        raise ValueError('q and candidate_angles must both have shape [N,K]')
    sine = (q * torch.sin(2 * candidate_angles)).sum(-1)
    cosine = (q * torch.cos(2 * candidate_angles)).sum(-1)
    concentration = torch.sqrt(sine.square() + cosine.square() + 1e-12)
    mean = 0.5 * torch.atan2(sine, cosine)
    return torch.where(concentration > 1e-5, axial_wrap(mean), axial_wrap(fallback)), concentration


def posterior_tail_risk(q: Tensor, candidate_angles: Tensor, refined: Tensor) -> Tensor:
    """Frozen no-GT risk: expected axial deviation from posterior mean / pi/2."""
    delta = axial_wrap(candidate_angles - refined[:, None]).abs() / (torch.pi / 2)
    return (q * delta).sum(-1).clamp(0., 1.)


@dataclass(frozen=True)
class CandidateProvenance:
    candidate_uid: Tensor
    source_row: Tensor
    batch_id: Tensor
    level_id: Tensor
    cell_id: Tensor
    proposal_id: Tensor

    def select_final(self, kept_source_rows: Tensor) -> Mapping[str, Tensor]:
        """NMS must pass source rows, never reconstruct provenance from boxes."""
        if kept_source_rows.ndim != 1 or kept_source_rows.dtype not in (torch.int32, torch.int64):
            raise ValueError('NMS keep indices must be one-dimensional integer source rows')
        if kept_source_rows.numel() and (kept_source_rows.min() < 0 or kept_source_rows.max() >= len(self.source_row)):
            raise ValueError('NMS keep index outside decoded proposal rows')
        return {name: getattr(self, name)[kept_source_rows] for name in self.__dataclass_fields__}


def make_provenance(batch_ids: Tensor, level_ids: Tensor, cell_ids: Tensor, proposal_ids: Tensor) -> CandidateProvenance:
    """Create immutable decoded-proposal IDs before candidate generation/NMS."""
    values = (batch_ids, level_ids, cell_ids, proposal_ids)
    n = len(batch_ids)
    if any(v.ndim != 1 or len(v) != n for v in values):
        raise ValueError('all provenance components must be rank-1 and aligned')
    if any(v.dtype not in (torch.int32, torch.int64) for v in values):
        raise ValueError('provenance components must use integer identifiers')
    source = torch.arange(n, device=batch_ids.device, dtype=torch.long)
    # Row identity is collision-free within an image batch and remains the only
    # permitted handle across NMS. Component fields are exported for mutation checks.
    uid = source.clone()
    return CandidateProvenance(uid, source, batch_ids.long(), level_ids.long(), cell_ids.long(), proposal_ids.long())


class CMRRoIEvidence(nn.Module):
    """Shared 7x7 candidate scorer plus cyclic posterior/marginal primitives."""

    def __init__(self, channels: int, num_classes: int = 15, k: int = K_DEFAULT,
                 roi_size: int = ROI_SIZE_DEFAULT) -> None:
        super().__init__()
        if k != K_DEFAULT or roi_size != ROI_SIZE_DEFAULT:
            raise ValueError(f'CMR is frozen at K={K_DEFAULT}, RoI={ROI_SIZE_DEFAULT}x{ROI_SIZE_DEFAULT}')
        self.k, self.roi_size, self.num_classes = k, roi_size, num_classes
        self.encoder = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1))
        self.class_embedding = nn.Embedding(num_classes, channels)
        self.evidence = nn.Linear(channels, 1)
        nn.init.zeros_(self.evidence.weight)
        nn.init.zeros_(self.evidence.bias)

    def score_candidate_features(self, candidate_features: Tensor, class_ids: Tensor) -> Tensor:
        """Score [N,K,C,7,7] with exactly one shared encoder/head."""
        if candidate_features.ndim != 5 or candidate_features.shape[1] != self.k:
            raise ValueError(f'expected [N,{self.k},C,{self.roi_size},{self.roi_size}] candidate features')
        if tuple(candidate_features.shape[-2:]) != (self.roi_size, self.roi_size):
            raise ValueError('CMR evidence must consume complete frozen 7x7 rotated RoIs')
        n, k, c, h, w = candidate_features.shape
        if class_ids.shape != (n,) or class_ids.dtype not in (torch.int32, torch.int64):
            raise ValueError('class_ids must be integer [N] decoded proposal classes')
        if (class_ids < 0).any() or (class_ids >= self.num_classes).any():
            raise ValueError('decoded proposal class outside frozen class vocabulary')
        encoded = self.encoder(candidate_features.reshape(n * k, c, h, w)).flatten(1)
        encoded = encoded.reshape(n, k, c) + self.class_embedding(class_ids.long())[:, None]
        return self.evidence(encoded.reshape(n * k, c)).reshape(n, k)

    def forward_from_features(self, candidate_features: Tensor, source_angles: Tensor,
                              class_ids: Tensor) -> Mapping[str, Tensor]:
        logits = self.score_candidate_features(candidate_features, class_ids)
        offsets = torch.arange(self.k, device=logits.device, dtype=logits.dtype) * (torch.pi / self.k)
        angles = axial_wrap(source_angles[:, None] + offsets)
        q = logits.softmax(-1)
        refined, concentration = cyclic_mean(q, angles, source_angles)
        risk = posterior_tail_risk(q, angles, refined)
        # This is the likelihood term consumed by the integration head; it is
        # not a post-hoc score fusion and no detector score is read here.
        log_marginal = torch.logsumexp(logits, dim=-1) - torch.log(torch.tensor(float(self.k), device=logits.device))
        return dict(logits=logits, q=q, candidate_angles=angles, refined_angle=refined,
                    native_risk=risk, concentration=concentration,
                    log_marginal_likelihood=log_marginal)

    def forward_with_extractor(self, feats: tuple[Tensor, ...], proposals: Tensor, batch_ids: Tensor,
                               class_ids: Tensor,
                               roi_extractor: Callable[[tuple[Tensor, ...], Tensor], Tensor]) -> Mapping[str, Tensor]:
        rois = build_candidate_ring(proposals, batch_ids, self.k)
        roi_features = roi_extractor(feats, rois)
        n = len(proposals)
        candidate_features = roi_features.reshape(n, self.k, *roi_features.shape[1:])
        result = dict(self.forward_from_features(candidate_features, proposals[:, 4], class_ids))
        result['candidate_rois'] = rois
        return result

    def forward_direct_with_extractor(self, feats: tuple[Tensor, ...], proposals: Tensor,
                                      batch_ids: Tensor, class_ids: Tensor,
                                      roi_extractor: Callable[[tuple[Tensor, ...], Tensor], Tensor]) -> Mapping[str, Tensor]:
        """Strong DIRECT_DIST control: one host-angle RoI, no grid intervention.

        It reuses exactly the CMR encoder, class embedding and scalar evidence
        head.  A fixed, parameter-free periodic phase code exposes a K-way
        residual distribution without taking K rotated observations.
        """
        rois = torch.cat((batch_ids.to(proposals.dtype)[:, None], proposals), dim=1)
        feature = roi_extractor(feats, rois)
        n, c = len(proposals), feature.shape[1]
        encoded = self.encoder(feature).flatten(1) + self.class_embedding(class_ids.long())
        channel = torch.arange(c, device=feature.device, dtype=feature.dtype) + 1
        phase = torch.arange(self.k, device=feature.device, dtype=feature.dtype)[:, None]
        phase_code = torch.cos(2 * torch.pi * phase * channel[None] / float(self.k))
        logits = self.evidence((encoded[:, None] + phase_code[None]).reshape(n * self.k, c)).reshape(n, self.k)
        offsets = torch.arange(self.k, device=feature.device, dtype=feature.dtype) * (torch.pi / self.k)
        angles = axial_wrap(proposals[:, 4, None] + offsets)
        q = logits.softmax(-1)
        refined, concentration = cyclic_mean(q, angles, proposals[:, 4])
        return dict(logits=logits, q=q, candidate_angles=angles, refined_angle=refined,
                    native_risk=posterior_tail_risk(q, angles, refined), concentration=concentration,
                    log_marginal_likelihood=torch.logsumexp(logits, -1) - torch.log(torch.tensor(float(self.k), device=feature.device)))

    def forward_single_with_extractor(self, feats: tuple[Tensor, ...], proposals: Tensor,
                                      batch_ids: Tensor, class_ids: Tensor,
                                      roi_extractor: Callable[[tuple[Tensor, ...], Tensor], Tensor]) -> Mapping[str, Tensor]:
        """SINGLE_ROI_QUALITY control with one host-angle observation only."""
        rois = torch.cat((batch_ids.to(proposals.dtype)[:, None], proposals), dim=1)
        feature = roi_extractor(feats, rois)
        encoded = self.encoder(feature).flatten(1) + self.class_embedding(class_ids.long())
        quality_logit = self.evidence(encoded).squeeze(-1)
        return dict(quality_logit=quality_logit, native_risk=quality_logit.sigmoid(),
                    refined_angle=axial_wrap(proposals[:, 4]))
