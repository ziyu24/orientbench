import inspect
import torch
from cora_head import (CORAAngleBranchRetinaHead, axial_wrap, counterfactual_angles,
                       counterfactual_harm_logits, normalized_harm)


def test_pi_periodicity():
    x = torch.tensor([-2.4, -.4, 0., .8, 2.6])
    assert torch.allclose(axial_wrap(x), axial_wrap(x + torch.pi), atol=1e-6)


def test_zero_intervention_identity_and_angle_only():
    angle = torch.tensor([.2, -.8])
    box = torch.tensor([[1., 2., 3., 4., .2], [5., 6., 7., 8., -.8]])
    changed = box.clone()
    changed[:, -1] = counterfactual_angles(box[:, -1], torch.zeros(2))
    assert torch.equal(box, changed)
    changed[:, -1] = counterfactual_angles(box[:, -1], torch.tensor([5., -10.]))
    assert torch.equal(box[:, :-1], changed[:, :-1])


def test_harm_bounds_and_counterfactual_mutation():
    err = torch.tensor([0., .1, 1.])
    harm = normalized_harm(err)
    assert bool(((harm >= 0) & (harm <= 1)).all())
    angle = torch.tensor([0.])
    assert not torch.equal(counterfactual_angles(angle, torch.tensor([5.])), angle)


def test_counterfactual_logits_identity_mutation_and_gradient():
    base = torch.zeros(2, 8, requires_grad=True)
    slope = torch.tensor([.2, -.4], requires_grad=True)
    delta = torch.tensor([0., 10.])
    logits = counterfactual_harm_logits(base, slope, delta)
    assert torch.equal(logits[:, 0], base)
    assert not torch.equal(logits[:, 0], logits[:, 1])
    logits.square().mean().backward()
    assert torch.isfinite(base.grad).all() and torch.isfinite(slope.grad).all()
    assert slope.grad.abs().sum() > 0


def test_inference_signature_has_no_ground_truth_input():
    params = inspect.signature(CORAAngleBranchRetinaHead.predict_by_feat).parameters
    assert not any('gt' in name.lower() for name in params)
