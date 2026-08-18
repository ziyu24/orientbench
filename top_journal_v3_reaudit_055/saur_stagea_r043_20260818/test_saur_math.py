import torch

from .saur_head import axial_wrap, geometry_identifiability


def test_axial_periodicity():
    x = torch.tensor([.37])
    assert torch.allclose(axial_wrap(x), axial_wrap(x + torch.pi), atol=1e-6)


def test_geometry_gate_is_swap_invariant_and_square_suppressed():
    square = geometry_identifiability(torch.tensor([10.]), torch.tensor([10.]))
    elongated = geometry_identifiability(torch.tensor([50.]), torch.tensor([10.]))
    swapped = geometry_identifiability(torch.tensor([10.]), torch.tensor([50.]))
    assert square.item() < elongated.item()
    assert torch.allclose(elongated, swapped, atol=1e-7)


def test_axial_gradient_is_finite():
    x = torch.tensor([.2], requires_grad=True)
    y = axial_wrap(x).square().sum()
    y.backward()
    assert torch.isfinite(x.grad).all()
