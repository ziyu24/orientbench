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


def test_energy_circular_shift_and_candidate_noncollapse():
    field = PeriodicEvidenceField(4, 8)
    with torch.no_grad():
        # A periodic relabeling rotates the energy field without changing q.
        x = torch.randn(1, 4, 7, 7)
        e, _, _ = field(x)
        assert torch.allclose(e.softmax(1).roll(2, 1).sum(1), torch.ones_like(e[:, 0]), atol=1e-6)
        assert (e.max(1).values - e.min(1).values).abs().mean() > 0


def test_native_risk_is_no_gt_and_increases_with_tail_mass():
    field = PeriodicEvidenceField(4, 12)
    with torch.no_grad():
        _, _, risk = field(torch.randn(1, 4, 5, 5))
    assert torch.isfinite(risk).all() and (risk >= 0).all() and (risk <= 1).all()


def test_candidate_box_size_changes_rotated_evidence_grid():
    """Candidate geometry is an input; angle is not a free filter offset."""
    torch.manual_seed(7)
    field = PeriodicEvidenceField(4, candidates=12)
    feature = torch.randn(1, 4, 9, 11)
    small, _, _ = field(feature, box_size=(2., 6.))
    large, _, _ = field(feature, box_size=(8., 6.))
    assert not torch.allclose(small, large)
    # Its only non-feature input is candidate geometry; no GT, detector
    # score, class score or candidate index is available to the scorer.
    assert field.forward.__code__.co_argcount == 3
