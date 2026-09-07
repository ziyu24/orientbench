"""A conditional future-prediction distribution, integrated under the frozen loss.

All query APIs accept only the current first-model map and nominal look geometry.
Candidate probabilities and labels occur only in fitting or outcome measurement.
"""
import numpy as np
from orientbench.r017.measurement import weighted_log_loss

BINS, CONTEXTS = 16, 80


def context(p, look):
    p=np.asarray(p,dtype=np.float64)
    if p.ndim!=2 or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
        raise ValueError('complete finite first-view probability map required')
    gy,gx=np.gradient(p)
    magnitude=np.hypot(gx,gy)
    east,north=np.asarray(look,dtype=float)
    denom=np.maximum(magnitude*np.hypot(east,north),1e-12)
    cosine2=((gx*east-gy*north)/denom)**2
    direction=np.minimum((np.clip(cosine2,0,1)*4).astype(int),3)
    direction[magnitude<.01]=4
    bins=np.minimum((p*16).astype(int),15)
    return bins*5+direction


def joint_counts(p,q,y,look):
    if p.shape!=q.shape or p.shape!=y.shape or not np.isin(y,[0,1]).all():
        raise ValueError('same-grid future probabilities and binary training labels required')
    if not np.isfinite(q).all() or np.any((q<0)|(q>1)):
        raise ValueError('invalid future probabilities')
    c=context(p,look)[4::8,4::8]
    qb=np.minimum((np.asarray(q)[4::8,4::8]*16).astype(int),15)
    label=y[4::8,4::8].astype(int)
    index=c*32+label*16+qb
    return np.bincount(index.ravel(),minlength=80*32).reshape(80,2,16).astype(float)


def risk(p,q,y,pi,sampled=False):
    if sampled:
        p,q,y=[x[4::8,4::8] for x in (p,q,y)]
    return weighted_log_loss((p.astype(float)+q.astype(float))/2,y,np.ones(y.shape,bool),pi)


def features(p,first,second):
    p=np.asarray(p,dtype=float)
    gy,gx=np.gradient(p)
    g=np.r_[first,second]
    histogram=np.histogram(p,bins=np.linspace(0,1,17))[0]/p.size
    return np.r_[g,g*g,[g[i]*g[j] for i in range(4) for j in range(i)],histogram,
                 np.mean(np.hypot(gx,gy)),np.mean(gx*gx-gy*gy),np.mean(2*gx*gy)]


class Transport:
    def __init__(self,geometry,counts,pair_risk,pi):
        self.geometry=np.asarray(geometry,dtype=float)
        self.n=len(self.geometry)
        self.pairs=np.array([(i,j) for i in range(self.n) for j in range(self.n)])
        self.pair_geometry=np.array([np.r_[self.geometry[i],self.geometry[j]] for i,j in self.pairs])
        self.counts=np.asarray(counts,dtype=float).reshape(self.n*self.n,80,2,16)
        self.pair_risk=np.asarray(pair_risk).reshape(-1)
        self.pi=pi
        self.prior=self.counts.sum(axis=(0,1))
        self.prior=self.prior/self.prior.sum()
        self.cache={}
        self.bias={name:0. for name in ('transport','independence','geometry','ridge')}
        centers=(np.arange(16)+.5)/16
        first=np.repeat(centers,5)[:,None,None]
        second=centers[None,None,:]
        label=np.arange(2)[None,:,None]
        fused=(first+second)/2
        weights=np.where(label==1,1/(2*pi),1/(2*(1-pi)))
        self.loss_tensor=weights*(-label*np.log(fused)-(1-label)*np.log1p(-fused))

    def kernel(self,first,second,same):
        d=((self.pair_geometry-np.r_[first,second])**2).sum(1)/(.25**2*2)
        allowed=(self.pairs[:,0]==self.pairs[:,1]) if same else (self.pairs[:,0]!=self.pairs[:,1])
        logits=-d[allowed]
        weights=np.exp(logits-logits.max())
        weights/=weights.sum()
        return allowed,weights

    def conditional_risk(self,first,second,same,independence=False):
        key=(tuple(first),tuple(second),same,independence)
        if key not in self.cache:
            allowed,w=self.kernel(first,second,same)
            counts=np.einsum('i,icyd->cyd',w,self.counts[allowed])+32*self.prior[None]
            distribution=counts/counts.sum(axis=(1,2),keepdims=True)
            if independence:
                distribution=distribution.sum(2,keepdims=True)*distribution.sum(1,keepdims=True)
            self.cache[key]=(distribution*self.loss_tensor).sum(axis=(1,2))
        return self.cache[key]

    def fit_ridge(self,x,y):
        x,y=np.asarray(x),np.asarray(y)
        self.xmean=x.mean(0)
        self.xscale=np.maximum(x.std(0),1e-6)
        z=(x-self.xmean)/self.xscale
        self.ymean=float(y.mean())
        self.coef=np.linalg.solve(z.T@z/len(z)+.01*np.eye(z.shape[1]),z.T@(y-self.ymean)/len(z))

    def predict(self,p,first,second):
        # No future probabilities, truth, tile IDs or acquisition IDs in this API.
        h_same=np.bincount(context(p,first).ravel(),minlength=80)/p.size
        h_new=np.bincount(context(p,second).ravel(),minlength=80)/p.size
        out={}
        for name,ind in (('transport',False),('independence',True)):
            out[name]=float(h_same@self.conditional_risk(first,first,True,ind)-
                            h_new@self.conditional_risk(first,second,False,ind))+self.bias[name]
        a,wa=self.kernel(first,first,True)
        b,wb=self.kernel(first,second,False)
        out['geometry']=float(wa@self.pair_risk[a]-wb@self.pair_risk[b])+self.bias['geometry']
        z=(features(p,first,second)-self.xmean)/self.xscale
        out['ridge']=float(z@self.coef+self.ymean)+self.bias['ridge']
        return out

    def save(self,path):
        np.savez_compressed(path,geometry=self.geometry,counts=self.counts,pair_risk=self.pair_risk,
                            pi=self.pi,prior=self.prior,xmean=self.xmean,xscale=self.xscale,coef=self.coef,ymean=self.ymean,
                            bias_names=np.array(list(self.bias)),bias_values=np.array(list(self.bias.values())))


