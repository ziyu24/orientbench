"""Mathematical core for r048 P2C-Lift; independent of detector scores."""
import math
import torch
from torch import nn

TAU=2*math.pi
def wrap(x): return torch.remainder(x+math.pi,TAU)-math.pi
def vm_logprob(angle,mu,kappa):
    return kappa*torch.cos(wrap(angle-mu))-math.log(TAU)-torch.log(torch.i0(kappa).clamp_min(1e-12))
def axial_vm_nll(delta,mu2,kappa):
    """Proper likelihood on RP1: doubled residual is an S1 variable."""
    return -vm_logprob(2*delta,mu2,kappa).mean()
def circular_bayes_action(axis_mu2,pole_logit):
    """Mean direction of the lifted two-sheet distribution."""
    axis=.5*axis_mu2; p=torch.sigmoid(pole_logit)
    return torch.atan2((2*p-1)*torch.sin(axis),(2*p-1)*torch.cos(axis))
def intrinsic_confidence(kappa,pole_logit):
    """Intrinsic orientation certainty: axial concentration × pole certainty."""
    return torch.tanh(kappa.clamp_min(0)/4)*torch.abs(2*torch.sigmoid(pole_logit)-1)
def action(phi,kind):
    if kind=='hflip': return math.pi-phi
    if kind=='vflip': return -phi
    if kind.startswith('rot'): return phi+math.radians(float(kind[3:]))
    raise ValueError(kind)
def transform_distribution(axis_mu2,pole_logit,kind):
    # Analytic S1 action lifted back to doubled axial sheet; reflections flip sheet.
    if kind=='hflip': return wrap(2*(math.pi-.5*axis_mu2)), -pole_logit
    if kind=='vflip': return wrap(-axis_mu2), -pole_logit
    if kind.startswith('rot'): return wrap(axis_mu2+2*math.radians(float(kind[3:]))), pole_logit
    raise ValueError(kind)
def distribution_kl(mu_a,k_a,p_a,mu_b,k_b,p_b):
    # Differentiable sampled KL over both sheets; used for frozen equivariance loss.
    grid=torch.linspace(-math.pi,math.pi,72,device=mu_a.device)[None,:]
    def logp(mu,k,p):
      axial=vm_logprob(2*grid,mu[:,None],k[:,None])-math.log(2)
      pole=torch.nn.functional.logsigmoid(p)[:,None]
      other=torch.nn.functional.logsigmoid(-p)[:,None]
      return torch.logsumexp(torch.stack([axial+pole,axial+other],0),0)
    la,lb=logp(mu_a,k_a,p_a),logp(mu_b,k_b,p_b);pa=torch.softmax(la,1)
    return (pa*(la-lb)).sum(1).mean()
class P2CHeads(nn.Module):
 def __init__(self,d):
  super().__init__();self.axis=nn.Linear(d,3);self.pole=nn.Linear(d,1);self.vector=nn.Linear(d,2)
 def forward(self,x):
  a=self.axis(x);mu2=torch.atan2(a[:,1],a[:,0]);k=torch.nn.functional.softplus(a[:,2])+1e-4
  return mu2,k,self.pole(x).flatten(),torch.tanh(self.vector(x))
