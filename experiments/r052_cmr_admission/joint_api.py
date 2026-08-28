"""Frozen shared r052 proposal-conditioned joint-likelihood primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import torch
from torch import Tensor, nn
import torch.nn.functional as F

K = 12
EPS = 1e-3
DIRECT_LOGIT_SCALE = 4.0


def axial_wrap(x: Tensor) -> Tensor:
    return torch.remainder(x + torch.pi / 2, torch.pi) - torch.pi / 2


def axial_delta(x: Tensor) -> Tensor:
    return axial_wrap(x).abs()


def _log_i0(x: Tensor) -> Tensor:
    # torch.special.i0e is finite through the frozen kappa bound.
    return torch.log(torch.special.i0e(x)) + x.abs()


def axial_von_mises_log_prob(theta: Tensor, mean: Tensor, raw_kappa: Tensor) -> Tensor:
    kappa = F.softplus(raw_kappa).add(EPS).clamp(max=100.0)
    return (kappa * torch.cos(2.0 * axial_wrap(theta - mean))
            - torch.log(torch.as_tensor(torch.pi, dtype=kappa.dtype, device=kappa.device))
            - _log_i0(kappa))


def laplace4_log_prob(target: Tensor, loc: Tensor, raw_scale: Tensor) -> Tensor:
    scale = F.softplus(raw_scale).add(EPS)
    log_scale = scale.log().clamp(-5., 3.)
    scale = log_scale.exp()
    per_dim = -(target[:, None, :] - loc).abs() / scale - log_scale - torch.log(torch.tensor(2., device=target.device))
    return per_dim.mean(-1)


@dataclass
class JointOutput:
    logits: Tensor
    q: Tensor
    class_log_probs: Tensor
    box_loc: Tensor
    box_raw_scale: Tensor
    angle_mean: Tensor
    angle_raw_kappa: Tensor
    candidate_angles: Tensor
    class_log_likelihood: Tensor
    box_log_likelihood: Tensor
    angle_log_likelihood: Tensor
    joint_terms: Tensor
    joint_log_likelihood: Tensor
    marginal_class_log_likelihood: Tensor
    marginal_box_loc: Tensor
    marginal_angle: Tensor
    native_risk: Tensor
    # These responsibilities are target-conditioned and exist only for the
    # training NLL.  Inference must use ``InferenceOutput.class_weights``.
    train_responsibilities: Tensor
    proposal_uids: tuple[str, ...]
    class_uids: tuple[tuple[str, ...], ...]
    candidate_uids: tuple[tuple[tuple[str, ...], ...], ...]


@dataclass
class InferenceOutput:
    """No-GT detector-native marginalization for every proposal/class pair."""
    logits: Tensor
    q: Tensor
    class_log_probs: Tensor
    marginal_class_log_probs: Tensor  # [N,C]
    class_weights: Tensor              # [N,K,C]
    box_residuals: Tensor              # [N,C,4]
    angles: Tensor                     # [N,C]
    native_risk: Tensor                # [N,C]
    proposal_uids: tuple[str, ...]
    class_uids: tuple[tuple[str, ...], ...]
    candidate_uids: tuple[tuple[tuple[str, ...], ...], ...]


class SharedJointLikelihood(nn.Module):
    """The one API used by all r052 controls and CMR.

    Inputs are candidate embeddings [N,K,C], whatever observation operator
    produced them.  The distribution family is deliberately frozen here.
    """
    def __init__(self, channels: int, num_classes: int = 15) -> None:
        super().__init__()
        self.channels, self.num_classes = channels, num_classes
        self.trunk = nn.Sequential(nn.Linear(channels, channels), nn.SiLU(), nn.Linear(channels, channels), nn.SiLU())
        self.posterior = nn.Linear(channels, 1)
        self.class_head = nn.Linear(channels, num_classes)
        self.box_loc_head = nn.Linear(channels, 4)
        self.box_scale_head = nn.Linear(channels, 4)
        self.angle_head = nn.Linear(channels, 2)

    def _candidate_parameters(self, embeddings: Tensor, source_angles: Tensor,
                    posterior_logits: Tensor | None = None):
        """Compute shared candidate parameters without touching a GT target."""
        if embeddings.ndim != 3 or embeddings.shape[1] != K:
            raise ValueError('expected N,K,C candidate embeddings with K=12')
        n, k, _ = embeddings.shape
        if source_angles.shape != (n,):
            raise ValueError('unaligned source angles')
        z = self.trunk(embeddings)
        logits = self.posterior(z).squeeze(-1) if posterior_logits is None else posterior_logits
        if logits.shape != (n, K):
            raise ValueError('posterior logits must be [N,12]')
        class_log_probs = F.log_softmax(self.class_head(z), dim=-1)
        box_loc = self.box_loc_head(z)
        box_raw_scale = self.box_scale_head(z)
        angle_params = self.angle_head(z)
        offsets = torch.arange(K, device=z.device, dtype=z.dtype) * (torch.pi / K)
        candidate_angles = axial_wrap(source_angles[:, None] + offsets)
        angle_mean = axial_wrap(candidate_angles + .25 * torch.tanh(angle_params[..., 0]))
        return (logits, class_log_probs, box_loc, box_raw_scale, angle_mean,
                angle_params[..., 1], candidate_angles)

    @staticmethod
    def _uids(proposal_uids: Sequence[str] | None, n: int, c: int):
        if proposal_uids is None:
            proposal_uids = tuple(f'proposal:{i}' for i in range(n))
        if len(proposal_uids) != n or len(set(proposal_uids)) != n:
            raise ValueError('immutable proposal_uids must be unique and aligned')
        p = tuple(str(x) for x in proposal_uids)
        class_uids = tuple(tuple(f'{uid}:{cls}' for cls in range(c)) for uid in p)
        candidate_uids = tuple(
            tuple(tuple(f'{class_uid}:{k}' for k in range(K)) for class_uid in row)
            for row in class_uids)
        return p, class_uids, candidate_uids

    def forward(self, embeddings: Tensor, proposal_classes: Tensor, box_target: Tensor,
                angle_target: Tensor, source_angles: Tensor,
                posterior_logits: Tensor | None = None,
                proposal_uids: Sequence[str] | None = None) -> JointOutput:
        if embeddings.ndim != 3 or embeddings.shape[1] != K:
            raise ValueError('expected N,K,C candidate embeddings with K=12')
        n, k, _ = embeddings.shape
        if proposal_classes.shape != (n,) or box_target.shape != (n, 4) or angle_target.shape != (n,):
            raise ValueError('unaligned frozen proposal targets')
        (logits, class_log_probs, box_loc, box_raw_scale, angle_mean,
         angle_raw_kappa, candidate_angles) = self._candidate_parameters(
             embeddings, source_angles, posterior_logits)
        q = logits.softmax(-1)
        row = torch.arange(n, device=logits.device)[:, None]
        candidate = torch.arange(k, device=logits.device)[None, :]
        class_ll = class_log_probs[row, candidate, proposal_classes[:, None]]
        box_ll = laplace4_log_prob(box_target, box_loc, box_raw_scale)
        angle_ll = axial_von_mises_log_prob(angle_target[:, None], angle_mean, angle_raw_kappa)
        joint_terms = logits.log_softmax(-1) + class_ll + box_ll + angle_ll
        joint = torch.logsumexp(joint_terms, dim=-1)
        resp = joint_terms.softmax(-1)
        # This is explicitly a training-only quantity.  It uses log resp,
        # never probability-plus-log-probability; no target-conditioned value
        # is exposed as the detector inference posterior.
        marginal_class = torch.logsumexp(resp.clamp_min(1e-12).log() + class_ll, dim=-1)
        marginal_box = (resp[..., None] * box_loc).sum(1)
        sin = (resp * torch.sin(2 * angle_mean)).sum(-1)
        cos = (resp * torch.cos(2 * angle_mean)).sum(-1)
        marginal_angle = .5 * torch.atan2(sin, cos)
        risk = (resp * axial_delta(angle_mean - marginal_angle[:, None]) / (torch.pi / 2)).sum(-1)
        p_uids, c_uids, k_uids = self._uids(proposal_uids, n, self.num_classes)
        return JointOutput(logits, q, class_log_probs, box_loc, box_raw_scale, angle_mean,
                           angle_raw_kappa, candidate_angles, class_ll, box_ll, angle_ll,
                           joint_terms, joint, marginal_class, marginal_box,
                           axial_wrap(marginal_angle), risk, resp, p_uids, c_uids, k_uids)

    def infer(self, embeddings: Tensor, source_angles: Tensor,
              proposal_uids: Sequence[str] | None = None,
              posterior_logits: Tensor | None = None) -> InferenceOutput:
        """Marginalize solely from proposal evidence — no GT enters this path."""
        (logits, class_log_probs, box_loc, _box_raw_scale, angle_mean,
         _angle_raw_kappa, _candidate_angles) = self._candidate_parameters(
             embeddings, source_angles, posterior_logits)
        n, _, c = class_log_probs.shape
        log_q = logits.log_softmax(-1)
        log_joint_class = log_q[..., None] + class_log_probs
        marginal_class = torch.logsumexp(log_joint_class, dim=1)
        weights = log_joint_class.softmax(dim=1)
        box_residuals = (weights[..., None] * box_loc[:, :, None, :]).sum(1)
        sin = (weights * torch.sin(2 * angle_mean[:, :, None])).sum(1)
        cos = (weights * torch.cos(2 * angle_mean[:, :, None])).sum(1)
        angles = axial_wrap(.5 * torch.atan2(sin, cos))
        risk = (weights * axial_delta(angle_mean[:, :, None] - angles[:, None, :]) /
                (torch.pi / 2)).sum(1)
        p_uids, c_uids, k_uids = self._uids(proposal_uids, n, c)
        return InferenceOutput(logits, logits.softmax(-1), class_log_probs,
                               marginal_class, weights, box_residuals, angles,
                               risk, p_uids, c_uids, k_uids)


class ProposalObservationArms(nn.Module):
    """Frozen observation operators; all terminate in one SharedJointLikelihood."""
    def __init__(self, channels: int, num_classes: int = 15, mode: Literal['direct', 'single', 'cmr'] = 'cmr') -> None:
        super().__init__()
        if mode not in ('direct', 'single', 'cmr'):
            raise ValueError(mode)
        self.mode = mode
        self.channels = channels
        self.project = nn.Sequential(nn.Linear(channels, channels), nn.SiLU(), nn.Linear(channels, channels))
        # A nontrivial fixed-scale phase basis makes every direct-V2 residual
        # logit depend on the proposal feature through a nonlinear interaction.
        self.phase = nn.Parameter(torch.randn(K, channels) * .5)
        self.direct_logits = nn.Sequential(nn.Linear(channels, channels), nn.SiLU(), nn.Linear(channels, K))
        self.joint = SharedJointLikelihood(channels, num_classes)

    def candidate_embeddings(self, features: Tensor) -> Tensor:
        """features is [N,C] for direct/single, [N,K,C] for CMR."""
        if self.mode == 'cmr':
            if features.ndim != 3 or features.shape[1] != K:
                raise ValueError('CMR requires the 12 real candidate observations')
            return self.project(features)
        if features.ndim != 2:
            raise ValueError('direct/single require exactly one proposal observation')
        h = self.project(features)
        # Direct V2 is a nonlinear instance-conditioned K-way MLP, not a
        # linear encoded-plus-phase score; single has a real feature x phase
        # interaction through the same nonlinear projection.
        return self.project(torch.tanh(h[:, None, :] * (1. + self.phase[None, :, :])))

    def forward(self, features: Tensor, proposal_classes: Tensor, box_target: Tensor,
                angle_target: Tensor, source_angles: Tensor,
                proposal_uids: Sequence[str] | None = None) -> JointOutput:
        embeddings = self.candidate_embeddings(features)
        logits = (self.direct_logits(features) * DIRECT_LOGIT_SCALE
                  if self.mode == 'direct' else None)
        return self.joint(embeddings, proposal_classes, box_target, angle_target,
                          source_angles, logits, proposal_uids)

    def infer(self, features: Tensor, source_angles: Tensor,
              proposal_uids: Sequence[str] | None = None) -> InferenceOutput:
        embeddings = self.candidate_embeddings(features)
        logits = (self.direct_logits(features) * DIRECT_LOGIT_SCALE
                  if self.mode == 'direct' else None)
        return self.joint.infer(embeddings, source_angles, proposal_uids, logits)


def joint_loss(out: JointOutput) -> Tensor:
    return -out.joint_log_likelihood.mean()
