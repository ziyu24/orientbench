"""Equal-budget non-PEF controls retained outside the PEF evidence path."""
from __future__ import annotations

import torch
from torch import nn
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


@MODELS.register_module()
class DirectDistributionAngleBranchRetinaHead(AngleBranchRetinaHead):
    """AQE/O2-like direct periodic distribution control; no resampling grid."""
    def _init_layers(self):
        super()._init_layers()
        self.direct_distribution = nn.Conv2d(self.feat_channels, self.num_anchors * 12, 3, padding=1)

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        return cls, bbox, angle, self.direct_distribution(x)

    def loss_by_feat(self, cls, bbox, angle, direct, *args, **kwargs):
        return super().loss_by_feat(cls, bbox, angle, *args, **kwargs)

    def predict_by_feat(self, cls, bbox, angle, direct, **kwargs):
        return super().predict_by_feat(cls, bbox, angle, **kwargs)


@MODELS.register_module()
class ScalarQualityAngleBranchRetinaHead(AngleBranchRetinaHead):
    """PQA-like scalar-quality control; explicitly not a PEF energy field."""
    def _init_layers(self):
        super()._init_layers()
        self.scalar_quality = nn.Conv2d(self.feat_channels, self.num_anchors, 3, padding=1)

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        return cls, bbox, angle, self.scalar_quality(x)

    def loss_by_feat(self, cls, bbox, angle, scalar, *args, **kwargs):
        return super().loss_by_feat(cls, bbox, angle, *args, **kwargs)

    def predict_by_feat(self, cls, bbox, angle, scalar, **kwargs):
        return super().predict_by_feat(cls, bbox, angle, **kwargs)
