#!/usr/bin/env python3
"""G1 source LODO admission for the monotone additive GR-EQS selector.

All model inputs come from sealed prediction-time feature parquet files.  GT
labels are read only after source/target folds are specified; the held-out
dataset never participates in fitting or hyperparameter selection.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
import numpy as np, pandas as pd, torch

ROOT=Path(__file__).resolve().parents[2]
import sys;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc,risk_at_coverage
RUNTIME=ROOT/'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
UNITS={'A':('DIOR-R','dior22'),'B':('DIOR-R','dior3'),'C':('DIOR-R','dior61'),'D':('FAIR1M-v1.0','fair24'),'E':('SODA-A','soda23'),'F':('SODA-A','soda4')}
DATASETS=('DIOR-R','FAIR1M-v1.0','SODA-A')
# Positive features have non-decreasing risk.  Score/support/margin are
# sign-normalized so their positive coefficients implement non-increasing risk.
POS=('neg_logit_score','missing_fraction','u_axis','iou_loss','axial_dispersion','center_dispersion','side_dispersion','score_dispersion','neg_association_margin','neg_support_fraction')
FREE=('log_pred_ar','half_log_pred_area')

def nrc(score,risk): return float(nrc_auc(np.asarray(score),np.asarray(risk))['nrc_auc'])
def load(key,labels=True):
 f=pd.read_parquet(RUNTIME/'features'/f'{key}.parquet'); f['unit']=key;f['dataset']=UNITS[key][0]
 f['neg_logit_score']=-f.logit_score;f['neg_association_margin']=-f.association_margin;f['neg_support_fraction']=-f.support_fraction
 if not labels:return f
 y=pd.read_parquet(RUNTIME/'labels'/f'{key}.parquet')
 return f.merge(y,on=['image_id','pred_id','class_id'],how='inner',validate='one_to_one')
def attach_audit_labels(feature_frame,key):
 """Attach outcome labels only after a held-out score has been sealed."""
 y=pd.read_parquet(RUNTIME/'labels'/f'{key}.parquet')
 return feature_frame.merge(y,on=['image_id','pred_id','class_id'],how='inner',validate='one_to_one')
def raw_eqs(f):
 # The frozen standalone EQS comparator is intentionally training-free.  Do
 # not let later GR-EQS inputs leak into this primary baseline.
 return f.u_axis+f.missing_fraction+f.iou_loss
class Model(torch.nn.Module):
 def __init__(self):
  super().__init__();self.raw=torch.nn.Parameter(torch.zeros(len(POS)));self.free=torch.nn.Parameter(torch.zeros(len(FREE)));self.bias=torch.nn.Parameter(torch.zeros(1))
 def forward(self,xp,xf): return xp@torch.nn.functional.softplus(self.raw)+xf@self.free+self.bias
def fit(frame,seed,l2,steps=240):
 torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
 # fixed source-only robust scaling preserves every monotonic direction.
 med=frame[list(POS)+list(FREE)].median(); scale=(frame[list(POS)+list(FREE)].quantile(.9)-frame[list(POS)+list(FREE)].quantile(.1)).clip(lower=1e-5)
 x=((frame[list(POS)+list(FREE)]-med)/scale).clip(-8,8);xp=torch.tensor(x[list(POS)].values,dtype=torch.float32);xf=torch.tensor(x[list(FREE)].values,dtype=torch.float32);y=torch.tensor(frame.risk.values,dtype=torch.float32)
 groups=[np.where(frame.unit.values==u)[0] for u in sorted(frame.unit.unique())]
 m=Model();o=torch.optim.Adam(m.parameters(),lr=.05,weight_decay=l2)
 for step in range(steps):
  losses=[]
  for ix in groups:
   # NumPy legacy MT19937 requires a uint32 seed; preserve the deterministic
   # schedule while folding the composite seed into that valid domain.
   rng=np.random.RandomState((seed*1000003+step*97+len(ix)) % (2**32)); a=rng.choice(ix,min(4096,len(ix)),replace=len(ix)<4096);b=rng.choice(ix,len(a),replace=len(ix)<len(a))
   target=torch.sign(y[a]-y[b]);keep=target!=0
   if keep.any(): losses.append(torch.nn.functional.softplus(-target[keep]*(m(xp[a[keep]],xf[a[keep]])-m(xp[b[keep]],xf[b[keep]]))).mean())
  loss=torch.stack(losses).max();o.zero_grad();loss.backward();o.step()
 return m,med,scale
def predict(frame,fitobj):
 m,med,scale=fitobj;x=((frame[list(POS)+list(FREE)]-med)/scale).clip(-8,8);m.eval()
 with torch.no_grad(): return m(torch.tensor(x[list(POS)].values,dtype=torch.float32),torch.tensor(x[list(FREE)].values,dtype=torch.float32)).numpy()
def save_fit(path,fitobj,meta):
 m,med,scale=fitobj
 torch.save({'state_dict':m.state_dict(),'median':med.to_dict(),'scale':scale.to_dict(),
             'positive_features':POS,'free_features':FREE,'metadata':meta},path)
def boot(frame,base,gr,seed,reps=10000):
 clu=frame.cluster.astype(str).values;uniq=np.unique(clu);loc={u:np.flatnonzero(clu==u) for u in uniq};seeds=np.random.RandomState(seed).randint(0,2**31-1,reps);risk=frame.risk.values;out=np.empty(reps);d70=np.empty(reps);d90=np.empty(reps)
 for k,s in enumerate(seeds):
  ix=np.concatenate([loc[z] for z in np.random.RandomState(int(s)).choice(uniq,len(uniq),replace=True)])
  out[k]=nrc(-base[ix],risk[ix])-nrc(-gr[ix],risk[ix])
  d70[k]=risk_at_coverage(-base[ix],risk[ix],.7)-risk_at_coverage(-gr[ix],risk[ix],.7)
  d90[k]=risk_at_coverage(-base[ix],risk[ix],.9)-risk_at_coverage(-gr[ix],risk[ix],.9)
 return seeds,out,d70,d90
def metric(frame,risk):
 # selector convention: higher score is safer
 s=-np.asarray(risk);y=frame.risk.values
 return dict(NRC=nrc(s,y),AUGRC=float(aurc(s,y)),Risk70=float(risk_at_coverage(s,y,.7)),Risk90=float(risk_at_coverage(s,y,.9)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--reps',type=int,default=10000);a=p.parse_args();out=RUNTIME/'g1';out.mkdir(exist_ok=True)
 # Prediction-time feature frames are available for all datasets.  Labels are
 # deliberately loaded per outer fold below: source labels for fitting first,
 # then held-out labels only after that fold's complete scores are persisted.
 features={k:load(k,labels=False) for k in UNITS}; rows=[];draws=[]
 # Nested LODO over the two source datasets chooses l2 solely on source folds.
 for held in DATASETS:
  sources=[d for d in DATASETS if d!=held]; candidates=(1e-5,1e-3,1e-1);chosen=[]
  frames={k:attach_audit_labels(features[k],k) for k in UNITS if UNITS[k][0] in sources}
  for seed in (20260830,20260831,20260832):
   validation=[]
   for l2 in candidates:
    vals=[]
    for val in sources:
     train=pd.concat([f[f.role=='D_cal-fit'] for k,f in frames.items() if UNITS[k][0] in sources and UNITS[k][0]!=val]);test=pd.concat([f[f.role=='D_cal-calib'] for k,f in frames.items() if UNITS[k][0]==val])
     gr=predict(test,fit(train,seed,l2));vals.append(nrc(-raw_eqs(test),test.risk)-nrc(-gr,test.risk))
    validation.append((min(vals),l2))
   l2=max(validation)[1];chosen.append(l2)
   train=pd.concat([f[f.role.isin(('D_cal-fit','D_cal-calib'))] for k,f in frames.items() if UNITS[k][0] in sources]);fitobj=fit(train,seed,l2)
   # Lambda is determined using source calibration outcomes only, then frozen
   # before any held-out score is emitted.
   source_cal=pd.concat([f[(UNITS[k][0] in sources)&(f.role=='D_cal-calib')] for k,f in frames.items()])
   source_risk=predict(source_cal,fitobj);lambda_grid=(0.0,.05,.10,.25,.50,1.0,2.0)
   lambda_scores=[]
   for lam0 in lambda_grid:
    fusion=source_cal.logit_score.values-lam0*source_risk
    lambda_scores.append((min(nrc(fusion[source_cal.dataset.values==d],source_cal.risk.values[source_cal.dataset.values==d]) for d in sources),lam0))
   lam=max(lambda_scores)[1]
   model_path=out/f'gr_eqs_{held.replace("/", "_")}_seed{seed}.pt'
   save_fit(model_path,fitobj,{'heldout_dataset':held,'source_datasets':sources,'seed':seed,'l2':l2,'lambda':lam,'training_rows':len(train),'lambda_objective':'source_calibration_worst_dataset_NRC'})
   for key in UNITS:
    if UNITS[key][0]!=held:continue
    sealed=features[key].copy();sealed_gr=predict(sealed,fitobj)
    sealed[['image_id','pred_id','class_id','detection_score','logit_score']].assign(predicted_risk=sealed_gr,fusion_score=sealed.logit_score.values-lam*sealed_gr,heldout_dataset=held,seed=seed,lambda_=lam).to_parquet(out/f'sealed_scores_{held.replace("/", "_")}_{key}_seed{seed}.parquet',index=False,compression='zstd')
    # Only now is the held-out label table read and attached for audit.
    test=attach_audit_labels(sealed,key);test=test[test.role=='D_audit'].copy();gr=predict(test,fitobj);base=raw_eqs(test).values;dseed=seed+ord(key)*1009;seeds,delta,d70,d90=boot(test,base,gr,dseed,a.reps)
    bm=metric(test,base);gm=metric(test,gr);row=dict(heldout_dataset=held,unit=key,seed=seed,n=len(test),clusters=test.cluster.nunique(),l2=l2,lambda_=lam,delta_NRC=bm['NRC']-gm['NRC'],ci_low=float(np.quantile(delta,.025)),ci_high=float(np.quantile(delta,.975)),risk70_ci_low=float(np.quantile(d70,.025)),risk90_ci_low=float(np.quantile(d90,.025)),**{f'standalone_{k}':v for k,v in bm.items()},**{f'gr_eqs_{k}':v for k,v in gm.items()});rows.append(row)
    draws.extend(dict(heldout_dataset=held,unit=key,seed=seed,replicate=i,draw_seed=int(s),delta_NRC=float(v),delta_Risk70=float(x),delta_Risk90=float(y)) for i,(s,v,x,y) in enumerate(zip(seeds,delta,d70,d90)))
  (out/f'nested_lodo_{held}.json').write_text(json.dumps(dict(heldout=held,seeds=[20260830,20260831,20260832],chosen_l2=chosen),indent=2)+'\n')
 pd.DataFrame(rows).to_csv(out/'g1_unit_metrics.csv',index=False);pd.DataFrame(draws).to_parquet(out/'bootstrap_replicates.parquet',index=False,compression='zstd')
 # Strict conjunction uses every held-out unit and all three seeds.
 r=pd.DataFrame(rows);checks=[]
 for held in DATASETS:
  q=r[r.heldout_dataset==held];checks.append(dict(dataset=held,delta_nrc_all=bool(((q.delta_NRC>=.02)&(q.ci_low>0)).all()),risk_noninferior=bool(((q.risk70_ci_low>=0)&(q.risk90_ci_low>=0)).all()),no_significant_reverse=bool((q.ci_high>=0).all()),seed_direction_consistent=bool((q.groupby('unit').delta_NRC.apply(lambda x:(x>0).all() or (x<0).all())).all())))
 gate=pd.DataFrame(checks);gate.to_csv(out/'g1_gate_partial.csv',index=False);print(json.dumps(dict(units=len(rows),gate=checks)))
if __name__=='__main__':main()
