import math
import torch
from .pef_field import PeriodicEvidenceField, axial_wrap


def test_q_normalizes_and_is_pi_periodic():
    field = PeriodicEvidenceField(8, 12)
    energy, angle, risk = field(torch.randn(2, 8, 9, 11, requires_grad=True))
    assert torch.allclose(energy.softmax(1).sum(1), torch.ones_like(angle), atol=1e-6)
    assert torch.all(axial_wrap(angle + math.pi - angle).abs() < 1e-5)
    assert torch.isfinite(risk).all()


def test_candidate_feature_mutation_and_gradients():
    field = PeriodicEvidenceField(4, 8)
    x = torch.randn(1, 4, 7, 7, requires_grad=True)
    energy, angle, risk = field(x)
    (energy.square().mean() + angle.square().mean() + risk.mean()).backward()
    assert x.grad is not None and torch.isfinite(x.grad).all() and x.grad.abs().sum() > 0
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in field.scorer.parameters())
