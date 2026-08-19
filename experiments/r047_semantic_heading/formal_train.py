#!/usr/bin/env python3
"""R047 formal four-arm semantic-heading training (train/val only).

This deliberately does not enumerate or parse the HRSC official-test XMLs.
"""
import argparse, json, math, os, random, time, xml.etree.ElementTree as ET
from pathlib import Path
import cv2, numpy as np, torch
import sys
# The registered checkpoint was serialized with NumPy 2; mr/torch uses NumPy 1.x.
# These aliases are read-only compatibility shims for torch.load.
if not hasattr(np, '_core'):
    sys.modules.setdefault('numpy._core', np.core)
    sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
    sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import Dataset, DataLoader, DistributedSampler
from torchvision.models import resnet50

DATA = Path('/home/rspip/cqc/data/dataset/HRSC2016')
PTH = Path('/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth')
MEAN = torch.tensor([123.675,116.28,103.53]).view(3,1,1)
STD = torch.tensor([58.395,57.12,57.375]).view(3,1,1)

def rows(split):
    out=[]
    for iid in (DATA/'splits'/f'{split}.txt').read_text().split():
        root=ET.parse(DATA/'annfiles'/f'{iid}.xml').getroot()
        for o in root.findall('HRSC_Objects/HRSC_Object'):
            def f(k): return float(o.find(k).text)
            cx,cy,w,h,a,hx,hy=[f(k) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang','header_x','header_y')]
            if h>w: w,h,a=h,w,a+math.pi/2
            a=(a+math.pi/2)%math.pi-math.pi/2; dx,dy=hx-cx,hy-cy; ux,uy=math.cos(a),math.sin(a)
            if math.hypot(dx,dy)<.1*w or abs(dx*ux+dy*uy)<.1*w: continue
            out.append((iid,cx,cy,w,h,a,int(dx*ux+dy*uy>0)))
    return out

def crop(r, aug=False):
    iid,cx,cy,w,h,a,y=r; im=cv2.imread(str(DATA/'images'/f'{iid}.bmp'))
    if aug:
        j=(random.uniform(-.05,.05)*w,random.uniform(-.05,.05)*h); cx+=j[0];cy+=j[1]
        s=random.uniform(.9,1.1); w*=s;h*=s;a+=math.radians(random.uniform(-10,10))
    M=cv2.getRotationMatrix2D((cx,cy),math.degrees(a),1); M[0,2]+=96-cx; M[1,2]+=32-cy
    z=cv2.warpAffine(im,M,(192,64),borderMode=cv2.BORDER_REFLECT)
    z=cv2.cvtColor(z,cv2.COLOR_BGR2RGB); z=torch.from_numpy(z.copy()).permute(2,0,1).float()
    z=(z-MEAN)/STD
    if aug and random.random()<.5: z=torch.flip(z,[2]); y=1-y
    return z[:,:,:64],z[:,:,128:],z,torch.tensor(y,dtype=torch.float32)

class DS(Dataset):
    def __init__(self, rr, aug=False): self.rr,self.aug=rr,aug
    def __len__(self): return len(self.rr)
    def __getitem__(self,i): return crop(self.rr[i],self.aug)

def load_backbone():
    b=resnet50(weights=None)
    x=torch.load(PTH,map_location='cpu'); s=x['state_dict']; mapped={}
    for k,v in s.items():
        if k.startswith('backbone.'):
            q=k[9:]
            if q in b.state_dict() and b.state_dict()[q].shape==v.shape: mapped[q]=v
    miss,unexpected=b.load_state_dict(mapped,strict=False)
    if len(mapped)<200 or any(k.startswith(('conv1','layer1','layer2','layer3','layer4')) for k in miss):
        raise RuntimeError(f'backbone mapping failed mapped={len(mapped)} missing={miss[:8]}')
    for n,p in b.named_parameters():
        if n.startswith(('conv1','bn1','layer1','layer2','layer3')) or n.startswith('fc.'):
            p.requires_grad=False
    for m in b.modules():
        if isinstance(m,nn.BatchNorm2d): m.eval()
    return b,{'mapped_tensors':len(mapped),'missing_keys':miss,'unexpected_keys':unexpected}

class Arm(nn.Module):
    def __init__(self,mode):
        super().__init__(); self.mode=mode; self.b=load_backbone()[0]
        if mode=='AHC': self.head=nn.Linear(2048,1,bias=False)
        elif mode=='WHOLE_CROP': self.head=nn.Linear(2048,1)
        elif mode=='CONCAT_ENDPOINT': self.head=nn.Linear(4096,1)
        elif mode=='HEADPOINT_REG': self.head=nn.Linear(2048,2)
        else: raise ValueError(mode)
    def feat(self,x):
        x=self.b.relu(self.b.bn1(self.b.conv1(x)))
        x=self.b.maxpool(x); x=self.b.layer1(x); x=self.b.layer2(x)
        x=self.b.layer3(x); x=self.b.layer4(x)
        return self.b.avgpool(x).flatten(1)
    def forward(self,minus,plus,whole):
        if self.mode=='AHC': return self.head(self.feat(plus)-self.feat(minus)).squeeze(1)
        if self.mode=='WHOLE_CROP': return self.head(self.feat(whole)).squeeze(1)
        if self.mode=='CONCAT_ENDPOINT': return self.head(torch.cat([self.feat(minus),self.feat(plus)],1)).squeeze(1)
        return self.head(self.feat(whole))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',required=True,choices=['AHC','WHOLE_CROP','CONCAT_ENDPOINT','HEADPOINT_REG']); ap.add_argument('--out',required=True); ap.add_argument('--epochs',type=int,default=30); ap.add_argument('--smoke',action='store_true'); a=ap.parse_args()
    rank=int(os.environ.get('LOCAL_RANK',0)); world=int(os.environ.get('WORLD_SIZE',1));
    if world>1: dist.init_process_group('nccl'); torch.cuda.set_device(rank)
    torch.manual_seed(20260818); np.random.seed(20260818); random.seed(20260818)
    dev=torch.device('cuda',rank) if torch.cuda.is_available() else torch.device('cpu')
    tr,va=rows('train'),rows('val'); ds=DS(tr,True); vd=DS(va,False)
    sm=DistributedSampler(ds,shuffle=True) if world>1 else None; dl=DataLoader(ds,batch_size=max(1,64//world),sampler=sm,shuffle=sm is None,num_workers=4,pin_memory=True)
    vdl=DataLoader(vd,batch_size=64,num_workers=4,pin_memory=True)
    m=Arm(a.mode).to(dev); m=DDP(m,device_ids=[rank]) if world>1 else m
    opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],1e-4,weight_decay=.05); scaler=torch.cuda.amp.GradScaler(enabled=dev.type=='cuda')
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); log=out/'epoch_metrics.jsonl'; best=-1; latest=None; t0=time.time(); epochs=1 if a.smoke else a.epochs
    for ep in range(epochs):
        if sm: sm.set_epoch(ep)
        m.train();
        for xminus,xplus,whole,y in dl:
            xminus,xplus,whole,y=[q.to(dev,non_blocking=True) for q in (xminus,xplus,whole,y)]
            with torch.cuda.amp.autocast(enabled=dev.type=='cuda'):
                z=m(xminus,xplus,whole); loss=(nn.functional.binary_cross_entropy_with_logits(z,y) if a.mode!='HEADPOINT_REG' else nn.functional.mse_loss(z,torch.stack([y*2-1,torch.zeros_like(y)],1)))
            opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            if a.smoke and ep==0: break
        m.eval(); n=correct=0; losses=[]
        with torch.no_grad():
            for xm,xp,w,y in vdl:
                xm,xp,w,y=[q.to(dev) for q in (xm,xp,w,y)]; z=m(xm,xp,w); pred=(z[:,0]>0 if a.mode=='HEADPOINT_REG' else z>0); correct+=int((pred==y.bool()).sum());n+=len(y); losses.append(float(loss))
        rec={'epoch':ep+1,'val_accuracy':correct/max(n,1),'val_loss':float(np.mean(losses)),'world_size':world,'cards':torch.cuda.device_count(),'seconds':time.time()-t0}
        if rank==0:
            with log.open('a') as f:f.write(json.dumps(rec)+'\n')
            torch.save((m.module if isinstance(m,DDP) else m).state_dict(),out/'latest.pt'); latest=rec
            if rec['val_accuracy']>best: best=rec['val_accuracy']; torch.save((m.module if isinstance(m,DDP) else m).state_dict(),out/'best.pt')
        if a.smoke and ep==0: break
    if world>1: dist.barrier(); dist.destroy_process_group()
    if rank==0: (out/'run_summary.json').write_text(json.dumps({'mode':a.mode,'train_instances':len(tr),'val_instances':len(va),'best_val_accuracy':best,'formal':not a.smoke,'backbone_checkpoint':str(PTH),'elapsed_seconds':time.time()-t0},indent=2)+'\n')
if __name__=='__main__': main()
