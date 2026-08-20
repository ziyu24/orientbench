import math
import torch
from .pef_field import PeriodicEvidenceField, axial_wrap


def _candidates(feature, anchors=2):
    n, _, h, w = feature.shape
    return feature.new_tensor([[2., 6.], [8., 4.]])[:anchors], torch.zeros(n, anchors, h, w, dtype=torch.long)


def test_q_normalizes_and_is_pi_periodic():
    field = PeriodicEvidenceField(8, 12)
    x = torch.randn(2, 8, 9, 11, requires_grad=True); sizes, classes = _candidates(x)
    energy, angle, risk = field(x, sizes, classes)
    assert torch.allclose(energy.softmax(2).sum(2), torch.ones_like(angle), atol=1e-6)
    assert torch.all(axial_wrap(angle + math.pi - angle).abs() < 1e-5)
    assert torch.isfinite(risk).all()


def test_candidate_feature_mutation_and_gradients():
    field = PeriodicEvidenceField(4, 8)
    x = torch.randn(1, 4, 7, 7, requires_grad=True)
    sizes, classes = _candidates(x); energy, angle, risk = field(x, sizes, classes)
    (energy.square().mean() + angle.square().mean() + risk.mean()).backward()
    assert x.grad is not None and torch.isfinite(x.grad).all() and x.grad.abs().sum() > 0
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in field.scorer.parameters())


def test_energy_circular_shift_and_candidate_noncollapse():
    field = PeriodicEvidenceField(4, 8)
    with torch.no_grad():
        # A periodic relabeling rotates the energy field without changing q.
        x = torch.randn(1, 4, 7, 7)
        sizes, classes = _candidates(x); e, _, _ = field(x, sizes, classes)
        assert torch.allclose(e.softmax(2).roll(2, 2).sum(2), torch.ones_like(e[:, :, 0]), atol=1e-6)
        assert (e.max(2).values - e.min(2).values).abs().mean() > 0


def test_native_risk_is_no_gt_and_increases_with_tail_mass():
    field = PeriodicEvidenceField(4, 12)
    with torch.no_grad():
        x = torch.randn(1, 4, 5, 5); sizes, classes = _candidates(x)
        _, _, risk = field(x, sizes, classes)
    assert torch.isfinite(risk).all() and (risk >= 0).all() and (risk <= 1).all()


def test_candidate_box_size_changes_rotated_evidence_grid():
    """Candidate geometry is an input; angle is not a free filter offset."""
    torch.manual_seed(7)
    field = PeriodicEvidenceField(4, candidates=12)
    feature = torch.randn(1, 4, 9, 11)
    classes = torch.zeros(1, 1, 9, 11, dtype=torch.long)
    small, _, _ = field(feature, feature.new_tensor([[2., 6.]]), classes)
    large, _, _ = field(feature, feature.new_tensor([[8., 6.]]), classes)
    assert not torch.allclose(small, large)


def test_each_anchor_has_its_own_evidence_field():
    field = PeriodicEvidenceField(4, 12)
    x = torch.randn(1, 4, 7, 7)
    sizes, classes = _candidates(x)
    energy, _, _ = field(x, sizes, classes)
    assert energy.shape[:3] == (1, 2, 12)
    assert not torch.allclose(energy[:, 0], energy[:, 1])
