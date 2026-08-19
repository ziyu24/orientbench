"""Frozen r048 development metrics, independent of model-selection code."""
import math,numpy as np
def circ_deg(a,b): return np.abs((np.asarray(a)-np.asarray(b)+math.pi)%(2*math.pi)-math.pi)*180/math.pi
def augrc(err,conf):
 order=np.argsort(-np.asarray(conf));e=np.asarray(err)[order];risk=np.cumsum(e)/np.arange(1,len(e)+1);cov=np.arange(1,len(e)+1)/len(e);return float(np.trapz(risk,cov))
def ece(err,conf,bins=15):
 e,c=np.asarray(err),np.asarray(conf);out=0.
 for x in np.array_split(np.argsort(c),bins):
  if len(x):out+=len(x)/len(c)*abs(c[x].mean()-(1-e[x]).mean())
 return float(out)
def summary(phi,pred,prob,confidence,nll=None):
 err=circ_deg(phi,pred);binary=(err>=90).astype(float);p=np.clip(np.asarray(prob),1e-6,1-1e-6)
 return {'accuracy':float((err<90).mean()),'mean_circular_error_deg':float(err.mean()),'median_circular_error_deg':float(np.median(err)),'nll':float(np.mean(nll) if nll is not None else -np.log(p).mean()),'brier':float(np.mean((p-(err<90))**2)),'ece':ece(binary,confidence),'augrc':augrc(binary,confidence),'n':int(len(err))}
