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


def test_axial_circular_shift_rotates_mean_and_preserves_risk():
    field = PeriodicEvidenceField(4, 8)
    with torch.no_grad():
        q = torch.randn(1, 2, 8, 3, 3).softmax(2)
        angle, risk = field.summarize_q(q)
        shifted_angle, shifted_risk = field.summarize_q(q.roll(4, 2))
        assert torch.all(axial_wrap(shifted_angle - angle - math.pi / 2).abs() < 1e-5)
        assert torch.allclose(shifted_risk, risk, atol=1e-6)


def test_native_risk_is_no_gt_and_increases_with_tail_mass():
    field = PeriodicEvidenceField(4, 12)
    with torch.no_grad():
        narrow = torch.zeros(1, 1, 12, 1, 1); narrow[:, :, 0] = 1
        broad = torch.full_like(narrow, 1 / 12)
        _, narrow_risk = field.summarize_q(narrow)
        _, broad_risk = field.summarize_q(broad)
    assert torch.isfinite(broad_risk).all() and (broad_risk >= 0).all() and (broad_risk <= 1).all()
    assert narrow_risk.item() == 0 and broad_risk.item() > narrow_risk.item()


def test_candidate_box_size_changes_rotated_evidence_grid():
    """Candidate geometry is an input; angle is not a free filter offset."""
    torch.manual_seed(7)
    field = PeriodicEvidenceField(4, candidates=12)
    feature = torch.randn(1, 4, 9, 11)
    classes = torch.zeros(1, 1, 9, 11, dtype=torch.long)
    small, _, _ = field(feature, feature.new_tensor([[2., 6.]]), classes)
    large, _, _ = field(feature, feature.new_tensor([[8., 6.]]), classes)
    assert not torch.allclose(small, large)


def test_candidate_class_changes_evidence_without_score_input():
    torch.manual_seed(19)
    field = PeriodicEvidenceField(4, candidates=12, num_classes=3)
    feature = torch.randn(1, 4, 9, 11)
    sizes = feature.new_tensor([[2., 6.]])
    cls0 = torch.zeros(1, 1, 9, 11, dtype=torch.long)
    cls1 = torch.ones(1, 1, 9, 11, dtype=torch.long)
    e0, _, _ = field(feature, sizes, cls0)
    e1, _, _ = field(feature, sizes, cls1)
    assert not torch.allclose(e0, e1)


def test_each_anchor_has_its_own_evidence_field():
    field = PeriodicEvidenceField(4, 12)
    x = torch.randn(1, 4, 7, 7)
    sizes, classes = _candidates(x)
    energy, _, _ = field(x, sizes, classes)
    assert energy.shape[:3] == (1, 2, 12)
    assert not torch.allclose(energy[:, 0], energy[:, 1])


def test_identity_field_has_zero_residual_about_host_angle():
    field = PeriodicEvidenceField(4, 12)
    field.init_identity()
    x = torch.randn(1, 4, 7, 7)
    sizes, classes = _candidates(x, anchors=1)
    host = torch.full((1, 1, 7, 7), .37)
    _, residual, risk = field(x, sizes, classes, host)
    assert torch.all(axial_wrap(residual).abs() < 1e-6)
    assert torch.isfinite(risk).all()
