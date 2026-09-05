"""Fixed r015 backbone construction and paired ImageNet initialization."""
from __future__ import annotations
from pathlib import Path
import torch
from torch import nn
from torchvision.models import resnet50,vit_b_16
from torchvision.models.vision_transformer import interpolate_embeddings

INIT=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization')
class Heads(nn.Module):
 def __init__(self,kind,size):
  super().__init__();self.kind,self.size=kind,size
  self.backbone=resnet50(weights=None) if kind=='resnet50' else vit_b_16(weights=None,image_size=size)
  width=self.backbone.fc.in_features if kind=='resnet50' else self.backbone.heads.head.in_features
  if kind=='resnet50':self.backbone.fc=nn.Identity()
  else:self.backbone.heads=nn.Identity()
  self.heads=nn.ModuleList([nn.Linear(width,2) for _ in range(3)])
 def forward(self,x):
  z=self.backbone(x);return torch.stack([head(z) for head in self.heads],1)
def initialize(model):
 path=INIT/('resnet50-11ad3fa6.pth' if model.kind=='resnet50' else 'vit_b_16-c867db91.pth')
 state=torch.load(path,map_location='cpu',weights_only=True)
 if model.kind=='resnet50':
  state.pop('fc.weight');state.pop('fc.bias')
 else:
  state.pop('heads.head.weight');state.pop('heads.head.bias')
  if model.size!=224:state=interpolate_embeddings(model.size,16,state,interpolation_mode='bicubic',reset_heads=False)
 model.backbone.load_state_dict(state,strict=True)
 return path
