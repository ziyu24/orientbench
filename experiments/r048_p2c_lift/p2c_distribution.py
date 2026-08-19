"""Frozen mathematical contract for the r048 projective-to-circular lift.

All angles here are *relative to the rectified OBB axis*.  The axial state is
canonicalised to [-pi/2, pi/2), while the second sheet is the bow/stern pole.
The pole head is conditional on the axial residual through its first Fourier
terms; it is not a standalone endpoint-sign classifier.
"""
import math
import torch
from torch import nn

TAU = 2 * math.pi
LOG2 = math.log(2.0)

def wrap(x):
    return torch.remainder(x + math.pi, TAU) - math.pi

def axial_wrap(x):
    return torch.remainder(x + math.pi / 2, math.pi) - math.pi / 2

def vm_logprob(angle, mu, kappa):
    return kappa * torch.cos(wrap(angle - mu)) - math.log(TAU) - torch.log(torch.i0(kappa).clamp_min(1e-12))

def axial_vm_nll(delta, mu2, kappa):
    """Proper RP1 likelihood; the factor two is its required Jacobian."""
    return -(vm_logprob(2 * axial_wrap(delta), mu2, kappa) + LOG2).mean()

def pole_logit(coeff, delta):
    """Logit of q(s=1 | delta,I), conditional on the actual axial residual."""
    return coeff[..., 0] + coeff[..., 1] * torch.cos(2 * delta) + coeff[..., 2] * torch.sin(2 * delta)

def _sheet(phi):
    # Canonical delta has cos(delta) >= 0; the other antipodal point is sheet 1.
    return (torch.cos(wrap(phi)) < 0).to(torch.long)

def p2c_logprob(phi, mu2, kappa, coeff):
    """Log density on S1 of q_axis(delta) q_pole(sheet | delta)."""
    delta = axial_wrap(phi)
    axis = vm_logprob(2 * delta, mu2[..., None] if phi.ndim > mu2.ndim else mu2,
                      kappa[..., None] if phi.ndim > kappa.ndim else kappa) + LOG2
    c = coeff[..., None, :] if phi.ndim > coeff.ndim - 1 else coeff
    logit = pole_logit(c, delta)
    # `pole_logit` is q(sheet=1); this same convention is used by BCE, density,
    # decoding and confidence.  Do not invert it in one consumer only.
    return axis + torch.where(_sheet(phi).bool(), torch.nn.functional.logsigmoid(logit), torch.nn.functional.logsigmoid(-logit))

def _grid(x, n=144):
    return torch.linspace(-math.pi, math.pi, n, device=x.device, dtype=x.dtype)[None, :]

def _density_stats(mu2, kappa, coeff, grid=None):
    g = _grid(mu2) if grid is None else grid
    lp = p2c_logprob(g, mu2[:, None], kappa[:, None], coeff[:, None, :])
    # Equal spacing integrates to one; normalise removes endpoint discretisation error.
    w = torch.softmax(lp, dim=1)
    return g, lp, w

def circular_bayes_action(mu2, kappa, coeff):
    """Bayes action for circular absolute error (circular mean direction)."""
    g, _, w = _density_stats(mu2, kappa, coeff)
    return torch.atan2((w * torch.sin(g)).sum(1), (w * torch.cos(g)).sum(1))

def intrinsic_confidence(mu2, kappa, coeff):
    """Intrinsic (no detector score) concentration × expected pole certainty."""
    g, _, w = _density_stats(mu2, kappa, coeff)
    q_sheet1 = torch.sigmoid(pole_logit(coeff[:, None, :], axial_wrap(g)))
    return torch.tanh(kappa.clamp_min(0) / 4) * (w * torch.abs(2 * q_sheet1 - 1)).sum(1)

def probability_within(pred, mu2, kappa, coeff, degrees=90):
    g, _, w = _density_stats(mu2, kappa, coeff)
    e = torch.abs(wrap(g - pred[:, None]))
    return (w * (e < math.radians(degrees)).to(w.dtype)).sum(1)

IDENTITY, HFLIP, VFLIP, R90, R180, R270 = range(6)

def transform_angle(phi, op):
    """Forward S1 action for the six frozen image transforms."""
    if not torch.is_tensor(op):
        op = torch.as_tensor(op, device=phi.device if torch.is_tensor(phi) else None)
    out = phi
    out = torch.where(op == HFLIP, math.pi - phi, out)
    out = torch.where(op == VFLIP, -phi, out)
    out = torch.where(op == R90, phi + math.pi / 2, out)
    out = torch.where(op == R180, phi + math.pi, out)
    out = torch.where(op == R270, phi + 3 * math.pi / 2, out)
    return wrap(out)

def transformed_logprob(phi, src_mu2, src_kappa, src_coeff, op):
    """Analytic pull-back log p_g(phi)=log p(g^-1 phi) for H/V/R actions."""
    if not torch.is_tensor(op): op = torch.as_tensor(op, device=phi.device)
    inv = phi
    inv = torch.where(op == HFLIP, math.pi - phi, inv)
    inv = torch.where(op == VFLIP, -phi, inv)
    inv = torch.where(op == R90, phi - math.pi / 2, inv)
    inv = torch.where(op == R180, phi - math.pi, inv)
    inv = torch.where(op == R270, phi - 3 * math.pi / 2, inv)
    return p2c_logprob(wrap(inv), src_mu2, src_kappa, src_coeff)

def equivariance_kl(aug_mu2, aug_kappa, aug_coeff, src_mu2, src_kappa, src_coeff, op):
    """KL(q_aug || g q_src), exact group action evaluated on S1 quadrature."""
    g = _grid(aug_mu2)
    la = p2c_logprob(g, aug_mu2[:, None], aug_kappa[:, None], aug_coeff[:, None, :])
    lb = transformed_logprob(g, src_mu2[:, None], src_kappa[:, None], src_coeff[:, None, :], op[:, None])
    pa = torch.softmax(la, dim=1)
    return (pa * (la - lb)).sum(1).mean()

class P2CHeads(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.axis = nn.Linear(dim, 3)
        self.pole = nn.Linear(dim, 3)
        self.vector = nn.Linear(dim, 2)

    def forward(self, x):
        a = self.axis(x)
        mu2 = torch.atan2(a[:, 1], a[:, 0])
        kappa = torch.nn.functional.softplus(a[:, 2]) + 1e-4
        return mu2, kappa, self.pole(x), torch.tanh(self.vector(x))
