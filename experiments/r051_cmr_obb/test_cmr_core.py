import pytest
import torch

from experiments.r051_cmr_obb.cmr_core import (CMRRoIEvidence, K_DEFAULT,
    axial_wrap, build_candidate_ring, make_provenance, posterior_tail_risk)


def _proposals():
    return torch.tensor([[20., 30., 40., 10., .2], [50., 60., 30., 8., -.4]])


def test_ring_is_pi_periodic_and_preserves_non_angle_fields():
    proposals = _proposals(); rois = build_candidate_ring(proposals, torch.tensor([0, 1]))
    assert rois.shape == (2 * K_DEFAULT, 6)
    ring = rois.reshape(2, K_DEFAULT, 6)
    assert torch.allclose(ring[..., 1:5], proposals[:, None, :4].expand(-1, K_DEFAULT, -1))
    assert torch.allclose(axial_wrap(ring[:, 0, 5] + torch.pi), ring[:, 0, 5])


def test_shared_candidate_evidence_has_circular_shift_and_mutation_response():
    torch.manual_seed(1); module = CMRRoIEvidence(channels=3)
    with torch.no_grad(): module.evidence.weight.fill_(.2)
    feat = torch.randn(2, K_DEFAULT, 3, 7, 7, requires_grad=True)
    first = module.forward_from_features(feat, _proposals()[:, 4])
    shifted = module.forward_from_features(feat.roll(1, 1), _proposals()[:, 4])
    assert torch.allclose(shifted['q'], first['q'].roll(1, 1), atol=1e-6)
    altered = feat.detach().clone(); altered[:, 3] += 10
    changed = module.forward_from_features(altered, _proposals()[:, 4])
    assert not torch.allclose(first['q'], changed['q'])
    (first['native_risk'].sum() + first['log_marginal_likelihood'].sum()).backward()
    assert torch.isfinite(feat.grad).all() and feat.grad.abs().sum() > 0


def test_q_normalizes_and_risk_grows_when_mass_is_spread():
    angles = torch.arange(K_DEFAULT).float()[None] * torch.pi / K_DEFAULT
    sharp = torch.full((1, K_DEFAULT), 1e-6); sharp[:, 0] = 1.; sharp /= sharp.sum(-1, keepdim=True)
    broad = torch.full((1, K_DEFAULT), 1 / K_DEFAULT)
    assert posterior_tail_risk(broad, angles, torch.zeros(1)) > posterior_tail_risk(sharp, angles, torch.zeros(1))


def test_provenance_is_selected_by_explicit_pre_nms_rows_and_rejects_mutations():
    p = make_provenance(torch.tensor([0, 0, 1]), torch.tensor([2, 3, 2]), torch.tensor([8, 9, 10]), torch.tensor([20, 21, 22]))
    final = p.select_final(torch.tensor([2, 0]))
    assert final['candidate_uid'].tolist() == [2, 0]
    with pytest.raises(ValueError): p.select_final(torch.tensor([3]))
    with pytest.raises(ValueError): p.select_final(torch.tensor([0.]))