def choose(scores,anchor):
    """Stop wins ties at zero; otherwise first fixed candidate order wins ties."""
    action,best=anchor,0.
    for candidate,gain in scores.items():
        if not np.isfinite(gain):
            raise ValueError('nonfinite forecast')
        if gain>best:
            action,best=candidate,gain
    return action


def evaluate_policies(costs,scores,anchor,geometry):
    names=('transport','independence','geometry','ridge')
    out={name:costs[choose({j:s[name] for j,s in scores.items()},anchor)] for name in names}
    out['stop']=costs[anchor]
    candidates=[j for j in costs if j!=anchor]
    far=max(candidates,key=lambda j:np.linalg.norm(np.asarray(geometry[anchor])-geometry[j]))
    nadir=min(costs,key=lambda j:np.linalg.norm(geometry[j]))
    out['max_separation'],out['near_nadir']=costs[far],costs[nadir]
    out['oracle']=min(costs.values())
    for name in names:
        out['mae_'+name]=float(np.mean([abs(s[name]-(costs[anchor]-costs[j])) for j,s in scores.items()]))
        out['bias_'+name]=float(np.mean([s[name]-(costs[anchor]-costs[j]) for j,s in scores.items()]))
        out['acquire_'+name]=float(choose({j:s[name] for j,s in scores.items()},anchor)!=anchor)
    return out


def block_summary(rows,tiles,anchors=range(4)):
    block=lambda t:tuple(int(v)//2700 for v in t.split('_'))
    blocks=list(dict.fromkeys(map(block,tiles)))
    lookup={(r['tile'],r['anchor']) for r in rows}
    if len(lookup)!=len(rows) or lookup!={(t,a) for t in tiles for a in anchors}:
        raise ValueError('incomplete fixed region table')
    keys=[k for k in rows[0] if k not in ('tile','anchor')]
    values={k:np.array([np.mean([np.mean([r[k] for r in rows if r['tile']==t]) for t in tiles if block(t)==b])
                       for b in blocks]) for k in keys}
    index=np.random.Generator(np.random.PCG64(17021)).integers(0,len(blocks),(20000,len(blocks)))
    return {'blocks':blocks,'means':{k:float(v.mean()) for k,v in values.items()},
            'block_values':{k:v.tolist() for k,v in values.items()},
            'intervals_97_5':{k:np.quantile(v[index].mean(1),[.0125,.9875]).tolist() for k,v in values.items()},
            'scope':'Region mean over anchors, equal geographic blocks; fixed products from one pass. Two coprimary intervals use Bonferroni approximate bootstrap; others descriptive.'}
