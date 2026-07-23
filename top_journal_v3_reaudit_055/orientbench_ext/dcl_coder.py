"""Project-local DCLCoder (Densely Coded Labels, BCL variant) for the R1 angle-head matrix.

Reference: Yang et al., "Dense Label Encoding for Boundary Discontinuity Free Rotation
Detection" (DCL). The dense (binary) coding maps the discretised angle bin index into
ceil(log2(N)) bits instead of CSL's N-way one-hot, shrinking the angle branch.

We implement the BCL (Binary Coded Label) variant and mirror the exact interface of
mmrotate's CSLCoder/PSCCoder (encode_size attr; encode(angle)->(M,encode_size);
decode(preds, keepdim)->(M,1)|(M,)). Registered into mmrotate's TASK_UTILS registry so
configs referencing type='DCLCoder' resolve. NOT installed into third_party.

Provenance note: this is a project-local reimplementation, gated by a round-trip unit test
(test_dcl_coder.py). DCL cells carry head_impl='project_local_BCL' in the matrix; no
mechanism conclusion is drawn from a single implementation without the pre-registered matrix.
"""
import math
import torch
from torch import Tensor
from mmdet.models.task_modules.coders.base_bbox_coder import BaseBBoxCoder
from mmrotate.registry import TASK_UTILS


@TASK_UTILS.register_module()
class DCLCoder(BaseBBoxCoder):
    """Densely Coded Label (Binary Coded Label) angle coder.

    Args:
        angle_version (str): 'oc' | 'le90' | 'le135'.
        omega (float): angle discretisation granularity in degrees. Default 1.
    """

    def __init__(self, angle_version: str = 'le90', omega: float = 1.0):
        super().__init__()
        assert angle_version in ['oc', 'le90', 'le135']
        self.angle_version = angle_version
        self.angle_range = 90 if angle_version == 'oc' else 180
        self.angle_offset = {'oc': 0, 'le90': 90, 'le135': 45}[angle_version]
        self.omega = omega
        self.num_bins = int(self.angle_range // omega)
        # bits needed to index num_bins-1
        self.encode_size = max(1, int(math.ceil(math.log2(self.num_bins))))
        # LSB-first bit weights, registered as a buffer-free constant tensor
        self._bit_weights = torch.tensor(
            [1 << b for b in range(self.encode_size)], dtype=torch.float32)

    def _to_index(self, angle_targets: Tensor) -> Tensor:
        deg = angle_targets * (180.0 / math.pi)
        idx = ((deg + self.angle_offset) / self.omega).floor().long()
        return idx.clamp(0, self.num_bins - 1)

    def encode(self, angle_targets: Tensor) -> Tensor:
        """(M,1) radians -> (M, encode_size) binary code in {0.,1.} (LSB first)."""
        idx = self._to_index(angle_targets)  # (M,1)
        bit_pos = torch.arange(self.encode_size, device=angle_targets.device)
        bits = (idx >> bit_pos) & 1  # broadcast (M, encode_size)
        return bits.to(angle_targets.dtype)

    def decode(self, angle_preds: Tensor, keepdim: bool = False) -> Tensor:
        """(M, encode_size) logits -> angle (radians). Bit set iff logit > 0."""
        if angle_preds.shape[0] == 0:
            shape = list(angle_preds.size())
            if keepdim:
                shape[-1] = 1
            else:
                shape = shape[:-1]
            return angle_preds.new_zeros(shape)
        w = self._bit_weights.to(angle_preds)
        bits = (angle_preds > 0).to(angle_preds.dtype)
        idx = torch.sum(bits * w, dim=-1, keepdim=keepdim)
        angle = ((idx + 0.5) * self.omega) % self.angle_range - self.angle_offset
        return angle * (math.pi / 180.0)
