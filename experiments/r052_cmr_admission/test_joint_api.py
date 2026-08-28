"""Focused unit tests for frozen r052 joint-likelihood invariants."""
from __future__ import annotations

import torch

from .joint_api import K, ProposalObservationArms, joint_loss


def _inputs(n: int = 24, c: int = 32):
    torch.manual_seed(52)
    return (torch.randn(n, c), torch.randn(n, K, c),
            torch.randint(0, 15, (n,)), torch.randn(n, 4),
            torch.randn(n), torch.randn(n))


def test_all_arms_use_joint_class_box_angle_likelihood_and_gradients():
    single, candidates, labels, box, angle, source = _inputs()
    for mode, features in (('direct', single), ('single', single), ('cmr', candidates)):
        arm = ProposalObservationArms(32, mode=mode)
        out = arm(features, labels, box, angle, source)
        loss = joint_loss(out)
        loss.backward()
        assert torch.isfinite(loss)
        assert out.class_log_likelihood.shape == (len(labels), K)
        assert out.box_log_likelihood.shape == (len(labels), K)
        assert out.angle_log_likelihood.shape == (len(labels), K)
        assert arm.joint.class_head.weight.grad.abs().sum() > 0
        assert arm.joint.box_loc_head.weight.grad.abs().sum() > 0
        assert arm.joint.angle_head.weight.grad.abs().sum() > 0


def test_direct_v2_is_instance_conditioned():
    single, _, labels, box, angle, source = _inputs()
    arm = ProposalObservationArms(32, mode='direct')
    out = arm(single.requires_grad_(), labels, box, angle, source)
    diff = (out.q[0] - out.q[1]).abs().sum()
    grad = torch.autograd.grad((out.q[:, 1].log() - out.q[:, 0].log()).sum(), single)[0]
    assert diff > .05
    assert grad.norm(dim=1).median() > 1e-6


def test_detach_preserves_forward_but_removes_posterior_path_gradient():
    single, _, labels, box, angle, source = _inputs()
    arm = ProposalObservationArms(32, mode='direct')
    out = arm(single, labels, box, angle, source)
    normal = joint_loss(out)
    detached = -torch.logsumexp(
        out.q.detach().log() + out.class_log_likelihood + out.box_log_likelihood + out.angle_log_likelihood,
        dim=-1).mean()
    assert torch.allclose(normal, detached, atol=1e-6)
